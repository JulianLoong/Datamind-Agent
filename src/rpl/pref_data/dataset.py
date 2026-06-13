from __future__ import annotations

import json
from pathlib import Path

from rpl.pref_data.types import PreferencePair


class DatasetExporter:
    def export_jsonl(self, pairs: list[PreferencePair], path: str | Path) -> int:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as f:
            for pair in pairs:
                f.write(json.dumps(pair.to_dpo_record(), ensure_ascii=False) + "\n")
        return len(pairs)

    def split_train_val(
        self,
        pairs: list[PreferencePair],
        *,
        val_ratio: float = 0.2,
    ) -> tuple[list[PreferencePair], list[PreferencePair]]:
        if not pairs:
            return [], []
        val_size = max(1, int(len(pairs) * val_ratio)) if len(pairs) > 1 else 0
        return pairs[val_size:], pairs[:val_size]
