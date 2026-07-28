from __future__ import annotations

import random
from typing import Any

from rpl.config import ToolSettings
from rpl.tools.builtin.db_tool import DbQueryTool
from rpl.tools.builtin.file_tool import FileReadTool
from rpl.tools.builtin.http_tool import HttpRequestTool
from rpl.tools.builtin.json_tool import JsonParseTool
from rpl.tools.builtin.math_tool import MathCalcTool
from rpl.tools.registry import ToolRegistry


def build_builtin_registry(settings: ToolSettings | None = None) -> ToolRegistry:
    settings = settings or ToolSettings()
    rng = random.Random(settings.random_seed)
    configs: dict[str, dict[str, Any]] = settings.configs

    registry = ToolRegistry()
    registry.register(JsonParseTool(rng=rng, **configs.get("json_parse", {})))
    registry.register(MathCalcTool(rng=rng, **configs.get("math_calc", {})))
    registry.register(FileReadTool(rng=rng, **configs.get("file_read", {})))
    registry.register(HttpRequestTool(rng=rng, **configs.get("http_request", {})))
    registry.register(DbQueryTool(rng=rng, **configs.get("db_query", {})))
    return registry


__all__ = [
    "DbQueryTool",
    "FileReadTool",
    "HttpRequestTool",
    "JsonParseTool",
    "MathCalcTool",
    "build_builtin_registry",
]
