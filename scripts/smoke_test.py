from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from rpl.agent_engine.executor import Executor
from rpl.agent_engine.planner import RuleBasedPlanner
from rpl.pref_data import DataQualityFilter, DatasetExporter, PreferenceDataReporter, PreferenceExtractor
from rpl.pref_model import MockPrefModel
from rpl.recovery import CandidateDedup, CandidateGenerator, CandidateValidator, ErrorContextBuilder, PMSelector, RecoveryPipeline
from rpl.tools.builtin import build_builtin_registry
from rpl.trajectory.collector import TrajectoryCollector
from rpl.trajectory.store import TrajectoryStore


async def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        store = TrajectoryStore(tmp_path / "trajectories.db")
        registry = build_builtin_registry()
        executor = Executor(
            registry,
            RuleBasedPlanner(),
            RecoveryPipeline(
                ErrorContextBuilder(),
                CandidateGenerator(),
                CandidateDedup(),
                PMSelector(MockPrefModel()),
                candidate_count=3,
                validator=CandidateValidator(registry),
            ),
            TrajectoryCollector(store),
        )
        success = await executor.run_task("calculate math")
        recovered = await executor.run_task("calculate math divide by zero", max_retries_per_step=1)
        assert success.status == "success"
        assert recovered.status == "success"
        assert recovered.steps[0].recovery_attempts

        attempts = store.query_recovery_attempts(recovered.task_id)
        assert attempts
        assert attempts[0]["error_context_json"]
        assert attempts[0]["final_result_json"]

        pairs = PreferenceExtractor().extract(store)
        pairs = DataQualityFilter().filter(pairs)
        report = PreferenceDataReporter().build(pairs)
        assert report.total_pairs == len(pairs)
        assert pairs
        train, val = DatasetExporter().split_train_val(pairs)
        written = DatasetExporter().export_jsonl(train + val, tmp_path / "pref_pairs.jsonl")
        assert written == len(pairs)
        print("smoke ok")


if __name__ == "__main__":
    asyncio.run(main())
