from __future__ import annotations

import json
import re
from typing import Any

from rpl.llm.base import LLMClient, LLMRequest, LLMResponse


class FakeLLMClient(LLMClient):
    """Deterministic LLM substitute for local development and tests."""

    async def complete(self, request: LLMRequest) -> LLMResponse:
        error_type = self._extract_field(request.prompt, "Error Type")
        failed_tool = self._extract_field(request.prompt, "Failed Tool")
        tool_params = self._extract_json_field(request.prompt, "Tool Params")
        candidates = self._build_candidates(error_type, failed_tool, tool_params)
        return LLMResponse(text=json.dumps(candidates, ensure_ascii=False), tokens_used=len(request.prompt) // 4)

    def _build_candidates(
        self,
        error_type: str,
        failed_tool: str,
        tool_params: dict[str, Any],
    ) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []
        candidates.append(
            {
                "reasoning": "The failure might be transient, so retry once with unchanged parameters.",
                "action": "retry_same_tool",
                "tool_name": failed_tool,
                "tool_params": tool_params,
            }
        )
        candidates.append(
            {
                "reasoning": "No safe recovery is available within the current tool set.",
                "action": "give_up",
                "tool_name": None,
                "tool_params": None,
            }
        )
        if error_type == "invalid_json":
            repaired_text = self._repair_json_text(tool_params)
            candidates.append(
                {
                    "reasoning": "The payload is malformed JSON, so retry with a minimal valid object.",
                    "action": "repair_json_payload",
                    "tool_name": failed_tool,
                    "tool_params": {**tool_params, "text": repaired_text},
                }
            )
        elif error_type == "missing_field":
            repaired_text = self._repair_missing_field(tool_params)
            candidates.append(
                {
                    "reasoning": "The parsed object misses the requested field; add that field and retry.",
                    "action": "add_missing_json_field",
                    "tool_name": failed_tool,
                    "tool_params": {**tool_params, "text": repaired_text},
                }
            )
        elif error_type == "division_by_zero":
            expr = str(tool_params.get("expression", ""))
            candidates.append(
                {
                    "reasoning": "The expression divides by zero; replace the zero denominator.",
                    "action": "avoid_zero_division",
                    "tool_name": failed_tool,
                    "tool_params": {**tool_params, "expression": self._repair_division_by_zero(expr)},
                }
            )
        elif error_type == "not_found":
            candidates.append(
                {
                    "reasoning": "The URL fixture is missing; use a known health-check fixture.",
                    "action": "try_known_fixture",
                    "tool_name": failed_tool,
                    "tool_params": {**tool_params, "url": "https://example.test/health"},
                }
            )
        return candidates

    @staticmethod
    def _repair_json_text(tool_params: dict[str, Any]) -> str:
        field = tool_params.get("field")
        if isinstance(field, str) and field:
            return json.dumps({field: None}, ensure_ascii=False)
        return "{}"

    @staticmethod
    def _repair_missing_field(tool_params: dict[str, Any]) -> str:
        field = tool_params.get("field")
        if not isinstance(field, str) or not field:
            field = "value"
        try:
            value = json.loads(str(tool_params.get("text", "{}")))
        except json.JSONDecodeError:
            value = {}
        if not isinstance(value, dict):
            value = {}
        value[field] = None
        return json.dumps(value, ensure_ascii=False)

    @staticmethod
    def _repair_division_by_zero(expression: str) -> str:
        if "/0" in expression:
            return expression.replace("/0", "/1")
        return "1"

    @staticmethod
    def _extract_field(prompt: str, field: str) -> str:
        match = re.search(rf"^{re.escape(field)}:\s*(.*)$", prompt, flags=re.MULTILINE)
        return match.group(1).strip() if match else ""

    @staticmethod
    def _extract_json_field(prompt: str, field: str) -> dict[str, Any]:
        raw = FakeLLMClient._extract_field(prompt, field)
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        return value if isinstance(value, dict) else {}
