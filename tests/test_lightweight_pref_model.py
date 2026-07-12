from __future__ import annotations

from rpl.pref_model import LightweightPrefModel, train_lightweight_pref_model
from rpl.recovery.types import Candidate, ErrorContext


def test_lightweight_pref_model_trains_and_loads(tmp_path) -> None:
    prompt = "\n".join(
        [
            "[Task Goal]: parse json",
            "[Current Step]: json",
            "[Failed Tool]: json_parse({'text': '{\"a\":', 'field': 'a'})",
            "[Error]: invalid_json: Expecting value",
            "[Recent History]:",
            "  - None",
        ]
    )
    records = [
        {
            "prompt": prompt,
            "chosen": '{"action":"repair_json_payload","tool_name":"json_parse","tool_params":{"text":"{\\"a\\": null}","field":"a"}}',
            "rejected": '{"action":"retry_same_tool","tool_name":"json_parse","tool_params":{"text":"{\\"a\\":","field":"a"}}',
            "confidence": 0.9,
        }
    ]

    model = train_lightweight_pref_model(records, epochs=4)
    path = tmp_path / "pm.json"
    model.save(path)
    loaded = LightweightPrefModel.load(path)
    ctx = ErrorContext(
        task_goal="parse json",
        step_description="json",
        tool_name="json_parse",
        tool_params={"text": '{"a":', "field": "a"},
        error_type="invalid_json",
        error_message="Expecting value",
        recent_history=[],
    )
    good = Candidate("repair", "repair_json_payload", "json_parse", {"text": '{"a": null}', "field": "a"}, "good")
    bad = Candidate("retry", "retry_same_tool", "json_parse", {"text": '{"a":', "field": "a"}, "bad")

    assert loaded.score(ctx, good) > loaded.score(ctx, bad)
