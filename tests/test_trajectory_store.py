from __future__ import annotations

from rpl.agent_engine.step import Step, StepStatus, TaskResult
from rpl.tools.base import ToolResult
from rpl.trajectory.store import TrajectoryStore


def test_store_saves_failed_step(tmp_path) -> None:
    store = TrajectoryStore(tmp_path / "trajectories.db")
    result = TaskResult(
        task_id="task-1",
        goal="bad json",
        status="failed",
        steps=[
            Step(
                index=0,
                description="Parse JSON",
                tool_name="json_parse",
                params={"text": "{bad"},
                status=StepStatus.FAILED,
                result=ToolResult.fail("invalid_json", "bad json"),
            )
        ],
    )

    store.save_task(result)
    failures = store.query_failures("invalid_json")

    assert len(failures) == 1
    assert failures[0]["task_id"] == "task-1"
