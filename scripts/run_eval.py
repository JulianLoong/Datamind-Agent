from __future__ import annotations

import argparse
import json
from pathlib import Path

from rpl.eval import run_eval_sync
from rpl.eval.report import summary_markdown


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
    parser.add_argument("--memory-db", default=None, help="Trajectory DB used to load successful recovery experiences")
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--out", default="data/eval/recovery_bench_lite.json")
    args = parser.parse_args()

    report = run_eval_sync(
        benchmark_name=args.benchmark,
        baseline_names=args.baselines,
        pm_path=args.pm_path,
        memory_db_path=args.memory_db,
        repeats=args.repeats,
        output_path=args.out,
    )
    print(f"wrote {args.out}")
    print(json.dumps(report["summaries"], ensure_ascii=False, indent=2))

    md_path = Path(args.out).with_suffix(".md")
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(summary_markdown(report), encoding="utf-8")
    print(f"wrote {md_path}")


if __name__ == "__main__":
    main()
