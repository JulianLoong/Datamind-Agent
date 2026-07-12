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
        error_message = self._extract_field(request.prompt, "Error Message")
        candidates = self._build_candidates(error_type, failed_tool, tool_params, error_message)
        return LLMResponse(
            text=json.dumps({"candidates": candidates}, ensure_ascii=False),
            tokens_used=len(request.prompt) // 4,
        )

    def _build_candidates(
        self,
        error_type: str,
        failed_tool: str,
        tool_params: dict[str, Any],
        error_message: str = "",
    ) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []
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
        elif error_type == "validation_error":
            candidates.extend(self._validation_error_candidates(failed_tool, tool_params, error_message))
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
        return candidates

    @staticmethod
    def _validation_error_candidates(
        failed_tool: str,
        tool_params: dict[str, Any],
        error_message: str,
    ) -> list[dict[str, Any]]:
        msg = error_message
        candidates: list[dict[str, Any]] = []
        if "must be a string" in msg:
            parts = msg.split("'")
            if len(parts) >= 2:
                field = parts[1]
                if field in tool_params:
                    val = tool_params[field]
                    repaired = val if isinstance(val, str) else json.dumps(val, ensure_ascii=False)
                    candidates.append(
                        {
                            "reasoning": f"Parameter '{field}' has wrong type; serialize to string.",
                            "action": "fix_param_type",
                            "tool_name": failed_tool,
                            "tool_params": {**tool_params, field: repaired},
                        }
                    )
        elif "must be one of" in msg and failed_tool == "http_request":
            candidates.append(
                {
                    "reasoning": "Method not in allowed enum; use GET.",
                    "action": "fix_enum_value",
                    "tool_name": failed_tool,
                    "tool_params": {**tool_params, "method": "GET"},
                }
            )
        elif "Unexpected properties" in msg:
            suffix = msg.split("Unexpected properties:")[-1]
            extra_names = [token.strip("' []") for token in suffix.split(",")]
            new_params = {k: v for k, v in tool_params.items() if k not in extra_names}
            candidates.append(
                {
                    "reasoning": "Unexpected parameter present; remove it.",
                    "action": "remove_extra_property",
                    "tool_name": failed_tool,
                    "tool_params": new_params,
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
