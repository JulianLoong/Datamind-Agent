from __future__ import annotations

import pytest

from rpl.llm import LLMClient, LLMRequest, LLMResponse
from rpl.recovery.candidate_gen import (
    CandidateGenerationError,
    CandidateGenerator,
    parse_candidates,
)
from rpl.recovery.types import ErrorContext
from rpl.tools.builtin import build_builtin_registry


def test_parse_candidates_from_json() -> None:
    candidates = parse_candidates(
        '[{"reasoning":"r","action":"a","tool_name":"math_calc","tool_params":{"expression":"1+1"}}]'
    )

    assert len(candidates) == 1
    assert candidates[0].action == "a"


def test_parse_candidates_from_object() -> None:
    candidates = parse_candidates(
        '{"candidates":[{"reasoning":"r","action":"a","tool_name":null,'
        '"tool_params":null}]}'
    )

    assert len(candidates) == 1
    assert candidates[0].action == "a"


@pytest.mark.asyncio
async def test_fake_llm_candidate_generator_recovers_invalid_json() -> None:
    ctx = ErrorContext(
        task_goal="parse json",
        step_description="json",
        tool_name="json_parse",
        tool_params={"text": '{"a":', "field": "a"},
        error_type="invalid_json",
        error_message="Expecting value: line 1 column 6 (char 5)",
        recent_history=[],
    )

    candidates = await CandidateGenerator().generate(ctx, k=2)

    assert any(
        candidate.action == "repair_json_payload" and candidate.tool_params.get("text") == '{"a": null}'
        for candidate in candidates
    )


@pytest.mark.asyncio
async def test_fake_llm_candidate_generator_recovers_validation_error_wrong_type() -> None:
    ctx = ErrorContext(
        task_goal="evaluate",
        step_description="math",
        tool_name="math_calc",
        tool_params={"expression": 42},
        error_type="validation_error",
        error_message="Invalid parameters for math_calc: 'expression' must be a string",
        recent_history=[],
    )

    candidates = await CandidateGenerator().generate(ctx, k=2)

    assert any(
        candidate.action == "fix_param_type" and candidate.tool_params == {"expression": "42"}
        for candidate in candidates
    )


@pytest.mark.asyncio
async def test_candidate_generator_raises_on_malformed_response_in_strict_mode() -> None:
    class MalformedClient(LLMClient):
        async def complete(self, request: LLMRequest) -> LLMResponse:
            return LLMResponse(text="not-json", tokens_used=3)

    ctx = ErrorContext(
        task_goal="parse json",
        step_description="json",
        tool_name="json_parse",
        tool_params={"text": '{"a":', "field": "a"},
        error_type="invalid_json",
        error_message="Expecting value",
        recent_history=[],
    )

    with pytest.raises(CandidateGenerationError, match="not-json"):
        await CandidateGenerator(MalformedClient(), strict_parsing=True).generate(ctx, k=2)


@pytest.mark.asyncio
async def test_candidate_generator_can_fallback_when_strict_mode_is_disabled() -> None:
    class MalformedClient(LLMClient):
        async def complete(self, request: LLMRequest) -> LLMResponse:
            return LLMResponse(text="not-json", tokens_used=3)

    ctx = ErrorContext(
        task_goal="evaluate",
        step_description="math",
        tool_name="math_calc",
        tool_params={"expression": 42},
        error_type="validation_error",
        error_message="Invalid parameters for math_calc: 'expression' must be a string",
        recent_history=[],
    )

    candidates = await CandidateGenerator(MalformedClient()).generate(ctx, k=2)

    assert candidates[0].action == "fix_param_type"


def test_candidate_prompt_includes_available_tool_schemas() -> None:
    ctx = ErrorContext(
        task_goal="parse json",
        step_description="parse",
        tool_name="json_parse",
        tool_params={"text": '{"a":', "field": "a"},
        error_type="invalid_json",
        error_message="Expecting value",
        recent_history=[],
    )
    registry = build_builtin_registry()

    prompt = CandidateGenerator.build_prompt(ctx, 3, tool_specs=registry.list_tools())

    assert "Available Tools JSON" in prompt
    assert '"name": "json_parse"' in prompt
    assert '"additionalProperties": false' in prompt
    assert "Only use tool_name values listed above. Do not invent tools." in prompt
