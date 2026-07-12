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
recovery preference data and evaluated against first-candidate, random, lightweight, and
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
  --baselines first random mock_pm lightweight_pm \
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

The older `data/pm_checkpoints/dpo_pm` checkpoint is an early recovery-bench-lite artifact. The
current thesis-facing checkpoint is `data/pm_checkpoints/dpo_pm_outcomes`, trained from
outcome-ranked recovery candidates and evaluated on both `recovery_bench_generated` and
RecoveryGym; see `DPO_PM主线实验计划.md` for the current mainline commands.

Current mainline status as of 2026-07-05:

- Branch: `dpo-pm-mainline` tracking `origin/codex/dpo-pm-mainline`.
- Outcome-ranked data was collected with `scripts/collect_candidate_outcomes.py` on
  `recovery_bench_generated` train split: `960` preference pairs, split into
  `768 train / 192 val` under `data/pref_pairs_outcomes`.
- `DPO_PM` was trained from the outcome-ranked pairs with
  `Qwen/Qwen2.5-0.5B-Instruct`, QLoRA 4-bit loading, bf16 precision, and gradient
  checkpointing. The saved adapter is `data/pm_checkpoints/dpo_pm_outcomes`, and
  the training log is `data/logs/dpo_pm_outcomes_train_bf16.log`.
- The generated benchmark evaluation result is checked in as
  `data/eval/dpo_pm_outcomes_generated.json` and `.md`.
- The current selector label for multi-round comparisons is `dpo_pm_r3`, which uses a
  three-retry recovery budget.
- On `recovery_bench_generated` with splits `test_unseen clean`, `dpo_pm_r3` reached
  `success_rate=1.000` and `recovery_success_rate=1.000`.
- On the full controlled RecoveryGym benchmark, `dpo_pm_r3` reached
  `success_rate=0.517` and `recovery_success_rate=0.462`, with average recovery
  attempts of `1.310`, average tool calls of `2.310`, and average recovery tokens
  of `653.871`.
  RecoveryGym should be presented as a supplemental generalization and failure-analysis
  result, not as open-world real-LLM evidence.

The RTX 5060 local environment required CUDA 12.8 PyTorch and `--bf16` for stable DPO training.
The original `--fp16` run failed during AMP gradient unscale with bf16 gradients.

Recommended first demo/training target:

- RTX 5060 8GB: `Qwen/Qwen2.5-0.5B-Instruct`
- RTX 4090 24GB: `Qwen/Qwen2.5-1.5B-Instruct`

On the CUDA machine, train or refresh the current thesis-facing checkpoint from
`data/pref_pairs_outcomes`:

```bash
pip install torch transformers datasets accelerate peft trl bitsandbytes
PYTHONPATH=src python3 scripts/train_dpo_pm.py \
  --base-model Qwen/Qwen2.5-0.5B-Instruct \
  --train data/pref_pairs_outcomes/train.jsonl \
  --val data/pref_pairs_outcomes/val.jsonl \
  --work-dir data/dpo_outcomes \
  --out data/pm_checkpoints/dpo_pm_outcomes \
  --use-4bit \
  --bf16 \
  --gradient-checkpointing
PYTHONPATH=src python3 scripts/run_eval.py \
  --benchmark recovery_bench_generated \
  --baselines first random_r3 dpo_pm_r3 \
  --pm-paths dpo_pm_r3=Qwen/Qwen2.5-0.5B-Instruct::data/pm_checkpoints/dpo_pm_outcomes \
  --splits test_unseen clean \
  --repeats 1 \
  --out data/eval/dpo_pm_outcomes_generated.json
```

The DPO_PM selector scores each recovery candidate by the DPO adapter's conditional log
probability for the candidate text under the error-context prompt. Use `dpo_pm_r3` in reports for
multi-round evaluation with a three-retry budget.

`run_eval.py` supports `--pm-paths baseline=path`, so different PM baselines can use different
checkpoints in one report.

## Real LLM candidate evaluation

To validate recovery ranking under a non-deterministic candidate generator, point the runtime at an
OpenAI-compatible chat completions API. The current selector protocol is `llm_greedy`,
`llm_self_pick`, and `dpo_pm`, all with one recovery attempt. The generated main benchmark defaults
to the `test_unseen` and `clean` splits; RecoveryGym defaults to all splits.

```powershell
$env:DEEPSEEK_API_KEY="..."
.\scripts\run_real_llm_dpo_pm_eval.ps1 `
  -LlmModel deepseek-chat `
  -LlmBaseUrl https://api.deepseek.com
```

That command runs the 110-task main controlled evaluation and writes
`data/eval/real_llm_main.json`. Run RecoveryGym with a separate cache and output:

```powershell
.\scripts\run_real_llm_dpo_pm_eval.ps1 `
  -Benchmark recovery_gym `
  -LlmModel deepseek-chat `
  -LlmBaseUrl https://api.deepseek.com `
  -LlmCache data/eval/real_llm_recovery_gym_candidates_v2.jsonl `
  -Out data/eval/real_llm_recovery_gym.json
```

The wrapper pins execution to `.venv\Scripts\python.exe`, verifies the DPO dependencies, and reuses
one candidate cache across selectors. Malformed real-LLM candidate responses stop the evaluation by
default. `run_real_llm_eval.py --allow-candidate-fallback` is available only for diagnostic runs;
do not use it for reported results. New candidate responses use
`{"candidates": [...]}` while legacy array-only cache entries remain readable.

For GLM 5.1, the real path should disable thinking and request JSON output. The current Zhipu
provider does this automatically.

A small DeepSeek real-LLM DPO_PM smoke result is checked in as
`data/eval/real_llm_deepseek_dpo_pm_r3_smoke.json` and `.md`. It is a historical
`recovery_bench_lite` path-validation artifact with `max_tasks=8`; its retired comparison baseline
is no longer available in the current evaluation code. The result should not be used as evidence for
the current evaluation design because the sample size is very small.

New evaluation records include a `recovery_trace` field with generated candidates, selected index,
PM scores, and initial/final tool results. Use this for future real-LLM failure analysis instead of
inferring candidate quality from aggregate metrics alone. Training DPO_PM directly from real-LLM
trace data is future work rather than part of the current mainline result.

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
  --baselines first random lightweight_pm \
  --pm-path data/pm_checkpoints/lightweight_pm_generated.json \
  --repeats 1 \
  --out data/eval/generated_lightweight.json
```

The default generated train split currently yields 640 deduplicated preference pairs
(`512 train / 128 val`) from 320 recovery tasks.

The generated 640-pair dataset remains useful for historical comparison or a fallback smoke run.
For the current thesis-facing result, prefer the outcome-ranked checkpoint above. If you do run a
generated-data DPO fallback, keep it separate from `data/pm_checkpoints/dpo_pm_outcomes`:

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
  --baselines first random_r3 dpo_pm_r3 \
  --pm-paths dpo_pm_r3=Qwen/Qwen2.5-0.5B-Instruct::data/pm_checkpoints/dpo_pm_generated \
  --splits test_unseen clean \
  --repeats 1 \
  --out data/eval/generated_dpo_pm_fallback.json
```
