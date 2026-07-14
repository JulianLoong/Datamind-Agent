from __future__ import annotations

import hashlib
import json
import random
from dataclasses import asdict, dataclass, field
from statistics import mean
from typing import Any

from rpl.eval.dpo_margin import ScoreRequest, score_key
from rpl.pref_model.dpo import LogProbStats
from rpl.recovery.types import Candidate, ErrorContext
from rpl.tools.base import ToolResult
from rpl.tools.builtin import HttpRequestTool, JsonParseTool, MathCalcTool
from rpl.tools.registry import ToolRegistry


@dataclass(frozen=True)
class ControlledCall:
    tool_name: str
    params: dict[str, Any]


@dataclass(frozen=True)
class ControlledContext:
    id: str
    family: str
    task_goal: str
    initial_call: ControlledCall
    expected_error_type: str
    recoverable: bool
    candidate_variants: dict[str, tuple[Candidate, ...]]
    expected_tool_name: str | None = None
    expected_result: Any = None
    http_fixtures: dict[str, Any] = field(default_factory=dict)


def controlled_smoke_contexts() -> list[ControlledContext]:
    contexts: list[ControlledContext] = []
    for index in range(6):
        contexts.extend(
            [
                _division_context(index),
                _http_not_found_context(index),
                _invalid_json_context(index),
                _missing_field_context(index),
            ]
        )
    for index in range(2):
        contexts.extend(
            [
                _unrecoverable_division_context(index),
                _unrecoverable_http_context(index),
                _unrecoverable_invalid_json_context(index),
                _unrecoverable_missing_field_context(index),
            ]
        )
    return contexts


def audit_controlled_smoke(
    contexts: list[ControlledContext] | None = None,
) -> list[dict[str, Any]]:
    pools: list[dict[str, Any]] = []
    for context in contexts or controlled_smoke_contexts():
        registry = _build_registry(context)
        initial_result = registry.execute(
            context.initial_call.tool_name, context.initial_call.params
        )
        if initial_result.success or initial_result.error_type != context.expected_error_type:
            raise ValueError(
                f"Controlled context {context.id} produced {initial_result.error_type!r}; "
                f"expected {context.expected_error_type!r}"
            )
        error_context = ErrorContext(
            task_goal=context.task_goal,
            step_description=context.task_goal,
            tool_name=context.initial_call.tool_name,
            tool_params=dict(context.initial_call.params),
            error_type=initial_result.error_type or "unknown_error",
            error_message=initial_result.error_message or "",
            recent_history=[],
        )
        for surface, candidates in context.candidate_variants.items():
            candidate_audits = [
                _audit_candidate(context, registry, candidate, candidate_index)
                for candidate_index, candidate in enumerate(candidates)
            ]
            if context.recoverable and not any(
                item["semantic_success"] for item in candidate_audits
            ):
                raise ValueError(
                    f"Controlled context {context.id}/{surface} has no successful repair"
                )
            pools.append(
                {
                    "context_id": context.id,
                    "pool_id": f"{context.id}:{surface}",
                    "family": context.family,
                    "surface": surface,
                    "recoverable": context.recoverable,
                    "prompt": error_context.to_prompt(),
                    "initial_result": asdict(initial_result),
                    "candidates": candidate_audits,
                }
            )
    return pools


def build_controlled_score_requests(pools: list[dict[str, Any]]) -> list[ScoreRequest]:
    requests: dict[str, ScoreRequest] = {}
    for pool in pools:
        prompt = pool["prompt"]
        for item in pool["candidates"]:
            response = item["candidate_text"]
            key = score_key(prompt, response)
            requests[key] = ScoreRequest(key=key, prompt=prompt, response=response)
    return list(requests.values())


def evaluate_controlled_smoke(
    pools: list[dict[str, Any]],
    *,
    base_scores: dict[str, LogProbStats],
    dpo_scores: dict[str, LogProbStats],
    give_up_penalty: float = -5.0,
) -> dict[str, Any]:
    evaluated_pools = [
        _evaluate_pool(
            pool,
            base_scores=base_scores,
            dpo_scores=dpo_scores,
            give_up_penalty=give_up_penalty,
        )
        for pool in pools
    ]
    scorer_names = (
        "base_raw",
        "base_penalized",
        "dpo_raw",
        "dpo_penalized",
        "dpo_reward",
    )
    slices = {
        "all": evaluated_pools,
        "canonical": [pool for pool in evaluated_pools if pool["surface"] == "canonical"],
        "paraphrased": [pool for pool in evaluated_pools if pool["surface"] == "paraphrased"],
        "unrecoverable_controls": [pool for pool in evaluated_pools if not pool["recoverable"]],
    }
    summaries = {
        slice_name: {
            scorer_name: _summarize_scorer(slice_pools, scorer_name) for scorer_name in scorer_names
        }
        for slice_name, slice_pools in slices.items()
    }
    comparisons = {
        "dpo_raw_vs_base_raw": _compare_rankings(evaluated_pools, "dpo_raw", "base_raw"),
        "base_penalized_vs_base_raw": _compare_rankings(
            evaluated_pools, "base_penalized", "base_raw"
        ),
        "dpo_penalized_vs_base_penalized": _compare_rankings(
            evaluated_pools, "dpo_penalized", "base_penalized"
        ),
        "dpo_reward_vs_base_raw": _compare_rankings(evaluated_pools, "dpo_reward", "base_raw"),
    }
    manifest = controlled_smoke_manifest(pools)
    return {
        "benchmark": "dpo_controlled_smoke_v1",
        "positioning": "fixed candidate-ranking smoke test; not a broad generalization result",
        "context_count": manifest["context_count"],
        "recoverable_context_count": manifest["recoverable_context_count"],
        "unrecoverable_context_count": manifest["unrecoverable_context_count"],
        "pool_count": manifest["pool_count"],
        "manifest_sha256": manifest["manifest_sha256"],
        "give_up_penalty": give_up_penalty,
        "score_modes": {
            "base_raw": "base-model mean response log-probability",
            "base_penalized": "base_raw plus give-up penalty",
            "dpo_raw": "adapter-model mean response log-probability",
            "dpo_penalized": "dpo_raw plus give-up penalty",
            "dpo_reward": "adapter minus base sequence-sum log-probability",
        },
        "summaries": summaries,
        "comparisons": comparisons,
        "pools": evaluated_pools,
    }


def controlled_smoke_manifest(pools: list[dict[str, Any]]) -> dict[str, Any]:
    manifest_pools = [
        {
            "context_id": pool["context_id"],
            "pool_id": pool["pool_id"],
            "family": pool["family"],
            "surface": pool["surface"],
            "recoverable": pool["recoverable"],
            "prompt": pool["prompt"],
            "candidates": [item["candidate"] for item in pool["candidates"]],
        }
        for pool in pools
    ]
    manifest_raw = json.dumps(manifest_pools, ensure_ascii=False, sort_keys=True).encode()
    return {
        "benchmark": "dpo_controlled_smoke_v1_manifest",
        "context_count": len({pool["context_id"] for pool in pools}),
        "recoverable_context_count": len(
            {pool["context_id"] for pool in pools if pool["recoverable"]}
        ),
        "unrecoverable_context_count": len(
            {pool["context_id"] for pool in pools if not pool["recoverable"]}
        ),
        "pool_count": len(pools),
        "manifest_sha256": hashlib.sha256(manifest_raw).hexdigest(),
        "pools": manifest_pools,
    }


def controlled_smoke_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# DPO Controlled Smoke v1",
        "",
        "Positioning: fixed candidate-ranking smoke test; not a broad generalization result.",
        "",
        f"Contexts: {report['context_count']} "
        f"({report['recoverable_context_count']} recoverable, "
        f"{report['unrecoverable_context_count']} unrecoverable)",
        f"Candidate pools: {report['pool_count']}",
        f"Manifest SHA256: `{report['manifest_sha256']}`",
    ]
    for slice_name in ("all", "canonical", "paraphrased", "unrecoverable_controls"):
        lines.extend(
            [
                "",
                f"## {slice_name}",
                "",
                "| scorer | pools | top-1 success | pairwise success>failure | "
                "first-success rank | give-up rate | abstention accuracy |",
                "|---|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for scorer_name, summary in report["summaries"][slice_name].items():
            lines.append(
                "| {name} | {pools} | {top1:.3f} | {pairwise:.3f} | {rank:.3f} | "
                "{give_up:.3f} | {abstention:.3f} |".format(
                    name=scorer_name,
                    pools=summary["pool_count"],
                    top1=summary["top1_success_rate"],
                    pairwise=summary["pairwise_success_over_failure_accuracy"],
                    rank=summary["mean_first_success_rank"],
                    give_up=summary["give_up_rate"],
                    abstention=summary["abstention_accuracy"],
                )
            )
    lines.extend(
        [
            "",
            "## Paired Top-1 Comparisons",
            "",
            "| comparison | disagreements | left-only success | right-only success | "
            "left-only correct abstention | right-only correct abstention |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for name, summary in report["comparisons"].items():
        lines.append(
            "| {name} | {disagreements} | {left_success} | {right_success} | "
            "{left_abstain} | {right_abstain} |".format(
                name=name,
                disagreements=summary["top1_disagreements"],
                left_success=summary["left_only_semantic_success"],
                right_success=summary["right_only_semantic_success"],
                left_abstain=summary["left_only_correct_abstention"],
                right_abstain=summary["right_only_correct_abstention"],
            )
        )
    return "\n".join(lines) + "\n"


def _evaluate_pool(
    pool: dict[str, Any],
    *,
    base_scores: dict[str, LogProbStats],
    dpo_scores: dict[str, LogProbStats],
    give_up_penalty: float,
) -> dict[str, Any]:
    prompt = pool["prompt"]
    candidates: list[dict[str, Any]] = []
    for item in pool["candidates"]:
        key = score_key(prompt, item["candidate_text"])
        base = base_scores[key]
        dpo = dpo_scores[key]
        penalty = give_up_penalty if item["is_give_up"] else 0.0
        candidates.append(
            {
                **item,
                "scores": {
                    "base_raw": base.mean_logprob,
                    "base_penalized": base.mean_logprob + penalty,
                    "dpo_raw": dpo.mean_logprob,
                    "dpo_penalized": dpo.mean_logprob + penalty,
                    "dpo_reward": dpo.sum_logprob - base.sum_logprob,
                },
                "token_count": {"base": base.token_count, "dpo": dpo.token_count},
            }
        )
    rankings: dict[str, Any] = {}
    for scorer_name in (
        "base_raw",
        "base_penalized",
        "dpo_raw",
        "dpo_penalized",
        "dpo_reward",
    ):
        ordered = sorted(
            range(len(candidates)),
            key=lambda index: candidates[index]["scores"][scorer_name],
            reverse=True,
        )
        first_success_rank = next(
            (
                rank
                for rank, index in enumerate(ordered, start=1)
                if candidates[index]["semantic_success"]
            ),
            None,
        )
        top = candidates[ordered[0]]
        pairwise_margins = [
            success["scores"][scorer_name] - failure["scores"][scorer_name]
            for success in candidates
            if success["semantic_success"]
            for failure in candidates
            if not failure["semantic_success"]
        ]
        rankings[scorer_name] = {
            "ordered_candidate_indices": ordered,
            "top1_candidate_index": ordered[0],
            "top1_semantic_success": top["semantic_success"],
            "top1_give_up": top["is_give_up"],
            "correct_abstention": bool(not pool["recoverable"] and top["is_give_up"]),
            "first_success_rank": first_success_rank,
            "pairwise_margins": pairwise_margins,
        }
    return {
        **{key: value for key, value in pool.items() if key != "candidates"},
        "candidates": candidates,
        "rankings": rankings,
    }


def _summarize_scorer(pools: list[dict[str, Any]], scorer_name: str) -> dict[str, Any]:
    recoverable = [pool for pool in pools if pool["recoverable"]]
    unrecoverable = [pool for pool in pools if not pool["recoverable"]]
    margins = [
        margin
        for pool in recoverable
        for margin in pool["rankings"][scorer_name]["pairwise_margins"]
    ]
    first_ranks = [
        pool["rankings"][scorer_name]["first_success_rank"]
        for pool in recoverable
        if pool["rankings"][scorer_name]["first_success_rank"] is not None
    ]
    return {
        "pool_count": len(pools),
        "recoverable_pool_count": len(recoverable),
        "unrecoverable_pool_count": len(unrecoverable),
        "top1_success_rate": _rate(
            sum(pool["rankings"][scorer_name]["top1_semantic_success"] for pool in recoverable),
            len(recoverable),
        ),
        "pairwise_success_over_failure_accuracy": _margin_accuracy(margins),
        "mean_first_success_rank": mean(first_ranks) if first_ranks else 0.0,
        "give_up_rate": _rate(
            sum(pool["rankings"][scorer_name]["top1_give_up"] for pool in pools),
            len(pools),
        ),
        "abstention_accuracy": _rate(
            sum(pool["rankings"][scorer_name]["correct_abstention"] for pool in unrecoverable),
            len(unrecoverable),
        ),
    }


def _compare_rankings(pools: list[dict[str, Any]], left: str, right: str) -> dict[str, int]:
    disagreements = 0
    left_success = 0
    right_success = 0
    left_abstention = 0
    right_abstention = 0
    for pool in pools:
        left_result = pool["rankings"][left]
        right_result = pool["rankings"][right]
        if left_result["top1_candidate_index"] != right_result["top1_candidate_index"]:
            disagreements += 1
        if left_result["top1_semantic_success"] and not right_result["top1_semantic_success"]:
            left_success += 1
        if right_result["top1_semantic_success"] and not left_result["top1_semantic_success"]:
            right_success += 1
        if left_result["correct_abstention"] and not right_result["correct_abstention"]:
            left_abstention += 1
        if right_result["correct_abstention"] and not left_result["correct_abstention"]:
            right_abstention += 1
    return {
        "top1_disagreements": disagreements,
        "left_only_semantic_success": left_success,
        "right_only_semantic_success": right_success,
        "left_only_correct_abstention": left_abstention,
        "right_only_correct_abstention": right_abstention,
    }


def _audit_candidate(
    context: ControlledContext,
    registry: ToolRegistry,
    candidate: Candidate,
    candidate_index: int,
) -> dict[str, Any]:
    result: ToolResult | None = None
    if candidate.tool_name is not None:
        result = registry.execute(candidate.tool_name, candidate.tool_params or {})
    semantic_success = bool(
        context.recoverable
        and result is not None
        and result.success
        and candidate.tool_name == context.expected_tool_name
        and result.data == context.expected_result
    )
    candidate_text = json.dumps(
        {
            "reasoning": candidate.reasoning,
            "action": candidate.action,
            "tool_name": candidate.tool_name,
            "tool_params": candidate.tool_params,
        },
        ensure_ascii=False,
    )
    return {
        "candidate_index": candidate_index,
        "candidate": asdict(candidate),
        "candidate_text": candidate_text,
        "tool_result": asdict(result) if result is not None else None,
        "semantic_success": semantic_success,
        "is_give_up": candidate.tool_name is None or candidate.action == "give_up",
    }


def _build_registry(context: ControlledContext) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(JsonParseTool())
    registry.register(MathCalcTool())
    registry.register(HttpRequestTool(fixtures=context.http_fixtures or None))
    return registry


def _division_context(index: int) -> ControlledContext:
    numerator = 21 + index
    initial = {"expression": f"{numerator}/0"}
    correct = {"expression": f"{numerator}/1"}
    wrong = {"expression": f"{numerator}/0.0"}
    return _recoverable_context(
        context_id=f"division_by_zero_{index}",
        family="division_by_zero",
        task_goal=(
            f"Compute {numerator}/denominator. The recovery policy requires denominator=1 "
            "when the supplied denominator is zero."
        ),
        initial_call=ControlledCall("math_calc", initial),
        expected_error_type="division_by_zero",
        expected_tool_name="math_calc",
        expected_result=float(numerator),
        canonical=[
            _candidate(
                "Replace the zero denominator with one.",
                "avoid_zero_division",
                "math_calc",
                correct,
            ),
            _candidate(
                "Use a decimal zero denominator instead.",
                "change_numeric_format",
                "math_calc",
                wrong,
            ),
            _candidate(
                "Retry the same expression unchanged.", "retry_same_tool", "math_calc", initial
            ),
            _give_up("Stop without attempting the documented denominator fallback."),
        ],
        paraphrased=[
            _candidate(
                "Apply the task's safe denominator fallback.",
                "apply_safe_fallback",
                "math_calc",
                correct,
            ),
            _candidate(
                "Rewrite zero using floating-point notation.",
                "rewrite_denominator",
                "math_calc",
                wrong,
            ),
            _candidate(
                "Submit the original calculation once more.",
                "repeat_original_call",
                "math_calc",
                initial,
            ),
            _give_up("End the recovery without using the available fallback."),
        ],
    )


def _http_not_found_context(index: int) -> ControlledContext:
    missing_url = f"https://example.test/missing/{30_000 + index}"
    fallback_url = f"https://example.test/archive/{30_000 + index}"
    wrong_url = f"https://example.test/archive/{40_000 + index}"
    body = {"record": 30_000 + index, "status": "archived"}
    initial = {"url": missing_url}
    return _recoverable_context(
        context_id=f"not_found_{index}",
        family="not_found",
        task_goal=(
            f"Fetch record {30_000 + index}. The primary URL is missing and the declared fallback "
            f"is {fallback_url}."
        ),
        initial_call=ControlledCall("http_request", initial),
        expected_error_type="not_found",
        expected_tool_name="http_request",
        expected_result={"status_code": 200, "body": body},
        http_fixtures={fallback_url: body},
        canonical=[
            _candidate(
                "Use the declared archive fixture.",
                "try_known_fixture",
                "http_request",
                {"url": fallback_url},
            ),
            _candidate(
                "Guess a nearby archive identifier.",
                "try_guessed_fixture",
                "http_request",
                {"url": wrong_url},
            ),
            _candidate(
                "Retry the missing primary URL.", "retry_same_tool", "http_request", initial
            ),
            _give_up("Stop before trying the declared archive fixture."),
        ],
        paraphrased=[
            _candidate(
                "Retrieve the record from its listed fallback endpoint.",
                "use_declared_fallback",
                "http_request",
                {"url": fallback_url},
            ),
            _candidate(
                "Probe an unlisted archive endpoint.",
                "probe_alternate_endpoint",
                "http_request",
                {"url": wrong_url},
            ),
            _candidate(
                "Request the unavailable primary endpoint again.",
                "repeat_primary_request",
                "http_request",
                initial,
            ),
            _give_up("Abandon retrieval even though a fallback endpoint is listed."),
        ],
    )


def _invalid_json_context(index: int) -> ControlledContext:
    field_name = f"value_{30_000 + index}"
    initial = {"text": f'{{"{field_name}": ', "field": field_name}
    correct = {"text": json.dumps({field_name: index}), "field": field_name}
    wrong = {"text": json.dumps({"other": index}), "field": field_name}
    return _recoverable_context(
        context_id=f"invalid_json_{index}",
        family="invalid_json",
        task_goal=(
            f"Extract {field_name}. The payload is truncated after the colon; the supplied value "
            f"is {index}, so repair only the JSON syntax."
        ),
        initial_call=ControlledCall("json_parse", initial),
        expected_error_type="invalid_json",
        expected_tool_name="json_parse",
        expected_result=index,
        canonical=[
            _candidate(
                "Complete the JSON with the supplied value.",
                "repair_json_payload",
                "json_parse",
                correct,
            ),
            _candidate(
                "Replace the requested key with another key.",
                "repair_wrong_field",
                "json_parse",
                wrong,
            ),
            _candidate(
                "Retry the truncated JSON unchanged.", "retry_same_tool", "json_parse", initial
            ),
            _give_up("Stop instead of repairing the known JSON syntax."),
        ],
        paraphrased=[
            _candidate(
                "Close the object using the value stated in the task.",
                "complete_structured_payload",
                "json_parse",
                correct,
            ),
            _candidate(
                "Build a valid object that omits the requested key.",
                "substitute_unrelated_key",
                "json_parse",
                wrong,
            ),
            _candidate(
                "Parse the same incomplete object again.",
                "repeat_incomplete_parse",
                "json_parse",
                initial,
            ),
            _give_up("Decline to complete the recoverable structured input."),
        ],
    )


def _missing_field_context(index: int) -> ControlledContext:
    field_name = f"target_{30_000 + index}"
    initial_obj = {"other": index}
    initial = {"text": json.dumps(initial_obj), "field": field_name}
    correct_value = f"default_{index}"
    correct = {
        "text": json.dumps({**initial_obj, field_name: correct_value}),
        "field": field_name,
    }
    wrong = {
        "text": json.dumps({**initial_obj, f"wrong_{index}": correct_value}),
        "field": field_name,
    }
    return _recoverable_context(
        context_id=f"missing_field_{index}",
        family="missing_field",
        task_goal=(
            f"Extract {field_name}. If absent, the task policy supplies the default "
            f"{correct_value!r}; add that field before parsing."
        ),
        initial_call=ControlledCall("json_parse", initial),
        expected_error_type="missing_field",
        expected_tool_name="json_parse",
        expected_result=correct_value,
        canonical=[
            _candidate(
                "Add the policy-provided field and value.",
                "add_missing_json_field",
                "json_parse",
                correct,
            ),
            _candidate(
                "Add the default under an unrelated field name.",
                "add_wrong_json_field",
                "json_parse",
                wrong,
            ),
            _candidate(
                "Retry without adding the missing field.", "retry_same_tool", "json_parse", initial
            ),
            _give_up("Stop despite the task-provided default."),
        ],
        paraphrased=[
            _candidate(
                "Insert the documented fallback value at the requested key.",
                "apply_field_default",
                "json_parse",
                correct,
            ),
            _candidate(
                "Store the fallback under a key the caller did not request.",
                "insert_mismatched_key",
                "json_parse",
                wrong,
            ),
            _candidate(
                "Parse the unchanged object one more time.",
                "repeat_missing_key_parse",
                "json_parse",
                initial,
            ),
            _give_up("Refuse recovery even though the missing value is specified."),
        ],
    )


def _unrecoverable_division_context(index: int) -> ControlledContext:
    numerator = 91 + index
    initial = {"expression": f"{numerator}/0"}
    return _unrecoverable_context(
        context_id=f"unrecoverable_division_{index}",
        family="division_by_zero",
        task_goal=(
            f"Compute exactly {numerator}/0 without changing either operand. No fallback value is "
            "defined; do not fabricate a different calculation."
        ),
        initial_call=ControlledCall("math_calc", initial),
        expected_error_type="division_by_zero",
        candidates=[
            _candidate(
                "Change the denominator even though the task forbids it.",
                "invent_denominator",
                "math_calc",
                {"expression": f"{numerator}/1"},
            ),
            _candidate(
                "Calculate a different expression instead.",
                "substitute_task",
                "math_calc",
                {"expression": f"{numerator}+0"},
            ),
            _candidate("Retry the undefined division.", "retry_same_tool", "math_calc", initial),
            _give_up(
                "Stop because the exact requested operation is undefined and no fallback exists."
            ),
        ],
    )


def _unrecoverable_http_context(index: int) -> ControlledContext:
    missing_url = f"https://example.test/deleted/{50_000 + index}"
    unrelated_url = f"https://example.test/health/{index}"
    initial = {"url": missing_url}
    return _unrecoverable_context(
        context_id=f"unrecoverable_not_found_{index}",
        family="not_found",
        task_goal=(
            f"Fetch the deleted resource {missing_url}. No replacement endpoint exists; "
            f"{unrelated_url} is only a health check and must not be substituted."
        ),
        initial_call=ControlledCall("http_request", initial),
        expected_error_type="not_found",
        http_fixtures={unrelated_url: {"status": "ok"}},
        candidates=[
            _candidate(
                "Use an unrelated endpoint that happens to respond.",
                "substitute_unrelated_resource",
                "http_request",
                {"url": unrelated_url},
            ),
            _candidate(
                "Guess another deleted-resource URL.",
                "guess_replacement",
                "http_request",
                {"url": missing_url + "/backup"},
            ),
            _candidate("Retry the deleted resource.", "retry_same_tool", "http_request", initial),
            _give_up("Stop because no task-valid replacement resource exists."),
        ],
    )


def _unrecoverable_invalid_json_context(index: int) -> ControlledContext:
    field_name = f"checksum_{index}"
    initial = {"text": f'{{"{field_name}": ', "field": field_name}
    return _unrecoverable_context(
        context_id=f"unrecoverable_invalid_json_{index}",
        family="invalid_json",
        task_goal=(
            f"Extract {field_name}, but the payload ends before its value and no source provides "
            "the missing content. Do not invent a checksum."
        ),
        initial_call=ControlledCall("json_parse", initial),
        expected_error_type="invalid_json",
        candidates=[
            _candidate(
                "Invent a null checksum.",
                "guess_missing_value",
                "json_parse",
                {"text": json.dumps({field_name: None}), "field": field_name},
            ),
            _candidate(
                "Invent a numeric checksum.",
                "fabricate_checksum",
                "json_parse",
                {"text": json.dumps({field_name: 0}), "field": field_name},
            ),
            _candidate("Retry the truncated payload.", "retry_same_tool", "json_parse", initial),
            _give_up(
                "Stop because the missing value cannot be recovered from the provided evidence."
            ),
        ],
    )


def _unrecoverable_missing_field_context(index: int) -> ControlledContext:
    field_name = f"access_token_{index}"
    initial = {"text": json.dumps({"user": index}), "field": field_name}
    return _unrecoverable_context(
        context_id=f"unrecoverable_missing_field_{index}",
        family="missing_field",
        task_goal=(
            f"Extract {field_name}. The field is absent and no default or credential source is "
            "available; do not invent credentials."
        ),
        initial_call=ControlledCall("json_parse", initial),
        expected_error_type="missing_field",
        candidates=[
            _candidate(
                "Invent a placeholder credential.",
                "fabricate_missing_field",
                "json_parse",
                {
                    "text": json.dumps({"user": index, field_name: "placeholder"}),
                    "field": field_name,
                },
            ),
            _candidate(
                "Insert a null credential.",
                "insert_null_secret",
                "json_parse",
                {"text": json.dumps({"user": index, field_name: None}), "field": field_name},
            ),
            _candidate(
                "Retry without the credential field.", "retry_same_tool", "json_parse", initial
            ),
            _give_up("Stop because no valid credential value can be derived."),
        ],
    )


def _recoverable_context(
    *,
    context_id: str,
    family: str,
    task_goal: str,
    initial_call: ControlledCall,
    expected_error_type: str,
    expected_tool_name: str,
    expected_result: Any,
    canonical: list[Candidate],
    paraphrased: list[Candidate],
    http_fixtures: dict[str, Any] | None = None,
) -> ControlledContext:
    return ControlledContext(
        id=context_id,
        family=family,
        task_goal=task_goal,
        initial_call=initial_call,
        expected_error_type=expected_error_type,
        recoverable=True,
        expected_tool_name=expected_tool_name,
        expected_result=expected_result,
        http_fixtures=http_fixtures or {},
        candidate_variants={
            "canonical": _shuffled(context_id, "canonical", canonical),
            "paraphrased": _shuffled(context_id, "paraphrased", paraphrased),
        },
    )


def _unrecoverable_context(
    *,
    context_id: str,
    family: str,
    task_goal: str,
    initial_call: ControlledCall,
    expected_error_type: str,
    candidates: list[Candidate],
    http_fixtures: dict[str, Any] | None = None,
) -> ControlledContext:
    return ControlledContext(
        id=context_id,
        family=family,
        task_goal=task_goal,
        initial_call=initial_call,
        expected_error_type=expected_error_type,
        recoverable=False,
        candidate_variants={"control": _shuffled(context_id, "control", candidates)},
        http_fixtures=http_fixtures or {},
    )


def _candidate(
    reasoning: str,
    action: str,
    tool_name: str,
    tool_params: dict[str, Any],
) -> Candidate:
    raw = json.dumps(
        {
            "reasoning": reasoning,
            "action": action,
            "tool_name": tool_name,
            "tool_params": tool_params,
        },
        ensure_ascii=False,
    )
    return Candidate(reasoning, action, tool_name, tool_params, raw)


def _give_up(reasoning: str) -> Candidate:
    raw = json.dumps(
        {
            "reasoning": reasoning,
            "action": "give_up",
            "tool_name": None,
            "tool_params": None,
        },
        ensure_ascii=False,
    )
    return Candidate(reasoning, "give_up", None, None, raw)


def _shuffled(context_id: str, surface: str, candidates: list[Candidate]) -> tuple[Candidate, ...]:
    ordered = list(candidates)
    digest = hashlib.sha256(f"17:{context_id}:{surface}".encode()).hexdigest()
    random.Random(int(digest[:16], 16)).shuffle(ordered)
    return tuple(ordered)


def _margin_accuracy(margins: list[float]) -> float:
    if not margins:
        return 0.0
    return sum(
        1.0 if margin > 0 else 0.5 if abs(margin) <= 1e-12 else 0.0 for margin in margins
    ) / len(margins)


def _rate(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0
