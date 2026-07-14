from __future__ import annotations

import hashlib
import json
import random
from collections import defaultdict
from collections.abc import Callable
from dataclasses import asdict, dataclass
from statistics import mean, median
from typing import Any, Protocol

from rpl.pref_data.dpo_data import normalize_recovery_text
from rpl.pref_model.dpo import LogProbStats


class TextScorer(Protocol):
    def score_text(self, error_context_prompt: str, response_text: str) -> LogProbStats: ...


@dataclass(frozen=True)
class ScoreRequest:
    key: str
    prompt: str
    response: str


def score_key(prompt: str, response: str) -> str:
    normalized = normalize_recovery_text(response)
    return hashlib.sha256(f"{prompt}\0{normalized}".encode()).hexdigest()


def build_pair_score_requests(records: list[dict[str, Any]]) -> list[ScoreRequest]:
    requests: dict[str, ScoreRequest] = {}
    for record in records:
        prompt = record.get("prompt")
        if not isinstance(prompt, str):
            continue
        for field in ("chosen", "rejected"):
            response = record.get(field)
            if not isinstance(response, str):
                continue
            normalized = normalize_recovery_text(response)
            key = score_key(prompt, normalized)
            requests[key] = ScoreRequest(key=key, prompt=prompt, response=normalized)
    return list(requests.values())


def score_requests(
    scorer: TextScorer,
    requests: list[ScoreRequest],
    *,
    progress: Callable[[int, int], None] | None = None,
) -> dict[str, LogProbStats]:
    scores: dict[str, LogProbStats] = {}
    total = len(requests)
    for index, request in enumerate(requests, start=1):
        scores[request.key] = scorer.score_text(request.prompt, request.response)
        if progress is not None:
            progress(index, total)
    return scores


def evaluate_pairwise_scores(
    records: list[dict[str, Any]],
    *,
    base_scores: dict[str, LogProbStats],
    dpo_scores: dict[str, LogProbStats],
    give_up_penalty: float = -5.0,
    bootstrap_samples: int = 10_000,
    bootstrap_seed: int = 17,
) -> dict[str, Any]:
    pair_rows = [
        row
        for record in records
        if (row := _pair_row(record, base_scores, dpo_scores, give_up_penalty)) is not None
    ]
    subsets = {
        "success_over_failure": [
            row for row in pair_rows if row["preference_reason"] == "success_over_failure"
        ],
        "executable_failure_over_give_up": [
            row
            for row in pair_rows
            if row["preference_reason"] == "executable_failure_over_give_up"
        ],
        "all": pair_rows,
    }
    subset_reports = {
        name: _summarize_subset(
            rows,
            bootstrap_samples=bootstrap_samples,
            bootstrap_seed=bootstrap_seed,
        )
        for name, rows in subsets.items()
    }
    primary = subset_reports["success_over_failure"]
    return {
        "benchmark": "dpo_pairwise_margin",
        "positioning": "candidate-level adapter-on/off diagnostic",
        "pair_count": len(pair_rows),
        "context_count": len({row["context_id"] for row in pair_rows}),
        "give_up_penalty": give_up_penalty,
        "bootstrap": {
            "unit": "error_context",
            "samples": bootstrap_samples,
            "seed": bootstrap_seed,
        },
        "score_modes": {
            "base_raw": "base-model mean response log-probability",
            "base_penalized": "base_raw plus give-up penalty",
            "dpo_raw": "adapter-model mean response log-probability",
            "dpo_penalized": "dpo_raw plus give-up penalty",
            "dpo_reward": "adapter minus base sequence-sum log-probability",
        },
        "subsets": subset_reports,
        "acceptance": {
            "dpo_raw_improves_primary": _comparison_passes(
                primary["comparisons"]["dpo_raw_minus_base_raw"]
            ),
            "dpo_penalized_improves_primary": _comparison_passes(
                primary["comparisons"]["dpo_penalized_minus_base_penalized"]
            ),
            "dpo_reward_has_positive_primary_margin": (
                primary["scorers"]["dpo_reward"]["mean_margin_ci95"][0] > 0
            ),
        },
        "pairs": pair_rows,
    }


def pairwise_margin_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# DPO Pairwise Margin Diagnostic",
        "",
        "Positioning: candidate-level adapter-on/off diagnostic; "
        "not an end-to-end generalization result.",
        "",
        f"Pairs: {report['pair_count']} across {report['context_count']} error contexts",
        f"Give-up sensitivity penalty: {report['give_up_penalty']}",
    ]
    for subset_name in (
        "success_over_failure",
        "executable_failure_over_give_up",
        "all",
    ):
        subset = report["subsets"][subset_name]
        lines.extend(
            [
                "",
                f"## {subset_name}",
                "",
                f"Pairs: {subset['pair_count']} | Contexts: {subset['context_count']}",
                "",
                "| scorer | accuracy | accuracy 95% CI | mean margin | margin 95% CI | "
                "median margin | ties |",
                "|---|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for scorer_name, summary in subset["scorers"].items():
            lines.append(
                "| {name} | {accuracy:.3f} | [{acc_lo:.3f}, {acc_hi:.3f}] | "
                "{margin:.4f} | [{margin_lo:.4f}, {margin_hi:.4f}] | {median:.4f} | "
                "{ties:.3f} |".format(
                    name=scorer_name,
                    accuracy=summary["pairwise_accuracy"],
                    acc_lo=summary["pairwise_accuracy_ci95"][0],
                    acc_hi=summary["pairwise_accuracy_ci95"][1],
                    margin=summary["mean_margin"],
                    margin_lo=summary["mean_margin_ci95"][0],
                    margin_hi=summary["mean_margin_ci95"][1],
                    median=summary["median_margin"],
                    ties=summary["tie_rate"],
                )
            )
        lines.extend(
            [
                "",
                "| paired comparison | delta accuracy | accuracy delta 95% CI | "
                "delta mean margin | margin delta 95% CI |",
                "|---|---:|---:|---:|---:|",
            ]
        )
        for comparison_name, summary in subset["comparisons"].items():
            lines.append(
                "| {name} | {accuracy:.3f} | [{acc_lo:.3f}, {acc_hi:.3f}] | "
                "{margin:.4f} | [{margin_lo:.4f}, {margin_hi:.4f}] |".format(
                    name=comparison_name,
                    accuracy=summary["delta_accuracy"],
                    acc_lo=summary["delta_accuracy_ci95"][0],
                    acc_hi=summary["delta_accuracy_ci95"][1],
                    margin=summary["delta_mean_margin"],
                    margin_lo=summary["delta_mean_margin_ci95"][0],
                    margin_hi=summary["delta_mean_margin_ci95"][1],
                )
            )
    acceptance = report["acceptance"]
    lines.extend(
        [
            "",
            "## Acceptance Checks",
            "",
            f"- DPO raw improves the primary subset: `{acceptance['dpo_raw_improves_primary']}`",
            "- DPO with the same penalty improves the primary subset: "
            f"`{acceptance['dpo_penalized_improves_primary']}`",
            "- DPO implicit reward has a positive primary margin: "
            f"`{acceptance['dpo_reward_has_positive_primary_margin']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def _pair_row(
    record: dict[str, Any],
    base_scores: dict[str, LogProbStats],
    dpo_scores: dict[str, LogProbStats],
    give_up_penalty: float,
) -> dict[str, Any] | None:
    prompt = record.get("prompt")
    chosen = record.get("chosen")
    rejected = record.get("rejected")
    if not all(isinstance(value, str) for value in (prompt, chosen, rejected)):
        return None
    chosen_key = score_key(prompt, chosen)
    rejected_key = score_key(prompt, rejected)
    if chosen_key not in base_scores or rejected_key not in base_scores:
        return None
    if chosen_key not in dpo_scores or rejected_key not in dpo_scores:
        return None

    base_chosen = base_scores[chosen_key]
    base_rejected = base_scores[rejected_key]
    dpo_chosen = dpo_scores[chosen_key]
    dpo_rejected = dpo_scores[rejected_key]
    chosen_penalty = give_up_penalty if _is_give_up(chosen) else 0.0
    rejected_penalty = give_up_penalty if _is_give_up(rejected) else 0.0
    margins = {
        "base_raw": base_chosen.mean_logprob - base_rejected.mean_logprob,
        "base_penalized": (
            base_chosen.mean_logprob
            + chosen_penalty
            - base_rejected.mean_logprob
            - rejected_penalty
        ),
        "dpo_raw": dpo_chosen.mean_logprob - dpo_rejected.mean_logprob,
        "dpo_penalized": (
            dpo_chosen.mean_logprob + chosen_penalty - dpo_rejected.mean_logprob - rejected_penalty
        ),
        "dpo_reward": (
            dpo_chosen.sum_logprob
            - base_chosen.sum_logprob
            - dpo_rejected.sum_logprob
            + base_rejected.sum_logprob
        ),
    }
    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    return {
        "context_id": hashlib.sha256(prompt.encode()).hexdigest(),
        "preference_reason": str(metadata.get("preference_reason") or "unknown"),
        "error_type": str(metadata.get("error_type") or "unknown"),
        "chosen_action": _candidate_action(chosen),
        "rejected_action": _candidate_action(rejected),
        "chosen_is_give_up": _is_give_up(chosen),
        "rejected_is_give_up": _is_give_up(rejected),
        "chosen_token_count": {
            "base": base_chosen.token_count,
            "dpo": dpo_chosen.token_count,
        },
        "rejected_token_count": {
            "base": base_rejected.token_count,
            "dpo": dpo_rejected.token_count,
        },
        "margins": margins,
    }


def _summarize_subset(
    rows: list[dict[str, Any]],
    *,
    bootstrap_samples: int,
    bootstrap_seed: int,
) -> dict[str, Any]:
    scorer_names = ("base_raw", "base_penalized", "dpo_raw", "dpo_penalized", "dpo_reward")
    scorers: dict[str, Any] = {}
    for scorer_name in scorer_names:
        margins = [row["margins"][scorer_name] for row in rows]
        accuracy_samples, margin_samples = _cluster_bootstrap(
            rows,
            lambda sampled, name=scorer_name: _accuracy([row["margins"][name] for row in sampled]),
            lambda sampled, name=scorer_name: (
                mean([row["margins"][name] for row in sampled]) if sampled else 0.0
            ),
            samples=bootstrap_samples,
            seed=bootstrap_seed,
        )
        scorers[scorer_name] = {
            "pairwise_accuracy": _accuracy(margins),
            "pairwise_accuracy_ci95": _ci95(accuracy_samples),
            "mean_margin": mean(margins) if margins else 0.0,
            "mean_margin_ci95": _ci95(margin_samples),
            "median_margin": median(margins) if margins else 0.0,
            "tie_rate": (
                sum(abs(value) <= 1e-12 for value in margins) / len(margins) if margins else 0.0
            ),
        }

    comparison_pairs = {
        "dpo_raw_minus_base_raw": ("dpo_raw", "base_raw"),
        "base_penalized_minus_base_raw": ("base_penalized", "base_raw"),
        "dpo_penalized_minus_base_penalized": ("dpo_penalized", "base_penalized"),
    }
    comparisons = {
        name: _summarize_comparison(
            rows,
            left=left,
            right=right,
            bootstrap_samples=bootstrap_samples,
            bootstrap_seed=bootstrap_seed,
        )
        for name, (left, right) in comparison_pairs.items()
    }
    return {
        "pair_count": len(rows),
        "context_count": len({row["context_id"] for row in rows}),
        "scorers": scorers,
        "comparisons": comparisons,
    }


def _summarize_comparison(
    rows: list[dict[str, Any]],
    *,
    left: str,
    right: str,
    bootstrap_samples: int,
    bootstrap_seed: int,
) -> dict[str, Any]:
    delta_accuracy = _accuracy([row["margins"][left] for row in rows]) - _accuracy(
        [row["margins"][right] for row in rows]
    )
    margin_deltas = [row["margins"][left] - row["margins"][right] for row in rows]
    accuracy_samples, margin_samples = _cluster_bootstrap(
        rows,
        lambda sampled: (
            _accuracy([row["margins"][left] for row in sampled])
            - _accuracy([row["margins"][right] for row in sampled])
        ),
        lambda sampled: (
            mean([row["margins"][left] - row["margins"][right] for row in sampled])
            if sampled
            else 0.0
        ),
        samples=bootstrap_samples,
        seed=bootstrap_seed,
    )
    return {
        "delta_accuracy": delta_accuracy,
        "delta_accuracy_ci95": _ci95(accuracy_samples),
        "delta_mean_margin": mean(margin_deltas) if margin_deltas else 0.0,
        "delta_mean_margin_ci95": _ci95(margin_samples),
    }


def _cluster_bootstrap(
    rows: list[dict[str, Any]],
    first_metric: Callable[[list[dict[str, Any]]], float],
    second_metric: Callable[[list[dict[str, Any]]], float],
    *,
    samples: int,
    seed: int,
) -> tuple[list[float], list[float]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[row["context_id"]].append(row)
    group_values = list(groups.values())
    if not group_values or samples <= 0:
        return [first_metric(rows)], [second_metric(rows)]
    rng = random.Random(seed)
    first_values: list[float] = []
    second_values: list[float] = []
    for _ in range(samples):
        sampled: list[dict[str, Any]] = []
        for _ in group_values:
            sampled.extend(rng.choice(group_values))
        first_values.append(first_metric(sampled))
        second_values.append(second_metric(sampled))
    return first_values, second_values


def _accuracy(margins: list[float]) -> float:
    if not margins:
        return 0.0
    wins = sum(1.0 if margin > 0 else 0.5 if abs(margin) <= 1e-12 else 0.0 for margin in margins)
    return wins / len(margins)


def _ci95(values: list[float]) -> list[float]:
    if not values:
        return [0.0, 0.0]
    ordered = sorted(values)
    low = ordered[int(0.025 * (len(ordered) - 1))]
    high = ordered[int(0.975 * (len(ordered) - 1))]
    return [low, high]


def _comparison_passes(comparison: dict[str, Any]) -> bool:
    return bool(
        comparison["delta_accuracy"] > 0
        and comparison["delta_mean_margin"] > 0
        and comparison["delta_accuracy_ci95"][0] > 0
        and comparison["delta_mean_margin_ci95"][0] > 0
    )


def _candidate_action(text: str) -> str:
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return "unknown"
    return str(value.get("action") or "unknown") if isinstance(value, dict) else "unknown"


def _is_give_up(text: str) -> bool:
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return False
    return bool(
        isinstance(value, dict)
        and (value.get("action") == "give_up" or value.get("tool_name") is None)
    )


def scores_to_json(scores: dict[str, LogProbStats]) -> dict[str, dict[str, float | int]]:
    return {key: asdict(value) for key, value in scores.items()}


def scores_from_json(raw: dict[str, dict[str, Any]]) -> dict[str, LogProbStats]:
    return {
        key: LogProbStats(
            mean_logprob=float(value["mean_logprob"]),
            sum_logprob=float(value["sum_logprob"]),
            token_count=int(value["token_count"]),
        )
        for key, value in raw.items()
    }
