from __future__ import annotations

import pytest

from rpl.eval import run_eval_sync
from rpl.eval.runner import parse_pm_path_items


def test_eval_runner_produces_baseline_summary(tmp_path) -> None:
    output = tmp_path / "eval.json"

    report = run_eval_sync(
        baseline_names=["no_recovery", "first"],
        repeats=1,
        output_path=output,
    )

    assert output.exists()
    assert "no_recovery" in report["summaries"]
    assert "first" in report["summaries"]
    assert report["summaries"]["first"]["success_rate"] >= report["summaries"]["no_recovery"]["success_rate"]
    assert "first" in report["failure_family_summaries"]


def test_eval_runner_records_recovery_trace(tmp_path) -> None:
    report = run_eval_sync(
        baseline_names=["first"],
        repeats=1,
        output_path=tmp_path / "eval.json",
    )

    recovered_records = [
        record
        for record in report["records"]
        if record["recovery_attempts"] > 0
    ]

    assert recovered_records
    trace = recovered_records[0]["recovery_trace"]
    assert trace
    assert "chosen_index" in trace[0]
    assert "candidates" in trace[0]
    assert trace[0]["candidates"]
    assert "final_result" in trace[0]


def test_eval_runner_filters_splits_and_limits_tasks(tmp_path) -> None:
    report = run_eval_sync(
        benchmark_name="recovery_gym",
        baseline_names=["no_recovery"],
        splits=["seen_template_unseen_params"],
        max_tasks=2,
        repeats=1,
        output_path=tmp_path / "eval.json",
    )

    assert report["task_count"] == 2
    assert report["splits"] == ["seen_template_unseen_params"]
    assert report["summaries"]["no_recovery"]["tasks"] == 2


def test_parse_pm_path_items() -> None:
    paths = parse_pm_path_items(
        [
            "lightweight_pm=data/pm_checkpoints/lightweight_pm_generated.json",
            "dpo_pm=Qwen/Qwen2.5-0.5B-Instruct::data/pm_checkpoints/dpo_pm",
        ]
    )

    assert paths["lightweight_pm"] == "data/pm_checkpoints/lightweight_pm_generated.json"
    assert paths["dpo_pm"] == "Qwen/Qwen2.5-0.5B-Instruct::data/pm_checkpoints/dpo_pm"


def test_parse_pm_path_items_rejects_invalid_item() -> None:
    with pytest.raises(ValueError, match="expected baseline=path"):
        parse_pm_path_items(["lightweight_pm"])


def test_eval_runner_uses_per_baseline_pm_paths(tmp_path) -> None:
    report = run_eval_sync(
        benchmark_name="recovery_bench_generated",
        baseline_names=["no_recovery", "lightweight_pm"],
        pm_paths={"lightweight_pm": "data/pm_checkpoints/lightweight_pm_generated.json"},
        splits=["test_unseen", "clean"],
        max_tasks=4,
        repeats=1,
        output_path=tmp_path / "eval.json",
    )

    assert report["summaries"]["no_recovery"]["tasks"] == 4
    assert report["summaries"]["lightweight_pm"]["tasks"] == 4
    assert report["summaries"]["lightweight_pm"]["success_rate"] >= report["summaries"]["no_recovery"]["success_rate"]
