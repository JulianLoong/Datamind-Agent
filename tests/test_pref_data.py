from __future__ import annotations

import pytest

from rpl.agent_engine.executor import Executor
from rpl.agent_engine.planner import RuleBasedPlanner
from rpl.pref_data import DataQualityFilter, DatasetExporter, PreferenceExtractor
from rpl.recovery import CandidateDedup, CandidateGenerator, DefaultSelector, ErrorContextBuilder, RecoveryPipeline
from rpl.tools.builtin import build_builtin_registry
from rpl.trajectory.collector import TrajectoryCollector
from rpl.trajectory.store import TrajectoryStore


@pytest.mark.asyncio
async def test_preference_extractor_exports_pairs(tmp_path) -> None:
    store = TrajectoryStore(tmp_path / "trajectories.db")
    executor = Executor(
        build_builtin_registry(),
        RuleBasedPlanner(),
        RecoveryPipeline(
            ErrorContextBuilder(),
            CandidateGenerator(),
            CandidateDedup(),
            DefaultSelector("first"),
            candidate_count=3,
        ),
        TrajectoryCollector(store),
    )
    await executor.run_task(
        'rpl_task {"description": "Parse invalid JSON", "tool_name": "json_parse", "params": {"text": "{bad json", "field": "value"}}',
        max_retries_per_step=1,
    )

    pairs = DataQualityFilter().filter(PreferenceExtractor().extract(store))
    assert pairs
    output = tmp_path / "train.jsonl"
    count = DatasetExporter().export_jsonl(pairs, output)

    assert count == len(pairs)
    assert output.read_text(encoding="utf-8").strip()
