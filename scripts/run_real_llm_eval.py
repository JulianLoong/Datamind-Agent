from __future__ import annotations

import argparse
import json
from pathlib import Path

from rpl.eval import run_eval_sync
from rpl.eval.report import summary_markdown
from rpl.eval.runner import parse_pm_path_items


def main() -> None:
    parser = argparse.ArgumentParser(description="Run recovery evaluation with a real OpenAI-compatible LLM.")
    parser.add_argument("--benchmark", default="recovery_gym")
    parser.add_argument(
        "--baselines",
        nargs="+",
        default=["fixed_retry", "mock_pm", "memory_mock_pm", "lightweight_pm", "memory_lightweight_pm"],
    )
    parser.add_argument("--pm-path", default=None)
    parser.add_argument(
        "--pm-paths",
        nargs="*",
        default=None,
        help="Per-baseline PM checkpoints, e.g. lightweight_pm=path dpo_pm=base::adapter",
    )
    parser.add_argument("--memory-db", default=None)
    parser.add_argument("--llm-provider", default="openai_compatible")
    parser.add_argument("--llm-model", default=None)
    parser.add_argument("--llm-base-url", default=None)
    parser.add_argument("--llm-api-key", default=None)
    parser.add_argument("--splits", nargs="+", default=None)
    parser.add_argument("--max-tasks", type=int, default=0, help="Maximum tasks after split filtering; 0 means no limit")
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--out", default="data/eval/real_llm_recovery.json")
    args = parser.parse_args()

    report = run_eval_sync(
        benchmark_name=args.benchmark,
        baseline_names=args.baselines,
        pm_path=args.pm_path,
        pm_paths=_parse_pm_paths(args.pm_paths),
        memory_db_path=args.memory_db,
        llm_provider=args.llm_provider,
        llm_model=args.llm_model,
        llm_base_url=args.llm_base_url,
        llm_api_key=args.llm_api_key,
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


def _parse_pm_paths(items: list[str] | None) -> dict[str, str]:
    try:
        return parse_pm_path_items(items)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
