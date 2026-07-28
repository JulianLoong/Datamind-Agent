from __future__ import annotations

import os

import pytest

from rpl.recovery.types import Candidate, ErrorContext

# This repo runs offline against locally-cached HF models (every training script
# sets HF_HUB_OFFLINE=1). huggingface_hub reads this flag at import time, so set
# it before _torch_available() imports transformers below. setdefault keeps an
# explicit override (e.g. HF_HUB_OFFLINE=0 in online CI).
os.environ.setdefault("HF_HUB_OFFLINE", "1")


def _torch_available() -> bool:
    try:
        import torch  # noqa: F401
        from transformers import AutoModelForCausalLM  # noqa: F401

        return True
    except ModuleNotFoundError:
        return False


def _make_ctx() -> ErrorContext:
    return ErrorContext(
        task_goal="parse json",
        step_description="json",
        tool_name="json_parse",
        tool_params={"text": '{"a":', "field": "a"},
        error_type="invalid_json",
        error_message="Expecting value",
        recent_history=[],
    )


def _make_candidates() -> tuple[Candidate, Candidate]:
    good = Candidate(
        reasoning="repair the broken json",
        action="repair_json_payload",
        tool_name="json_parse",
        tool_params={"text": '{"a": null}', "field": "a"},
        raw_text="Repair the malformed JSON and retry.",
    )
    bad = Candidate(
        reasoning="just retry",
        action="retry_same_tool",
        tool_name="json_parse",
        tool_params={"text": '{"a":', "field": "a"},
        raw_text="Retry the same tool with the same parameters.",
    )
    return good, bad


@pytest.mark.skipif(
    not _torch_available(),
    reason="torch/transformers not installed",
)
def test_base_model_pref_model_scores():
    """BaseModelPrefModel loads the base model without LoRA and produces scores."""
    from rpl.pref_model import BaseModelPrefModel

    model = BaseModelPrefModel(base_model="Qwen/Qwen2.5-0.5B-Instruct")
    assert model.is_loaded()

    ctx = _make_ctx()
    good, bad = _make_candidates()

    good_score = model.score(ctx, good)
    bad_score = model.score(ctx, bad)

    # Both should be finite floats
    assert isinstance(good_score, float)
    assert isinstance(bad_score, float)
    assert good_score != -1e9
    assert bad_score != -1e9


@pytest.mark.skipif(
    not _torch_available(),
    reason="torch/transformers not installed",
)
def test_base_model_vs_dpo_pm_different_scores():
    """BaseModelPrefModel and DPOPrefModel should produce different scores for the same input.

    This validates that the DPO adapter actually changes the model's logprob output.
    """
    from rpl.pref_model import BaseModelPrefModel, DPOPrefModel

    base = BaseModelPrefModel(base_model="Qwen/Qwen2.5-0.5B-Instruct")
    dpo = DPOPrefModel(
        base_model="Qwen/Qwen2.5-0.5B-Instruct",
        adapter_path="data/pm_checkpoints/dpo_pm_outcomes",
    )

    ctx = _make_ctx()
    good, bad = _make_candidates()

    base_good = base.score(ctx, good)
    base_bad = base.score(ctx, bad)
    dpo_good = dpo.score(ctx, good)
    dpo_bad = dpo.score(ctx, bad)

    # At least one pair should differ — the DPO adapter must change something
    assert (base_good != dpo_good) or (base_bad != dpo_bad), (
        "DPO adapter produced identical scores to base model — adapter may not be loaded correctly"
    )


@pytest.mark.skipif(
    not _torch_available(),
    reason="torch/transformers not installed",
)
def test_base_model_rank_order():
    """BaseModelPrefModel.rank() returns valid index-score pairs."""
    from rpl.pref_model import BaseModelPrefModel

    model = BaseModelPrefModel(base_model="Qwen/Qwen2.5-0.5B-Instruct")
    ctx = _make_ctx()
    good, bad = _make_candidates()

    ranked = model.rank(ctx, [good, bad])
    assert len(ranked) == 2
    assert all(isinstance(idx, int) and isinstance(score, float) for idx, score in ranked)
    # Indices should be 0 and 1
    assert {idx for idx, _ in ranked} == {0, 1}


def test_base_model_import_without_torch():
    """BaseModelPrefModel can be imported even without torch (lazy import)."""
    from rpl.pref_model import BaseModelPrefModel

    assert BaseModelPrefModel is not None
