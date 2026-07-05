# recovery_bench_generated Results

repeats: 1

Note: controlled synthetic benchmarks validate the recovery pipeline and ranking behavior; split-level results should be used when discussing generalization.

| baseline | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls | avg_recovery_tokens | avg_recovery_latency_ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| no_recovery | 0.273 | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 |
| random | 0.473 | 0.275 | 0.727 | 1.000 | 1.727 | 366.609 | 0.025 |
| fixed_retry | 1.000 | 1.000 | 1.455 | 2.000 | 2.455 | 733.218 | 0.038 |
| dpo_pm_r3 | 1.000 | 1.000 | 0.727 | 1.000 | 1.727 | 366.609 | 0.033 |

## Split: clean

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 30 | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| random | 30 | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| fixed_retry | 30 | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| dpo_pm_r3 | 30 | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |

## Split: test_unseen

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 80 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| random | 80 | 0.275 | 0.275 | 1.000 | 1.000 | 2.000 |
| fixed_retry | 80 | 1.000 | 1.000 | 2.000 | 2.000 | 3.000 |
| dpo_pm_r3 | 80 | 1.000 | 1.000 | 1.000 | 1.000 | 2.000 |

## Failure Type: clean

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 30 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| random | 30 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| fixed_retry | 30 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| dpo_pm_r3 | 30 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## Failure Type: division_by_zero

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 20 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| random | 20 | 0.200 | 0.200 | 1.000 | 1.000 | 2.000 |
| fixed_retry | 20 | 1.000 | 1.000 | 2.000 | 2.000 | 3.000 |
| dpo_pm_r3 | 20 | 1.000 | 1.000 | 1.000 | 1.000 | 2.000 |

## Failure Type: invalid_json

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 20 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| random | 20 | 0.250 | 0.250 | 1.000 | 1.000 | 2.000 |
| fixed_retry | 20 | 1.000 | 1.000 | 2.000 | 2.000 | 3.000 |
| dpo_pm_r3 | 20 | 1.000 | 1.000 | 1.000 | 1.000 | 2.000 |

## Failure Type: missing_field

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 20 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| random | 20 | 0.450 | 0.450 | 1.000 | 1.000 | 2.000 |
| fixed_retry | 20 | 1.000 | 1.000 | 2.000 | 2.000 | 3.000 |
| dpo_pm_r3 | 20 | 1.000 | 1.000 | 1.000 | 1.000 | 2.000 |

## Failure Type: not_found

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 20 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| random | 20 | 0.200 | 0.200 | 1.000 | 1.000 | 2.000 |
| fixed_retry | 20 | 1.000 | 1.000 | 2.000 | 2.000 | 3.000 |
| dpo_pm_r3 | 20 | 1.000 | 1.000 | 1.000 | 1.000 | 2.000 |

## Failure Family: clean

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 30 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| random | 30 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| fixed_retry | 30 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| dpo_pm_r3 | 30 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## Failure Family: unlabeled_failure

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 80 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| random | 80 | 0.275 | 0.275 | 1.000 | 1.000 | 2.000 |
| fixed_retry | 80 | 1.000 | 1.000 | 2.000 | 2.000 | 3.000 |
| dpo_pm_r3 | 80 | 1.000 | 1.000 | 1.000 | 1.000 | 2.000 |
