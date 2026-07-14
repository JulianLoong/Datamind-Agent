from __future__ import annotations

import json

from rpl.eval.dpo_margin import (
    build_pair_score_requests,
    evaluate_pairwise_scores,
    pairwise_margin_markdown,
    score_key,
)
from rpl.pref_model.dpo import LogProbStats


def _candidate(action: str, *, tool_name: str | None = "json_parse") -> str:
    return json.dumps(
        {
            "reasoning": action,
            "action": action,
            "tool_name": tool_name,
            "tool_params": {"text": "{}"} if tool_name else None,
        }
    )


def _records() -> list[dict]:
    repair = _candidate("repair_json_payload")
    retry = _candidate("retry_same_tool")
    give_up = _candidate("give_up", tool_name=None)
    records: list[dict] = []
    for index in range(2):
        prompt = f"[Error]: invalid_json: context {index}"
        records.extend(
            [
                {
                    "prompt": prompt,
                    "chosen": repair,
                    "rejected": retry,
                    "metadata": {
                        "preference_reason": "success_over_failure",
                        "error_type": "invalid_json",
                    },
                },
                {
                    "prompt": prompt,
                    "chosen": repair,
                    "rejected": give_up,
                    "metadata": {
                        "preference_reason": "success_over_failure",
                        "error_type": "invalid_json",
                    },
                },
                {
                    "prompt": prompt,
                    "chosen": retry,
                    "rejected": give_up,
                    "metadata": {
                        "preference_reason": "executable_failure_over_give_up",
                        "error_type": "invalid_json",
                    },
                },
            ]
        )
    return records


def _stats(value: float, token_count: int = 10) -> LogProbStats:
    return LogProbStats(value, value * token_count, token_count)


def test_pair_score_requests_deduplicate_candidates_within_context() -> None:
    requests = build_pair_score_requests(_records())

    assert len(requests) == 6


def test_pairwise_report_separates_adapter_and_penalty_effects() -> None:
    records = _records()
    base_scores: dict[str, LogProbStats] = {}
    dpo_scores: dict[str, LogProbStats] = {}
    for record in records:
        prompt = record["prompt"]
        for field in ("chosen", "rejected"):
            text = record[field]
            action = json.loads(text)["action"]
            base_value = {
                "repair_json_payload": -1.4,
                "retry_same_tool": -1.2,
                "give_up": -0.8,
            }[action]
            dpo_value = {
                "repair_json_payload": -0.7,
                "retry_same_tool": -1.1,
                "give_up": -0.9,
            }[action]
            base_scores[score_key(prompt, text)] = _stats(base_value)
            dpo_scores[score_key(prompt, text)] = _stats(dpo_value)

    report = evaluate_pairwise_scores(
        records,
        base_scores=base_scores,
        dpo_scores=dpo_scores,
        give_up_penalty=-5.0,
        bootstrap_samples=200,
        bootstrap_seed=7,
    )

    primary = report["subsets"]["success_over_failure"]
    assert report["pair_count"] == 6
    assert report["context_count"] == 2
    assert primary["pair_count"] == 4
    assert primary["scorers"]["base_raw"]["pairwise_accuracy"] == 0.0
    assert primary["scorers"]["dpo_raw"]["pairwise_accuracy"] == 1.0
    assert primary["scorers"]["dpo_reward"]["pairwise_accuracy"] == 1.0
    assert report["acceptance"]["dpo_raw_improves_primary"] is True
    assert "DPO Pairwise Margin Diagnostic" in pairwise_margin_markdown(report)
