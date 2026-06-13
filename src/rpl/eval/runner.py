from __future__ import annotations

import asyncio
import json
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any

from rpl.agent_engine.executor import Executor
from rpl.agent_engine.planner import RuleBasedPlanner
from rpl.eval.baselines import build_baseline
from rpl.eval.benchmarks import BenchmarkTask, get_benchmark
from rpl.eval.metrics import TaskEvalRecord, summarize_records, summarize_records_by_split, task_record
from rpl.recovery import CandidateDedup, CandidateGenerator, CandidateValidator, ErrorContextBuilder, RecoveryPipeline
from rpl.tools.builtin import build_builtin_registry
from rpl.trajectory.collector import TrajectoryCollector
from rpl.trajectory.store import TrajectoryStore


async def run_eval(
    *,
    benchmark_name: str = "recovery_bench_lite",
    baseline_names: list[str] | None = None,
    pm_path: str | None = None,
    repeats: int = 5,
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    tasks = get_benchmark(benchmark_name)
    baseline_names = baseline_names or ["no_recovery", "first", "random"]
    all_records: list[TaskEvalRecord] = []
    summaries: dict[str, dict[str, float | int | str]] = {}

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for baseline_name in baseline_names:
            spec = build_baseline(baseline_name, pm_path=pm_path)
            records = await _run_baseline(
                spec_name=spec.name,
                tasks=tasks,
                repeats=repeats,
                max_retries_per_step=spec.max_retries_per_step,
                selector=spec.selector,
                db_path=tmp_path / f"{spec.name}.db",
            )
            all_records.extend(records)
            summaries[spec.name] = summarize_records(records)

    report = {
        "benchmark": benchmark_name,
        "repeats": repeats,
        "summaries": summaries,
        "split_summaries": {
            baseline: summarize_records_by_split(
                [record for record in all_records if record.baseline == baseline]
            )
            for baseline in summaries
        },
        "records": [asdict(record) for record in all_records],
    }
    if output_path is not None:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


async def _run_baseline(
    *,
    spec_name: str,
    tasks: list[BenchmarkTask],
    repeats: int,
    max_retries_per_step: int,
    selector,
    db_path: Path,
) -> list[TaskEvalRecord]:
    registry = build_builtin_registry()
    store = TrajectoryStore(db_path)
    executor = Executor(
        registry,
        RuleBasedPlanner(),
        RecoveryPipeline(
            ErrorContextBuilder(),
            CandidateGenerator(),
            CandidateDedup(),
            selector,
            candidate_count=3,
            validator=CandidateValidator(registry),
        ),
        TrajectoryCollector(store),
    )

    records: list[TaskEvalRecord] = []
    for _ in range(repeats):
        for task in tasks:
            result = await executor.run_task(
                task.goal,
                max_steps=20,
                max_retries_per_step=max_retries_per_step,
            )
            records.append(
                task_record(
                    baseline=spec_name,
                    goal=task.goal,
                    split=task.split,
                    expected_error_type=task.expected_error_type,
                    result=result,
                )
            )
    return records


def run_eval_sync(**kwargs: Any) -> dict[str, Any]:
    return asyncio.run(run_eval(**kwargs))
