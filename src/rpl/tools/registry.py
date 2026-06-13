from __future__ import annotations

import time
from typing import Any

from rpl.tools.base import BaseTool, ToolResult


class ParameterValidationError(ValueError):
    pass


def validate_params(params: dict[str, Any], schema: dict[str, Any]) -> None:
    required = schema.get("required", [])
    for field in required:
        if field not in params:
            raise ParameterValidationError(f"'{field}' is a required property")

    if schema.get("additionalProperties") is False:
        allowed = set(schema.get("properties", {}).keys())
        extra = set(params.keys()) - allowed
        if extra:
            raise ParameterValidationError(f"Unexpected properties: {sorted(extra)}")

    properties = schema.get("properties", {})
    for field, value in params.items():
        spec = properties.get(field, {})
        expected_type = spec.get("type")
        if expected_type == "string" and not isinstance(value, str):
            raise ParameterValidationError(f"'{field}' must be a string")
        enum = spec.get("enum")
        if enum is not None and value not in enum:
            raise ParameterValidationError(f"'{field}' must be one of {enum}")


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, tool_name: str) -> BaseTool:
        try:
            return self._tools[tool_name]
        except KeyError as exc:
            raise KeyError(f"Unknown tool: {tool_name}") from exc

    def execute(self, tool_name: str, params: dict[str, Any] | None = None) -> ToolResult:
        params = params or {}
        started = time.perf_counter()
        try:
            tool = self.get(tool_name)
            validate_params(params, tool.schema)
            result = tool.execute(**params)
            result.latency_ms = result.latency_ms or (time.perf_counter() - started) * 1000
            return result
        except ParameterValidationError as exc:
            return ToolResult.fail(
                "validation_error",
                f"Invalid parameters for {tool_name}: {exc}",
                latency_ms=(time.perf_counter() - started) * 1000,
            )
        except Exception as exc:  # defensive normalization for tool bugs
            return ToolResult.fail(
                "tool_exception",
                f"{type(exc).__name__}: {exc}",
                latency_ms=(time.perf_counter() - started) * 1000,
            )

    def list_tools(self) -> list[BaseTool]:
        return list(self._tools.values())
