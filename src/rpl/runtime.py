from __future__ import annotations

from dataclasses import dataclass

from rpl.agent_engine.executor import Executor
from rpl.agent_engine.planner import RuleBasedPlanner
from rpl.config import Settings, load_settings
from rpl.pref_model import LightweightPrefModel, MockPrefModel
from rpl.recovery import CandidateDedup, CandidateGenerator, CandidateValidator, DefaultSelector, ErrorContextBuilder, PMSelector, RecoveryPipeline
from rpl.tools.builtin import build_builtin_registry
from rpl.trajectory.collector import TrajectoryCollector
from rpl.trajectory.store import TrajectoryStore


@dataclass
class RuntimeComponents:
    settings: Settings
    executor: Executor
    store: TrajectoryStore


def build_runtime(
    config_path: str = "config/default.yaml",
    *,
    selector_name: str | None = None,
    pm_path: str | None = None,
) -> RuntimeComponents:
    settings = load_settings(config_path)
    registry = build_builtin_registry(settings.tools)
    store = TrajectoryStore(settings.paths.trajectory_db)
    collector = TrajectoryCollector(store)
    selector = _build_selector(selector_name or settings.recovery.selector, settings.recovery.default_selector, pm_path)
    recovery_pipeline = RecoveryPipeline(
        ErrorContextBuilder(),
        CandidateGenerator(),
        CandidateDedup(),
        selector,
        candidate_count=settings.recovery.candidate_count,
        validator=CandidateValidator(registry),
    )
    executor = Executor(registry, RuleBasedPlanner(), recovery_pipeline, collector)
    return RuntimeComponents(settings=settings, executor=executor, store=store)


def _build_selector(selector_name: str, default_strategy: str, pm_path: str | None):
    if selector_name == "mock_pm":
        return PMSelector(MockPrefModel())
    if selector_name == "lightweight_pm":
        if not pm_path:
            raise ValueError("pm_path is required when selector is lightweight_pm")
        return PMSelector(LightweightPrefModel.load(pm_path))
    if selector_name == "dpo_pm":
        if not pm_path:
            raise ValueError("pm_path is required when selector is dpo_pm")
        from rpl.pref_model import DPOPrefModel

        base_model, adapter_path = _parse_dpo_path(pm_path)
        return PMSelector(DPOPrefModel(base_model=base_model, adapter_path=adapter_path))
    if selector_name == "random":
        return DefaultSelector("random")
    return DefaultSelector(default_strategy)


def _parse_dpo_path(pm_path: str) -> tuple[str, str]:
    if "::" in pm_path:
        base_model, adapter_path = pm_path.split("::", 1)
        return base_model, adapter_path
    return "Qwen/Qwen2.5-0.5B-Instruct", pm_path
