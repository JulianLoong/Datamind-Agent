from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from rpl.tools.base import ToolResult
from rpl.trajectory.store import from_json

if TYPE_CHECKING:
    from rpl.recovery.types import Candidate, ErrorContext


@dataclass(frozen=True)
class ExperienceRecord:
    tool_name: str
    error_type: str
    error_message: str
    failed_params: dict[str, Any]
    successful_candidate: Candidate
    final_result: ToolResult | None = None
    recovery_attempts: int = 1
    tool_calls: int = 1
    tokens: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class ExperienceMemory:
    """Small in-process store for successful recovery experiences.

    The first implementation intentionally uses transparent lexical/schema overlap instead of
    embeddings. This keeps the cold-start loop reproducible and makes memory influence auditable.
    """

    def __init__(self, records: list[ExperienceRecord] | None = None) -> None:
        self._records = list(records or [])

    def add(self, record: ExperienceRecord) -> None:
        self._records.append(record)

    def records(self) -> list[ExperienceRecord]:
        return list(self._records)

    def retrieve(
        self,
        ctx: ErrorContext,
        *,
        candidate: Candidate | None = None,
        top_k: int = 3,
        min_score: float = 0.0,
    ) -> list[tuple[ExperienceRecord, float]]:
        scored = [
            (record, self.score(ctx, record, candidate=candidate))
            for record in self._records
        ]
        scored = [(record, score) for record, score in scored if score > min_score]
        return sorted(scored, key=lambda item: item[1], reverse=True)[:top_k]

    def score(self, ctx: ErrorContext, record: ExperienceRecord, *, candidate: Candidate | None = None) -> float:
        score = 0.0
        if ctx.tool_name == record.tool_name:
            score += 3.0
        if ctx.error_type == record.error_type:
            score += 4.0
        score += _jaccard(set(ctx.tool_params.keys()), set(record.failed_params.keys()))
        score += _jaccard(_tokens(ctx.error_message), _tokens(record.error_message))
        if candidate is not None:
            score += _candidate_similarity(candidate, record.successful_candidate) * 3.0
        return score

    @classmethod
    def from_recovery_rows(cls, rows: list[dict[str, Any]]) -> "ExperienceMemory":
        memory = cls()
        for row in rows:
            record = experience_from_recovery_row(row)
            if record is not None:
                memory.add(record)
        return memory


def experience_from_recovery_row(row: dict[str, Any]) -> ExperienceRecord | None:
    final_result = _tool_result_from_json(row.get("final_result_json"))
    if final_result is None or not final_result.success:
        return None

    error_context = from_json(row.get("error_context_json"), {})
    candidate = from_json(row.get("chosen_candidate_json"), {})
    if not isinstance(error_context, dict) or not isinstance(candidate, dict):
        return None

    tool_name = error_context.get("tool_name")
    error_type = error_context.get("error_type")
    failed_params = error_context.get("tool_params")
    if not isinstance(tool_name, str) or not isinstance(error_type, str) or not isinstance(failed_params, dict):
        return None

    successful_candidate = _candidate_from_dict(candidate)
    if successful_candidate is None or successful_candidate.tool_name is None:
        return None

    return ExperienceRecord(
        tool_name=tool_name,
        error_type=error_type,
        error_message=str(error_context.get("error_message") or ""),
        failed_params=failed_params,
        successful_candidate=successful_candidate,
        final_result=final_result,
        recovery_attempts=1,
        tool_calls=1,
        tokens=final_result.tokens_used,
        metadata={
            "task_id": row.get("task_id"),
            "step_id": row.get("step_id"),
            "recovery_id": row.get("id"),
        },
    )


def _candidate_from_dict(value: dict[str, Any]) -> Candidate | None:
    from rpl.recovery.types import Candidate

    reasoning = value.get("reasoning")
    action = value.get("action")
    tool_name = value.get("tool_name")
    tool_params = value.get("tool_params")
    raw_text = value.get("raw_text")
    if not isinstance(reasoning, str) or not isinstance(action, str):
        return None
    if tool_name is not None and not isinstance(tool_name, str):
        return None
    if tool_params is not None and not isinstance(tool_params, dict):
        return None
    return Candidate(
        reasoning=reasoning,
        action=action,
        tool_name=tool_name,
        tool_params=tool_params,
        raw_text=raw_text if isinstance(raw_text, str) else "",
    )


def _tool_result_from_json(value: str | None) -> ToolResult | None:
    data = from_json(value, None)
    if not isinstance(data, dict):
        return None
    success = data.get("success")
    if not isinstance(success, bool):
        return None
    return ToolResult(
        success=success,
        data=data.get("data"),
        error_type=data.get("error_type") if isinstance(data.get("error_type"), str) else None,
        error_message=data.get("error_message") if isinstance(data.get("error_message"), str) else None,
        tokens_used=int(data.get("tokens_used") or 0),
        latency_ms=float(data.get("latency_ms") or 0.0),
    )


def _candidate_similarity(candidate: Candidate, remembered: Candidate) -> float:
    score = 0.0
    if candidate.action == remembered.action:
        score += 1.0
    if candidate.tool_name == remembered.tool_name:
        score += 1.0
    candidate_keys = set((candidate.tool_params or {}).keys())
    remembered_keys = set((remembered.tool_params or {}).keys())
    score += _jaccard(candidate_keys, remembered_keys)
    return score / 3.0


def _tokens(text: str) -> set[str]:
    return {part.lower() for part in text.replace("_", " ").replace(":", " ").split() if part.strip()}


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 0.0
    union = left | right
    if not union:
        return 0.0
    return len(left & right) / len(union)
