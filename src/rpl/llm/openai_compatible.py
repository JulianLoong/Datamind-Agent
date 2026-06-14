from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any
from urllib import error, request

from rpl.llm.base import LLMClient, LLMRequest, LLMResponse


@dataclass(frozen=True)
class OpenAICompatibleLLMClient(LLMClient):
    """Minimal OpenAI-compatible chat completions client.

    This uses only the Python standard library so the local repo can exercise the real candidate
    generation path without introducing a hard dependency on the OpenAI SDK.
    """

    model: str
    base_url: str = "https://api.openai.com"
    api_path: str = "/v1/chat/completions"
    api_key: str | None = None
    api_key_env: str = "OPENAI_API_KEY"
    timeout: float = 60.0
    extra_headers: dict[str, str] = field(default_factory=dict)

    async def complete(self, request: LLMRequest) -> LLMResponse:
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": request.prompt}],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }
        raw_response = self._post_json(payload)
        return LLMResponse(
            text=_extract_completion_text(raw_response),
            tokens_used=_extract_tokens_used(raw_response),
        )

    def _post_json(self, payload: dict[str, Any]) -> dict[str, Any]:
        url = self.base_url.rstrip("/") + self.api_path
        api_key = self.api_key or os.environ.get(self.api_key_env)
        if not api_key:
            raise RuntimeError(
                f"Missing API key for OpenAI-compatible client. Set {self.api_key_env} or pass api_key."
            )

        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            **self.extra_headers,
        }
        req = request.Request(url, data=body, headers=headers, method="POST")
        try:
            with request.urlopen(req, timeout=self.timeout) as resp:
                data = resp.read().decode("utf-8")
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
            raise RuntimeError(f"OpenAI-compatible request failed: {exc.code} {exc.reason} {detail}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"OpenAI-compatible request failed: {exc.reason}") from exc

        try:
            parsed = json.loads(data)
        except json.JSONDecodeError as exc:
            raise RuntimeError("OpenAI-compatible response was not valid JSON") from exc
        if not isinstance(parsed, dict):
            raise RuntimeError("OpenAI-compatible response must be a JSON object")
        return parsed


def _extract_completion_text(response: dict[str, Any]) -> str:
    choices = response.get("choices")
    if isinstance(choices, list) and choices:
        first = choices[0]
        if isinstance(first, dict):
            message = first.get("message")
            if isinstance(message, dict):
                content = message.get("content")
                if isinstance(content, str):
                    return content
            text = first.get("text")
            if isinstance(text, str):
                return text
    output_text = response.get("output_text")
    if isinstance(output_text, str):
        return output_text
    return ""


def _extract_tokens_used(response: dict[str, Any]) -> int:
    usage = response.get("usage")
    if isinstance(usage, dict):
        total = usage.get("total_tokens")
        if isinstance(total, int):
            return total
        prompt_tokens = usage.get("prompt_tokens")
        completion_tokens = usage.get("completion_tokens")
        if isinstance(prompt_tokens, int) and isinstance(completion_tokens, int):
            return prompt_tokens + completion_tokens
    return 0
