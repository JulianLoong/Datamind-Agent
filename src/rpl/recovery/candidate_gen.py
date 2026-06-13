from __future__ import annotations

import json
from typing import Any

from rpl.llm import FakeLLMClient, LLMClient, LLMRequest
from rpl.recovery.types import Candidate, ErrorContext


class CandidateParseError(ValueError):
    pass


class CandidateGenerator:
    """Generate recovery candidates via an LLM-compatible interface.

    The default client is deterministic (`FakeLLMClient`) so the M2 pipeline remains fully local
    and reproducible. A real LLM client can later be injected without changing the recovery flow.
    """

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or FakeLLMClient()

    async def generate(self, ctx: ErrorContext, k: int = 3) -> list[Candidate]:
        prompt = self.build_prompt(ctx, k)
        response = await self.llm_client.complete(LLMRequest(prompt=prompt, temperature=0.7))
        try:
            candidates = parse_candidates(response.text)
        except CandidateParseError:
            candidates = []
        if not candidates:
            candidates = deterministic_fallback_candidates(ctx)
        return pad_candidates(candidates, ctx, k)[:k]

    @staticmethod
    def build_prompt(ctx: ErrorContext, k: int) -> str:
        return (
            "You are an agent recovery expert. Generate recovery candidates as a JSON array.\n"
            f"Candidate Count: {k}\n"
            f"Task Goal: {ctx.task_goal}\n"
            f"Current Step: {ctx.step_description}\n"
            f"Failed Tool: {ctx.tool_name}\n"
            f"Tool Params: {json.dumps(ctx.tool_params, ensure_ascii=False)}\n"
            f"Error Type: {ctx.error_type}\n"
            f"Error Message: {ctx.error_message}\n"
            "Each item must contain reasoning, action, tool_name, tool_params."
        )


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
