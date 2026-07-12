from __future__ import annotations

import pytest

from rpl.agent_engine.executor import Executor
from rpl.agent_engine.planner import RuleBasedPlanner
from rpl.pref_model import MockPrefModel
from rpl.recovery import CandidateDedup, CandidateGenerator, DefaultSelector, ErrorContextBuilder, PMSelector, RecoveryPipeline
from rpl.tools.builtin import build_builtin_registry
from rpl.trajectory.collector import TrajectoryCollector
from rpl.trajectory.store import TrajectoryStore


def build_executor(tmp_path) -> Executor:
    registry = build_builtin_registry()
    store = TrajectoryStore(tmp_path / "trajectories.db")
    collector = TrajectoryCollector(store)
    recovery = RecoveryPipeline(
        ErrorContextBuilder(),
        CandidateGenerator(),
        CandidateDedup(),
        DefaultSelector("first"),
        candidate_count=3,
    )
    return Executor(registry, RuleBasedPlanner(), recovery, collector)


@pytest.mark.asyncio
async def test_executor_runs_success_task(tmp_path) -> None:
    executor = build_executor(tmp_path)

    result = await executor.run_task("calculate math")

    assert result.status == "success"
    assert result.steps[0].result is not None
    assert result.steps[0].result.success is True


@pytest.mark.asyncio
async def test_executor_recovers_invalid_json(tmp_path) -> None:
    registry = build_builtin_registry()
    store = TrajectoryStore(tmp_path / "trajectories.db")
    collector = TrajectoryCollector(store)
    recovery = RecoveryPipeline(
        ErrorContextBuilder(),
        CandidateGenerator(),
        CandidateDedup(),
        PMSelector(MockPrefModel()),
        candidate_count=3,
    )
    executor = Executor(registry, RuleBasedPlanner(), recovery, collector)

    goal = 'rpl_task {"description": "Parse invalid JSON", "tool_name": "json_parse", "params": {"text": "{bad json", "field": "value"}}'
    result = await executor.run_task(goal, max_retries_per_step=1)

    assert result.status == "success"
    assert result.steps[0].recovery_attempts
    assert store.query_recovery_attempts(result.task_id)
