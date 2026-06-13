from __future__ import annotations

from abc import ABC, abstractmethod
import random

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
