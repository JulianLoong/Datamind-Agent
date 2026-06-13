from __future__ import annotations

import random
from typing import Any

from rpl.tools.base import ToolResult


class ErrorProneMixin:
    def __init__(
        self,
        *,
        error_rate: float = 0.0,
        error_types: list[str] | None = None,
        rng: random.Random | None = None,
    ) -> None:
        self.error_rate = error_rate
        self.error_types = error_types or []
        self.rng = rng or random.Random()

    def maybe_injected_error(self) -> ToolResult | None:
        if self.error_rate <= 0 or not self.error_types:
            return None
        if self.rng.random() >= self.error_rate:
            return None
        error_type = self.rng.choice(self.error_types)
        return ToolResult.fail(error_type, f"Injected {error_type} error")


def require_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    return value
