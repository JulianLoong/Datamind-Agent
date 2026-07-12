from __future__ import annotations

import json
from typing import Any

from rpl.agent_engine.step import Step
from rpl.tools.base import BaseTool


class Planner:
    def plan(self, task_goal: str, available_tools: list[BaseTool]) -> list[Step]:
        raise NotImplementedError


class StaticPlanner(Planner):
    def __init__(self, steps: list[Step]) -> None:
        self.steps = steps

    def plan(self, task_goal: str, available_tools: list[BaseTool]) -> list[Step]:
        return [
            Step(
                index=idx,
                description=step.description,
                tool_name=step.tool_name,
                params=dict(step.params or {}),
            )
            for idx, step in enumerate(self.steps)
        ]


class RuleBasedPlanner(Planner):
    """Tiny deterministic planner for development and tests."""

    def plan(self, task_goal: str, available_tools: list[BaseTool]) -> list[Step]:
        structured = _parse_structured_task(task_goal)
        if structured is not None:
            return [
                Step(
                    index=0,
                    description=structured.get("description", "Run structured benchmark task"),
                    tool_name=structured.get("tool_name"),
                    params=structured.get("params", {}),
                )
            ]

        goal = task_goal.lower()
        if "json" in goal:
            params: dict[str, Any] = {"text": '{"value": 1}', "field": "value"}
            if "invalid" in goal or "bad" in goal:
                params["text"] = "{bad json"
            return [Step(index=0, description="Parse JSON content", tool_name="json_parse", params=params)]
        if "math" in goal or "calculate" in goal:
            return [
                Step(
                    index=0,
                    description="Evaluate arithmetic expression",
                    tool_name="math_calc",
                    params={"expression": "1 + 2"},
                )
            ]
        if "http" in goal or "fetch" in goal:
            return [
                Step(
                    index=0,
                    description="Fetch mock HTTP URL",
                    tool_name="http_request",
                    params={"url": "https://example.test/users/1"},
                )
            ]
        return [Step(index=0, description="Default health check", tool_name="http_request", params={"url": "https://example.test/health"})]


def _parse_structured_task(task_goal: str) -> dict[str, Any] | None:
    prefix = "rpl_task "
    if not task_goal.startswith(prefix):
        return None
    try:
        payload = json.loads(task_goal[len(prefix) :])
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    tool_name = payload.get("tool_name")
    params = payload.get("params")
    if not isinstance(tool_name, str) or not isinstance(params, dict):
        return None
    description = payload.get("description")
    return {
        "tool_name": tool_name,
        "params": params,
        "description": description if isinstance(description, str) else "Run structured benchmark task",
    }
