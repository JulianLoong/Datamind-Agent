from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from rpl.agent_engine.step import TaskResult


@dataclass
class TaskEvalRecord:
    baseline: str
    goal: str
    split: str
    expected_error_type: str | None
    failure_family: str | None
    status: str
    recovery_attempts: int
    tool_calls: int
    tokens: int
    latency_ms: float
    recovery_tokens: int
    recovery_latency_ms: float
    recovery_trace: list[dict[str, Any]]
    selector_tokens: int = 0
    selector_evals: int = 0


def task_record(
    *,
    baseline: str,
    goal: str,
    split: str,
    expected_error_type: str | None,
    failure_family: str | None = None,
    result: TaskResult,
) -> TaskEvalRecord:
    return TaskEvalRecord(
        baseline=baseline,
        goal=goal,
        split=split,
        expected_error_type=expected_error_type,
        failure_family=failure_family,
        status=result.status,
        recovery_attempts=sum(len(step.recovery_attempts) for step in result.steps),
        tool_calls=sum(1 + len(step.recovery_attempts) for step in result.steps),
        tokens=result.total_tokens,
        latency_ms=result.total_latency_ms,
        recovery_tokens=result.recovery_tokens,
        recovery_latency_ms=result.recovery_latency_ms,
        recovery_trace=_recovery_trace(result),
        selector_tokens=result.selector_tokens,
        selector_evals=result.selector_evals,
    )


def summarize_records(records: list[TaskEvalRecord]) -> dict[str, float | int | str]:
    total = len(records)
    failed_tasks = [record for record in records if record.expected_error_type is not None]
    recovered = sum(1 for record in failed_tasks if record.status == "success")
    return {
        "tasks": total,
        "failure_tasks": len(failed_tasks),
        "recovery_success_rate": recovered / len(failed_tasks) if failed_tasks else 0.0,
        "avg_recovery_attempts": _avg(record.recovery_attempts for record in failed_tasks),
        "avg_total_recovery_tokens": _avg(
            record.recovery_tokens + record.selector_tokens for record in failed_tasks
        ),
    }


def summarize_records_by_split(
    records: list[TaskEvalRecord],
) -> dict[str, dict[str, float | int | str]]:
    grouped: dict[str, list[TaskEvalRecord]] = {}
    for record in records:
        grouped.setdefault(record.split, []).append(record)
    return {
        split: summarize_records(split_records) for split, split_records in sorted(grouped.items())
    }


def summarize_records_by_failure_type(
    records: list[TaskEvalRecord],
) -> dict[str, dict[str, float | int | str]]:
    grouped: dict[str, list[TaskEvalRecord]] = {}
    for record in records:
        key = record.expected_error_type or "clean"
        grouped.setdefault(key, []).append(record)
    return {
        error_type: summarize_records(type_records)
        for error_type, type_records in sorted(grouped.items())
    }


def summarize_records_by_failure_family(
    records: list[TaskEvalRecord],
) -> dict[str, dict[str, float | int | str]]:
    grouped: dict[str, list[TaskEvalRecord]] = {}
    for record in records:
        key = record.failure_family or (
            "clean" if record.expected_error_type is None else "unlabeled_failure"
        )
        grouped.setdefault(key, []).append(record)
    return {
        family: summarize_records(family_records)
        for family, family_records in sorted(grouped.items())
    }


def _avg(values) -> float:
    items = list(values)
    return sum(items) / len(items) if items else 0.0


def _recovery_trace(result: TaskResult) -> list[dict[str, Any]]:
    trace: list[dict[str, Any]] = []
    for step in result.steps:
        for attempt_index, attempt in enumerate(step.recovery_attempts):
            trace.append(
                {
                    "step_index": step.index,
                    "step_description": step.description,
                    "attempt_index": attempt_index,
                    "chosen_index": attempt.chosen_index,
                    "outcome": attempt.outcome.value,
                    "error_context": asdict(attempt.error_context)
                    if attempt.error_context is not None
                    else None,
                    "initial_result": asdict(attempt.initial_result)
                    if attempt.initial_result is not None
                    else None,
                    "final_result": asdict(attempt.final_result)
                    if attempt.final_result is not None
                    else None,
                    "candidate_tokens": attempt.candidate_tokens,
                    "candidate_latency_ms": attempt.candidate_latency_ms,
                    "selector_tokens": attempt.selector_tokens,
                    "selector_evals": attempt.selector_evals,
                    "pm_scores": attempt.pm_scores,
                    "candidates": [asdict(candidate) for candidate in attempt.candidates],
                }
            )
    return trace
