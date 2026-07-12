from __future__ import annotations

import pytest

from rpl.pref_model import MockPrefModel
from rpl.recovery.selector import PMSelector
from rpl.recovery.types import Candidate, ErrorContext


@pytest.mark.asyncio
async def test_pm_selector_prefers_specific_repair() -> None:
    ctx = ErrorContext(
        task_goal="parse json",
        step_description="json",
        tool_name="json_parse",
        tool_params={"text": '{"a":', "field": "a"},
        error_type="invalid_json",
        error_message="Expecting value",
        recent_history=[],
    )
    candidates = [
        Candidate("retry", "retry_same_tool", "json_parse", {"text": '{"a":', "field": "a"}, "retry"),
        Candidate("repair", "repair_json_payload", "json_parse", {"text": '{"a": null}', "field": "a"}, "repair"),
        Candidate("stop", "give_up", None, None, "stop"),
    ]
    selector = PMSelector(MockPrefModel())

    idx, candidate = await selector.select(ctx, candidates)

    assert idx == 1
    assert candidate.action == "repair_json_payload"
    assert selector.last_scores() is not None
