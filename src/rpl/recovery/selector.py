from __future__ import annotations

import json
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass

from rpl.experience.memory import ExperienceMemory
from rpl.llm import LLMClient, LLMRequest
from rpl.pref_model.model import PrefModel
from rpl.recovery.types import Candidate, ErrorContext


@dataclass(frozen=True)
class SelectorCost:
    """Cost incurred by a selector's pick, for fair efficiency accounting.

    selector_tokens: API tokens spent by the selector's own LLM call (e.g. LLMSelfSelector).
    selector_evals: number of candidate evaluations performed (PM ranks all k; LLM-self is 1 call).
    """

    selector_tokens: int = 0
    selector_evals: int = 0


class RecoverySelector(ABC):
    @abstractmethod
    async def select(self, ctx: ErrorContext, candidates: list[Candidate]) -> tuple[int, Candidate]:
        """Return the chosen index and candidate."""

    def last_scores(self) -> list[float] | None:
        return None

    def last_cost(self) -> SelectorCost:
        return SelectorCost()


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

    def last_cost(self) -> SelectorCost:
        return SelectorCost(selector_evals=len(self._last_scores or []))


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

        memory_scores = [self._candidate_memory_score(ctx, candidate) for candidate in candidates]
        self._last_scores = [
            base_score + self.memory_weight * memory_score
            for base_score, memory_score in zip(base_scores, memory_scores, strict=True)
        ]
        best_idx = max(range(len(candidates)), key=lambda idx: self._last_scores[idx])
        return best_idx, candidates[best_idx]

    def last_scores(self) -> list[float] | None:
        return self._last_scores

    def last_cost(self) -> SelectorCost:
        if self.base_selector is not None:
            return self.base_selector.last_cost()
        return SelectorCost()

    def _candidate_memory_score(self, ctx: ErrorContext, candidate: Candidate) -> float:
        matches = self.memory.retrieve(ctx, candidate=candidate, top_k=3)
        if not matches:
            return 0.0
        return matches[0][1]


class LLMSelfSelector(RecoverySelector):
    """Let the generator LLM itself pick the best candidate from the pool.

    This is the "LLM-as-selector" baseline that DPO_PM must beat to justify a learned PM:
    same candidate pool as the PM path, but the model's own judgment chooses instead of a
    learned scorer. It reuses the same LLMClient as the candidate generator so --llm-cache
    keeps the self-pick deterministic across selectors.

    Caveat: FakeLLMClient emits a candidate array (not a chosen_index), so under the fake
    provider this selector always falls back to index 0 and behaves like DefaultSelector("first").
    The real LLM (GLM/OpenAI) honors the selection prompt; unit tests must inject a stub client
    that returns {"chosen_index": int}.
    """

    def __init__(
        self, llm_client: LLMClient, *, temperature: float = 0.0, max_tokens: int = 256
    ) -> None:
        self.llm_client = llm_client
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._last_scores: list[float] | None = None
        self._last_tokens = 0

    async def select(self, ctx: ErrorContext, candidates: list[Candidate]) -> tuple[int, Candidate]:
        if not candidates:
            raise ValueError("Cannot select from empty candidates")
        prompt = self._build_prompt(ctx, candidates)
        response = await self.llm_client.complete(
            LLMRequest(prompt=prompt, temperature=self.temperature, max_tokens=self.max_tokens)
        )
        self._last_tokens = response.tokens_used
        chosen = self._parse_index(response.text, len(candidates))
        self._last_scores = [0.0 for _ in candidates]
        self._last_scores[chosen] = 1.0
        return chosen, candidates[chosen]

    def last_scores(self) -> list[float] | None:
        return self._last_scores

    def last_cost(self) -> SelectorCost:
        return SelectorCost(selector_tokens=self._last_tokens, selector_evals=1)

    @staticmethod
    def _build_prompt(ctx: ErrorContext, candidates: list[Candidate]) -> str:
        items = [
            {
                "index": idx,
                "action": candidate.action,
                "tool_name": candidate.tool_name,
                "tool_params": candidate.tool_params,
            }
            for idx, candidate in enumerate(candidates)
        ]
        return (
            "You are an agent recovery selector. Choose the single best recovery candidate to "
            'execute next. Return a JSON object exactly: {"chosen_index": <integer>}.\n'
            f"Task Goal: {ctx.task_goal}\n"
            f"Current Step: {ctx.step_description}\n"
            f"Failed Tool: {ctx.tool_name}({ctx.tool_params})\n"
            f"Error: {ctx.error_type}: {ctx.error_message}\n"
            f"Candidates:\n{json.dumps(items, ensure_ascii=False, sort_keys=True)}\n"
            "Pick the candidate most likely to resolve the error. Prefer concrete repairs over "
            "retry_same_tool, and avoid give_up unless no listed tool can succeed. "
            f"chosen_index must be an integer in [0, {len(candidates) - 1}].\n"
            "Return valid JSON only. Do not wrap in markdown or prose."
        )

    @staticmethod
    def _parse_index(text: str, count: int) -> int:
        try:
            start = text.find("{")
            end = text.rfind("}")
            raw_obj = text[start : end + 1] if start != -1 and end != -1 else text
            obj = json.loads(raw_obj)
            raw = obj.get("chosen_index")
        except (ValueError, AttributeError):
            return 0
        # bool is an int subclass; reject True/False silently masquerading as an index.
        if isinstance(raw, bool) or not isinstance(raw, int):
            return 0
        return raw if 0 <= raw < count else 0
