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
