from __future__ import annotations

import argparse
import gc
import json
from pathlib import Path

from rpl.eval.dpo_controlled_smoke import (
    audit_controlled_smoke,
    build_controlled_score_requests,
    controlled_smoke_manifest,
    controlled_smoke_markdown,
    evaluate_controlled_smoke,
)
from rpl.eval.dpo_margin import score_requests, scores_from_json, scores_to_json


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a fixed base-vs-DPO candidate-ranking smoke test without retraining."
    )
    parser.add_argument("--base-model", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--adapter", default="data/pm_checkpoints/dpo_pm_outcomes")
    parser.add_argument("--device", default=None)
    parser.add_argument("--give-up-penalty", type=float, default=-5.0)
    parser.add_argument(
        "--score-cache",
        default="data/eval/dpo_controlled_smoke_scores.json",
    )
    parser.add_argument(
        "--manifest-out",
        default="data/eval/dpo_controlled_smoke_manifest.json",
    )
    parser.add_argument("--manifest-only", action="store_true")
    parser.add_argument("--out", default="data/eval/dpo_controlled_smoke.json")
    args = parser.parse_args()

    pools = audit_controlled_smoke()
    manifest_path = Path(args.manifest_out)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(controlled_smoke_manifest(pools), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"wrote {manifest_path}")
    if args.manifest_only:
        return
    requests = build_controlled_score_requests(pools)
    cache_path = Path(args.score_cache)
    cache = _load_cache(cache_path, args.base_model, args.adapter)

    base_scores = scores_from_json(cache.get("base_scores", {}))
    missing_base = [request for request in requests if request.key not in base_scores]
    if missing_base:
        from rpl.pref_model import BaseModelPrefModel

        print(f"scoring {len(missing_base)} base-model controlled candidates")
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

        print(f"scoring {len(missing_dpo)} DPO controlled candidates")
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

    report = evaluate_controlled_smoke(
        pools,
        base_scores=base_scores,
        dpo_scores=dpo_scores,
        give_up_penalty=args.give_up_penalty,
    )
    report.update(
        {
            "base_model": args.base_model,
            "adapter": args.adapter,
            "score_cache": str(cache_path),
            "manifest_path": str(manifest_path),
        }
    )
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown = output.with_suffix(".md")
    markdown.write_text(controlled_smoke_markdown(report), encoding="utf-8")
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
