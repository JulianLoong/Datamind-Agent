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
