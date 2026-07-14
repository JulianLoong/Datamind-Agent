from __future__ import annotations

import argparse
import gc
import json
from pathlib import Path

from rpl.eval.dpo_margin import (
    build_pair_score_requests,
    evaluate_pairwise_scores,
    pairwise_margin_markdown,
    score_requests,
    scores_from_json,
    scores_to_json,
)
from rpl.pref_data import load_preference_jsonl


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare base and DPO candidate-level preference margins without retraining."
    )
    parser.add_argument("--pairs", default="data/pref_pairs_outcomes/val.jsonl")
    parser.add_argument("--base-model", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--adapter", default="data/pm_checkpoints/dpo_pm_outcomes")
    parser.add_argument("--device", default=None)
    parser.add_argument("--give-up-penalty", type=float, default=-5.0)
    parser.add_argument("--bootstrap-samples", type=int, default=10_000)
    parser.add_argument("--bootstrap-seed", type=int, default=17)
    parser.add_argument(
        "--score-cache",
        default="data/eval/dpo_pairwise_margin_scores.json",
        help="Reusable base/DPO raw score cache keyed by prompt and candidate text.",
    )
    parser.add_argument("--out", default="data/eval/dpo_pairwise_margin.json")
    args = parser.parse_args()

    records = load_preference_jsonl(args.pairs)
    if not records:
        raise SystemExit(f"No preference pairs found at {args.pairs}")
    requests = build_pair_score_requests(records)
    cache_path = Path(args.score_cache)
    cache = _load_cache(cache_path, args.base_model, args.adapter)

    base_scores = scores_from_json(cache.get("base_scores", {}))
    missing_base = [request for request in requests if request.key not in base_scores]
    if missing_base:
        from rpl.pref_model import BaseModelPrefModel

        print(f"scoring {len(missing_base)} base-model prompt/candidate combinations")
        model = BaseModelPrefModel(
            base_model=args.base_model,
            device=args.device,
            give_up_penalty=0.0,
        )
        base_scores.update(score_requests(model, missing_base, progress=_progress("base")))
        del model
        _release_model_memory()

    dpo_scores = scores_from_json(cache.get("dpo_scores", {}))
    missing_dpo = [request for request in requests if request.key not in dpo_scores]
    if missing_dpo:
        from rpl.pref_model import DPOPrefModel

        print(f"scoring {len(missing_dpo)} DPO prompt/candidate combinations")
        model = DPOPrefModel(
            base_model=args.base_model,
            adapter_path=args.adapter,
            device=args.device,
            give_up_penalty=0.0,
        )
        dpo_scores.update(score_requests(model, missing_dpo, progress=_progress("dpo")))
        del model
        _release_model_memory()

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(
        json.dumps(
            {
                "base_model": args.base_model,
                "adapter": args.adapter,
                "base_scores": scores_to_json(base_scores),
                "dpo_scores": scores_to_json(dpo_scores),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    report = evaluate_pairwise_scores(
        records,
        base_scores=base_scores,
        dpo_scores=dpo_scores,
        give_up_penalty=args.give_up_penalty,
        bootstrap_samples=args.bootstrap_samples,
        bootstrap_seed=args.bootstrap_seed,
    )
    report.update(
        {
            "pairs_path": args.pairs,
            "base_model": args.base_model,
            "adapter": args.adapter,
            "score_cache": str(cache_path),
        }
    )
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown = output.with_suffix(".md")
    markdown.write_text(pairwise_margin_markdown(report), encoding="utf-8")
    print(f"wrote {output}")
    print(f"wrote {markdown}")


def _load_cache(path: Path, base_model: str, adapter: str) -> dict:
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("base_model") != base_model or value.get("adapter") != adapter:
        return {}
    return value


def _progress(label: str):
    def report(index: int, total: int) -> None:
        if index == total or index % 25 == 0:
            print(f"{label}: {index}/{total}")

    return report


def _release_model_memory() -> None:
    gc.collect()
    try:
        import torch
    except ModuleNotFoundError:
        return
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
