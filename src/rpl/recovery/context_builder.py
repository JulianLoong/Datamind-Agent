from __future__ import annotations

from rpl.agent_engine.step import Step
from rpl.recovery.types import ErrorContext


class ErrorContextBuilder:
    def build(self, step: Step, history: list[Step], task_goal: str) -> ErrorContext:
        if step.result is None:
            error_type = "unknown_error"
            error_message = "Step failed without a ToolResult"
        else:
            error_type = step.result.error_type or "unknown_error"
            error_message = step.result.error_message or "No error message"

        recent_history = []
        for item in history[-5:]:
            brief_result = ""
            if item.result is not None:
                if item.result.success:
                    brief_result = str(item.result.data)[:120]
                else:
                    brief_result = f"{item.result.error_type}: {item.result.error_message}"
            recent_history.append(
                {
                    "index": item.index,
                    "tool_name": item.tool_name,
                    "status": item.status.value,
                    "brief_result": brief_result,
                }
            )

        return ErrorContext(
            task_goal=task_goal,
            step_description=step.description,
            tool_name=step.tool_name or "unknown_tool",
            tool_params=step.params or {},
            error_type=error_type,
            error_message=error_message,
            recent_history=recent_history,
        )
