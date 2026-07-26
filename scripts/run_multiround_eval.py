from __future__ import annotations

import argparse
import json
from pathlib import Path

from rpl.eval import run_eval_sync
from rpl.eval.report import summary_markdown


def main() -> None:
    parser = argparse.ArgumentParser(description="Run multi-round recovery evaluation.")
    parser.add_argument("--benchmark", default="recovery_bench_lite")
    parser.add_argument(
        "--baselines",
        nargs="+",
        default=["random_r3", "mock_pm_r3"],
    )
    parser.add_argument("--pm-path", default=None)
    parser.add_argument("--memory-db", default=None)
    parser.add_argument(
        "--llm-provider",
        default=None,
        help="LLM provider (defaults to a real openai_compatible LLM); pass 'fake' for offline.",
    )
    parser.add_argument("--llm-model", default=None)
    parser.add_argument("--llm-base-url", default=None)
    parser.add_argument("--llm-api-key", default=None)
    parser.add_argument(
        "--llm-cache",
        default=None,
        help="JSONL cache used to replay generated candidates across baselines",
    )
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--out", default="data/eval/multiround_recovery.json")
    args = parser.parse_args()

    report = run_eval_sync(
        benchmark_name=args.benchmark,
        baseline_names=args.baselines,
        pm_path=args.pm_path,
        memory_db_path=args.memory_db,
        llm_provider=args.llm_provider,
        llm_model=args.llm_model,
        llm_base_url=args.llm_base_url,
        llm_api_key=args.llm_api_key,
        llm_cache_path=args.llm_cache,
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
