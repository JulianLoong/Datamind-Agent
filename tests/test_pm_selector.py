from __future__ import annotations

import pytest

from rpl.pref_model import MockPrefModel
from rpl.recovery.selector import FixedRetrySelector, PMSelector
from rpl.recovery.types import Candidate, ErrorContext


@pytest.mark.asyncio
async def test_pm_selector_prefers_specific_repair() -> None:
    ctx = ErrorContext(
        task_goal="calculate",
        step_description="math",
        tool_name="math_calc",
        tool_params={"expression": "1/0"},
        error_type="division_by_zero",
        error_message="division by zero",
        recent_history=[],
    )
    candidates = [
        Candidate("retry", "retry_same_tool", "math_calc", {"expression": "1/0"}, "retry"),
        Candidate("fix", "avoid_zero_division", "math_calc", {"expression": "1/1"}, "fix"),
        Candidate("stop", "give_up", None, None, "stop"),
    ]
    selector = PMSelector(MockPrefModel())

    idx, candidate = await selector.select(ctx, candidates)

    assert idx == 1
    assert candidate.action == "avoid_zero_division"
    assert selector.last_scores() is not None


@pytest.mark.asyncio
async def test_fixed_retry_selector_tries_retry_then_repair_then_give_up() -> None:
    ctx = ErrorContext(
        task_goal="calculate",
        step_description="math",
        tool_name="math_calc",
        tool_params={"expression": "1/0"},
        error_type="division_by_zero",
        error_message="division by zero",
        recent_history=[],
    )
    candidates = [
        Candidate("retry", "retry_same_tool", "math_calc", {"expression": "1/0"}, "retry"),
        Candidate("stop", "give_up", None, None, "stop"),
        Candidate("fix", "avoid_zero_division", "math_calc", {"expression": "1/1"}, "fix"),
    ]
    selector = FixedRetrySelector()

    _, first = await selector.select(ctx, candidates)
    _, second = await selector.select(ctx, candidates)
    _, third = await selector.select(ctx, candidates)

    assert first.action == "retry_same_tool"
    assert second.action == "avoid_zero_division"
    assert third.action == "give_up"
