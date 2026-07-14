from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar

from rpl.pref_data.dpo_data import build_dpo_prompt, normalize_recovery_text
from rpl.pref_model.model import PrefModel

if TYPE_CHECKING:
    from rpl.recovery.types import Candidate, ErrorContext


@dataclass(frozen=True)
class LogProbStats:
    """Conditional response log-probability under a causal language model."""

    mean_logprob: float
    sum_logprob: float
    token_count: int


def _candidate_response(candidate: Candidate) -> str:
    return json.dumps(
        {
            "reasoning": candidate.reasoning,
            "action": candidate.action,
            "tool_name": candidate.tool_name,
            "tool_params": candidate.tool_params,
        },
        ensure_ascii=False,
    )


def _conditional_logprob_stats(
    *,
    torch: Any,
    model: Any,
    tokenizer: Any,
    prompt: str,
    response: str,
) -> LogProbStats:
    full_text = prompt + "\n" + response
    prompt_ids = tokenizer(prompt + "\n", return_tensors="pt").input_ids
    full = tokenizer(full_text, return_tensors="pt")
    input_ids = full.input_ids.to(model.device)
    attention_mask = full.attention_mask.to(model.device)
    prompt_len = prompt_ids.shape[1]

    with torch.no_grad():
        logits = model(input_ids=input_ids, attention_mask=attention_mask).logits
    shift_logits = logits[:, :-1, :]
    shift_labels = input_ids[:, 1:]
    log_probs = torch.log_softmax(shift_logits, dim=-1)
    token_log_probs = log_probs.gather(-1, shift_labels.unsqueeze(-1)).squeeze(-1)

    response_start = max(prompt_len - 1, 0)
    response_log_probs = token_log_probs[:, response_start:]
    token_count = int(response_log_probs.numel())
    if token_count == 0:
        return LogProbStats(mean_logprob=-1e9, sum_logprob=-1e9, token_count=0)
    return LogProbStats(
        mean_logprob=float(response_log_probs.mean().item()),
        sum_logprob=float(response_log_probs.sum().item()),
        token_count=token_count,
    )


@dataclass
class BaseModelPrefModel(PrefModel):
    """Base model scored by conditional response log probability — no LoRA adapter.

    Ablation baseline: uses the same scoring mechanism as DPOPrefModel but loads only
    the un-finetuned base model. Comparing base_model vs dpo_pm isolates the contribution
    of DPO training to preference ranking ability.
    """

    base_model: str
    device: str | None = None
    give_up_penalty: float | None = None

    GIVE_UP_PENALTY: ClassVar[float] = -5.0

    def __post_init__(self) -> None:
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "Missing DPO inference dependencies. Install torch and transformers."
            ) from exc

        self._torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(self.base_model, trust_remote_code=True)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        self.model = AutoModelForCausalLM.from_pretrained(
            self.base_model,
            trust_remote_code=True,
            device_map="auto" if self.device is None else None,
        )
        if self.device is not None:
            self.model.to(self.device)
        self.model.eval()

    def score(self, error_context: ErrorContext, candidate: Candidate) -> float:
        raw = self.score_stats(error_context, candidate).mean_logprob
        if candidate.action == "give_up" or candidate.tool_name is None:
            return raw + self.effective_give_up_penalty
        return raw

    @property
    def effective_give_up_penalty(self) -> float:
        if self.give_up_penalty is None:
            return self.GIVE_UP_PENALTY
        return self.give_up_penalty

    def score_stats(self, error_context: ErrorContext, candidate: Candidate) -> LogProbStats:
        return self.score_text(error_context.to_prompt(), _candidate_response(candidate))

    def score_text(self, error_context_prompt: str, response_text: str) -> LogProbStats:
        prompt = build_dpo_prompt(error_context_prompt)
        response = normalize_recovery_text(response_text)
        return self._conditional_logprob_stats(prompt, response)

    def is_loaded(self) -> bool:
        return True

    def _conditional_logprob_stats(self, prompt: str, response: str) -> LogProbStats:
        return _conditional_logprob_stats(
            torch=self._torch,
            model=self.model,
            tokenizer=self.tokenizer,
            prompt=prompt,
            response=response,
        )

    def _conditional_logprob(self, prompt: str, response: str) -> float:
        """Backward-compatible mean log-probability helper."""

        return self._conditional_logprob_stats(prompt, response).mean_logprob


@dataclass
class DPOPrefModel(PrefModel):
    """DPO-trained LoRA preference model scored by conditional response log probability."""

    base_model: str
    adapter_path: str
    device: str | None = None
    give_up_penalty: float | None = None

    GIVE_UP_PENALTY: ClassVar[float] = -5.0

    def __post_init__(self) -> None:
        try:
            import torch
            from peft import PeftModel
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "Missing DPO inference dependencies. Install torch, transformers, and peft."
            ) from exc

        self._torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(self.adapter_path, trust_remote_code=True)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        model = AutoModelForCausalLM.from_pretrained(
            self.base_model,
            trust_remote_code=True,
            device_map="auto" if self.device is None else None,
        )
        self.model = PeftModel.from_pretrained(model, self.adapter_path)
        if self.device is not None:
            self.model.to(self.device)
        self.model.eval()

    def score(self, error_context: ErrorContext, candidate: Candidate) -> float:
        raw = self.score_stats(error_context, candidate).mean_logprob
        if candidate.action == "give_up" or candidate.tool_name is None:
            return raw + self.effective_give_up_penalty
        return raw

    @property
    def effective_give_up_penalty(self) -> float:
        if self.give_up_penalty is None:
            return self.GIVE_UP_PENALTY
        return self.give_up_penalty

    def score_stats(self, error_context: ErrorContext, candidate: Candidate) -> LogProbStats:
        return self.score_text(error_context.to_prompt(), _candidate_response(candidate))

    def score_text(self, error_context_prompt: str, response_text: str) -> LogProbStats:
        prompt = build_dpo_prompt(error_context_prompt)
        response = normalize_recovery_text(response_text)
        return self._conditional_logprob_stats(prompt, response)

    def is_loaded(self) -> bool:
        return True

    def _conditional_logprob_stats(self, prompt: str, response: str) -> LogProbStats:
        return _conditional_logprob_stats(
            torch=self._torch,
            model=self.model,
            tokenizer=self.tokenizer,
            prompt=prompt,
            response=response,
        )

    def _conditional_logprob(self, prompt: str, response: str) -> float:
        """Backward-compatible mean log-probability helper."""

        return self._conditional_logprob_stats(prompt, response).mean_logprob
