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
        task_goal="calculate",
        step_description="math",
        tool_name="math_calc",
        tool_params={"expression": "1/0"},
        error_type="division_by_zero",
        error_message="division by zero",
        recent_history=[],
    )


def _record() -> ExperienceRecord:
    return ExperienceRecord(
        tool_name="math_calc",
        error_type="division_by_zero",
        error_message="division by zero",
        failed_params={"expression": "1/0"},
        successful_candidate=Candidate(
            "fix zero denominator",
            "avoid_zero_division",
            "math_calc",
            {"expression": "1/1"},
            "fix",
        ),
        final_result=ToolResult.ok(1.0),
    )


def test_experience_memory_retrieves_similar_record() -> None:
    memory = ExperienceMemory([_record()])

    matches = memory.retrieve(_ctx())

    assert matches
    assert matches[0][0].successful_candidate.action == "avoid_zero_division"
    assert matches[0][1] > 0


def test_experience_memory_loads_successful_recovery_rows() -> None:
    row = {
        "task_id": "task-1",
        "step_id": "step-1",
        "id": "recovery-1",
        "error_context_json": to_json(_ctx()),
        "chosen_candidate_json": to_json(_record().successful_candidate),
        "final_result_json": to_json(ToolResult.ok(1.0)),
    }

    memory = ExperienceMemory.from_recovery_rows([row])

    assert len(memory.records()) == 1
    assert memory.records()[0].metadata["task_id"] == "task-1"


@pytest.mark.asyncio
async def test_memory_prior_selector_can_override_base_selector() -> None:
    memory = ExperienceMemory([_record()])
    selector = MemoryPriorSelector(memory, DefaultSelector("first"), memory_weight=1.0)
    candidates = [
        Candidate("retry", "retry_same_tool", "math_calc", {"expression": "1/0"}, "retry"),
        Candidate("fix", "avoid_zero_division", "math_calc", {"expression": "1/1"}, "fix"),
    ]

    idx, candidate = await selector.select(_ctx(), candidates)

    assert idx == 1
    assert candidate.action == "avoid_zero_division"
    assert selector.last_scores() is not None
