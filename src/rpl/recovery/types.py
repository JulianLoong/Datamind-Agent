from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ErrorContext:
    task_goal: str
    step_description: str
    tool_name: str
    tool_params: dict[str, Any]
    error_type: str
    error_message: str
    recent_history: list[dict[str, Any]]

    def to_prompt(self) -> str:
        history = "\n".join(
            f"  - Step {item.get('index')}: {item.get('tool_name')} -> "
            f"{item.get('status')} ({item.get('brief_result')})"
            for item in self.recent_history
        )
        return (
            f"[Task Goal]: {self.task_goal}\n"
            f"[Current Step]: {self.step_description}\n"
            f"[Failed Tool]: {self.tool_name}({self.tool_params})\n"
            f"[Error]: {self.error_type}: {self.error_message}\n"
            f"[Recent History]:\n{history or '  - None'}"
        )


@dataclass
class Candidate:
    reasoning: str
    action: str
    tool_name: str | None
    tool_params: dict[str, Any] | None
    raw_text: str
