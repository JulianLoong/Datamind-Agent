from __future__ import annotations

import asyncio

from rpl.llm import CachedLLMClient, FakeLLMClient, LLMClient, LLMRequest, LLMResponse, OpenAICompatibleLLMClient
from rpl.llm.openai_compatible import _extract_completion_text, _extract_tokens_used
from rpl.recovery.candidate_gen import build_llm_client


def test_build_llm_client_defaults_to_fake() -> None:
    client = build_llm_client()

    assert isinstance(client, FakeLLMClient)


def test_build_llm_client_can_create_openai_compatible_client() -> None:
    client = build_llm_client(provider="openai_compatible", model="gpt-test", api_key="secret")

    assert isinstance(client, OpenAICompatibleLLMClient)
    assert client.model == "gpt-test"


def test_build_llm_client_can_create_zhipu_client() -> None:
    client = build_llm_client(provider="glm", model="glm-5.1", api_key="secret")

    assert isinstance(client, OpenAICompatibleLLMClient)
    assert client.model == "glm-5.1"
    assert client.extra_body["response_format"] == {"type": "json_object"}


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
    request = LLMRequest(
        prompt='Error Type: invalid_json\nFailed Tool: json_parse\n'
        'Tool Params: {"text": "{bad", "field": "value"}\n'
        "Error Message: Expecting value\n"
    )

    # No network call, just make sure the fake path is still intact.
    response = asyncio.run(client.complete(request))

    assert "repair_json_payload" in response.text
    assert '"candidates"' in response.text


def test_cached_llm_client_replays_identical_requests(tmp_path) -> None:
    class CountingLLMClient(LLMClient):
        def __init__(self) -> None:
            self.calls = 0

        async def complete(self, request: LLMRequest) -> LLMResponse:
            self.calls += 1
            return LLMResponse(text=f"response-{self.calls}", tokens_used=7)

    base = CountingLLMClient()
    cache_path = tmp_path / "llm_cache.jsonl"
    client = CachedLLMClient(base, cache_path=cache_path, namespace="test")
    request = LLMRequest(prompt="same prompt", temperature=0.2, max_tokens=12)

    first = asyncio.run(client.complete(request))
    second = asyncio.run(client.complete(request))
    replay = asyncio.run(CachedLLMClient(base, cache_path=cache_path, namespace="test").complete(request))

    assert first == second == replay
    assert base.calls == 1
    assert cache_path.exists()
