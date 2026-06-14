from __future__ import annotations

from rpl.eval import run_eval_sync


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
