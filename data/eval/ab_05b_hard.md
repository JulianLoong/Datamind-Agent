# recovery_bench_hard Results

repeats: 1

Note: controlled synthetic benchmarks validate the recovery pipeline and ranking behavior; split-level results should be used when discussing generalization.

| baseline | failure_tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| base_model | 20 | 0.000 | 1.000 | 626.750 |
| dpo_pm | 20 | 0.000 | 1.000 | 626.750 |

## Split: test_unseen

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| base_model | 20 | 0.000 | 1.000 | 626.750 |
| dpo_pm | 20 | 0.000 | 1.000 | 626.750 |

## Failure Type: no_rows

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| base_model | 20 | 0.000 | 1.000 | 626.750 |
| dpo_pm | 20 | 0.000 | 1.000 | 626.750 |

## Failure Family: contextual_filter

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| base_model | 20 | 0.000 | 1.000 | 626.750 |
| dpo_pm | 20 | 0.000 | 1.000 | 626.750 |
