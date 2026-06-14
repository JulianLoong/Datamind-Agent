# DataMindAgent RPL

Recovery Preference Learning (RPL) prototype for agent tool-call failure recovery.

The current implementation is a controlled research prototype for building a DPO-trained
Preference Model (`DPO_PM`) for recovery candidate ranking. The codebase already includes:

- Built-in deterministic tools with configurable error rates.
- Tool registry with parameter validation.
- SQLite trajectory storage.
- Static/rule-based agent execution loop with multi-round recovery.
- Recovery pipeline with candidate generation, validation, de-duplication, and selector injection.
- Preference-pair extraction, outcome-ranked multi-candidate data collection, and report generation.
- Lightweight PM, memory-prior selector, and DPO_PM training/evaluation paths.
- Controlled synthetic and RecoveryGym benchmark evaluation scripts.

The project intentionally does not use ToolBench or a standalone error injection module in the
current phase. Built-in tools keep the early recovery loop reproducible; more realistic tools can be
added later through the same `BaseTool` and `ToolRegistry` interfaces.

## Model roles

`DPO_PM` is the target model for the thesis-facing system. It should be trained from executable
recovery preference data and evaluated against no-recovery, fixed-retry, random, lightweight, and
memory-augmented baselines.

`lightweight_pm` is a dependency-free pairwise ranker. It is useful as a fast local sanity check and
as a baseline for DPO_PM, but it is not the final target.

`memory_lightweight_pm` adds retrieval-based experience priors on top of `lightweight_pm`. It is an
experience-memory ablation, not a replacement for DPO_PM. In the current RecoveryGym results it does
not yet improve over `lightweight_pm`.

`mock_pm` is a rule-based oracle-like selector used only for controlled debugging and cold-start data
collection. It should not be presented as the learned method.

## Lightweight baseline loop

Use this loop to check the data and evaluation pipeline quickly before spending GPU time on DPO:

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

This path proves that trajectory-derived preference pairs can train a working selector. It should be
reported as a baseline or implementation sanity check, not as the final DPO_PM result.

## DPO_PM target path

The repository includes a LoRA DPO training and inference path. DPO dependencies are imported only by
the DPO scripts/model, so the lightweight loop still runs without PyTorch.

The existing `data/pm_checkpoints/dpo_pm` checkpoint is an early recovery-bench-lite artifact. The
next DPO_PM milestone is to retrain on the newer generated/outcome-ranked data and evaluate on
`recovery_bench_generated`; see `DPO_PM主线实验计划.md` for the current mainline commands.

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
  --baselines no_recovery first random dpo_pm \
  --pm-paths dpo_pm=Qwen/Qwen2.5-0.5B-Instruct::data/pm_checkpoints/dpo_pm \
  --repeats 5 \
  --out data/eval/dpo_pm.json
```

The `dpo_pm` selector scores each recovery candidate by the DPO adapter's conditional log
probability for the candidate text under the error-context prompt.

`run_eval.py` supports `--pm-paths baseline=path`, so different PM baselines can use different
checkpoints in one report.

## Real LLM candidate evaluation

To validate recovery ranking under a non-deterministic candidate generator, point the runtime at an
OpenAI-compatible chat completions API. Zhipu GLM 5.1 is supported through the same path. This is
the P5 entry point for comparing PM and memory behavior when candidate generation is no longer
deterministic:

```bash
export ZHIPU_API_KEY=...
PYTHONPATH=src python3 scripts/run_real_llm_eval.py \
  --benchmark recovery_gym \
  --llm-provider glm \
  --llm-model glm-5.1 \
  --llm-base-url https://open.bigmodel.cn/api/paas/v4 \
  --memory-db data/trajectories.db \
  --repeats 1 \
  --out data/eval/real_llm_recovery.json
```

The same `PMSelector` and `MemoryPriorSelector` paths are used; only the candidate generator
changes. For fair final comparisons, cache or otherwise reuse the same generated candidates across
selectors.

For GLM 5.1, the real path should disable thinking and request JSON output. The current Zhipu
provider does this automatically.

## Generated benchmark data

For thesis-scale experiments, use the generated benchmark or RecoveryGym instead of repeatedly
running the three toy cold-start tasks. The generated benchmark creates parameterized structured
tasks across four failure types:
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
  --baselines no_recovery first random dpo_pm \
  --pm-paths dpo_pm=Qwen/Qwen2.5-0.5B-Instruct::data/pm_checkpoints/dpo_pm_generated \
  --repeats 1 \
  --out data/eval/generated_dpo_pm.json
```
