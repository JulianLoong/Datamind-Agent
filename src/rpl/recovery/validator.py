from __future__ import annotations

from dataclasses import dataclass

from rpl.recovery.types import Candidate
from rpl.tools.registry import ParameterValidationError, ToolRegistry, validate_params


@dataclass(frozen=True)
class CandidateValidationResult:
    candidate: Candidate
    valid: bool
    reason: str = ""


class CandidateValidator:
    """Validate recovery candidates before selector ranking.

    Invalid candidates are removed before selection so the agent does not waste recovery attempts on
    unknown tools or malformed parameters. `give_up` candidates (`tool_name is None`) are considered
    valid because they are an explicit bounded-failure action.
    """

    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry

    def validate(self, candidate: Candidate) -> CandidateValidationResult:
        if candidate.tool_name is None:
            return CandidateValidationResult(candidate, True)
        try:
            tool = self.registry.get(candidate.tool_name)
        except KeyError as exc:
            return CandidateValidationResult(candidate, False, str(exc))
        try:
            validate_params(candidate.tool_params or {}, tool.schema)
        except ParameterValidationError as exc:
            return CandidateValidationResult(candidate, False, str(exc))
        return CandidateValidationResult(candidate, True)

    def filter_valid(self, candidates: list[Candidate]) -> list[Candidate]:
        return [result.candidate for result in map(self.validate, candidates) if result.valid]
