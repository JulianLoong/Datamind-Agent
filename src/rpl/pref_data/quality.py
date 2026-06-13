from __future__ import annotations

from rpl.pref_data.types import PreferencePair


class DataQualityFilter:
    def filter(
        self,
        pairs: list[PreferencePair],
        *,
        min_confidence: float = 0.6,
    ) -> list[PreferencePair]:
        return self.deduplicate([pair for pair in pairs if pair.confidence >= min_confidence])

    def deduplicate(self, pairs: list[PreferencePair]) -> list[PreferencePair]:
        seen: set[tuple[str, str, str]] = set()
        unique: list[PreferencePair] = []
        for pair in pairs:
            key = (pair.prompt, pair.chosen, pair.rejected)
            if key in seen:
                continue
            seen.add(key)
            unique.append(pair)
        return unique
