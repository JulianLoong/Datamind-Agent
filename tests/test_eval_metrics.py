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
    recovery_tokens: int = 0,
    selector_tokens: int = 0,
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
        recovery_tokens,
        0.0,
        [],
        selector_tokens,
    )


def test_summarize_records_reports_recovery_headline_metrics() -> None:
    records = [
        _record("a", "train", "invalid_json", "success", 1, 2),
        _record("b", "train", "missing_field", "failed", 3, 4),
        _record("c", "clean", None, "success", 0, 1),
    ]

    summary = summarize_records(records)

    assert summary["tasks"] == 3
    assert summary["failure_tasks"] == 2
    assert summary["recovery_success_rate"] == 0.5
    assert summary["avg_recovery_attempts"] == 2.0
    assert summary["avg_total_recovery_tokens"] == 0.0


def test_summarize_records_total_recovery_tokens_adds_selector_cost() -> None:
    records = [
        _record(
            "a",
            "train",
            "invalid_json",
            "success",
            1,
            2,
            recovery_tokens=100,
            selector_tokens=25,
        ),
        _record(
            "b",
            "train",
            "missing_field",
            "failed",
            1,
            2,
            recovery_tokens=200,
            selector_tokens=75,
        ),
    ]

    summary = summarize_records(records)

    # (100+25 + 200+75) / 2 = 200
    assert summary["avg_total_recovery_tokens"] == 200.0


def test_summarize_records_by_split() -> None:
    records = [
        _record("a", "train", "invalid_json", "success", 1, 2),
        _record("b", "train", "missing_field", "failed", 1, 2),
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
        _record("a", "train", "invalid_json", "success", 1, 2),
        _record("b", "train", "missing_field", "failed", 1, 2),
        _record("c", "clean", None, "success", 0, 1),
    ]

    summary = summarize_records_by_failure_type(records)

    assert summary["invalid_json"]["tasks"] == 1
    assert summary["missing_field"]["failure_tasks"] == 1
    assert summary["clean"]["failure_tasks"] == 0


def test_summarize_records_by_failure_family() -> None:
    records = [
        _record(
            "a", "train", "invalid_json", "success", 1, 2, failure_family="malformed_input"
        ),
        _record("b", "train", "validation_error", "failed", 1, 2, failure_family="schema_error"),
        _record("c", "clean", None, "success", 0, 1),
    ]

    summary = summarize_records_by_failure_family(records)

    assert summary["malformed_input"]["tasks"] == 1
    assert summary["schema_error"]["failure_tasks"] == 1
    assert summary["clean"]["tasks"] == 1
