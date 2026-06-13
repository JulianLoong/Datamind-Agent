from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SYSTEM_PROMPT = (
    "You are an agent recovery preference model. Given a tool-call failure context, "
    "prefer the recovery plan that is more likely to fix the failure with bounded cost."
)


def load_preference_jsonl(path: str | Path) -> list[dict[str, Any]]:
    input_path = Path(path)
    if not input_path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in input_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if isinstance(value, dict):
            records.append(value)
    return records


def to_trl_dpo_record(record: dict[str, Any]) -> dict[str, str]:
    prompt = str(record.get("prompt", ""))
    chosen = normalize_recovery_text(str(record.get("chosen", "")))
    rejected = normalize_recovery_text(str(record.get("rejected", "")))
    return {
        "prompt": build_dpo_prompt(prompt),
        "chosen": chosen,
        "rejected": rejected,
    }


def build_dpo_prompt(error_context: str) -> str:
    return (
        f"{SYSTEM_PROMPT}\n\n"
        "[Error Context]\n"
        f"{error_context}\n\n"
        "[Instruction]\n"
        "Write the best recovery plan as JSON with reasoning, action, tool_name, and tool_params."
    )


def normalize_recovery_text(text: str) -> str:
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return text.strip()
    if not isinstance(value, dict):
        return text.strip()
    return json.dumps(
        {
            "reasoning": value.get("reasoning", ""),
            "action": value.get("action", ""),
            "tool_name": value.get("tool_name"),
            "tool_params": value.get("tool_params"),
        },
        ensure_ascii=False,
    )


def export_trl_dpo_jsonl(records: list[dict[str, Any]], path: str | Path) -> int:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    converted = [
        to_trl_dpo_record(record)
        for record in records
        if isinstance(record.get("prompt"), str)
        and isinstance(record.get("chosen"), str)
        and isinstance(record.get("rejected"), str)
    ]
    with output.open("w", encoding="utf-8") as f:
        for record in converted:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return len(converted)
