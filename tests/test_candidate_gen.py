from __future__ import annotations

import pytest

from rpl.recovery.candidate_gen import CandidateGenerator, parse_candidates
from rpl.recovery.types import ErrorContext
from rpl.tools.builtin import build_builtin_registry


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


def test_candidate_prompt_includes_available_tool_schemas() -> None:
    ctx = ErrorContext(
        task_goal="fetch http",
        step_description="fetch",
        tool_name="http_request",
        tool_params={"url": "https://example.test/missing"},
        error_type="not_found",
        error_message="No fixture for URL",
        recent_history=[],
    )
    registry = build_builtin_registry()

    prompt = CandidateGenerator.build_prompt(ctx, 3, tool_specs=registry.list_tools())

    assert "Available Tools JSON" in prompt
    assert '"name": "http_request"' in prompt
    assert '"additionalProperties": false' in prompt
    assert "Only use tool_name values listed above. Do not invent tools." in prompt
