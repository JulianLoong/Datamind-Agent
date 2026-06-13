from __future__ import annotations

from abc import ABC, abstractmethod
import json
import random

from rpl.experience.memory import ExperienceMemory
from rpl.pref_model.model import PrefModel
from rpl.recovery.types import Candidate, ErrorContext


class RecoverySelector(ABC):
    @abstractmethod
    async def select(self, ctx: ErrorContext, candidates: list[Candidate]) -> tuple[int, Candidate]:
        """Return the chosen index and candidate."""

    def last_scores(self) -> list[float] | None:
        return None


class DefaultSelector(RecoverySelector):
    def __init__(self, strategy: str = "first", *, rng: random.Random | None = None) -> None:
        if strategy not in {"first", "random"}:
            raise ValueError("strategy must be 'first' or 'random'")
        self.strategy = strategy
        self.rng = rng or random.Random()

    async def select(self, ctx: ErrorContext, candidates: list[Candidate]) -> tuple[int, Candidate]:
        if not candidates:
            raise ValueError("Cannot select from empty candidates")
        if self.strategy == "random":
            idx = self.rng.randrange(len(candidates))
        else:
            idx = 0
        return idx, candidates[idx]


class FixedRetrySelector(RecoverySelector):
    """Deterministic cold-start baseline: retry, then repair, then give up."""

    def __init__(self) -> None:
        self._attempts_by_context: dict[str, int] = {}
        self._last_scores: list[float] | None = None

    async def select(self, ctx: ErrorContext, candidates: list[Candidate]) -> tuple[int, Candidate]:
        if not candidates:
            raise ValueError("Cannot select from empty candidates")

        key = _context_key(ctx)
        attempt_no = self._attempts_by_context.get(key, 0)
        self._attempts_by_context[key] = attempt_no + 1

        if attempt_no == 0:
            idx = _find_action(candidates, "retry_same_tool")
        elif attempt_no == 1:
            idx = _find_executable_repair(candidates)
        else:
            idx = _find_action(candidates, "give_up")

        if idx is None:
            idx = 0
        self._last_scores = [0.0 for _ in candidates]
        self._last_scores[idx] = 1.0
        return idx, candidates[idx]

    def last_scores(self) -> list[float] | None:
        return self._last_scores


class PMSelector(RecoverySelector):
    def __init__(self, pref_model: PrefModel) -> None:
        self.pref_model = pref_model
        self._last_scores: list[float] | None = None

    async def select(self, ctx: ErrorContext, candidates: list[Candidate]) -> tuple[int, Candidate]:
        if not candidates:
            raise ValueError("Cannot select from empty candidates")
        ranked = self.pref_model.rank(ctx, candidates)
        self._last_scores = [0.0 for _ in candidates]
        for idx, score in ranked:
            self._last_scores[idx] = score
        best_idx = ranked[0][0]
        return best_idx, candidates[best_idx]

    def last_scores(self) -> list[float] | None:
        return self._last_scores


class MemoryPriorSelector(RecoverySelector):
    """Add a retrieval-based prior to another selector or use memory directly."""

    def __init__(
        self,
        memory: ExperienceMemory,
        base_selector: RecoverySelector | None = None,
        *,
        memory_weight: float = 1.0,
    ) -> None:
        self.memory = memory
        self.base_selector = base_selector
        self.memory_weight = memory_weight
        self._last_scores: list[float] | None = None

    async def select(self, ctx: ErrorContext, candidates: list[Candidate]) -> tuple[int, Candidate]:
        if not candidates:
            raise ValueError("Cannot select from empty candidates")

        base_scores = [0.0 for _ in candidates]
        if self.base_selector is not None:
            await self.base_selector.select(ctx, candidates)
            base_scores = self.base_selector.last_scores() or base_scores

        memory_scores = [
            self._candidate_memory_score(ctx, candidate)
            for candidate in candidates
        ]
        self._last_scores = [
            base_score + self.memory_weight * memory_score
            for base_score, memory_score in zip(base_scores, memory_scores, strict=True)
        ]
        best_idx = max(range(len(candidates)), key=lambda idx: self._last_scores[idx])
        return best_idx, candidates[best_idx]

    def last_scores(self) -> list[float] | None:
        return self._last_scores

    def _candidate_memory_score(self, ctx: ErrorContext, candidate: Candidate) -> float:
        matches = self.memory.retrieve(ctx, candidate=candidate, top_k=3)
        if not matches:
            return 0.0
        return matches[0][1]


def _context_key(ctx: ErrorContext) -> str:
    return json.dumps(
        {
            "task_goal": ctx.task_goal,
            "step_description": ctx.step_description,
            "tool_name": ctx.tool_name,
            "tool_params": ctx.tool_params,
            "error_type": ctx.error_type,
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def _find_action(candidates: list[Candidate], action: str) -> int | None:
    for idx, candidate in enumerate(candidates):
        if candidate.action == action:
            return idx
    return None


def _find_executable_repair(candidates: list[Candidate]) -> int | None:
    for idx, candidate in enumerate(candidates):
        if candidate.tool_name is not None and candidate.action not in {"retry_same_tool", "give_up"}:
            return idx
    return None
