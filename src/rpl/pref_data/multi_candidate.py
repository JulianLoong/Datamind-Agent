from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from rpl.agent_engine.planner import Planner, RuleBasedPlanner
from rpl.agent_engine.step import Step
from rpl.pref_data.types import PreferencePair
from rpl.recovery import CandidateDedup, CandidateGenerator, CandidateValidator, ErrorContextBuilder
from rpl.recovery.types import Candidate, ErrorContext
from rpl.tools.base import ToolResult
from rpl.tools.registry import ToolRegistry
from rpl.trajectory.store import to_json


@dataclass(frozen=True)
class CandidateOutcome:
    index: int
    candidate: Candidate
    result: ToolResult
    valid: bool
    validation_reason: str = ""

    @property
    def rank_key(self) -> tuple[int, int, int, int, float]:
        executable = 1 if self.candidate.tool_name is not None and self.valid else 0
        success = 1 if self.result.success else 0
        give_up_penalty = 1 if self.candidate.tool_name is None or self.candidate.action == "give_up" else 0
        return (
            success,
            executable,
            -give_up_penalty,
            -self.result.tokens_used,
            -self.result.latency_ms,
        )

    def to_metadata(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "valid": self.valid,
            "validation_reason": self.validation_reason,
            "candidate": asdict(self.candidate),
            "result": asdict(self.result),
            "rank_key": list(self.rank_key),
        }


@dataclass(frozen=True)
class MultiCandidateEvaluation:
    task_goal: str
    step: Step
    error_context: ErrorContext | None
    initial_result: ToolResult
    outcomes: list[CandidateOutcome]

    @property
    def failed_before_recovery(self) -> bool:
        return not self.initial_result.success

    def preference_pairs(self, *, confidence: float = 0.95) -> list[PreferencePair]:
        if self.error_context is None:
            return []
        ranked = sorted(self.outcomes, key=lambda outcome: outcome.rank_key, reverse=True)
        if len(ranked) < 2:
            return []

        pairs: list[PreferencePair] = []
        for better_index, better in enumerate(ranked):
            for worse in ranked[better_index + 1 :]:
                if better.rank_key == worse.rank_key:
                    continue
                pair_confidence = confidence if better.result.success != worse.result.success else min(confidence, 0.7)
                pairs.append(
                    PreferencePair(
                        prompt=self.error_context.to_prompt(),
                        chosen=_candidate_to_text(better.candidate),
                        rejected=_candidate_to_text(worse.candidate),
                        source="outcome_multi_candidate",
                        confidence=pair_confidence,
                        metadata={
                            "task_goal": self.task_goal,
                            "step_index": self.step.index,
                            "error_type": self.error_context.error_type,
                            "preference_reason": _preference_reason(better, worse),
                            "chosen_outcome": better.to_metadata(),
                            "rejected_outcome": worse.to_metadata(),
                            "all_outcomes": [outcome.to_metadata() for outcome in self.outcomes],
                        },
                    )
                )
        return pairs


class MultiCandidateEvaluator:
    """Execute every generated candidate for a failed step to build outcome-ranked data.

    This evaluator is intended for offline cold-start data construction. It only mutates a copied
    step object and is safest for deterministic or sandboxed tools.
    """

    def __init__(
        self,
        registry: ToolRegistry,
        *,
        planner: Planner | None = None,
        context_builder: ErrorContextBuilder | None = None,
        candidate_generator: CandidateGenerator | None = None,
        dedup: CandidateDedup | None = None,
        validator: CandidateValidator | None = None,
    ) -> None:
        self.registry = registry
        self.planner = planner or RuleBasedPlanner()
        self.context_builder = context_builder or ErrorContextBuilder()
        self.candidate_generator = candidate_generator or CandidateGenerator()
        self.dedup = dedup or CandidateDedup()
        self.validator = validator or CandidateValidator(registry)

    async def evaluate_task(self, task_goal: str, *, candidate_count: int = 3) -> MultiCandidateEvaluation:
        steps = self.planner.plan(task_goal, self.registry.list_tools())
        if not steps:
            raise ValueError("Planner returned no steps")

        step = _copy_step(steps[0])
        initial_result = self.registry.execute(step.tool_name or "", step.params or {})
        step.result = initial_result

        if initial_result.success:
            return MultiCandidateEvaluation(
                task_goal=task_goal,
                step=step,
                error_context=None,
                initial_result=initial_result,
                outcomes=[],
            )

        ctx = self.context_builder.build(step, [], task_goal)
        candidates = await self.candidate_generator.generate(ctx, k=candidate_count)
        candidates = self.dedup.deduplicate(candidates)
        outcomes = [self._execute_candidate(index, candidate) for index, candidate in enumerate(candidates)]
        return MultiCandidateEvaluation(
            task_goal=task_goal,
            step=step,
            error_context=ctx,
            initial_result=initial_result,
            outcomes=outcomes,
        )

    def _execute_candidate(self, index: int, candidate: Candidate) -> CandidateOutcome:
        validation = self.validator.validate(candidate)
        if candidate.tool_name is None:
            return CandidateOutcome(
                index=index,
                candidate=candidate,
                result=ToolResult.fail("give_up", "Candidate chose not to execute a recovery tool."),
                valid=validation.valid,
                validation_reason=validation.reason,
            )
        if not validation.valid:
            return CandidateOutcome(
                index=index,
                candidate=candidate,
                result=ToolResult.fail("candidate_validation_error", validation.reason),
                valid=False,
                validation_reason=validation.reason,
            )
        return CandidateOutcome(
            index=index,
            candidate=candidate,
            result=self.registry.execute(candidate.tool_name, candidate.tool_params or {}),
            valid=True,
        )


def _copy_step(step: Step) -> Step:
    return Step(
        index=step.index,
        description=step.description,
        tool_name=step.tool_name,
        params=dict(step.params or {}),
    )


def _candidate_to_text(candidate: Candidate) -> str:
    return to_json(
        {
            "reasoning": candidate.reasoning,
            "action": candidate.action,
            "tool_name": candidate.tool_name,
            "tool_params": candidate.tool_params,
        }
    )


def _preference_reason(better: CandidateOutcome, worse: CandidateOutcome) -> str:
    if better.result.success and not worse.result.success:
        return "success_over_failure"
    if better.result.success and worse.result.success:
        return "lower_cost_success"
    if better.candidate.tool_name is not None and worse.candidate.tool_name is None:
        return "executable_failure_over_give_up"
    return "rank_key_order"
