from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from rpl.eval.benchmarks import get_benchmark
from rpl.pref_data import DataQualityFilter, DatasetExporter, MultiCandidateEvaluator, PreferenceDataReporter
from rpl.tools.builtin import build_builtin_registry


async def main_async() -> None:
    parser = argparse.ArgumentParser(description="Execute every recovery candidate and export outcome-ranked pairs.")
    parser.add_argument("--benchmark", default="recovery_bench_generated")
    parser.add_argument("--splits", nargs="+", default=["train"])
    parser.add_argument("--max-tasks", type=int, default=0, help="0 means no limit")
    parser.add_argument("--candidate-count", type=int, default=3)
    parser.add_argument("--out-dir", default="data/pref_pairs_outcomes")
    parser.add_argument("--min-confidence", type=float, default=0.6)
    args = parser.parse_args()

    split_filter = set(args.splits)
    tasks = [task for task in get_benchmark(args.benchmark) if task.split in split_filter]
    if args.max_tasks > 0:
        tasks = tasks[: args.max_tasks]

    evaluator = MultiCandidateEvaluator(build_builtin_registry())
    pairs = []
    evaluations: list[dict[str, Any]] = []
    failed_tasks = 0
    skipped_clean = 0

    for task in tasks:
        evaluation = await evaluator.evaluate_task(task.goal, candidate_count=args.candidate_count)
        task_pairs = evaluation.preference_pairs()
        pairs.extend(task_pairs)
        if evaluation.failed_before_recovery:
            failed_tasks += 1
        else:
            skipped_clean += 1
        evaluations.append(_evaluation_to_report(task.split, task.expected_error_type, evaluation, len(task_pairs)))

    pairs = DataQualityFilter().filter(pairs, min_confidence=args.min_confidence)
    exporter = DatasetExporter()
    train, val = exporter.split_train_val(pairs)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    train_count = exporter.export_jsonl(train, out_dir / "train.jsonl")
    val_count = exporter.export_jsonl(val, out_dir / "val.jsonl")
    pair_report = PreferenceDataReporter().build(pairs)
    report = {
        "benchmark": args.benchmark,
        "splits": args.splits,
        "candidate_count": args.candidate_count,
        "tasks": len(tasks),
        "failed_tasks": failed_tasks,
        "skipped_clean_or_success": skipped_clean,
        "pairs": len(pairs),
        "train_pairs": train_count,
        "val_pairs": val_count,
        "pair_report": pair_report.to_dict(),
        "evaluations": evaluations,
    }
    (out_dir / "outcome_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps({key: value for key, value in report.items() if key != "evaluations"}, ensure_ascii=False, indent=2))


def _evaluation_to_report(split: str, expected_error_type: str | None, evaluation, pair_count: int) -> dict[str, Any]:
    return {
        "goal": evaluation.task_goal,
        "split": split,
        "expected_error_type": expected_error_type,
        "initial_success": evaluation.initial_result.success,
        "initial_error_type": evaluation.initial_result.error_type,
        "pair_count": pair_count,
        "outcomes": [
            {
                "index": outcome.index,
                "action": outcome.candidate.action,
                "tool_name": outcome.candidate.tool_name,
                "tool_params": outcome.candidate.tool_params,
                "valid": outcome.valid,
                "success": outcome.result.success,
                "error_type": outcome.result.error_type,
                "tokens": outcome.result.tokens_used,
                "latency_ms": outcome.result.latency_ms,
                "rank_key": list(outcome.rank_key),
            }
            for outcome in evaluation.outcomes
        ],
        "error_context": asdict(evaluation.error_context) if evaluation.error_context is not None else None,
    }


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
