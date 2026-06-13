from __future__ import annotations

from typing import Any

from rpl.pref_data.types import PreferencePair, candidate_to_text, error_context_to_prompt
from rpl.trajectory.store import TrajectoryStore, from_json


class PreferenceExtractor:
    """Build initial DPO-style preference pairs from recovery attempts.

    M2 scope uses two weak but useful signals:
    - outcome: selected candidate succeeded, so prefer it over non-selected alternatives.
    - heuristic: among alternatives, prefer non-give-up/non-retry actions over give_up/retry_same_tool.
    """

    def extract(self, store: TrajectoryStore, *, limit: int = 1000) -> list[PreferencePair]:
        pairs: list[PreferencePair] = []
        rows = store.query_recovery_attempts_with_context(limit=limit)
        for row in rows:
            pairs.extend(self._extract_from_row(row))
        return pairs

    def _extract_from_row(self, row: dict[str, Any]) -> list[PreferencePair]:
        error_context = from_json(row.get("error_context_json"), {})
        candidates = from_json(row.get("candidates_json"), [])
        chosen_candidate = from_json(row.get("chosen_candidate_json"), None)
        final_result = from_json(row.get("final_result_json"), {})
        if not isinstance(error_context, dict) or not isinstance(candidates, list):
            return []
        if not isinstance(chosen_candidate, dict):
            return []

        prompt = error_context_to_prompt(error_context)
        chosen_index = int(row.get("chosen_index", -1))
        pairs: list[PreferencePair] = []
        final_success = isinstance(final_result, dict) and final_result.get("success") is True

        if final_success:
            for idx, candidate in enumerate(candidates):
                if idx == chosen_index or not isinstance(candidate, dict):
                    continue
                pairs.append(
                    PreferencePair(
                        prompt=prompt,
                        chosen=candidate_to_text(chosen_candidate),
                        rejected=candidate_to_text(candidate),
                        source="outcome",
                        confidence=0.9,
                        metadata={
                            "task_id": row.get("task_id"),
                            "step_id": row.get("step_id"),
                            "recovery_id": row.get("id"),
                            "chosen_index": chosen_index,
                            "rejected_index": idx,
                        },
                    )
                )

        pairs.extend(self._heuristic_pairs(prompt, row, candidates))
        return pairs

    def _heuristic_pairs(
        self,
        prompt: str,
        row: dict[str, Any],
        candidates: list[Any],
    ) -> list[PreferencePair]:
        good = [c for c in candidates if isinstance(c, dict) and self._heuristic_score(c) > 0]
        bad = [c for c in candidates if isinstance(c, dict) and self._heuristic_score(c) < 0]
        pairs: list[PreferencePair] = []
        for good_candidate in good[:2]:
            for bad_candidate in bad[:2]:
                pairs.append(
                    PreferencePair(
                        prompt=prompt,
                        chosen=candidate_to_text(good_candidate),
                        rejected=candidate_to_text(bad_candidate),
                        source="heuristic",
                        confidence=0.65,
                        metadata={
                            "task_id": row.get("task_id"),
                            "step_id": row.get("step_id"),
                            "recovery_id": row.get("id"),
                        },
                    )
                )
        return pairs

    @staticmethod
    def _heuristic_score(candidate: dict[str, Any]) -> int:
        action = candidate.get("action")
        if action == "give_up":
            return -2
        if action == "retry_same_tool":
            return -1
        if candidate.get("tool_name") is not None and candidate.get("tool_params") is not None:
            return 1
        return 0
