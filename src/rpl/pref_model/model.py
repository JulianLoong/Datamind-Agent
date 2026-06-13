from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from rpl.recovery.types import Candidate, ErrorContext


class PrefModel:
    """Preference model interface for recovery candidate ranking."""

    def score(self, error_context: "ErrorContext", candidate: "Candidate") -> float:
        raise NotImplementedError

    def rank(
        self,
        error_context: ErrorContext,
        candidates: list[Candidate],
    ) -> list[tuple[int, float]]:
        scored = [(idx, self.score(error_context, candidate)) for idx, candidate in enumerate(candidates)]
        return sorted(scored, key=lambda item: item[1], reverse=True)

    def is_loaded(self) -> bool:
        return False


class MockPrefModel(PrefModel):
    """Rule-based ranking substitute before real DPO checkpoints exist."""

    def score(self, error_context: "ErrorContext", candidate: "Candidate") -> float:
        score = 0.0
        if candidate.tool_name is None or candidate.action == "give_up":
            score -= 10.0
        if candidate.action == "retry_same_tool":
            score -= 2.0
        if candidate.tool_name is not None and candidate.tool_params is not None:
            score += 1.0
        if error_context.error_type == "division_by_zero" and candidate.action == "avoid_zero_division":
            score += 5.0
        if error_context.error_type == "invalid_json" and candidate.action == "repair_json_payload":
            score += 5.0
        if error_context.error_type == "not_found" and candidate.action == "try_known_fixture":
            score += 5.0
        return score

    def is_loaded(self) -> bool:
        return True


@dataclass
class LightweightPrefModel(PrefModel):
    """Small pairwise linear ranker trained from exported preference pairs.

    This is intentionally simple and dependency-free. It gives the project a real train -> save
    -> load -> select loop for thesis experiments before heavier DPO training is introduced.
    """

    weights: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def score(self, error_context: "ErrorContext", candidate: "Candidate") -> float:
        features = candidate_features(
            context={
                "error_type": error_context.error_type,
                "tool_name": error_context.tool_name,
                "tool_params": error_context.tool_params,
            },
            candidate={
                "action": candidate.action,
                "tool_name": candidate.tool_name,
                "tool_params": candidate.tool_params,
            },
        )
        return score_features(self.weights, features)

    def is_loaded(self) -> bool:
        return bool(self.weights)

    def save(self, path: str | Path) -> None:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(
                {
                    "model_type": "lightweight_pairwise_linear",
                    "weights": self.weights,
                    "metadata": self.metadata,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: str | Path) -> "LightweightPrefModel":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        weights = data.get("weights", {})
        metadata = data.get("metadata", {})
        if not isinstance(weights, dict):
            raise ValueError("Invalid lightweight PM checkpoint: weights must be an object")
        return cls(
            weights={str(key): float(value) for key, value in weights.items()},
            metadata=metadata if isinstance(metadata, dict) else {},
        )


def train_lightweight_pref_model(
    records: list[dict[str, Any]],
    *,
    epochs: int = 12,
    learning_rate: float = 0.25,
    margin: float = 1.0,
) -> LightweightPrefModel:
    """Train a pairwise perceptron-style ranker from DPO JSONL records."""

    weights: dict[str, float] = {}
    usable_records = [
        record
        for record in records
        if isinstance(record.get("prompt"), str)
        and isinstance(record.get("chosen"), str)
        and isinstance(record.get("rejected"), str)
    ]
    updates = 0
    for _ in range(max(1, epochs)):
        for record in usable_records:
            context = parse_prompt_context(record["prompt"])
            chosen = parse_candidate_text(record["chosen"])
            rejected = parse_candidate_text(record["rejected"])
            if not chosen or not rejected:
                continue

            chosen_features = candidate_features(context=context, candidate=chosen)
            rejected_features = candidate_features(context=context, candidate=rejected)
            chosen_score = score_features(weights, chosen_features)
            rejected_score = score_features(weights, rejected_features)
            confidence = float(record.get("confidence", 1.0) or 1.0)
            if chosen_score - rejected_score >= margin:
                continue

            delta = learning_rate * max(0.1, min(confidence, 1.0))
            for name, value in chosen_features.items():
                weights[name] = weights.get(name, 0.0) + delta * value
            for name, value in rejected_features.items():
                weights[name] = weights.get(name, 0.0) - delta * value
            updates += 1

    return LightweightPrefModel(
        weights=weights,
        metadata={
            "training_records": len(usable_records),
            "epochs": epochs,
            "learning_rate": learning_rate,
            "margin": margin,
            "updates": updates,
        },
    )


def score_features(weights: dict[str, float], features: dict[str, float]) -> float:
    return sum(weights.get(name, 0.0) * value for name, value in features.items())


def parse_candidate_text(text: str) -> dict[str, Any]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def parse_prompt_context(prompt: str) -> dict[str, Any]:
    error_match = re.search(r"^\[Error\]:\s*([^:\n]+):", prompt, flags=re.MULTILINE)
    tool_match = re.search(r"^\[Failed Tool\]:\s*([^(]+)\((.*)\)$", prompt, flags=re.MULTILINE)
    tool_params: dict[str, Any] = {}
    if tool_match:
        raw_params = tool_match.group(2).strip()
        try:
            parsed = json.loads(raw_params.replace("'", '"'))
        except json.JSONDecodeError:
            parsed = {}
        if isinstance(parsed, dict):
            tool_params = parsed
    return {
        "error_type": error_match.group(1).strip() if error_match else "unknown_error",
        "tool_name": tool_match.group(1).strip() if tool_match else "unknown_tool",
        "tool_params": tool_params,
    }


def candidate_features(context: dict[str, Any], candidate: dict[str, Any]) -> dict[str, float]:
    error_type = str(context.get("error_type") or "unknown_error")
    failed_tool = str(context.get("tool_name") or "unknown_tool")
    original_params = context.get("tool_params") if isinstance(context.get("tool_params"), dict) else {}
    action = str(candidate.get("action") or "unknown_action")
    tool_name = candidate.get("tool_name")
    tool_params = candidate.get("tool_params") if isinstance(candidate.get("tool_params"), dict) else None

    features: dict[str, float] = {
        "bias": 1.0,
        f"error={error_type}": 1.0,
        f"action={action}": 1.0,
        f"error_action={error_type}|{action}": 1.0,
    }
    if tool_name is None:
        features["tool_name=None"] = 1.0
        features["is_give_up"] = 1.0
    else:
        tool_name_str = str(tool_name)
        features[f"tool={tool_name_str}"] = 1.0
        features["same_tool"] = 1.0 if tool_name_str == failed_tool else 0.0
        features["has_executable_tool"] = 1.0

    if action == "retry_same_tool":
        features["is_retry_same_tool"] = 1.0
    if action == "give_up":
        features["is_give_up"] = 1.0
    if tool_params is not None:
        features["has_tool_params"] = 1.0
        features["params_changed"] = 1.0 if tool_params != original_params else 0.0
        for key, value in tool_params.items():
            if original_params.get(key) != value:
                features[f"changed_param={key}"] = 1.0
    return features
