from __future__ import annotations

import pytest

from rpl.recovery.candidate_gen import CandidateGenerator, parse_candidates
from rpl.recovery.types import ErrorContext


def test_parse_candidates_from_json() -> None:
    candidates = parse_candidates(
        '[{"reasoning":"r","action":"a","tool_name":"math_calc","tool_params":{"expression":"1+1"}}]'
    )

    assert len(candidates) == 1
    assert candidates[0].action == "a"


@pytest.mark.asyncio
async def test_fake_llm_candidate_generator_recovers_division_by_zero() -> None:
    ctx = ErrorContext(
        task_goal="calculate",
        step_description="math",
        tool_name="math_calc",
        tool_params={"expression": "1/0"},
        error_type="division_by_zero",
        error_message="division by zero",
        recent_history=[],
    )

    candidates = await CandidateGenerator().generate(ctx, k=2)

    assert any(
        candidate.action == "avoid_zero_division"
        and candidate.tool_params == {"expression": "1/1"}
        for candidate in candidates
    )
