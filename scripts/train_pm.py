from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from rpl.pref_model import train_lightweight_pref_model


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    input_path = Path(path)
    if not input_path.exists():
        return records
    for line in input_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if isinstance(value, dict):
            records.append(value)
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the lightweight preference model.")
    parser.add_argument("--train", default="data/pref_pairs/train.jsonl", help="Training JSONL")
    parser.add_argument("--val", default="data/pref_pairs/val.jsonl", help="Optional validation JSONL")
    parser.add_argument("--out", default="data/pm_checkpoints/lightweight_pm.json", help="Output model path")
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--learning-rate", type=float, default=0.25)
    args = parser.parse_args()

    records = load_jsonl(args.train) + load_jsonl(args.val)
    model = train_lightweight_pref_model(
        records,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
    )
    model.save(args.out)
    print(f"trained records={len(records)} updates={model.metadata.get('updates')} out={args.out}")


if __name__ == "__main__":
    main()
