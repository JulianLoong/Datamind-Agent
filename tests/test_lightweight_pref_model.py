from __future__ import annotations

from rpl.pref_model import LightweightPrefModel, train_lightweight_pref_model
from rpl.recovery.types import Candidate, ErrorContext


def test_lightweight_pref_model_trains_and_loads(tmp_path) -> None:
    prompt = "\n".join(
        [
            "[Task Goal]: calculate",
            "[Current Step]: math",
            "[Failed Tool]: math_calc({'expression': '1/0'})",
            "[Error]: division_by_zero: division by zero",
            "[Recent History]:",
            "  - None",
        ]
    )
    records = [
        {
            "prompt": prompt,
            "chosen": '{"action":"avoid_zero_division","tool_name":"math_calc","tool_params":{"expression":"1/1"}}',
            "rejected": '{"action":"retry_same_tool","tool_name":"math_calc","tool_params":{"expression":"1/0"}}',
            "confidence": 0.9,
        }
    ]

    model = train_lightweight_pref_model(records, epochs=4)
    path = tmp_path / "pm.json"
    model.save(path)
    loaded = LightweightPrefModel.load(path)
    ctx = ErrorContext(
        task_goal="calculate",
        step_description="math",
        tool_name="math_calc",
        tool_params={"expression": "1/0"},
        error_type="division_by_zero",
        error_message="division by zero",
        recent_history=[],
    )
    good = Candidate("fix", "avoid_zero_division", "math_calc", {"expression": "1/1"}, "good")
    bad = Candidate("retry", "retry_same_tool", "math_calc", {"expression": "1/0"}, "bad")

    assert loaded.score(ctx, good) > loaded.score(ctx, bad)
