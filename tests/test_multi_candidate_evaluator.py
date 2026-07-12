from __future__ import annotations

import pytest

from rpl.pref_data import MultiCandidateEvaluator
from rpl.tools.builtin import build_builtin_registry


@pytest.mark.asyncio
async def test_multi_candidate_evaluator_builds_outcome_pairs() -> None:
    evaluator = MultiCandidateEvaluator(build_builtin_registry())

    goal = (
        'rpl_task {"description": "Parse invalid JSON", "tool_name": "json_parse", '
        '"params": {"text": "{bad json", "field": "value"}}'
    )
    evaluation = await evaluator.evaluate_task(goal, candidate_count=3)
    pairs = evaluation.preference_pairs()

    assert evaluation.failed_before_recovery is True
    assert evaluation.error_context is not None
    assert evaluation.error_context.error_type == "invalid_json"
    assert any(outcome.result.success for outcome in evaluation.outcomes)
    assert pairs
    assert all(pair.source == "outcome_multi_candidate" for pair in pairs)
    assert any("repair_json_payload" in pair.chosen for pair in pairs)
    assert any("retry_same_tool" in pair.rejected or "give_up" in pair.rejected for pair in pairs)


@pytest.mark.asyncio
async def test_multi_candidate_evaluator_skips_successful_initial_step() -> None:
    evaluator = MultiCandidateEvaluator(build_builtin_registry())

    evaluation = await evaluator.evaluate_task("calculate math", candidate_count=3)

    assert evaluation.failed_before_recovery is False
    assert evaluation.outcomes == []
    assert evaluation.preference_pairs() == []
