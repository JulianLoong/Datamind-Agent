from __future__ import annotations

from dataclasses import dataclass

from rpl.experience import ExperienceMemory
from rpl.pref_model import LightweightPrefModel, MockPrefModel
from rpl.recovery import DefaultSelector, MemoryPriorSelector, PMSelector, RecoverySelector
from rpl.trajectory.store import TrajectoryStore


@dataclass(frozen=True)
class BaselineSpec:
    name: str
    selector: RecoverySelector
    max_retries_per_step: int


def build_baseline(
    name: str,
    *,
    pm_path: str | None = None,
    memory_db_path: str | None = None,
) -> BaselineSpec:
    if name == "no_recovery":
        return BaselineSpec(name=name, selector=DefaultSelector("first"), max_retries_per_step=0)
    if name == "first":
        return BaselineSpec(name=name, selector=DefaultSelector("first"), max_retries_per_step=1)
    if name == "random":
        return BaselineSpec(name=name, selector=DefaultSelector("random"), max_retries_per_step=1)
    if name == "mock_pm":
        return BaselineSpec(name=name, selector=PMSelector(MockPrefModel()), max_retries_per_step=1)
    if name == "memory_mock_pm":
        memory = _load_memory(memory_db_path)
        return BaselineSpec(
            name=name,
            selector=MemoryPriorSelector(memory, PMSelector(MockPrefModel()), memory_weight=1.0),
            max_retries_per_step=1,
        )
    if name == "lightweight_pm":
        if not pm_path:
            raise ValueError("pm_path is required for lightweight_pm baseline")
        return BaselineSpec(
            name=name,
            selector=PMSelector(LightweightPrefModel.load(pm_path)),
            max_retries_per_step=1,
        )
    if name == "memory_lightweight_pm":
        if not pm_path:
            raise ValueError("pm_path is required for memory_lightweight_pm baseline")
        memory = _load_memory(memory_db_path)
        return BaselineSpec(
            name=name,
            selector=MemoryPriorSelector(
                memory,
                PMSelector(LightweightPrefModel.load(pm_path)),
                memory_weight=1.0,
            ),
            max_retries_per_step=1,
        )
    if name == "dpo_pm":
        if not pm_path:
            raise ValueError("pm_path is required for dpo_pm baseline")
        from rpl.pref_model import DPOPrefModel

        base_model, adapter_path = _parse_dpo_path(pm_path)
        return BaselineSpec(
            name=name,
            selector=PMSelector(DPOPrefModel(base_model=base_model, adapter_path=adapter_path)),
            max_retries_per_step=1,
        )
    raise ValueError(f"Unknown baseline: {name}")


def _parse_dpo_path(pm_path: str) -> tuple[str, str]:
    if "::" in pm_path:
        base_model, adapter_path = pm_path.split("::", 1)
        return base_model, adapter_path
    return "Qwen/Qwen2.5-0.5B-Instruct", pm_path


def _load_memory(memory_db_path: str | None) -> ExperienceMemory:
    if not memory_db_path:
        return ExperienceMemory()
    store = TrajectoryStore(memory_db_path)
    return ExperienceMemory.from_recovery_rows(store.query_recovery_attempts_with_context(limit=10000))
