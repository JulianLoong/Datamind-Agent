from __future__ import annotations

import argparse
import json
from pathlib import Path

from rpl.pref_data import DataQualityFilter, DatasetExporter, PreferenceDataReporter, PreferenceExtractor
from rpl.trajectory.store import TrajectoryStore


def main() -> None:
    parser = argparse.ArgumentParser(description="Build DPO preference data from trajectories.")
    parser.add_argument("--db", default="data/trajectories.db", help="SQLite trajectory DB path")
    parser.add_argument("--out-dir", default="data/pref_pairs", help="Output directory")
    parser.add_argument("--limit", type=int, default=1000, help="Max recovery attempts to scan")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    store = TrajectoryStore(args.db)
    pairs = PreferenceExtractor().extract(store, limit=args.limit)
    pairs = DataQualityFilter().filter(pairs, min_confidence=0.6)
    report = PreferenceDataReporter().build(pairs)

    exporter = DatasetExporter()
    train, val = exporter.split_train_val(pairs)
    train_count = exporter.export_jsonl(train, out_dir / "train.jsonl")
    val_count = exporter.export_jsonl(val, out_dir / "val.jsonl")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.json").write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"exported train={train_count} val={val_count}")
    print(report.to_markdown())


if __name__ == "__main__":
    main()
