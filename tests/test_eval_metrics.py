from __future__ import annotations

from rpl.eval.metrics import (
    TaskEvalRecord,
    summarize_records,
    summarize_records_by_failure_family,
    summarize_records_by_failure_type,
    summarize_records_by_split,
)


def _record(
    goal: str,
    split: str,
    expected_error_type: str | None,
    status: str,
    recovery_attempts: int,
    tool_calls: int,
    *,
    failure_family: str | None = None,
) -> TaskEvalRecord:
    return TaskEvalRecord(
        "pm",
        goal,
        split,
        expected_error_type,
        failure_family,
        status,
        recovery_attempts,
        tool_calls,
        0,
        1.0,
        0,
        0.0,
        [],
    )


def test_summarize_records_reports_recovery_headline_metrics() -> None:
    records = [
        _record("a", "train", "division_by_zero", "success", 1, 2),
        _record("b", "train", "not_found", "failed", 3, 4),
        _record("c", "clean", None, "success", 0, 1),
    ]

    summary = summarize_records(records)

    assert summary["tasks"] == 3
    assert summary["failure_tasks"] == 2
    assert summary["recovery_success_rate"] == 0.5
    assert summary["avg_recovery_attempts"] == 2.0
    assert summary["avg_recovery_tokens"] == 0.0


def test_summarize_records_by_split() -> None:
    records = [
        _record("a", "train", "division_by_zero", "success", 1, 2),
        _record("b", "train", "not_found", "failed", 1, 2),
        _record("c", "clean", None, "success", 0, 1),
    ]

    summary = summarize_records_by_split(records)

    assert summary["train"]["tasks"] == 2
    assert summary["train"]["recovery_success_rate"] == 0.5
    assert summary["train"]["avg_recovery_attempts"] == 1.0
    assert summary["clean"]["tasks"] == 1
    assert summary["clean"]["recovery_success_rate"] == 0.0


def test_summarize_records_by_failure_type_groups_clean_tasks() -> None:
    records = [
        _record("a", "train", "division_by_zero", "success", 1, 2),
        _record("b", "train", "not_found", "failed", 1, 2),
        _record("c", "clean", None, "success", 0, 1),
    ]

    summary = summarize_records_by_failure_type(records)

    assert summary["division_by_zero"]["tasks"] == 1
    assert summary["not_found"]["failure_tasks"] == 1
    assert summary["clean"]["failure_tasks"] == 0


def test_summarize_records_by_failure_family() -> None:
    records = [
        _record(
            "a", "train", "division_by_zero", "success", 1, 2, failure_family="semantic_param_error"
        ),
        _record("b", "train", "validation_error", "failed", 1, 2, failure_family="schema_error"),
        _record("c", "clean", None, "success", 0, 1),
    ]

    summary = summarize_records_by_failure_family(records)

    assert summary["semantic_param_error"]["tasks"] == 1
    assert summary["schema_error"]["failure_tasks"] == 1
    assert summary["clean"]["tasks"] == 1
