from __future__ import annotations

import pytest

from rpl.eval.baselines import build_baseline
from rpl.llm import FakeLLMClient
from rpl.recovery.selector import LLMSelfSelector


def test_build_baseline_supports_retry_suffix() -> None:
    spec = build_baseline("random_r3")

    assert spec.name == "random_r3"
    assert spec.max_retries_per_step == 3


def test_build_baseline_supports_pm_retry_suffix(tmp_path) -> None:
    checkpoint = tmp_path / "lightweight_pm.json"
    checkpoint.write_text('{"weights": {"bias": 1.0}, "metadata": {}}', encoding="utf-8")

    spec = build_baseline(
        "lightweight_pm_r3",
        pm_path=str(checkpoint),
    )

    assert spec.name == "lightweight_pm_r3"
    assert spec.max_retries_per_step == 3


def test_build_baseline_supports_fixed_retry() -> None:
    spec = build_baseline("fixed_retry")

    assert spec.name == "fixed_retry"
    assert spec.max_retries_per_step == 3


def test_build_baseline_rejects_removed_no_recovery() -> None:
    with pytest.raises(ValueError, match="Unknown baseline"):
        build_baseline("no_recovery")


def test_build_baseline_llm_greedy() -> None:
    spec = build_baseline("llm_greedy")

    assert spec.name == "llm_greedy"
    assert spec.max_retries_per_step == 1
    assert spec.candidate_count == 1


def test_build_baseline_llm_self_pick() -> None:
    spec = build_baseline("llm_self_pick", llm_client=FakeLLMClient())

    assert spec.name == "llm_self_pick"
    assert isinstance(spec.selector, LLMSelfSelector)
    assert spec.candidate_count is None
    assert spec.max_retries_per_step == 1


def test_build_baseline_llm_self_pick_requires_client() -> None:
    with pytest.raises(ValueError, match="llm_client"):
        build_baseline("llm_self_pick")


def test_build_baseline_retry_suffix_preserves_candidate_count() -> None:
    spec = build_baseline("llm_greedy_r2")

    assert spec.candidate_count == 1
    assert spec.max_retries_per_step == 2
