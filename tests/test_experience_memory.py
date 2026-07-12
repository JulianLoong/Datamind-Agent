from __future__ import annotations

import pytest

from rpl.experience import ExperienceMemory, ExperienceRecord
from rpl.recovery import MemoryPriorSelector
from rpl.recovery.selector import DefaultSelector
from rpl.recovery.types import Candidate, ErrorContext
from rpl.tools.base import ToolResult
from rpl.trajectory.store import to_json


def _ctx() -> ErrorContext:
    return ErrorContext(
        task_goal="parse json",
        step_description="json",
        tool_name="json_parse",
        tool_params={"text": '{"a":', "field": "a"},
        error_type="invalid_json",
        error_message="Expecting value",
        recent_history=[],
    )


def _record() -> ExperienceRecord:
    return ExperienceRecord(
        tool_name="json_parse",
        error_type="invalid_json",
        error_message="Expecting value",
        failed_params={"text": '{"a":', "field": "a"},
        successful_candidate=Candidate(
            "repair malformed JSON",
            "repair_json_payload",
            "json_parse",
            {"text": '{"a": null}', "field": "a"},
            "repair",
        ),
        final_result=ToolResult.ok(None),
    )


def test_experience_memory_retrieves_similar_record() -> None:
    memory = ExperienceMemory([_record()])

    matches = memory.retrieve(_ctx())

    assert matches
    assert matches[0][0].successful_candidate.action == "repair_json_payload"
    assert matches[0][1] > 0


def test_experience_memory_loads_successful_recovery_rows() -> None:
    row = {
        "task_id": "task-1",
        "step_id": "step-1",
        "id": "recovery-1",
        "error_context_json": to_json(_ctx()),
        "chosen_candidate_json": to_json(_record().successful_candidate),
        "final_result_json": to_json(ToolResult.ok(None)),
    }

    memory = ExperienceMemory.from_recovery_rows([row])

    assert len(memory.records()) == 1
    assert memory.records()[0].metadata["task_id"] == "task-1"


@pytest.mark.asyncio
async def test_memory_prior_selector_can_override_base_selector() -> None:
    memory = ExperienceMemory([_record()])
    selector = MemoryPriorSelector(memory, DefaultSelector("first"), memory_weight=1.0)
    candidates = [
        Candidate("retry", "retry_same_tool", "json_parse", {"text": '{"a":', "field": "a"}, "retry"),
        Candidate("repair", "repair_json_payload", "json_parse", {"text": '{"a": null}', "field": "a"}, "repair"),
    ]

    idx, candidate = await selector.select(_ctx(), candidates)

    assert idx == 1
    assert candidate.action == "repair_json_payload"
    assert selector.last_scores() is not None
