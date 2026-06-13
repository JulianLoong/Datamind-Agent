from __future__ import annotations

import json
import random
from typing import Any

from rpl.tools.base import BaseTool, ToolResult
from rpl.tools.builtin.common import ErrorProneMixin


class JsonParseTool(ErrorProneMixin, BaseTool):
    def __init__(
        self,
        *,
        error_rate: float = 0.0,
        error_types: list[str] | None = None,
        rng: random.Random | None = None,
    ) -> None:
        ErrorProneMixin.__init__(self, error_rate=error_rate, error_types=error_types, rng=rng)

    @property
    def name(self) -> str:
        return "json_parse"

    @property
    def description(self) -> str:
        return "Parse JSON text and optionally extract a top-level field."

    @property
    def schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "field": {"type": "string"},
            },
            "required": ["text"],
            "additionalProperties": False,
        }

    def execute(self, **params: Any) -> ToolResult:
        if injected := self.maybe_injected_error():
            return injected
        try:
            parsed = json.loads(params["text"])
        except json.JSONDecodeError as exc:
            return ToolResult.fail("invalid_json", str(exc))

        field = params.get("field")
        if field is not None:
            if not isinstance(parsed, dict) or field not in parsed:
                return ToolResult.fail("missing_field", f"Field not found: {field}")
            return ToolResult.ok(parsed[field])
        return ToolResult.ok(parsed)
