from __future__ import annotations

import asyncio

from rpl.llm import FakeLLMClient, LLMRequest, OpenAICompatibleLLMClient
from rpl.llm.openai_compatible import _extract_completion_text, _extract_tokens_used
from rpl.recovery.candidate_gen import build_llm_client


def test_build_llm_client_defaults_to_fake() -> None:
    client = build_llm_client()

    assert isinstance(client, FakeLLMClient)


def test_build_llm_client_can_create_openai_compatible_client() -> None:
    client = build_llm_client(provider="openai_compatible", model="gpt-test", api_key="secret")

    assert isinstance(client, OpenAICompatibleLLMClient)
    assert client.model == "gpt-test"


def test_openai_compatible_extract_helpers_handle_chat_payload() -> None:
    response = {
        "choices": [{"message": {"content": "hello"}}],
        "usage": {"total_tokens": 11},
    }

    client = OpenAICompatibleLLMClient(model="gpt-test", api_key="secret")

    assert _extract_completion_text(response) == "hello"
    assert _extract_tokens_used(response) == 11


def test_fake_llm_still_returns_recoverable_candidates() -> None:
    client = FakeLLMClient()
    request = LLMRequest(prompt="Error Type: division_by_zero\nFailed Tool: math_calc\nTool Params: {\"expression\": \"1/0\"}")

    # No network call, just make sure the fake path is still intact.
    response = asyncio.run(client.complete(request))

    assert "avoid_zero_division" in response.text
