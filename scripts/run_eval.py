from __future__ import annotations

import argparse
import json
from pathlib import Path

from rpl.eval import run_eval_sync


def main() -> None:
    parser = argparse.ArgumentParser(description="Run RecoveryBench-lite evaluation.")
    parser.add_argument("--benchmark", default="recovery_bench_lite")
    parser.add_argument(
        "--baselines",
        nargs="+",
        default=["no_recovery", "first", "random", "mock_pm"],
        help="Baselines to run",
    )
    parser.add_argument("--pm-path", default=None, help="Checkpoint for lightweight_pm baseline")
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--out", default="data/eval/recovery_bench_lite.json")
    args = parser.parse_args()

    report = run_eval_sync(
        benchmark_name=args.benchmark,
        baseline_names=args.baselines,
        pm_path=args.pm_path,
        repeats=args.repeats,
        output_path=args.out,
    )
    print(f"wrote {args.out}")
    print(json.dumps(report["summaries"], ensure_ascii=False, indent=2))

    md_path = Path(args.out).with_suffix(".md")
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(_summary_markdown(report), encoding="utf-8")
    print(f"wrote {md_path}")


def _summary_markdown(report: dict) -> str:
    lines = [
        f"# {report['benchmark']} Results",
        "",
        f"repeats: {report['repeats']}",
        "",
        "Note: controlled synthetic benchmarks validate the recovery pipeline and ranking behavior; "
        "split-level results should be used when discussing generalization.",
        "",
        "| baseline | success_rate | recovery_success_rate | avg_recovery_attempts | avg_tool_calls |",
        "|---|---:|---:|---:|---:|",
    ]
    for baseline, summary in report["summaries"].items():
        lines.append(
            "| {baseline} | {success:.3f} | {recovery:.3f} | {attempts:.3f} | {calls:.3f} |".format(
                baseline=baseline,
                success=summary["success_rate"],
                recovery=summary["recovery_success_rate"],
                attempts=summary["avg_recovery_attempts"],
                calls=summary["avg_tool_calls"],
            )
        )
    split_summaries = report.get("split_summaries", {})
    split_names = sorted({split for splits in split_summaries.values() for split in splits})
    for split in split_names:
        lines.extend(
            [
                "",
                f"## Split: {split}",
                "",
                "| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_tool_calls |",
                "|---|---:|---:|---:|---:|---:|",
            ]
        )
        for baseline, splits in split_summaries.items():
            summary = splits.get(split)
            if summary is None:
                continue
            lines.append(
                "| {baseline} | {tasks} | {success:.3f} | {recovery:.3f} | {attempts:.3f} | {calls:.3f} |".format(
                    baseline=baseline,
                    tasks=summary["tasks"],
                    success=summary["success_rate"],
                    recovery=summary["recovery_success_rate"],
                    attempts=summary["avg_recovery_attempts"],
                    calls=summary["avg_tool_calls"],
                )
            )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
