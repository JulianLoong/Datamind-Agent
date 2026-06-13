from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from rpl.pref_data.dpo_data import build_dpo_prompt, normalize_recovery_text
from rpl.pref_model.model import PrefModel

if TYPE_CHECKING:
    from rpl.recovery.types import Candidate, ErrorContext


@dataclass
class DPOPrefModel(PrefModel):
    """DPO-trained LoRA preference model scored by conditional response log probability."""

    base_model: str
    adapter_path: str
    device: str | None = None

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

    def score(self, error_context: "ErrorContext", candidate: "Candidate") -> float:
        prompt = build_dpo_prompt(error_context.to_prompt())
        response = normalize_recovery_text(
            json.dumps(
                {
                    "reasoning": candidate.reasoning,
                    "action": candidate.action,
                    "tool_name": candidate.tool_name,
                    "tool_params": candidate.tool_params,
                },
                ensure_ascii=False,
            )
        )
        return float(self._conditional_logprob(prompt, response))

    def is_loaded(self) -> bool:
        return True

    def _conditional_logprob(self, prompt: str, response: str) -> float:
        torch = self._torch
        full_text = prompt + "\n" + response
        prompt_ids = self.tokenizer(prompt + "\n", return_tensors="pt").input_ids
        full = self.tokenizer(full_text, return_tensors="pt")
        input_ids = full.input_ids.to(self.model.device)
        attention_mask = full.attention_mask.to(self.model.device)
        prompt_len = prompt_ids.shape[1]

        with torch.no_grad():
            logits = self.model(input_ids=input_ids, attention_mask=attention_mask).logits
        shift_logits = logits[:, :-1, :]
        shift_labels = input_ids[:, 1:]
        log_probs = torch.log_softmax(shift_logits, dim=-1)
        token_log_probs = log_probs.gather(-1, shift_labels.unsqueeze(-1)).squeeze(-1)

        response_start = max(prompt_len - 1, 0)
        response_log_probs = token_log_probs[:, response_start:]
        if response_log_probs.numel() == 0:
            return -1e9
        return response_log_probs.mean().item()
