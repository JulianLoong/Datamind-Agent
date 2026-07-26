from __future__ import annotations

import pytest

from rpl.eval import run_eval_sync
from rpl.eval.runner import _resolve_pm_path, parse_pm_path_items
from rpl.llm import LLMClient, LLMRequest, LLMResponse
from rpl.recovery.candidate_gen import CandidateGenerationError


def test_eval_runner_produces_baseline_summary(tmp_path) -> None:
    output = tmp_path / "eval.json"

    report = run_eval_sync(
        baseline_names=["first"],
        llm_provider="fake",
        repeats=1,
        output_path=output,
    )

    assert output.exists()
    assert "first" in report["summaries"]
    assert report["baseline_configs"]["first"]["max_retries_per_step"] == 1
    assert "first" in report["failure_family_summaries"]


def test_eval_runner_records_recovery_trace(tmp_path) -> None:
    report = run_eval_sync(
        baseline_names=["first"],
        llm_provider="fake",
        repeats=1,
        output_path=tmp_path / "eval.json",
    )

    recovered_records = [record for record in report["records"] if record["recovery_attempts"] > 0]

    assert recovered_records
    trace = recovered_records[0]["recovery_trace"]
    assert trace
    assert "chosen_index" in trace[0]
    assert "candidates" in trace[0]
    assert trace[0]["candidates"]
    assert "final_result" in trace[0]


def test_eval_runner_can_write_llm_cache(tmp_path) -> None:
    cache_path = tmp_path / "llm_cache.jsonl"

    run_eval_sync(
        baseline_names=["first", "random"],
        llm_provider="fake",
        repeats=1,
        max_tasks=1,
        llm_cache_path=cache_path,
        output_path=tmp_path / "eval.json",
    )

    assert cache_path.exists()
    assert cache_path.read_text(encoding="utf-8").strip()


def test_eval_runner_filters_splits_and_limits_tasks(tmp_path) -> None:
    report = run_eval_sync(
        benchmark_name="recovery_gym",
        baseline_names=["first"],
        llm_provider="fake",
        splits=["seen_template_unseen_params"],
        max_tasks=2,
        repeats=1,
        output_path=tmp_path / "eval.json",
    )

    assert report["task_count"] == 2
    assert report["splits"] == ["seen_template_unseen_params"]
    assert report["summaries"]["first"]["tasks"] == 2


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
    checkpoint = tmp_path / "lightweight_pm.json"
    checkpoint.write_text('{"weights": {"bias": 1.0}, "metadata": {}}', encoding="utf-8")

    report = run_eval_sync(
        benchmark_name="recovery_bench_generated",
        baseline_names=["lightweight_pm"],
        llm_provider="fake",
        pm_paths={"lightweight_pm": str(checkpoint)},
        splits=["test_unseen", "clean"],
        max_tasks=4,
        repeats=1,
        output_path=tmp_path / "eval.json",
    )

    assert report["summaries"]["lightweight_pm"]["tasks"] == 4


def test_eval_runner_resolves_pm_path_for_retry_suffixed_baseline() -> None:
    path = _resolve_pm_path(
        "dpo_pm_r3",
        default_pm_path=None,
        pm_paths={"dpo_pm": "Qwen/Qwen2.5-0.5B-Instruct::data/pm_checkpoints/dpo_pm_outcomes"},
    )

    assert path == "Qwen/Qwen2.5-0.5B-Instruct::data/pm_checkpoints/dpo_pm_outcomes"


def test_eval_runner_llm_self_pick_baseline_runs(tmp_path) -> None:
    report = run_eval_sync(
        baseline_names=["llm_self_pick"],
        llm_provider="fake",
        repeats=1,
        output_path=tmp_path / "eval.json",
    )

    assert "llm_self_pick" in report["summaries"]
    assert "recovery_success_rate" in report["summaries"]["llm_self_pick"]
    # selector cost is dropped from the summary but retained in the raw recovery trace
    trace_entries = [
        attempt for record in report["records"] for attempt in record["recovery_trace"]
    ]
    if trace_entries:
        assert "selector_tokens" in trace_entries[0]
        assert "selector_evals" in trace_entries[0]


def test_eval_runner_candidate_count_param(tmp_path) -> None:
    report = run_eval_sync(
        baseline_names=["first"],
        llm_provider="fake",
        candidate_count=2,
        repeats=1,
        output_path=tmp_path / "eval.json",
    )

    candidate_counts = [
        len(attempt["candidates"])
        for record in report["records"]
        for attempt in record["recovery_trace"]
    ]
    assert candidate_counts, "expected at least one recovery attempt with candidates"
    assert max(candidate_counts) <= 2


def test_eval_runner_records_strict_real_llm_setting(tmp_path) -> None:
    report = run_eval_sync(
        baseline_names=["first"],
        llm_provider="fake",
        strict_llm_candidates=True,
        max_tasks=1,
        repeats=1,
        output_path=tmp_path / "eval.json",
    )

    assert report["strict_llm_candidates"] is True


def test_eval_runner_real_provider_fails_fast_on_malformed_candidates(
    tmp_path, monkeypatch
) -> None:
    class MalformedClient(LLMClient):
        async def complete(self, request: LLMRequest) -> LLMResponse:
            return LLMResponse(text="not-json", tokens_used=3)

    monkeypatch.setattr(
        "rpl.eval.runner.build_llm_client",
        lambda **kwargs: MalformedClient(),
    )

    with pytest.raises(CandidateGenerationError, match="not-json"):
        run_eval_sync(
            baseline_names=["first"],
            llm_provider="openai_compatible",
            max_tasks=1,
            repeats=1,
            output_path=tmp_path / "eval.json",
        )


def test_eval_runner_real_default_fails_fast_without_api_key(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ValueError, match="API key"):
        run_eval_sync(
            baseline_names=["first"],
            max_tasks=1,
            repeats=1,
            output_path=tmp_path / "eval.json",
        )
