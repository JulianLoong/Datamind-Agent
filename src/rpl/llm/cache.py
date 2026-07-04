from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from rpl.llm.base import LLMClient, LLMRequest, LLMResponse


@dataclass
class CachedLLMClient(LLMClient):
    """Replay identical LLM prompts across baselines while preserving real generated candidates."""

    client: LLMClient
    cache_path: str | Path | None = None
    namespace: str = ""

    def __post_init__(self) -> None:
        self._cache: dict[str, LLMResponse] = {}
        self._path = Path(self.cache_path) if self.cache_path is not None else None
        if self._path is not None and self._path.exists():
            for line in self._path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                item = json.loads(line)
                response = item.get("response", {})
                self._cache[str(item["key"])] = LLMResponse(
                    text=str(response.get("text", "")),
                    tokens_used=int(response.get("tokens_used", 0)),
                )

    async def complete(self, request: LLMRequest) -> LLMResponse:
        key = self.cache_key(request)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        response = await self.client.complete(request)
        self._cache[key] = response
        if self._path is not None:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._path.open("a", encoding="utf-8") as handle:
                handle.write(
                    json.dumps(
                        {
                            "key": key,
                            "namespace": self.namespace,
                            "request": asdict(request),
                            "response": asdict(response),
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
        return response

    def cache_key(self, request: LLMRequest) -> str:
        payload = {
            "namespace": self.namespace,
            "prompt": request.prompt,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()
