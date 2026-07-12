from __future__ import annotations

import pytest

from rpl.llm import LLMClient, LLMRequest, LLMResponse
from rpl.recovery.selector import LLMSelfSelector
from rpl.recovery.types import Candidate, ErrorContext


class _StubClient(LLMClient):
    def __init__(self, text: str, tokens: int = 7) -> None:
        self._text = text
        self._tokens = tokens

    async def complete(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(text=self._text, tokens_used=self._tokens)


def _ctx() -> ErrorContext:
    return ErrorContext(
        task_goal="parse json",
        step_description="json",
        tool_name="json_parse",
        tool_params={"text": '{"a":', "field": "a"},
        error_type="invalid_json",
        error_message="Expecting value",
        recent_history=[],
    )


def _candidates() -> list[Candidate]:
    return [
        Candidate("retry", "retry_same_tool", "json_parse", {"text": '{"a":', "field": "a"}, "retry"),
        Candidate("repair", "repair_json_payload", "json_parse", {"text": '{"a": null}', "field": "a"}, "repair"),
        Candidate("stop", "give_up", None, None, "stop"),
    ]


@pytest.mark.asyncio
async def test_llm_self_selector_picks_returned_index() -> None:
    selector = LLMSelfSelector(_StubClient('{"chosen_index": 1}', tokens=7))

    idx, candidate = await selector.select(_ctx(), _candidates())

    assert idx == 1
    assert candidate.action == "repair_json_payload"
    assert selector.last_scores() == [0.0, 1.0, 0.0]
    cost = selector.last_cost()
    assert cost.selector_tokens == 7
    assert cost.selector_evals == 1


@pytest.mark.asyncio
async def test_llm_self_selector_clamps_out_of_range() -> None:
    selector = LLMSelfSelector(_StubClient('{"chosen_index": 99}'))

    idx, candidate = await selector.select(_ctx(), _candidates())

    assert idx == 0
    assert candidate.action == "retry_same_tool"


@pytest.mark.asyncio
async def test_llm_self_selector_negative_index_falls_back() -> None:
    selector = LLMSelfSelector(_StubClient('{"chosen_index": -1}'))

    idx, _ = await selector.select(_ctx(), _candidates())

    assert idx == 0


@pytest.mark.asyncio
async def test_llm_self_selector_falls_back_on_garbage() -> None:
    selector = LLMSelfSelector(_StubClient("not json at all"))

    idx, candidate = await selector.select(_ctx(), _candidates())

    assert idx == 0
    assert candidate.action == "retry_same_tool"
    assert selector.last_scores() == [1.0, 0.0, 0.0]
