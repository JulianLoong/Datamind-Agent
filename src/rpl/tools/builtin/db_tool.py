from __future__ import annotations

import random
from typing import Any

from rpl.tools.base import BaseTool, ToolResult
from rpl.tools.builtin.common import ErrorProneMixin

# Deterministic mock fixtures. Each table is deliberately populated for a
# *restricted* set of filter values, so that a wrong-but-plausible filter_value
# (e.g. status="shipped" on orders) matches no rows and the tool returns
# ``no_rows`` instead of silently succeeding. This makes the tool the oracle of
# recovery correctness: candidate ranking changes the outcome.
# Deterministic mock latency. A constant (instead of wall-clock) makes two
# failing candidates share an identical outcome rank_key, so preference-pair
# extraction skips meaningless fail-vs-fail pairs and only emits
# success-over-failure pairs (the real goal -> value signal).
_FIXED_LATENCY_MS = 1.0


_DB_FIXTURES: dict[str, list[dict[str, Any]]] = {
    "orders": [
        {"id": 1, "customer": 42, "status": "pending", "total": 100},
        {"id": 2, "customer": 42, "status": "processing", "total": 55},
        {"id": 3, "customer": 11, "status": "pending", "total": 12},
        {"id": 4, "customer": 7, "status": "delivered", "total": 300},
        {"id": 5, "customer": 11, "status": "open", "total": 48},
        {"id": 6, "customer": 42, "status": "queued", "total": 73},
        {"id": 7, "customer": 7, "status": "invoiced", "total": 210},
    ],
    "users": [
        {"id": 1, "name": "Ada", "role": "admin"},
        {"id": 2, "name": "Lin", "role": "member"},
        {"id": 3, "name": "Gru", "role": "guest"},
        {"id": 4, "name": "Bo", "role": "member"},
    ],
    "products": [
        {"id": 1, "name": "Dune", "category": "books"},
        {"id": 2, "name": "Mouse", "category": "electronics"},
        {"id": 3, "name": "Shirt", "category": "clothing"},
        {"id": 4, "name": "Keyboard", "category": "electronics"},
    ],
}


class DbQueryTool(ErrorProneMixin, BaseTool):
    """Deterministic mock database lookup with an exact field filter.

    Avoids real storage. Returns rows only when an exact filter matches; an
    unfiltered or non-matching query fails. The intended use is the hard eval
    slice where the correct filter value is named in the task goal rather than in
    the error message, so a ranker must map goal intent -> filter value.
    """

    def __init__(
        self,
        *,
        fixtures: dict[str, list[dict[str, Any]]] | None = None,
        error_rate: float = 0.0,
        error_types: list[str] | None = None,
        rng: random.Random | None = None,
    ) -> None:
        ErrorProneMixin.__init__(self, error_rate=error_rate, error_types=error_types, rng=rng)
        self.fixtures = fixtures or _DB_FIXTURES

    @property
    def name(self) -> str:
        return "db_query"

    @property
    def description(self) -> str:
        return "Query a mock database table with an exact field filter."

    @property
    def schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "table": {"type": "string", "enum": ["users", "orders", "products"]},
                "filter_field": {"type": "string"},
                "filter_value": {"type": "string"},
                "limit": {"type": "integer"},
            },
            "required": ["table"],
            "additionalProperties": False,
        }

    def execute(self, **params: Any) -> ToolResult:
        if injected := self.maybe_injected_error():
            return injected
        table = params["table"]
        filter_field = params.get("filter_field")
        filter_value = params.get("filter_value")
        if not filter_field or filter_value is None:
            return ToolResult.fail(
                "ambiguous_filter",
                "Unfiltered query rejected; provide both filter_field and filter_value.",
                latency_ms=_FIXED_LATENCY_MS,
            )
        rows = self.fixtures.get(table, [])
        matched = [row for row in rows if str(row.get(filter_field)) == str(filter_value)]
        limit = params.get("limit")
        if isinstance(limit, int) and limit > 0:
            matched = matched[:limit]
        if not matched:
            return ToolResult.fail(
                "no_rows",
                f"No {table} matched {filter_field}={filter_value!r}.",
                latency_ms=_FIXED_LATENCY_MS,
            )
        return ToolResult.ok(
            {"table": table, "rows": matched, "count": len(matched)},
            latency_ms=_FIXED_LATENCY_MS,
        )
