# recovery_bench_generated Results

repeats: 1

Note: controlled synthetic benchmarks validate the recovery pipeline and ranking behavior; split-level results should be used when discussing generalization.

| baseline | failure_tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| dpo_pm | 100 | 0.800 | 1.000 | 939.710 |

## Split: test_unseen

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| dpo_pm | 100 | 0.800 | 1.000 | 939.710 |

## Failure Type: invalid_json

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| dpo_pm | 20 | 0.650 | 1.000 | 928.900 |

## Failure Type: missing_field

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| dpo_pm | 20 | 0.800 | 1.000 | 1058.650 |

## Failure Type: validation_error

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| dpo_pm | 60 | 0.850 | 1.000 | 903.667 |

## Failure Family: unlabeled_failure

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| dpo_pm | 100 | 0.800 | 1.000 | 939.710 |
