# recovery_bench_lite Results

repeats: 1

Note: controlled synthetic benchmarks validate the recovery pipeline and ranking behavior; split-level results should be used when discussing generalization.

| baseline | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls | avg_recovery_tokens | avg_recovery_latency_ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| fixed_retry | 1.000 | 1.000 | 1.500 | 2.000 | 2.500 | 954.250 | 8776.841 |
| dpo_pm | 0.875 | 0.833 | 0.750 | 1.000 | 1.750 | 470.250 | 4178.059 |

## Split: clean

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| fixed_retry | 2 | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| dpo_pm | 2 | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |

## Split: test_seen

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| fixed_retry | 3 | 1.000 | 1.000 | 2.000 | 2.000 | 3.000 |
| dpo_pm | 3 | 0.667 | 0.667 | 1.000 | 1.000 | 2.000 |

## Split: train

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| fixed_retry | 3 | 1.000 | 1.000 | 2.000 | 2.000 | 3.000 |
| dpo_pm | 3 | 1.000 | 1.000 | 1.000 | 1.000 | 2.000 |

## Failure Type: clean

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| fixed_retry | 2 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| dpo_pm | 2 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## Failure Type: division_by_zero

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| fixed_retry | 2 | 1.000 | 1.000 | 2.000 | 2.000 | 3.000 |
| dpo_pm | 2 | 0.500 | 0.500 | 1.000 | 1.000 | 2.000 |

## Failure Type: invalid_json

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| fixed_retry | 2 | 1.000 | 1.000 | 2.000 | 2.000 | 3.000 |
| dpo_pm | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 2.000 |

## Failure Type: not_found

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| fixed_retry | 2 | 1.000 | 1.000 | 2.000 | 2.000 | 3.000 |
| dpo_pm | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 2.000 |

## Failure Family: clean

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| fixed_retry | 2 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| dpo_pm | 2 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## Failure Family: unlabeled_failure

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| fixed_retry | 6 | 1.000 | 1.000 | 2.000 | 2.000 | 3.000 |
| dpo_pm | 6 | 0.833 | 0.833 | 1.000 | 1.000 | 2.000 |
