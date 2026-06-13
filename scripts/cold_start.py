from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from rpl.pref_data import DataQualityFilter, DatasetExporter, PreferenceDataReporter, PreferenceExtractor
from rpl.runtime import build_runtime

DEFAULT_TASKS = [
    "calculate math divide by zero",
    "fetch missing http",
    "parse invalid json",
]


async def run_tasks(
    config: str,
    tasks: list[str],
    repeats: int,
    *,
    selector: str | None = None,
    pm_path: str | None = None,
) -> tuple[str, int, int]:
    runtime = build_runtime(config, selector_name=selector, pm_path=pm_path)
    success_count = 0
    recovery_count = 0
    for _ in range(repeats):
        for task in tasks:
            result = await runtime.executor.run_task(
                task,
                max_steps=runtime.settings.agent.max_steps,
                max_retries_per_step=runtime.settings.agent.max_retries_per_step,
            )
            if result.status == "success":
                success_count += 1
            recovery_count += sum(len(step.recovery_attempts) for step in result.steps)
    return runtime.settings.paths.trajectory_db, success_count, recovery_count


def export_pref_data(db_path: str, out_dir: str, limit: int) -> tuple[int, int, dict]:
    from rpl.trajectory.store import TrajectoryStore

    store = TrajectoryStore(db_path)
    pairs = PreferenceExtractor().extract(store, limit=limit)
    pairs = DataQualityFilter().filter(pairs, min_confidence=0.6)
    report = PreferenceDataReporter().build(pairs)
    exporter = DatasetExporter()
    train, val = exporter.split_train_val(pairs)
    output = Path(out_dir)
    train_count = exporter.export_jsonl(train, output / "train.jsonl")
    val_count = exporter.export_jsonl(val, output / "val.jsonl")
    output.mkdir(parents=True, exist_ok=True)
    (output / "report.json").write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return train_count, val_count, report.to_dict()


async def async_main() -> None:
    parser = argparse.ArgumentParser(description="Run cold-start tasks to collect recovery data.")
    parser.add_argument("--config", default="config/default.yaml", help="Path to YAML config")
    parser.add_argument("--tasks", nargs="*", default=DEFAULT_TASKS, help="Task goals to run")
    parser.add_argument("--repeats", type=int, default=3, help="Repeat count for each task")
    parser.add_argument("--selector", default=None, help="Override selector: default, random, mock_pm, lightweight_pm")
    parser.add_argument("--pm-path", default=None, help="Checkpoint path for lightweight_pm selector")
    parser.add_argument("--export", action="store_true", help="Export preference data after collection")
    parser.add_argument("--out-dir", default="data/pref_pairs", help="Preference data output directory")
    parser.add_argument("--limit", type=int, default=1000, help="Max recovery attempts to scan")
    args = parser.parse_args()

    db_path, success_count, recovery_count = await run_tasks(
        args.config,
        args.tasks,
        args.repeats,
        selector=args.selector,
        pm_path=args.pm_path,
    )
    print(f"cold_start db={db_path} tasks_success={success_count} recovery_attempts={recovery_count}")
    if args.export:
        train_count, val_count, report = export_pref_data(db_path, args.out_dir, args.limit)
        print(f"exported train={train_count} val={val_count}")
        print(json.dumps(report, ensure_ascii=False, indent=2))


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
