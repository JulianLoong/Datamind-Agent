from __future__ import annotations

import pytest

from rpl.eval.baselines import build_baseline


def test_build_baseline_supports_retry_suffix() -> None:
    spec = build_baseline("random_r3")

    assert spec.name == "random_r3"
    assert spec.max_retries_per_step == 3


def test_build_baseline_supports_fixed_retry() -> None:
    spec = build_baseline("fixed_retry")

    assert spec.name == "fixed_retry"
    assert spec.max_retries_per_step == 3


def test_build_baseline_rejects_no_recovery_positive_retry_suffix() -> None:
    with pytest.raises(ValueError, match="no_recovery"):
        build_baseline("no_recovery_r2")
