from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from typing import Any

from rpl.pref_data.types import PreferencePair


@dataclass
class PreferenceDataReport:
    total_pairs: int
    source_counts: dict[str, int]
    chosen_action_counts: dict[str, int]
    rejected_action_counts: dict[str, int]
    confidence_min: float | None
    confidence_max: float | None
    confidence_avg: float | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_pairs": self.total_pairs,
            "source_counts": self.source_counts,
            "chosen_action_counts": self.chosen_action_counts,
            "rejected_action_counts": self.rejected_action_counts,
            "confidence_min": self.confidence_min,
            "confidence_max": self.confidence_max,
            "confidence_avg": self.confidence_avg,
        }

    def to_markdown(self) -> str:
        return "\n".join(
            [
                f"total_pairs: {self.total_pairs}",
                f"source_counts: {self.source_counts}",
                f"chosen_action_counts: {self.chosen_action_counts}",
                f"rejected_action_counts: {self.rejected_action_counts}",
                f"confidence_min: {self.confidence_min}",
                f"confidence_max: {self.confidence_max}",
                f"confidence_avg: {self.confidence_avg}",
            ]
        )


class PreferenceDataReporter:
    def build(self, pairs: list[PreferencePair]) -> PreferenceDataReport:
        confidences = [pair.confidence for pair in pairs]
        return PreferenceDataReport(
            total_pairs=len(pairs),
            source_counts=dict(Counter(pair.source for pair in pairs)),
            chosen_action_counts=dict(Counter(_extract_action(pair.chosen) for pair in pairs)),
            rejected_action_counts=dict(Counter(_extract_action(pair.rejected) for pair in pairs)),
            confidence_min=min(confidences) if confidences else None,
            confidence_max=max(confidences) if confidences else None,
            confidence_avg=(sum(confidences) / len(confidences)) if confidences else None,
        )


def _extract_action(candidate_text: str) -> str:
    try:
        data = json.loads(candidate_text)
    except json.JSONDecodeError:
        return "unknown"
    action = data.get("action")
    return action if isinstance(action, str) else "unknown"
