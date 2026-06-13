from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from rpl.eval.benchmarks import get_benchmark
from rpl.pref_data import DataQualityFilter, DatasetExporter, PreferenceDataReporter, PreferenceExtractor
from rpl.runtime import build_runtime
from rpl.trajectory.store import TrajectoryStore


async def main_async() -> None:
    parser = argparse.ArgumentParser(description="Collect preference pairs from generated benchmark tasks.")
    parser.add_argument("--benchmark", default="recovery_bench_generated")
    parser.add_argument("--config", default="config/default.yaml")
    parser.add_argument("--selector", default="mock_pm")
    parser.add_argument("--pm-path", default=None)
    parser.add_argument("--splits", nargs="+", default=["train"])
    parser.add_argument("--max-tasks", type=int, default=0, help="0 means no limit")
    parser.add_argument("--db", default="data/generated_trajectories.db")
    parser.add_argument("--out-dir", default="data/pref_pairs_generated")
    parser.add_argument("--limit", type=int, default=10000)
    args = parser.parse_args()

    tasks = [task for task in get_benchmark(args.benchmark) if task.split in set(args.splits)]
    if args.max_tasks > 0:
        tasks = tasks[: args.max_tasks]

    runtime = build_runtime(args.config, selector_name=args.selector, pm_path=args.pm_path)
    runtime.settings.paths.trajectory_db
    runtime.store.db_path = Path(args.db)
    runtime.store.db_path.parent.mkdir(parents=True, exist_ok=True)
    runtime.store._init_schema()
    runtime.executor.collector.store = runtime.store

    success_count = 0
    recovery_count = 0
    for task in tasks:
        result = await runtime.executor.run_task(
            task.goal,
            max_steps=runtime.settings.agent.max_steps,
            max_retries_per_step=runtime.settings.agent.max_retries_per_step,
        )
        if result.status == "success":
            success_count += 1
        recovery_count += sum(len(step.recovery_attempts) for step in result.steps)

    store = TrajectoryStore(args.db)
    pairs = PreferenceExtractor().extract(store, limit=args.limit)
    pairs = DataQualityFilter().filter(pairs, min_confidence=0.6)
    report = PreferenceDataReporter().build(pairs)
    exporter = DatasetExporter()
    train, val = exporter.split_train_val(pairs)
    out_dir = Path(args.out_dir)
    train_count = exporter.export_jsonl(train, out_dir / "train.jsonl")
    val_count = exporter.export_jsonl(val, out_dir / "val.jsonl")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.json").write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "benchmark": args.benchmark,
                "splits": args.splits,
                "tasks": len(tasks),
                "tasks_success": success_count,
                "recovery_attempts": recovery_count,
                "train_pairs": train_count,
                "val_pairs": val_count,
                "report": report.to_dict(),
                "db": args.db,
                "out_dir": args.out_dir,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
