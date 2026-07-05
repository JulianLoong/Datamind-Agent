# DPO_PM 涓荤嚎瀹為獙璁″垝

鏇存柊鏃堕棿锛?026-06-14

## 1. 鐩爣

褰撳墠闃舵涓绘敾 `DPO_PM`锛屼笉浼樺厛鍋氬畬鏁?memory 娑堣瀺銆傜涓€鐗堢洰鏍囨槸浜у嚭瀵煎笀鑳藉垵姝ヨ鍙殑涓诲疄楠岋細

```text
鍦ㄤ竴瀹氳妯＄殑鍙墽琛岃瘎娴嬮泦涓婏紝DPO_PM 鐩告瘮娌℃湁 PM 鎺掑簭鐨勬仮澶嶇瓥鐣ユ洿濂斤紝
鑷冲皯浣撶幇鍦?recovery_success_rate銆乤vg_recovery_attempts 鎴?avg_tool_calls 涓娿€?
```

涓?benchmark 浣跨敤 `recovery_bench_generated`銆俙RecoveryGym` 鏆備綔涓鸿ˉ鍏呮硾鍖栧帇鍔涙祴璇曞拰澶辫触鍒嗘瀽锛屼笉浣滀负绗竴鐗堝敮涓€涓荤粨璁恒€?

## 2. 褰撳墠鐘舵€?

- 鏃?`data/pm_checkpoints/dpo_pm` 鍙搴?`recovery_bench_lite` 鏃╂湡 demo銆?
- 褰撳墠浠撳簱宸叉湁 `data/pref_pairs_generated`锛歚512 train / 128 val`銆?
- 宸查噸鏂伴噰闆?`data/pref_pairs_outcomes`锛歚768 train / 192 val`锛屽叡 `960` 鏉?`outcome_multi_candidate` 鍋忓ソ瀵广€?
- 宸插鍑?`data/dpo_outcomes`锛歚768 train / 192 val`锛岀敤浜?TRL DPO 璁粌銆?
- 褰撳墠鏈満鐜缂哄皯 `torch`銆乣transformers`銆乣datasets`銆乣peft`銆乣trl`銆乣bitsandbytes`锛屼笉鑳界洿鎺ヨ缁?DPO_PM锛涜缁冮渶瑕佸湪 CUDA/4090 鐜鎵ц銆?
- `run_eval.py` 宸叉敮鎸?`--pm-paths baseline=path`锛屽彲鍦ㄥ悓涓€寮犺〃閲岀粰涓嶅悓 PM baseline 閰嶄笉鍚?checkpoint銆?

## 3. 鎺ㄨ崘鎵ц椤哄簭

### Step 1锛氶噰闆?outcome-ranked 鍋忓ソ鏁版嵁

```bash
PYTHONPATH=src python3 scripts/collect_candidate_outcomes.py \
  --benchmark recovery_bench_generated \
  --splits train \
  --candidate-count 3 \
  --out-dir data/pref_pairs_outcomes
```

楠屾敹锛?

- `data/pref_pairs_outcomes/train.jsonl` 闈炵┖銆?
- `data/pref_pairs_outcomes/val.jsonl` 闈炵┖銆?
- `data/pref_pairs_outcomes/outcome_report.json` 涓?`source_counts` 鍖呭惈 `outcome_multi_candidate`銆?
- 鎬?pair 鏁板缓璁笉灏戜簬 500锛涗笉瓒冲垯浣跨敤 `data/pref_pairs_generated` 浣滀负琛ュ厖鎴?fallback銆?

### Step 2锛氳缁?DPO_PM

棣栫増浣跨敤 `Qwen/Qwen2.5-0.5B-Instruct`锛岃緭鍑虹洰褰曚笉瑕佽鐩栨棫 checkpoint銆?

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

濡傛灉 outcome-ranked pair 鏁颁笉瓒?500锛屾敼鐢?generated 鏁版嵁鍏堣窇閫氾細

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

### Step 3锛歴anity check

```bash
PYTHONPATH=src python3 scripts/run_eval.py \
  --benchmark recovery_bench_lite \
  --baselines no_recovery random fixed_retry dpo_pm_r3 \
  --pm-paths dpo_pm_r3=Qwen/Qwen2.5-0.5B-Instruct::data/pm_checkpoints/dpo_pm_outcomes \
  --repeats 1 \
  --out data/eval/dpo_pm_outcomes_lite.json
```

### Step 4锛氫富瀹為獙

```bash
PYTHONPATH=src python3 scripts/run_eval.py \
  --benchmark recovery_bench_generated \
  --baselines no_recovery random fixed_retry dpo_pm_r3 \
  --pm-paths dpo_pm_r3=Qwen/Qwen2.5-0.5B-Instruct::data/pm_checkpoints/dpo_pm_outcomes \
  --splits test_unseen clean \
  --repeats 1 \
  --out data/eval/dpo_pm_outcomes_generated.json
```

涓昏〃鍏虫敞锛?

- `recovery_success_rate`
- `avg_recovery_attempts_on_failure_tasks`
- `avg_tool_calls_on_failure_tasks`
- split-wise `test_unseen` / `clean`

### Step 5锛氳ˉ鍏?RecoveryGym

```bash
PYTHONPATH=src python3 scripts/run_recovery_gym_eval.py \
  --baselines no_recovery fixed_retry random dpo_pm_r3 \
  --pm-paths dpo_pm_r3=Qwen/Qwen2.5-0.5B-Instruct::data/pm_checkpoints/dpo_pm_outcomes \
  --repeats 1 \
  --out data/eval/dpo_pm_outcomes_recovery_gym.json
```

RecoveryGym 鍙綔涓鸿ˉ鍏呫€傝嫢 DPO_PM 琛ㄧ幇涓嶄匠锛屽簲閲嶇偣鍒嗘瀽鍊欓€夎鐩栥€乫ailure family 鍜屾暟鎹垎甯冿紝涓嶇洿鎺ュ惁瀹氫富鏂规硶銆?

## 4. 鍒濈缁撴灉鍙ｅ緞

鎸夌粨鏋滈€夋嫨琛ㄨ堪锛?

- 濡傛灉 DPO_PM 鎴愬姛鐜囨渶楂橈細`DPO_PM 鎻愰珮鎭㈠鎴愬姛鐜囷紝骞堕檷浣庢棤鏁堟仮澶嶅皾璇曘€俙
- 濡傛灉 DPO_PM 涓?fixed_retry 鎴愬姛鐜囩浉杩戜絾灏濊瘯鏇村皯锛歚DPO_PM 鍦ㄤ繚鎸佹仮澶嶈兘鍔涚殑鍚屾椂鍑忓皯鎭㈠杞暟鍜屽伐鍏疯皟鐢ㄣ€俙
- 濡傛灉 DPO_PM 鍙己浜?random銆佷笉寮轰簬 fixed_retry锛歚DPO_PM 瀛﹀埌鏈夋晥鍊欓€夋帓搴忥紝浣嗗綋鍓嶆暟鎹拰鍊欓€夎鐩栬繕涓嶈冻浠ュ叏闈㈣秴杩囪鍒欑瓥鐣ャ€俙

绗竴鐗堜笉鍐?memory 娑堣瀺涓轰富缁撹銆?

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
| random | 0.473 | 0.275 | 0.727 | 1.727 |
| fixed_retry | 1.000 | 1.000 | 1.455 | 2.455 |
| dpo_pm_r3 | 1.000 | 1.000 | 0.727 | 1.727 |

On failure tasks only, `dpo_pm_r3` matched `fixed_retry` recovery success (`1.000`) while
using fewer recovery attempts (`1.0` vs `2.0`) and fewer tool calls (`2.0` vs `3.0`).
This supports the current first-version claim: DPO_PM can preserve recovery capability
while reducing invalid recovery rounds in the controlled synthetic setting.

Remaining work:

- Run a small real-LLM candidate smoke test with `dpo_pm_r3`.
- Keep memory ablations separate from the first DPO_PM claim.

## 6. RecoveryGym update: 2026-07-03

The supplemental RecoveryGym DPO_PM evaluation has now been completed and checked in as:

- `data/eval/dpo_pm_outcomes_recovery_gym.json` and `.md`

Smoke setting:

```text
benchmark: recovery_gym
splits: seen_template_unseen_params
max_tasks: 16
repeats: 1
baselines: no_recovery random fixed_retry dpo_pm_r3
```

Full RecoveryGym setting:

```text
benchmark: recovery_gym
task_count: 116
repeats: 1
baselines: no_recovery random fixed_retry dpo_pm_r3
```

Full RecoveryGym result:

| baseline | success_rate | recovery_success_rate | avg_recovery_attempts | avg_tool_calls | avg_recovery_tokens |
|---|---:|---:|---:|---:|---:|
| no_recovery | 0.103 | 0.000 | 0.000 | 1.000 | 0.000 |
| random | 0.259 | 0.173 | 0.897 | 1.897 | 450.319 |
| fixed_retry | 0.517 | 0.462 | 1.724 | 2.724 | 862.121 |
| dpo_pm_r3 | 0.517 | 0.462 | 1.310 | 2.310 | 653.871 |

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

## 7. DeepSeek real-LLM smoke update: 2026-07-05

A small real-LLM DPO_PM smoke evaluation has now been completed and checked in as:

- `data/eval/real_llm_deepseek_dpo_pm_r3_smoke.json`
- `data/eval/real_llm_deepseek_dpo_pm_r3_smoke.md`

Setting:

```text
benchmark: recovery_bench_lite
max_tasks: 8
repeats: 1
candidate generator: DeepSeek through the OpenAI-compatible path
baselines: fixed_retry dpo_pm_r3
```

Result:

| baseline | success_rate | recovery_success_rate | avg_recovery_attempts | avg_tool_calls | avg_recovery_tokens | avg_recovery_latency_ms |
|---|---:|---:|---:|---:|---:|---:|
| fixed_retry | 0.625 | 0.500 | 1.500 | 2.500 | 1154.750 | 3916.607 |
| dpo_pm_r3 | 0.625 | 0.500 | 1.250 | 2.250 | 967.000 | 967.692 |

Paper-safe wording:

- This is a real-LLM candidate-generation smoke test, not a main result.
- It verifies that the DPO_PM recovery pipeline can operate with non-deterministic candidates
  generated by an external LLM.
- The trend is consistent with the main controlled experiments: DPO_PM matches fixed-retry
  success while reducing recovery attempts, tool calls, token cost, and latency.
- Because the sample size is small, this result should not be used for a strong generalization
  claim. It is a path-validation smoke test with equal retry budgets; use `baseline_configs` to
  verify both `fixed_retry` and `dpo_pm_r3` use `max_retries_per_step=3`.

Implementation note:

- Future eval reports now include `recovery_trace`, which records generated candidates, the chosen
  index, PM scores, and initial/final tool results. Use that field for candidate-level failure
  analysis after rerunning real-LLM evals.
- Real-LLM eval now supports `--llm-cache path.jsonl`. Use it when comparing selectors so
  `fixed_retry`, `dpo_pm_r3`, and other baselines replay the same LLM-generated candidate sets.
- The 2026-07-05 eval wrapper defaults to `fixed_retry` versus `dpo_pm_r3`, records
  `baseline_configs`, and constrains real-LLM candidate prompts with the available tool schemas.

Remaining work:

- Rerun a small real-LLM eval with `--llm-cache` and equal retry budgets if a stricter
  selector-level comparison is needed.
- Update thesis and slides so RecoveryGym and DeepSeek smoke are supplemental evidence, while
  `recovery_bench_generated` remains the main DPO_PM result.
- Keep real-LLM trace-derived DPO retraining as future work: use `recovery_trace` for analysis now,
  and later convert production/real-LLM trajectories into outcome-ranked preference pairs.
- Keep memory ablations separate from the first DPO_PM claim.

