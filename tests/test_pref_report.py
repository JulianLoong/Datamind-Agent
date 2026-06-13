from __future__ import annotations

from rpl.pref_data.report import PreferenceDataReporter
from rpl.pref_data.types import PreferencePair


def test_preference_data_reporter_counts_sources_and_actions() -> None:
    pairs = [
        PreferencePair(
            prompt="p",
            chosen='{"action":"repair_json_payload"}',
            rejected='{"action":"give_up"}',
            source="heuristic",
            confidence=0.65,
            metadata={},
        ),
        PreferencePair(
            prompt="p",
            chosen='{"action":"avoid_zero_division"}',
            rejected='{"action":"retry_same_tool"}',
            source="outcome",
            confidence=0.9,
            metadata={},
        ),
    ]

    report = PreferenceDataReporter().build(pairs)

    assert report.total_pairs == 2
    assert report.source_counts == {"heuristic": 1, "outcome": 1}
    assert report.chosen_action_counts["repair_json_payload"] == 1
    assert report.rejected_action_counts["give_up"] == 1
