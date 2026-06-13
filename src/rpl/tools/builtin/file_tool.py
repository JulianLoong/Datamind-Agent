from __future__ import annotations

import random
from pathlib import Path
from typing import Any

from rpl.tools.base import BaseTool, ToolResult
from rpl.tools.builtin.common import ErrorProneMixin


class FileReadTool(ErrorProneMixin, BaseTool):
    def __init__(
        self,
        *,
        sandbox_dir: str | Path = "data/sandbox",
        error_rate: float = 0.0,
        error_types: list[str] | None = None,
        rng: random.Random | None = None,
    ) -> None:
        ErrorProneMixin.__init__(self, error_rate=error_rate, error_types=error_types, rng=rng)
        self.sandbox_dir = Path(sandbox_dir).resolve()

    @property
    def name(self) -> str:
        return "file_read"

    @property
    def description(self) -> str:
        return "Read a UTF-8 text file from the configured sandbox directory."

    @property
    def schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
            "additionalProperties": False,
        }

    def execute(self, **params: Any) -> ToolResult:
        if injected := self.maybe_injected_error():
            return injected
        target = (self.sandbox_dir / params["path"]).resolve()
        if not str(target).startswith(str(self.sandbox_dir)):
            return ToolResult.fail("permission_denied", "Path escapes sandbox directory")
        if not target.exists():
            return ToolResult.fail("file_not_found", f"File not found: {params['path']}")
        try:
            return ToolResult.ok(target.read_text(encoding="utf-8"))
        except PermissionError as exc:
            return ToolResult.fail("permission_denied", str(exc))
