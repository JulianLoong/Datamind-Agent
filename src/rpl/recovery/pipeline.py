from __future__ import annotations

from rpl.agent_engine.step import RecoveryAttempt, Step, StepStatus
from rpl.recovery.candidate_gen import CandidateGenerator
from rpl.recovery.context_builder import ErrorContextBuilder
from rpl.recovery.dedup import CandidateDedup
from rpl.recovery.selector import RecoverySelector
from rpl.recovery.types import Candidate
from rpl.recovery.validator import CandidateValidator


class RecoveryPipeline:
    def __init__(
        self,
        context_builder: ErrorContextBuilder,
        candidate_gen: CandidateGenerator,
        dedup: CandidateDedup,
        selector: RecoverySelector,
        *,
        candidate_count: int = 3,
        validator: CandidateValidator | None = None,
    ) -> None:
        self.context_builder = context_builder
        self.candidate_gen = candidate_gen
        self.dedup = dedup
        self.selector = selector
        self.candidate_count = candidate_count
        self.validator = validator

    async def recover(self, step: Step, history: list[Step], task_goal: str) -> RecoveryAttempt:
        ctx = self.context_builder.build(step, history, task_goal)
        candidates = await self.candidate_gen.generate(ctx, k=self.candidate_count)
        candidates = self.dedup.deduplicate(candidates)
        if self.validator is not None:
            candidates = self.validator.filter_valid(candidates)
        if not candidates:
            candidates = [
                Candidate(
                    reasoning="All generated candidates were invalid; stop recovery safely.",
                    action="give_up",
                    tool_name=None,
                    tool_params=None,
                    raw_text="Give up because every generated candidate failed validation.",
                )
            ]
        chosen_index, _ = await self.selector.select(ctx, candidates)
        pm_scores = self.selector.last_scores()
        return RecoveryAttempt(
            candidates=candidates,
            chosen_index=chosen_index,
            outcome=StepStatus.RECOVERING,
            error_context=ctx,
            initial_result=step.result,
            pm_scores=pm_scores,
            candidate_tokens=self.candidate_gen.last_tokens_used,
            candidate_latency_ms=self.candidate_gen.last_latency_ms,
        )
