from __future__ import annotations

import argparse
import json
from pathlib import Path

from rpl.eval import run_eval_sync
from rpl.eval.report import summary_markdown


def main() -> None:
    parser = argparse.ArgumentParser(description="Run RecoveryGym family/split generalization evaluation.")
    parser.add_argument("--baselines", nargs="+", default=["no_recovery", "fixed_retry", "mock_pm"])
    parser.add_argument("--pm-path", default=None)
    parser.add_argument("--memory-db", default=None)
    parser.add_argument("--splits", nargs="+", default=None)
    parser.add_argument("--max-tasks", type=int, default=0, help="Maximum tasks after split filtering; 0 means no limit")
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--out", default="data/eval/recovery_gym.json")
    args = parser.parse_args()

    report = run_eval_sync(
        benchmark_name="recovery_gym",
        baseline_names=args.baselines,
        pm_path=args.pm_path,
        memory_db_path=args.memory_db,
        splits=args.splits,
        max_tasks=args.max_tasks,
        repeats=args.repeats,
        output_path=args.out,
    )
    print(json.dumps(report["summaries"], ensure_ascii=False, indent=2))
    md_path = Path(args.out).with_suffix(".md")
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(summary_markdown(report), encoding="utf-8")
    print(f"wrote {args.out}")
    print(f"wrote {md_path}")


if __name__ == "__main__":
    main()
