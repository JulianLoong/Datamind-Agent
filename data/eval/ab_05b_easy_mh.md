# recovery_bench_generated Results

repeats: 1

Note: controlled synthetic benchmarks validate the recovery pipeline and ranking behavior; split-level results should be used when discussing generalization.

| baseline | failure_tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| dpo_pm | 100 | 1.000 | 1.000 | 624.910 |

## Split: test_unseen

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| dpo_pm | 100 | 1.000 | 1.000 | 624.910 |

## Failure Type: invalid_json

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| dpo_pm | 20 | 1.000 | 1.000 | 618.850 |

## Failure Type: missing_field

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| dpo_pm | 20 | 1.000 | 1.000 | 623.000 |

## Failure Type: validation_error

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| dpo_pm | 60 | 1.000 | 1.000 | 627.567 |

## Failure Family: unlabeled_failure

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| dpo_pm | 100 | 1.000 | 1.000 | 624.910 |
