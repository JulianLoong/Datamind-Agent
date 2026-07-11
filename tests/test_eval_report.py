from __future__ import annotations

from rpl.eval.report import summary_markdown


def test_summary_markdown_includes_split_and_failure_type_tables() -> None:
    summary = {
        "tasks": 1,
        "failure_tasks": 1,
        "recovery_success_rate": 1.0,
        "avg_recovery_attempts": 1.0,
        "avg_recovery_tokens": 12.0,
    }
    report = {
        "benchmark": "bench",
        "repeats": 1,
        "summaries": {"mock_pm": summary},
        "split_summaries": {"mock_pm": {"train": summary}},
        "failure_type_summaries": {"mock_pm": {"division_by_zero": summary}},
        "failure_family_summaries": {"mock_pm": {"semantic_param_error": summary}},
    }

    markdown = summary_markdown(report)

    assert "## Split: train" in markdown
    assert "## Failure Type: division_by_zero" in markdown
    assert "## Failure Family: semantic_param_error" in markdown
