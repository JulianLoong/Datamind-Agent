from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from rpl.eval.real_llm_smoke import real_llm_smoke_markdown, run_real_llm_smoke
from rpl.llm import CachedLLMClient
from rpl.recovery.candidate_gen import build_llm_client


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the 10-case real-LLM recovery candidate smoke evaluation."
    )
    parser.add_argument("--llm-provider", default="openai_compatible")
    parser.add_argument("--llm-model", default="deepseek-chat")
    parser.add_argument("--llm-base-url", default="https://api.deepseek.com")
    parser.add_argument("--llm-api-key", default=None)
    parser.add_argument("--llm-cache", default="data/eval/real_llm_smoke_v1_candidates.jsonl")
    parser.add_argument("--candidate-count", type=int, default=3)
    parser.add_argument("--dpo-base-model", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--dpo-adapter", default="data/pm_checkpoints/dpo_pm_outcomes")
    parser.add_argument("--give-up-penalty", type=float, default=-5.0)
    parser.add_argument("--random-seed", type=int, default=17)
    parser.add_argument("--out", default="data/eval/real_llm_smoke_v1.json")
    args = parser.parse_args()

    client = build_llm_client(
        provider=args.llm_provider,
        model=args.llm_model,
        base_url=args.llm_base_url,
        api_key=args.llm_api_key,
        api_key_env="DEEPSEEK_API_KEY",
    )
    namespace = json.dumps(
        {
            "benchmark": "real_llm_smoke_v1",
            "provider": args.llm_provider,
            "model": args.llm_model,
            "base_url": args.llm_base_url,
            "candidate_count": args.candidate_count,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    cached_client = CachedLLMClient(client, cache_path=args.llm_cache, namespace=namespace)

    from rpl.pref_model import BaseModelPrefModel, DPOPrefModel

    base_model = BaseModelPrefModel(
        base_model=args.dpo_base_model,
        give_up_penalty=args.give_up_penalty,
    )
    dpo_model = DPOPrefModel(
        base_model=args.dpo_base_model,
        adapter_path=args.dpo_adapter,
        give_up_penalty=args.give_up_penalty,
    )
    report = asyncio.run(
        run_real_llm_smoke(
            llm_client=cached_client,
            pref_models={"base_model": base_model, "dpo_pm": dpo_model},
            provider=args.llm_provider,
            model=args.llm_model,
            base_url=args.llm_base_url,
            cache_path=args.llm_cache,
            candidate_count=args.candidate_count,
            random_seed=args.random_seed,
        )
    )
    report["scoring_config"] = {
        "base_model": args.dpo_base_model,
        "adapter": args.dpo_adapter,
        "give_up_penalty": args.give_up_penalty,
        "pref_models": ["base_model", "dpo_pm"],
    }
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown_output = output.with_suffix(".md")
    markdown_output.write_text(real_llm_smoke_markdown(report), encoding="utf-8")
    print(json.dumps(report["generator_summary"], ensure_ascii=False, indent=2))
    print(json.dumps(report["selector_summaries"], ensure_ascii=False, indent=2))
    print(f"wrote {output}")
    print(f"wrote {markdown_output}")


if __name__ == "__main__":
    main()
