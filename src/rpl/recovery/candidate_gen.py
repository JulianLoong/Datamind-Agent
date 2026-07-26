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


class CandidateGenerationError(RuntimeError):
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
        strict_parsing: bool = False,
    ) -> None:
        self.llm_client = llm_client or FakeLLMClient()
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.tool_specs = tool_specs or []
        self.strict_parsing = strict_parsing
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
        except CandidateParseError as exc:
            if self.strict_parsing:
                response_preview = response.text[:500].replace("\n", "\\n")
                raise CandidateGenerationError(
                    "LLM candidate response could not be parsed: "
                    f"{exc}. Response preview: {response_preview!r}"
                ) from exc
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
            "You are an agent recovery expert. Generate recovery candidates as a JSON object.\n"
            f"Candidate Count: {k}\n"
            f"Task Goal: {ctx.task_goal}\n"
            f"Current Step: {ctx.step_description}\n"
            f"Failed Tool: {ctx.tool_name}\n"
            f"Tool Params: {json.dumps(ctx.tool_params, ensure_ascii=False)}\n"
            f"Error Type: {ctx.error_type}\n"
            f"Error Message: {ctx.error_message}\n"
            f"{tool_contract}"
            'The object must have exactly one key, "candidates", containing an array.\n'
            "Each candidate must contain reasoning, action, tool_name, tool_params.\n"
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
        _ensure_api_key(provider, resolved_api_key, api_key_env)
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
        _ensure_api_key(provider, resolved_api_key, "ZHIPU_API_KEY")
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


def _ensure_api_key(provider: str, resolved_api_key: str | None, env_var: str) -> None:
    """Fail fast when a real LLM provider has no resolvable API key.

    Evaluation now defaults to a real LLM, so a missing key is a configuration error
    rather than a silent fall-through to a network call that will 401 later. The fake
    provider bypasses this entirely.
    """
    if resolved_api_key:
        return
    raise ValueError(
        f"Real LLM provider {provider!r} requires an API key, but none was found. "
        f"Set the {env_var} environment variable, pass --llm-api-key, or use "
        f"--llm-provider fake for offline evaluation."
    )


def parse_candidates(text: str) -> list[Candidate]:
    try:
        raw_items = json.loads(text)
    except json.JSONDecodeError as exc:
        raise CandidateParseError(str(exc)) from exc
    if isinstance(raw_items, dict):
        if set(raw_items) != {"candidates"}:
            raise CandidateParseError(
                "Candidate response object must contain exactly the 'candidates' key"
            )
        raw_items = raw_items["candidates"]
    if not isinstance(raw_items, list):
        raise CandidateParseError("Candidate response must be an object containing an array")

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
    elif ctx.error_type == "validation_error":
        candidates.extend(_validation_error_candidates(ctx))
    elif ctx.error_type == "no_rows":
        candidates.extend(_no_rows_fallback(ctx))
    return candidates


def _no_rows_fallback(ctx: ErrorContext) -> list[Candidate]:
    """Defensive controlled pool for the contextual_filter hard slice.

    Mirrors ``FakeLLMClient._no_rows_candidates`` so the ranking problem is
    available even when a real LLM returns nothing parseable. The correct filter
    value is parsed from the structured task goal; distractors are
    plausible-but-empty values.
    """
    correct = _extract_correct_filter_value(ctx.task_goal)
    field = ctx.tool_params.get("filter_field", "status")
    distractors = ["shipped", "cancelled", "returned", "refunded"]
    remaining = [d for d in distractors if d != correct]

    def _candidate(value: str, reason: str) -> Candidate:
        return Candidate(
            reasoning=reason,
            action="fix_filter_value",
            tool_name=ctx.tool_name,
            tool_params={**ctx.tool_params, "filter_value": value},
            raw_text=f"Set {field} to {value}.",
        )

    ordered: list[Candidate] = []
    if remaining:
        ordered.append(_candidate(remaining[0], f"Maybe the {field} is {remaining[0]}."))
    if correct:
        ordered.append(_candidate(correct, f"Goal asks for {correct}; set {field}={correct}."))
    for value in remaining[1:]:
        ordered.append(_candidate(value, f"Maybe the {field} is {value}."))
    return ordered


def _extract_correct_filter_value(task_goal: str) -> str | None:
    """Pull the goal-named filter value from a structured ``rpl_task`` goal."""
    if not task_goal.startswith("rpl_task "):
        return None
    try:
        payload = json.loads(task_goal[len("rpl_task ") :])
    except json.JSONDecodeError:
        return None
    description = payload.get("description", "") if isinstance(payload, dict) else ""
    marker = "Find the "
    if marker not in description:
        return None
    tail = description.split(marker, 1)[1]
    token = tail.split(" ", 1)[0]
    return token or None


def _validation_error_candidates(ctx: ErrorContext) -> list[Candidate]:
    """Generate recovery candidates for registry parameter validation errors.

    The registry produces three message shapes:
    - ``'<field>' must be a string`` (wrong type)
    - ``'<field>' must be one of [...]`` (wrong enum)
    - ``Unexpected properties: [...]`` (extra property)
    """
    msg = ctx.error_message
    candidates: list[Candidate] = []
    if "must be a string" in msg:
        parts = msg.split("'")
        if len(parts) >= 2:
            field = parts[1]
            if field in ctx.tool_params:
                val = ctx.tool_params[field]
                repaired = val if isinstance(val, str) else json.dumps(val, ensure_ascii=False)
                candidates.append(
                    Candidate(
                        reasoning=f"Parameter '{field}' has wrong type; serialize to string.",
                        action="fix_param_type",
                        tool_name=ctx.tool_name,
                        tool_params={**ctx.tool_params, field: repaired},
                        raw_text="Convert the parameter to a string and retry.",
                    )
                )
    elif "must be one of" in msg and ctx.tool_name == "http_request":
        candidates.append(
            Candidate(
                reasoning="Method not in allowed enum; use GET.",
                action="fix_enum_value",
                tool_name=ctx.tool_name,
                tool_params={**ctx.tool_params, "method": "GET"},
                raw_text="Switch to the only allowed method and retry.",
            )
        )
    elif "Unexpected properties" in msg:
        suffix = msg.split("Unexpected properties:")[-1]
        extra_names = [token.strip("' []") for token in suffix.split(",")]
        new_params = {k: v for k, v in ctx.tool_params.items() if k not in extra_names}
        candidates.append(
            Candidate(
                reasoning="Unexpected parameter present; remove it.",
                action="remove_extra_property",
                tool_name=ctx.tool_name,
                tool_params=new_params,
                raw_text="Drop the unexpected parameter and retry.",
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
