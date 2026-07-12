# recovery_bench_generated Results

repeats: 1

Note: controlled synthetic benchmarks validate the recovery pipeline and ranking behavior; split-level results should be used when discussing generalization.

| baseline | failure_tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| llm_greedy | 100 | 0.670 | 1.000 | 661.000 |
| llm_self_pick | 100 | 0.850 | 1.000 | 1161.780 |
| dpo_pm | 100 | 0.850 | 1.000 | 831.760 |

## Split: clean

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| llm_greedy | 30 | 0.000 | 0.000 | 0.000 |
| llm_self_pick | 30 | 0.000 | 0.000 | 0.000 |
| dpo_pm | 30 | 0.000 | 0.000 | 0.000 |

## Split: test_unseen

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| llm_greedy | 100 | 0.670 | 1.000 | 661.000 |
| llm_self_pick | 100 | 0.850 | 1.000 | 1161.780 |
| dpo_pm | 100 | 0.850 | 1.000 | 831.760 |

## Failure Type: clean

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| llm_greedy | 30 | 0.000 | 0.000 | 0.000 |
| llm_self_pick | 30 | 0.000 | 0.000 | 0.000 |
| dpo_pm | 30 | 0.000 | 0.000 | 0.000 |

## Failure Type: invalid_json

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| llm_greedy | 20 | 0.550 | 1.000 | 685.650 |
| llm_self_pick | 20 | 0.650 | 1.000 | 1184.250 |
| dpo_pm | 20 | 0.650 | 1.000 | 832.150 |

## Failure Type: missing_field

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| llm_greedy | 20 | 0.850 | 1.000 | 706.500 |
| llm_self_pick | 20 | 0.950 | 1.000 | 1321.500 |
| dpo_pm | 20 | 0.950 | 1.000 | 948.700 |

## Failure Type: validation_error

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| llm_greedy | 60 | 0.650 | 1.000 | 637.617 |
| llm_self_pick | 60 | 0.883 | 1.000 | 1101.050 |
| dpo_pm | 60 | 0.883 | 1.000 | 792.650 |

## Failure Family: clean

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| llm_greedy | 30 | 0.000 | 0.000 | 0.000 |
| llm_self_pick | 30 | 0.000 | 0.000 | 0.000 |
| dpo_pm | 30 | 0.000 | 0.000 | 0.000 |

## Failure Family: unlabeled_failure

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| llm_greedy | 100 | 0.670 | 1.000 | 661.000 |
| llm_self_pick | 100 | 0.850 | 1.000 | 1161.780 |
| dpo_pm | 100 | 0.850 | 1.000 | 831.760 |
