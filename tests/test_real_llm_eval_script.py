from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_script_module():
    script_path = Path(__file__).parents[1] / "scripts" / "run_real_llm_eval.py"
    spec = importlib.util.spec_from_file_location("run_real_llm_eval", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_real_llm_defaults_use_current_selector_protocol() -> None:
    module = _load_script_module()

    assert module.DEFAULT_BASELINES == ["llm_greedy", "llm_self_pick", "dpo_pm"]
    assert "dpo_pm_outcomes" in module.DEFAULT_DPO_PATH


def test_real_llm_default_splits_only_filter_generated_benchmark() -> None:
    module = _load_script_module()

    assert module._resolve_splits("recovery_bench_generated", None) == [
        "test_unseen",
        "clean",
    ]
    assert module._resolve_splits("recovery_gym", None) is None
    assert module._resolve_splits("recovery_gym", ["clean"]) == ["clean"]
