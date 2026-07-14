from __future__ import annotations

from rpl.eval.dpo_controlled_smoke import (
    audit_controlled_smoke,
    build_controlled_score_requests,
    controlled_smoke_contexts,
    controlled_smoke_manifest,
    controlled_smoke_markdown,
    evaluate_controlled_smoke,
)
from rpl.eval.dpo_margin import score_key
from rpl.pref_model.dpo import LogProbStats


def _stats(value: float) -> LogProbStats:
    return LogProbStats(mean_logprob=value, sum_logprob=value * 10, token_count=10)


def test_controlled_smoke_manifest_has_fixed_context_and_pool_counts() -> None:
    contexts = controlled_smoke_contexts()
    pools = audit_controlled_smoke(contexts)

    assert len(contexts) == 32
    assert sum(context.recoverable for context in contexts) == 24
    assert sum(not context.recoverable for context in contexts) == 8
    assert len(pools) == 56
    manifest = controlled_smoke_manifest(pools)
    assert manifest["context_count"] == 32
    assert manifest["pool_count"] == 56
    assert len(manifest["manifest_sha256"]) == 64
    assert {pool["family"] for pool in pools} == {
        "division_by_zero",
        "not_found",
        "invalid_json",
        "missing_field",
    }
    for pool in pools:
        assert len(pool["candidates"]) == 4
        assert sum(item["is_give_up"] for item in pool["candidates"]) == 1
        if pool["recoverable"]:
            assert sum(item["semantic_success"] for item in pool["candidates"]) == 1
        else:
            assert not any(item["semantic_success"] for item in pool["candidates"])


def test_controlled_smoke_report_compares_shared_candidate_pools() -> None:
    pools = audit_controlled_smoke()
    requests = build_controlled_score_requests(pools)
    base_scores: dict[str, LogProbStats] = {}
    dpo_scores: dict[str, LogProbStats] = {}
    for pool in pools:
        for item in pool["candidates"]:
            key = score_key(pool["prompt"], item["candidate_text"])
            base_value = 0.3 if item["is_give_up"] else 0.2 if item["semantic_success"] else 0.1
            if item["semantic_success"]:
                dpo_value = 1.0
            elif item["is_give_up"]:
                dpo_value = 0.4
            else:
                dpo_value = 0.0
            base_scores[key] = _stats(base_value)
            dpo_scores[key] = _stats(dpo_value)

    report = evaluate_controlled_smoke(
        pools,
        base_scores=base_scores,
        dpo_scores=dpo_scores,
        give_up_penalty=0.0,
    )

    assert len(requests) == 224
    assert report["context_count"] == 32
    assert report["pool_count"] == 56
    all_summaries = report["summaries"]["all"]
    assert all_summaries["base_raw"]["top1_success_rate"] == 0.0
    assert all_summaries["dpo_raw"]["top1_success_rate"] == 1.0
    assert all_summaries["base_raw"]["abstention_accuracy"] == 1.0
    assert all_summaries["dpo_raw"]["abstention_accuracy"] == 1.0
    assert report["comparisons"]["dpo_raw_vs_base_raw"]["left_only_semantic_success"] == 48
    assert "DPO Controlled Smoke v1" in controlled_smoke_markdown(report)
