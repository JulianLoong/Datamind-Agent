# DPO_PM 主线实验计划

更新时间：2026-06-14

## 1. 目标

当前阶段主攻 `DPO_PM`，不优先做完整 memory 消融。第一版目标是产出导师能初步认可的主实验：

```text
在一定规模的可执行评测集上，DPO_PM 相比没有 PM 排序的恢复策略更好，
至少体现在 recovery_success_rate、avg_recovery_attempts 或 avg_tool_calls 上。
```

主 benchmark 使用 `recovery_bench_generated`。`RecoveryGym` 暂作为补充泛化压力测试和失败分析，不作为第一版唯一主结论。

## 2. 当前状态

- 旧 `data/pm_checkpoints/dpo_pm` 只对应 `recovery_bench_lite` 早期 demo。
- 当前仓库已有 `data/pref_pairs_generated`：`512 train / 128 val`。
- 已重新采集 `data/pref_pairs_outcomes`：`768 train / 192 val`，共 `960` 条 `outcome_multi_candidate` 偏好对。
- 已导出 `data/dpo_outcomes`：`768 train / 192 val`，用于 TRL DPO 训练。
- 当前本机环境缺少 `torch`、`transformers`、`datasets`、`peft`、`trl`、`bitsandbytes`，不能直接训练 DPO_PM；训练需要在 CUDA/4090 环境执行。
- `run_eval.py` 已支持 `--pm-paths baseline=path`，可在同一张表里给不同 PM baseline 配不同 checkpoint。

## 3. 推荐执行顺序

### Step 1：采集 outcome-ranked 偏好数据

```bash
PYTHONPATH=src python3 scripts/collect_candidate_outcomes.py \
  --benchmark recovery_bench_generated \
  --splits train \
  --candidate-count 3 \
  --out-dir data/pref_pairs_outcomes
```

验收：

- `data/pref_pairs_outcomes/train.jsonl` 非空。
- `data/pref_pairs_outcomes/val.jsonl` 非空。
- `data/pref_pairs_outcomes/outcome_report.json` 中 `source_counts` 包含 `outcome_multi_candidate`。
- 总 pair 数建议不少于 500；不足则使用 `data/pref_pairs_generated` 作为补充或 fallback。

### Step 2：训练 DPO_PM

首版使用 `Qwen/Qwen2.5-0.5B-Instruct`，输出目录不要覆盖旧 checkpoint。

```bash
PYTHONPATH=src python3 scripts/train_dpo_pm.py \
  --base-model Qwen/Qwen2.5-0.5B-Instruct \
  --train data/pref_pairs_outcomes/train.jsonl \
  --val data/pref_pairs_outcomes/val.jsonl \
  --work-dir data/dpo_outcomes \
  --out data/pm_checkpoints/dpo_pm_outcomes \
  --use-4bit \
  --fp16 \
  --gradient-checkpointing
```

如果 outcome-ranked pair 数不足 500，改用 generated 数据先跑通：

```bash
PYTHONPATH=src python3 scripts/train_dpo_pm.py \
  --base-model Qwen/Qwen2.5-0.5B-Instruct \
  --train data/pref_pairs_generated/train.jsonl \
  --val data/pref_pairs_generated/val.jsonl \
  --work-dir data/dpo_generated_v2 \
  --out data/pm_checkpoints/dpo_pm_generated_v2 \
  --use-4bit \
  --fp16 \
  --gradient-checkpointing
```

### Step 3：sanity check

```bash
PYTHONPATH=src python3 scripts/run_eval.py \
  --benchmark recovery_bench_lite \
  --baselines no_recovery random fixed_retry dpo_pm \
  --pm-paths dpo_pm=Qwen/Qwen2.5-0.5B-Instruct::data/pm_checkpoints/dpo_pm_outcomes \
  --repeats 1 \
  --out data/eval/dpo_pm_outcomes_lite.json
```

### Step 4：主实验

```bash
PYTHONPATH=src python3 scripts/run_eval.py \
  --benchmark recovery_bench_generated \
  --baselines no_recovery random fixed_retry dpo_pm \
  --pm-paths dpo_pm=Qwen/Qwen2.5-0.5B-Instruct::data/pm_checkpoints/dpo_pm_outcomes \
  --splits test_unseen clean \
  --repeats 1 \
  --out data/eval/dpo_pm_outcomes_generated.json
```

主表关注：

- `recovery_success_rate`
- `avg_recovery_attempts_on_failure_tasks`
- `avg_tool_calls_on_failure_tasks`
- split-wise `test_unseen` / `clean`

### Step 5：补充 RecoveryGym

```bash
PYTHONPATH=src python3 scripts/run_recovery_gym_eval.py \
  --baselines no_recovery fixed_retry random dpo_pm \
  --pm-paths dpo_pm=Qwen/Qwen2.5-0.5B-Instruct::data/pm_checkpoints/dpo_pm_outcomes \
  --repeats 1 \
  --out data/eval/dpo_pm_outcomes_recovery_gym.json
```

RecoveryGym 只作为补充。若 DPO_PM 表现不佳，应重点分析候选覆盖、failure family 和数据分布，不直接否定主方法。

## 4. 初稿结果口径

按结果选择表述：

- 如果 DPO_PM 成功率最高：`DPO_PM 提高恢复成功率，并降低无效恢复尝试。`
- 如果 DPO_PM 与 fixed_retry 成功率相近但尝试更少：`DPO_PM 在保持恢复能力的同时减少恢复轮数和工具调用。`
- 如果 DPO_PM 只强于 random、不强于 fixed_retry：`DPO_PM 学到有效候选排序，但当前数据和候选覆盖还不足以全面超过规则策略。`

第一版不写 memory 消融为主结论。

## 5. Execution update: 2026-06-15

The mainline DPO_PM run has been completed on branch `dpo-pm-mainline`, which tracks
`origin/codex/dpo-pm-mainline`.

Completed items:

- Pulled the remote mainline branch from `origin/codex/dpo-pm-mainline`.
- Installed DPO dependencies in the local `pytorch` Conda environment.
- Upgraded PyTorch to `2.11.0+cu128` so the RTX 5060 (`sm_120`) can run CUDA kernels.
- Collected outcome-ranked preference data with:
  `scripts/collect_candidate_outcomes.py --benchmark recovery_bench_generated --splits train --candidate-count 3 --out-dir data/pref_pairs_outcomes`.
- Collection result: `960` total `outcome_multi_candidate` pairs, split into
  `768 train / 192 val`.
- Trained `DPO_PM` from `data/pref_pairs_outcomes` using
  `Qwen/Qwen2.5-0.5B-Instruct`, QLoRA 4-bit loading, bf16 precision, and gradient checkpointing.
- Saved the adapter and tokenizer under `data/pm_checkpoints/dpo_pm_outcomes`.
- Saved the training log under `data/logs/dpo_pm_outcomes_train_bf16.log`.
- Ran the generated benchmark evaluation and saved:
  `data/eval/dpo_pm_outcomes_generated.json`
  and `data/eval/dpo_pm_outcomes_generated.md`.
- Pushed the evaluation output, checkpoint directory, and training log to
  `origin/codex/dpo-pm-mainline`.

Important training note:

- The original fp16 command reached the first optimizer step but failed with
  `NotImplementedError: "_amp_foreach_non_finite_check_and_unscale_cuda" not implemented for 'BFloat16'`.
- Re-running the same training with `--bf16` completed successfully.
- Final training summary from the log: `train_runtime=1567`, `train_loss=0.00429`,
  `epoch=3`; final eval summary included `eval_loss=6.959e-06` and
  `eval_rewards/accuracies=1`.

Main generated benchmark result:

```text
benchmark: recovery_bench_generated
splits: test_unseen clean
repeats: 1
checkpoint: Qwen/Qwen2.5-0.5B-Instruct::data/pm_checkpoints/dpo_pm_outcomes
```

| baseline | success_rate | recovery_success_rate | avg_recovery_attempts | avg_tool_calls |
|---|---:|---:|---:|---:|
| no_recovery | 0.273 | 0.000 | 0.000 | 1.000 |
| random | 0.491 | 0.300 | 0.727 | 1.727 |
| fixed_retry | 1.000 | 1.000 | 1.455 | 2.455 |
| dpo_pm | 1.000 | 1.000 | 0.727 | 1.727 |

On failure tasks only, `dpo_pm` matched `fixed_retry` recovery success (`1.000`) while
using fewer recovery attempts (`1.0` vs `2.0`) and fewer tool calls (`2.0` vs `3.0`).
This supports the current first-version claim: DPO_PM can preserve recovery capability
while reducing invalid recovery rounds in the controlled synthetic setting.

Remaining work:

- Run a small real-LLM candidate smoke test with `dpo_pm`.
- Keep memory ablations separate from the first DPO_PM claim.

## 6. RecoveryGym update: 2026-07-03

The supplemental RecoveryGym DPO_PM evaluation has now been completed and checked in as:

- `data/eval/dpo_pm_outcomes_recovery_gym_smoke.json` and `.md`
- `data/eval/dpo_pm_outcomes_recovery_gym.json` and `.md`

Smoke setting:

```text
benchmark: recovery_gym
splits: seen_template_unseen_params
max_tasks: 16
repeats: 1
baselines: no_recovery random fixed_retry dpo_pm
```

Full RecoveryGym setting:

```text
benchmark: recovery_gym
task_count: 116
repeats: 1
baselines: no_recovery random fixed_retry dpo_pm
```

Full RecoveryGym result:

| baseline | success_rate | recovery_success_rate | avg_recovery_attempts | avg_tool_calls | avg_recovery_tokens |
|---|---:|---:|---:|---:|---:|
| no_recovery | 0.103 | 0.000 | 0.000 | 1.000 | 0.000 |
| random | 0.241 | 0.154 | 0.897 | 1.897 | 146.638 |
| fixed_retry | 0.517 | 0.462 | 1.724 | 2.724 | 278.259 |
| dpo_pm | 0.517 | 0.462 | 0.897 | 1.897 | 146.638 |

Paper-safe wording:

- RecoveryGym is a controlled synthetic generalization and failure-analysis benchmark.
- DPO_PM matches fixed-retry recovery success on this benchmark while using fewer recovery
  attempts, tool calls, and recovery tokens.
- The gains are concentrated in recoverable families covered by the current candidate generator:
  `semantic_param_error`, `malformed_input`, and `unavailable_resource`.
- Cases such as `schema_error`, `permission_error`, `file_not_found`, and `invalid_expression`
  remain unresolved because the current candidate generator often does not provide a successful
  executable repair. This should be described as a candidate-coverage limitation rather than a
  broad failure of preference ranking.

## 7. DeepSeek real-LLM smoke update: 2026-07-04

A small real-LLM DPO_PM smoke evaluation has now been completed and checked in as:

- `data/eval/real_llm_deepseek_dpo_pm_smoke.json`
- `data/eval/real_llm_deepseek_dpo_pm_smoke.md`

Setting:

```text
benchmark: recovery_bench_lite
max_tasks: 4
repeats: 1
candidate generator: DeepSeek through the OpenAI-compatible path
baselines: fixed_retry dpo_pm
```

Result:

| baseline | success_rate | recovery_success_rate | avg_recovery_attempts | avg_tool_calls | avg_recovery_tokens | avg_recovery_latency_ms |
|---|---:|---:|---:|---:|---:|---:|
| fixed_retry | 0.250 | 0.250 | 1.750 | 2.750 | 2966.000 | 49892.170 |
| dpo_pm | 0.250 | 0.250 | 1.000 | 2.000 | 1571.250 | 27095.702 |

Paper-safe wording:

- This is a real-LLM candidate-generation smoke test, not a main result.
- It verifies that the DPO_PM recovery pipeline can operate with non-deterministic candidates
  generated by an external LLM.
- The trend is consistent with the main controlled experiments: DPO_PM matches fixed-retry
  success while reducing recovery attempts, tool calls, token cost, and latency.
- Because the sample size is only four tasks and candidate sets are not cached across baselines,
  this result should not be used for a strong generalization claim.

Implementation note:

- Future eval reports now include `recovery_trace`, which records generated candidates, the chosen
  index, PM scores, and initial/final tool results. Use that field for candidate-level failure
  analysis after rerunning real-LLM evals.
- Real-LLM eval now supports `--llm-cache path.jsonl`. Use it when comparing selectors so
  `fixed_retry`, `dpo_pm`, and other baselines replay the same LLM-generated candidate sets.

Remaining work:

- Rerun a small real-LLM eval with `--llm-cache` if a stricter selector-level comparison is needed.
- Update thesis and slides so RecoveryGym and DeepSeek smoke are supplemental evidence, while
  `recovery_bench_generated` remains the main DPO_PM result.
- Keep memory ablations separate from the first DPO_PM claim.
