from __future__ import annotations

import argparse

from rpl.pref_data import export_trl_dpo_jsonl, load_preference_jsonl


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert preference pairs to TRL DPO JSONL.")
    parser.add_argument("--train", default="data/pref_pairs/train.jsonl")
    parser.add_argument("--val", default="data/pref_pairs/val.jsonl")
    parser.add_argument("--out-train", default="data/dpo/train.jsonl")
    parser.add_argument("--out-val", default="data/dpo/val.jsonl")
    args = parser.parse_args()

    train_count = export_trl_dpo_jsonl(load_preference_jsonl(args.train), args.out_train)
    val_count = export_trl_dpo_jsonl(load_preference_jsonl(args.val), args.out_val)
    print(f"exported dpo train={train_count} val={val_count}")


if __name__ == "__main__":
    main()
