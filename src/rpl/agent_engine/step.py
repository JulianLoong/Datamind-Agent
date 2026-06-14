from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

from rpl.tools.base import ToolResult

if TYPE_CHECKING:
    from rpl.recovery.types import Candidate, ErrorContext


class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RECOVERING = "recovering"
    SKIPPED = "skipped"


@dataclass
class RecoveryAttempt:
    candidates: list["Candidate"]
    chosen_index: int
    outcome: StepStatus
    error_context: "ErrorContext | None" = None
    initial_result: ToolResult | None = None
    final_result: ToolResult | None = None
    pm_scores: list[float] | None = None
    candidate_tokens: int = 0
    candidate_latency_ms: float = 0.0


@dataclass
class Step:
    index: int
    description: str
    tool_name: str | None = None
    params: dict[str, Any] | None = None
    status: StepStatus = StepStatus.PENDING
    result: ToolResult | None = None
    recovery_attempts: list[RecoveryAttempt] = field(default_factory=list)


@dataclass
class TaskResult:
    task_id: str
    goal: str
    status: str
    steps: list[Step]
    total_tokens: int = 0
    total_latency_ms: float = 0.0
    recovery_tokens: int = 0
    recovery_latency_ms: float = 0.0
