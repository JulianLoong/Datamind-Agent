from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass
class PreferencePair:
    prompt: str
    chosen: str
    rejected: str
    source: str
    confidence: float
    metadata: dict[str, Any]

    def to_dpo_record(self) -> dict[str, Any]:
        return {
            "prompt": self.prompt,
            "chosen": self.chosen,
            "rejected": self.rejected,
            "source": self.source,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


def candidate_to_text(candidate: dict[str, Any]) -> str:
    return json.dumps(
        {
            "reasoning": candidate.get("reasoning", ""),
            "action": candidate.get("action", ""),
            "tool_name": candidate.get("tool_name"),
            "tool_params": candidate.get("tool_params"),
        },
        ensure_ascii=False,
    )


def error_context_to_prompt(error_context: dict[str, Any]) -> str:
    history_lines = []
    for item in error_context.get("recent_history", []) or []:
        history_lines.append(
            f"  - Step {item.get('index')}: {item.get('tool_name')} -> "
            f"{item.get('status')} ({item.get('brief_result')})"
        )
    history = "\n".join(history_lines) or "  - None"
    return (
        f"[Task Goal]: {error_context.get('task_goal')}\n"
        f"[Current Step]: {error_context.get('step_description')}\n"
        f"[Failed Tool]: {error_context.get('tool_name')}({error_context.get('tool_params')})\n"
        f"[Error]: {error_context.get('error_type')}: {error_context.get('error_message')}\n"
        f"[Recent History]:\n{history}"
    )
