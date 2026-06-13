from __future__ import annotations

import random
from typing import Any

from rpl.tools.base import BaseTool, ToolResult
from rpl.tools.builtin.common import ErrorProneMixin


class HttpRequestTool(ErrorProneMixin, BaseTool):
    """A deterministic mock HTTP tool for early RPL development.

    It intentionally avoids real network access. This keeps M1 tests reproducible while still
    exposing HTTP-like failure modes such as 404 and invalid response.
    """

    def __init__(
        self,
        *,
        fixtures: dict[str, Any] | None = None,
        error_rate: float = 0.0,
        error_types: list[str] | None = None,
        rng: random.Random | None = None,
    ) -> None:
        ErrorProneMixin.__init__(self, error_rate=error_rate, error_types=error_types, rng=rng)
        self.fixtures = fixtures or {
            "https://example.test/users/1": {"id": 1, "name": "Ada"},
            "https://example.test/health": {"status": "ok"},
        }

    @property
    def name(self) -> str:
        return "http_request"

    @property
    def description(self) -> str:
        return "Fetch a mock HTTP fixture by URL without real network access."

    @property
    def schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "method": {"type": "string", "enum": ["GET"]},
            },
            "required": ["url"],
            "additionalProperties": False,
        }

    def execute(self, **params: Any) -> ToolResult:
        if injected := self.maybe_injected_error():
            return injected
        method = params.get("method", "GET")
        if method != "GET":
            return ToolResult.fail("method_not_allowed", "Only GET is supported by the mock tool")
        url = params["url"]
        if url not in self.fixtures:
            return ToolResult.fail("not_found", f"No fixture for URL: {url}")
        return ToolResult.ok({"status_code": 200, "body": self.fixtures[url]})
