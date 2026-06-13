from __future__ import annotations

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
        goal = task_goal.lower()
        if "json" in goal:
            params: dict[str, Any] = {"text": '{"value": 1}', "field": "value"}
            if "invalid" in goal or "bad" in goal:
                params["text"] = "{bad json"
            return [Step(index=0, description="Parse JSON content", tool_name="json_parse", params=params)]
        if "math" in goal or "calculate" in goal:
            expression = "1 + 2"
            if "divide" in goal or "zero" in goal:
                expression = "1/0"
            return [
                Step(
                    index=0,
                    description="Evaluate arithmetic expression",
                    tool_name="math_calc",
                    params={"expression": expression},
                )
            ]
        if "http" in goal or "fetch" in goal:
            url = "https://example.test/users/1"
            if "missing" in goal or "404" in goal:
                url = "https://example.test/missing"
            return [
                Step(
                    index=0,
                    description="Fetch mock HTTP URL",
                    tool_name="http_request",
                    params={"url": url},
                )
            ]
        return [Step(index=0, description="Default health check", tool_name="http_request", params={"url": "https://example.test/health"})]
