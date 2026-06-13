from __future__ import annotations

from rpl.recovery.types import Candidate


class CandidateDedup:
    def deduplicate(self, candidates: list[Candidate]) -> list[Candidate]:
        seen: set[tuple[str | None, str]] = set()
        unique: list[Candidate] = []
        for candidate in candidates:
            key = (candidate.tool_name, candidate.raw_text.strip().lower())
            if key in seen:
                continue
            seen.add(key)
            unique.append(candidate)
        return unique
