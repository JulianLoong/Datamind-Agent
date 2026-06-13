from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ToolResult:
    success: bool
    data: Any = None
    error_type: str | None = None
    error_message: str | None = None
    tokens_used: int = 0
    latency_ms: float = 0.0

    @classmethod
    def ok(cls, data: Any = None, *, tokens_used: int = 0, latency_ms: float = 0.0) -> "ToolResult":
        return cls(success=True, data=data, tokens_used=tokens_used, latency_ms=latency_ms)

    @classmethod
    def fail(
        cls,
        error_type: str,
        error_message: str,
        *,
        data: Any = None,
        tokens_used: int = 0,
        latency_ms: float = 0.0,
    ) -> "ToolResult":
        return cls(
            success=False,
            data=data,
            error_type=error_type,
            error_message=error_message,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
        )


class BaseTool(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Stable tool name used by the agent."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description for planning and prompts."""

    @property
    @abstractmethod
    def schema(self) -> dict[str, Any]:
        """JSON Schema for tool parameters."""

    @abstractmethod
    def execute(self, **params: Any) -> ToolResult:
        """Execute the tool and return a normalized result."""
