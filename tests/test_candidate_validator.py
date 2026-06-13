from __future__ import annotations

from rpl.recovery.types import Candidate
from rpl.recovery.validator import CandidateValidator
from rpl.tools.builtin import build_builtin_registry


def test_candidate_validator_rejects_unknown_tool() -> None:
    validator = CandidateValidator(build_builtin_registry())
    candidate = Candidate("r", "a", "missing_tool", {}, "raw")

    result = validator.validate(candidate)

    assert result.valid is False


def test_candidate_validator_rejects_invalid_params() -> None:
    validator = CandidateValidator(build_builtin_registry())
    candidate = Candidate("r", "a", "math_calc", {}, "raw")

    result = validator.validate(candidate)

    assert result.valid is False


def test_candidate_validator_allows_give_up() -> None:
    validator = CandidateValidator(build_builtin_registry())
    candidate = Candidate("r", "give_up", None, None, "raw")

    result = validator.validate(candidate)

    assert result.valid is True
