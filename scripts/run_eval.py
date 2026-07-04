from __future__ import annotations

import argparse
import json
from pathlib import Path

from rpl.eval import run_eval_sync
from rpl.eval.report import summary_markdown
from rpl.eval.runner import parse_pm_path_items


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
    parser.add_argument(
        "--pm-paths",
        nargs="*",
        default=None,
        help="Per-baseline PM checkpoints, e.g. lightweight_pm=path dpo_pm=base::adapter",
    )
    parser.add_argument("--memory-db", default=None, help="Trajectory DB used to load successful recovery experiences")
    parser.add_argument("--llm-provider", default=None, help="LLM provider for candidate generation (fake, openai_compatible)")
    parser.add_argument("--llm-model", default=None, help="LLM model name for real candidate generation")
    parser.add_argument("--llm-base-url", default=None, help="Base URL for OpenAI-compatible LLM API")
    parser.add_argument("--llm-api-key", default=None, help="API key for OpenAI-compatible LLM API")
    parser.add_argument("--llm-cache", default=None, help="JSONL cache used to replay generated candidates across baselines")
    parser.add_argument("--splits", nargs="+", default=None, help="Optional benchmark splits to include")
    parser.add_argument("--max-tasks", type=int, default=0, help="Maximum tasks after split filtering; 0 means no limit")
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--out", default="data/eval/recovery_bench_lite.json")
    args = parser.parse_args()

    report = run_eval_sync(
        benchmark_name=args.benchmark,
        baseline_names=args.baselines,
        pm_path=args.pm_path,
        pm_paths=parse_pm_paths(args.pm_paths),
        memory_db_path=args.memory_db,
        llm_provider=args.llm_provider,
        llm_model=args.llm_model,
        llm_base_url=args.llm_base_url,
        llm_api_key=args.llm_api_key,
        llm_cache_path=args.llm_cache,
        splits=args.splits,
        max_tasks=args.max_tasks,
        repeats=args.repeats,
        output_path=args.out,
    )
    print(f"wrote {args.out}")
    print(json.dumps(report["summaries"], ensure_ascii=False, indent=2))

    md_path = Path(args.out).with_suffix(".md")
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(summary_markdown(report), encoding="utf-8")
    print(f"wrote {md_path}")


def parse_pm_paths(items: list[str] | None) -> dict[str, str]:
    try:
        return parse_pm_path_items(items)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
