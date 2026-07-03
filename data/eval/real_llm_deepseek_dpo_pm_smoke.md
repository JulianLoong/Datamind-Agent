# recovery_bench_lite Results

repeats: 1

Note: controlled synthetic benchmarks validate the recovery pipeline and ranking behavior; split-level results should be used when discussing generalization.

| baseline | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls | avg_recovery_tokens | avg_recovery_latency_ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| fixed_retry | 0.250 | 0.250 | 1.750 | 2.000 | 2.750 | 2966.000 | 49892.170 |
| dpo_pm | 0.250 | 0.250 | 1.000 | 1.000 | 2.000 | 1571.250 | 27095.702 |

## Split: test_seen

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| fixed_retry | 1 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |
| dpo_pm | 1 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |

## Split: train

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| fixed_retry | 3 | 0.333 | 0.333 | 2.000 | 2.000 | 3.000 |
| dpo_pm | 3 | 0.333 | 0.333 | 1.000 | 1.000 | 2.000 |

## Failure Type: division_by_zero

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| fixed_retry | 2 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |
| dpo_pm | 2 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |

## Failure Type: invalid_json

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| fixed_retry | 1 | 1.000 | 1.000 | 2.000 | 2.000 | 3.000 |
| dpo_pm | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 2.000 |

## Failure Type: not_found

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| fixed_retry | 1 | 0.000 | 0.000 | 3.000 | 0.000 | 4.000 |
| dpo_pm | 1 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |

## Failure Family: unlabeled_failure

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| fixed_retry | 4 | 0.250 | 0.250 | 1.750 | 2.000 | 2.750 |
| dpo_pm | 4 | 0.250 | 0.250 | 1.000 | 1.000 | 2.000 |
