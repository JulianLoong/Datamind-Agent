# DataMindAgent RPL

Recovery Preference Learning (RPL) prototype for agent tool-call failure recovery.

This first implementation focuses on the M1 + partial M2 scope:

- Built-in deterministic tools with configurable error rates.
- Tool registry with parameter validation.
- SQLite trajectory storage.
- Static/rule-based agent execution loop.
- Recovery pipeline skeleton with fake candidate generation and default selection.
- Pytest coverage for the runnable loop.

The current version intentionally does not include ToolBench, a standalone error injection module, REST API, MCP integration, or real Preference Model training.

## Thesis experiment loop

The current prototype includes a lightweight, reproducible experiment loop for the thesis draft:

```bash
PYTHONPATH=src python3 scripts/cold_start.py --selector mock_pm --repeats 10 --export
PYTHONPATH=src python3 scripts/train_pm.py \
  --train data/pref_pairs/train.jsonl \
  --val data/pref_pairs/val.jsonl \
  --out data/pm_checkpoints/lightweight_pm.json
PYTHONPATH=src python3 scripts/run_eval.py \
  --baselines no_recovery first random mock_pm lightweight_pm \
  --pm-path data/pm_checkpoints/lightweight_pm.json \
  --repeats 5 \
  --out data/eval/recovery_bench_lite.json
```

Outputs:

- `data/pref_pairs/train.jsonl` and `data/pref_pairs/val.jsonl`: DPO-style preference pairs.
- `data/pm_checkpoints/lightweight_pm.json`: dependency-free pairwise preference ranker.
- `data/eval/recovery_bench_lite.json` and `.md`: baseline comparison report.

`mock_pm` is used only to collect clean cold-start outcome data. The thesis-facing learned system is
`lightweight_pm`, which trains from exported trajectory preference pairs and is evaluated through
the same `PMSelector` interface.

## Optional DPO PM demo

The repository also includes an optional DPO path for the defense-stage experiment. DPO dependencies
are imported only by the DPO scripts/model, so the lightweight loop still runs without PyTorch.

Recommended first demo:

- RTX 5060 8GB: `Qwen/Qwen2.5-0.5B-Instruct`
- RTX 4090 24GB: `Qwen/Qwen2.5-1.5B-Instruct`

On the CUDA machine:

```bash
pip install torch transformers datasets accelerate peft trl bitsandbytes
PYTHONPATH=src python3 scripts/export_dpo_data.py
PYTHONPATH=src python3 scripts/train_dpo_pm.py \
  --base-model Qwen/Qwen2.5-0.5B-Instruct \
  --train data/pref_pairs/train.jsonl \
  --val data/pref_pairs/val.jsonl \
  --out data/pm_checkpoints/dpo_pm \
  --use-4bit \
  --fp16 \
  --gradient-checkpointing
PYTHONPATH=src python3 scripts/run_eval.py \
  --baselines no_recovery first random lightweight_pm dpo_pm \
  --pm-path Qwen/Qwen2.5-0.5B-Instruct::data/pm_checkpoints/dpo_pm \
  --repeats 5 \
  --out data/eval/dpo_pm.json
```

The `dpo_pm` selector scores each recovery candidate by the DPO adapter's conditional log
probability for the candidate text under the error-context prompt.

## Generated benchmark data

For thesis-scale experiments, use the generated benchmark instead of repeatedly running the three
toy cold-start tasks. It creates parameterized structured tasks across four failure types:
division-by-zero, HTTP not-found, invalid JSON, and missing JSON field.

```bash
PYTHONPATH=src python3 scripts/collect_benchmark_data.py \
  --benchmark recovery_bench_generated \
  --splits train \
  --db data/generated_trajectories.db \
  --out-dir data/pref_pairs_generated \
  --limit 20000

PYTHONPATH=src python3 scripts/train_pm.py \
  --train data/pref_pairs_generated/train.jsonl \
  --val data/pref_pairs_generated/val.jsonl \
  --out data/pm_checkpoints/lightweight_pm_generated.json

PYTHONPATH=src python3 scripts/export_dpo_data.py \
  --train data/pref_pairs_generated/train.jsonl \
  --val data/pref_pairs_generated/val.jsonl \
  --out-train data/dpo_generated/train.jsonl \
  --out-val data/dpo_generated/val.jsonl

PYTHONPATH=src python3 scripts/run_eval.py \
  --benchmark recovery_bench_generated \
  --baselines no_recovery first random lightweight_pm \
  --pm-path data/pm_checkpoints/lightweight_pm_generated.json \
  --repeats 1 \
  --out data/eval/generated_lightweight.json
```

The default generated train split currently yields 640 deduplicated preference pairs
(`512 train / 128 val`) from 320 recovery tasks.

To train DPO on the generated 640-pair dataset:

```bash
PYTHONPATH=src python3 scripts/train_dpo_pm.py \
  --base-model Qwen/Qwen2.5-0.5B-Instruct \
  --train data/pref_pairs_generated/train.jsonl \
  --val data/pref_pairs_generated/val.jsonl \
  --work-dir data/dpo_generated \
  --out data/pm_checkpoints/dpo_pm_generated \
  --use-4bit \
  --fp16 \
  --gradient-checkpointing

PYTHONPATH=src python3 scripts/run_eval.py \
  --benchmark recovery_bench_generated \
  --baselines no_recovery first random lightweight_pm dpo_pm \
  --pm-path Qwen/Qwen2.5-0.5B-Instruct::data/pm_checkpoints/dpo_pm_generated \
  --repeats 1 \
  --out data/eval/generated_dpo_pm.json
```
