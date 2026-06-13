from __future__ import annotations

import pytest

from rpl.pref_model import MockPrefModel
from rpl.recovery.selector import PMSelector
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
