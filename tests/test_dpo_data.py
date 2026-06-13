from __future__ import annotations

import json

from rpl.pref_data.dpo_data import build_dpo_prompt, export_trl_dpo_jsonl, to_trl_dpo_record


def test_to_trl_dpo_record_converts_pair() -> None:
    record = {
        "prompt": "[Error]: division_by_zero: division by zero",
        "chosen": '{"action":"avoid_zero_division","tool_name":"math_calc","tool_params":{"expression":"1/1"}}',
        "rejected": '{"action":"retry_same_tool","tool_name":"math_calc","tool_params":{"expression":"1/0"}}',
    }

    converted = to_trl_dpo_record(record)

    assert "prompt" in converted
    assert "chosen" in converted
    assert "rejected" in converted
    assert "division_by_zero" in converted["prompt"]
    assert "avoid_zero_division" in converted["chosen"]


def test_export_trl_dpo_jsonl(tmp_path) -> None:
    output = tmp_path / "train.jsonl"
    count = export_trl_dpo_jsonl(
        [
            {
                "prompt": build_dpo_prompt("ctx"),
                "chosen": json.dumps({"action": "repair"}),
                "rejected": json.dumps({"action": "give_up"}),
            }
        ],
        output,
    )

    assert count == 1
    assert output.read_text(encoding="utf-8").strip()
