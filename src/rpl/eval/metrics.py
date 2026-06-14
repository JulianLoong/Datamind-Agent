from __future__ import annotations

from dataclasses import dataclass

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
    )


def summarize_records(records: list[TaskEvalRecord]) -> dict[str, float | int | str]:
    total = len(records)
    success = sum(1 for record in records if record.status == "success")
    failed_tasks = [record for record in records if record.expected_error_type is not None]
    recovered = sum(1 for record in failed_tasks if record.status == "success")
    recovered_tasks = [record for record in failed_tasks if record.status == "success"]
    unrecovered_tasks = [record for record in failed_tasks if record.status != "success"]
    return {
        "tasks": total,
        "success_rate": success / total if total else 0.0,
        "failure_tasks": len(failed_tasks),
        "recovery_success_rate": recovered / len(failed_tasks) if failed_tasks else 0.0,
        "avg_recovery_attempts": _avg(record.recovery_attempts for record in records),
        "avg_recovery_attempts_on_failure_tasks": _avg(record.recovery_attempts for record in failed_tasks),
        "avg_recovery_attempts_on_recovered": _avg(record.recovery_attempts for record in recovered_tasks),
        "avg_recovery_attempts_on_unrecovered": _avg(record.recovery_attempts for record in unrecovered_tasks),
        "avg_tool_calls": _avg(record.tool_calls for record in records),
        "avg_tool_calls_on_failure_tasks": _avg(record.tool_calls for record in failed_tasks),
        "avg_tool_calls_on_recovered": _avg(record.tool_calls for record in recovered_tasks),
        "avg_tokens": _avg(record.tokens for record in records),
        "avg_latency_ms": _avg(record.latency_ms for record in records),
        "avg_recovery_tokens": _avg(record.recovery_tokens for record in records),
        "avg_recovery_latency_ms": _avg(record.recovery_latency_ms for record in records),
    }


def summarize_records_by_split(records: list[TaskEvalRecord]) -> dict[str, dict[str, float | int | str]]:
    grouped: dict[str, list[TaskEvalRecord]] = {}
    for record in records:
        grouped.setdefault(record.split, []).append(record)
    return {split: summarize_records(split_records) for split, split_records in sorted(grouped.items())}


def summarize_records_by_failure_type(records: list[TaskEvalRecord]) -> dict[str, dict[str, float | int | str]]:
    grouped: dict[str, list[TaskEvalRecord]] = {}
    for record in records:
        key = record.expected_error_type or "clean"
        grouped.setdefault(key, []).append(record)
    return {error_type: summarize_records(type_records) for error_type, type_records in sorted(grouped.items())}


def summarize_records_by_failure_family(records: list[TaskEvalRecord]) -> dict[str, dict[str, float | int | str]]:
    grouped: dict[str, list[TaskEvalRecord]] = {}
    for record in records:
        key = record.failure_family or ("clean" if record.expected_error_type is None else "unlabeled_failure")
        grouped.setdefault(key, []).append(record)
    return {family: summarize_records(family_records) for family, family_records in sorted(grouped.items())}


def _avg(values) -> float:
    items = list(values)
    return sum(items) / len(items) if items else 0.0
