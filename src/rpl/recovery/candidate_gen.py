from __future__ import annotations

import json
import os
import time
from typing import Any

from rpl.llm import FakeLLMClient, LLMClient, LLMRequest, OpenAICompatibleLLMClient
from rpl.recovery.types import Candidate, ErrorContext
from rpl.tools.base import BaseTool


class CandidateParseError(ValueError):
    pass


class CandidateGenerator:
    """Generate recovery candidates via an LLM-compatible interface.

    The default client is deterministic (`FakeLLMClient`) so the M2 pipeline remains fully local
    and reproducible. A real LLM client can later be injected without changing the recovery flow.
    """

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        *,
        temperature: float = 0.2,
        max_tokens: int = 512,
        tool_specs: list[BaseTool] | None = None,
    ) -> None:
        self.llm_client = llm_client or FakeLLMClient()
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.tool_specs = tool_specs or []
        self.last_tokens_used = 0
        self.last_latency_ms = 0.0

    async def generate(self, ctx: ErrorContext, k: int = 3) -> list[Candidate]:
        prompt = self.build_prompt(ctx, k, tool_specs=self.tool_specs)
        started = time.perf_counter()
        response = await self.llm_client.complete(
            LLMRequest(prompt=prompt, temperature=self.temperature, max_tokens=self.max_tokens)
        )
        self.last_tokens_used = response.tokens_used
        self.last_latency_ms = (time.perf_counter() - started) * 1000
        try:
            candidates = parse_candidates(response.text)
        except CandidateParseError:
            candidates = []
        if not candidates:
            candidates = deterministic_fallback_candidates(ctx)
        return pad_candidates(candidates, ctx, k)[:k]

    @staticmethod
    def build_prompt(
        ctx: ErrorContext,
        k: int,
        *,
        tool_specs: list[BaseTool] | None = None,
    ) -> str:
        tool_contract = _format_tool_contract(tool_specs or [])
        return (
            "You are an agent recovery expert. Generate recovery candidates as a JSON array.\n"
            f"Candidate Count: {k}\n"
            f"Task Goal: {ctx.task_goal}\n"
            f"Current Step: {ctx.step_description}\n"
            f"Failed Tool: {ctx.tool_name}\n"
            f"Tool Params: {json.dumps(ctx.tool_params, ensure_ascii=False)}\n"
            f"Error Type: {ctx.error_type}\n"
            f"Error Message: {ctx.error_message}\n"
            f"{tool_contract}"
            "Each item must contain reasoning, action, tool_name, tool_params.\n"
            "Return valid JSON only. Do not wrap the answer in markdown or prose.\n"
            "Use null for missing tool_name or tool_params.\n"
            "Only use tool_name values listed above. Do not invent tools.\n"
            "tool_params must satisfy the listed JSON schema exactly, including required fields "
            "and additionalProperties=false when present.\n"
            "If no listed tool can make progress, return a give_up candidate with null tool_name "
            "instead of naming an unavailable tool."
        )


def build_llm_client(
    *,
    provider: str = "fake",
    model: str | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
    api_key_env: str = "OPENAI_API_KEY",
) -> LLMClient:
    if provider == "fake":
        return FakeLLMClient()
    if provider in {"openai", "openai_compatible"}:
        resolved_model = model or os.environ.get("RPL_LLM_MODEL") or "gpt-4o-mini"
        resolved_base_url = base_url or os.environ.get("RPL_LLM_BASE_URL") or "https://api.openai.com"
        resolved_api_key = api_key or os.environ.get(api_key_env)
        return OpenAICompatibleLLMClient(
            model=resolved_model,
            base_url=resolved_base_url,
            api_path="/v1/chat/completions",
            api_key=resolved_api_key,
            api_key_env=api_key_env,
        )
    if provider in {"zhipu", "zhipu_compatible", "glm"}:
        resolved_model = model or os.environ.get("RPL_LLM_MODEL") or "glm-5.1"
        resolved_base_url = base_url or os.environ.get("RPL_LLM_BASE_URL") or "https://open.bigmodel.cn/api/paas/v4"
        resolved_api_key = api_key or os.environ.get("ZHIPU_API_KEY") or os.environ.get("GLM_API_KEY") or os.environ.get(api_key_env)
        return OpenAICompatibleLLMClient(
            model=resolved_model,
            base_url=resolved_base_url,
            api_path="/chat/completions",
            api_key=resolved_api_key,
            api_key_env="ZHIPU_API_KEY",
            extra_body={
                "thinking": {"type": "disabled"},
                "response_format": {"type": "json_object"},
            },
        )
    raise ValueError(f"Unknown LLM provider: {provider}")


def parse_candidates(text: str) -> list[Candidate]:
    try:
        raw_items = json.loads(text)
    except json.JSONDecodeError as exc:
        raise CandidateParseError(str(exc)) from exc
    if not isinstance(raw_items, list):
        raise CandidateParseError("Candidate response must be a JSON array")

    candidates: list[Candidate] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        reasoning = item.get("reasoning")
        action = item.get("action")
        tool_name = item.get("tool_name")
        tool_params = item.get("tool_params")
        if not isinstance(reasoning, str) or not isinstance(action, str):
            continue
        if tool_name is not None and not isinstance(tool_name, str):
            continue
        if tool_params is not None and not isinstance(tool_params, dict):
            continue
        candidates.append(
            Candidate(
                reasoning=reasoning,
                action=action,
                tool_name=tool_name,
                tool_params=tool_params,
                raw_text=json.dumps(item, ensure_ascii=False),
            )
        )
    if not candidates:
        raise CandidateParseError("No valid candidates found")
    return candidates


def _format_tool_contract(tool_specs: list[BaseTool]) -> str:
    if not tool_specs:
        return ""
    items = [
        {
            "name": tool.name,
            "description": tool.description,
            "schema": tool.schema,
        }
        for tool in sorted(tool_specs, key=lambda item: item.name)
    ]
    return (
        "Available Tools JSON:\n"
        f"{json.dumps(items, ensure_ascii=False, sort_keys=True)}\n"
        "Unavailable tool names are invalid.\n"
    )


def deterministic_fallback_candidates(ctx: ErrorContext) -> list[Candidate]:
    candidates: list[Candidate] = []
    if ctx.error_type == "invalid_json":
        repaired_text = _repair_json_text(ctx.tool_params)
        candidates.append(
            Candidate(
                reasoning="The JSON text is invalid; use a minimal valid object as a safe fallback.",
                action="repair_json_payload",
                tool_name=ctx.tool_name,
                tool_params={**ctx.tool_params, "text": repaired_text},
                raw_text="Replace malformed JSON with a minimal valid object and retry.",
            )
        )
    elif ctx.error_type == "missing_field":
        repaired_text = _repair_missing_field(ctx.tool_params)
        candidates.append(
            Candidate(
                reasoning="The parsed JSON lacks the requested field; add it with a null value.",
                action="add_missing_json_field",
                tool_name=ctx.tool_name,
                tool_params={**ctx.tool_params, "text": repaired_text},
                raw_text="Add the missing JSON field and retry.",
            )
        )
    elif ctx.error_type == "division_by_zero":
        expr = str(ctx.tool_params.get("expression", ""))
        candidates.append(
            Candidate(
                reasoning="The arithmetic expression divides by zero; replace /0 with /1.",
                action="avoid_zero_division",
                tool_name=ctx.tool_name,
                tool_params={**ctx.tool_params, "expression": _repair_division_by_zero(expr)},
                raw_text="Patch the expression to avoid zero division and retry.",
            )
        )
    elif ctx.error_type == "not_found":
        candidates.append(
            Candidate(
                reasoning="The mock HTTP URL is missing; try the known health endpoint.",
                action="try_known_fixture",
                tool_name=ctx.tool_name,
                tool_params={**ctx.tool_params, "url": "https://example.test/health"},
                raw_text="Use a known mock fixture URL and retry.",
            )
        )
    return candidates


def _repair_json_text(tool_params: dict[str, Any]) -> str:
    field = tool_params.get("field")
    if isinstance(field, str) and field:
        return json.dumps({field: None}, ensure_ascii=False)
    return "{}"


def _repair_missing_field(tool_params: dict[str, Any]) -> str:
    field = tool_params.get("field")
    if not isinstance(field, str) or not field:
        field = "value"
    try:
        parsed = json.loads(str(tool_params.get("text", "{}")))
    except json.JSONDecodeError:
        parsed = {}
    if not isinstance(parsed, dict):
        parsed = {}
    parsed[field] = None
    return json.dumps(parsed, ensure_ascii=False)


def _repair_division_by_zero(expression: str) -> str:
    if "/0" in expression:
        return expression.replace("/0", "/1")
    return "1"


def pad_candidates(candidates: list[Candidate], ctx: ErrorContext, k: int) -> list[Candidate]:
    padded = list(candidates)
    padded.append(
        Candidate(
            reasoning="Retry the failed tool once with the same parameters; transient errors may clear.",
            action="retry_same_tool",
            tool_name=ctx.tool_name,
            tool_params=dict(ctx.tool_params),
            raw_text="Retry the same tool with the same parameters.",
        )
    )
    while len(padded) < k:
        padded.append(
            Candidate(
                reasoning="Stop escalating and surface the error after bounded recovery attempts.",
                action="give_up",
                tool_name=None,
                tool_params=None,
                raw_text="Give up and report the current error.",
            )
        )
    return padded
