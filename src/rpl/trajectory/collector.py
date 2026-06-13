from __future__ import annotations

from rpl.agent_engine.step import RecoveryAttempt, Step, TaskResult
from rpl.trajectory.store import TrajectoryStore


class TrajectoryCollector:
    """Thin event collector for executor callbacks.

    The first version keeps state in memory during a task and persists the final TaskResult.
    Hook methods are intentionally present so the executor can evolve without coupling to SQLite.
    """

    def __init__(self, store: TrajectoryStore) -> None:
        self.store = store

    def on_step_start(self, step: Step) -> None:
        return None

    def on_tool_call(self, step: Step, tool_name: str, params: dict, result) -> None:
        return None

    def on_step_end(self, step: Step) -> None:
        return None

    def on_recovery(self, step: Step, attempt: RecoveryAttempt) -> None:
        return None

    def on_task_end(self, result: TaskResult) -> None:
        self.store.save_task(result)
