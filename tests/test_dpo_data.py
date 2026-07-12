from __future__ import annotations

import json

from rpl.pref_data.dpo_data import build_dpo_prompt, export_trl_dpo_jsonl, to_trl_dpo_record


def test_to_trl_dpo_record_converts_pair() -> None:
    record = {
        "prompt": "[Error]: invalid_json: Expecting value",
        "chosen": '{"action":"repair_json_payload","tool_name":"json_parse","tool_params":{"text":"{}"}}',
        "rejected": '{"action":"retry_same_tool","tool_name":"json_parse","tool_params":{"text":"{"}}',
    }

    converted = to_trl_dpo_record(record)

    assert "prompt" in converted
    assert "chosen" in converted
    assert "rejected" in converted
    assert "invalid_json" in converted["prompt"]
    assert "repair_json_payload" in converted["chosen"]


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
