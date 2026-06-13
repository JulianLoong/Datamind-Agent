from __future__ import annotations

from rpl.tools.builtin import build_builtin_registry
from rpl.tools.registry import ToolRegistry


def test_registry_executes_json_parse() -> None:
    registry = build_builtin_registry()

    result = registry.execute("json_parse", {"text": '{"value": 3}', "field": "value"})

    assert result.success is True
    assert result.data == 3


def test_registry_returns_validation_error() -> None:
    registry = build_builtin_registry()

    result = registry.execute("json_parse", {"field": "value"})

    assert result.success is False
    assert result.error_type == "validation_error"


def test_unknown_tool_is_normalized() -> None:
    registry = ToolRegistry()

    result = registry.execute("missing", {})

    assert result.success is False
    assert result.error_type == "tool_exception"
