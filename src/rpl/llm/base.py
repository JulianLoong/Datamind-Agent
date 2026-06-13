from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class LLMRequest:
    prompt: str
    temperature: float = 0.0
    max_tokens: int = 1024


@dataclass(frozen=True)
class LLMResponse:
    text: str
    tokens_used: int = 0


class LLMClient(ABC):
    @abstractmethod
    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Return a completion for the given prompt."""
