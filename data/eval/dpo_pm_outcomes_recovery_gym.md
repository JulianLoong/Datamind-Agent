# recovery_gym Results

repeats: 1

Note: controlled synthetic benchmarks validate the recovery pipeline and ranking behavior; split-level results should be used when discussing generalization.

| baseline | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls | avg_recovery_tokens | avg_recovery_latency_ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| no_recovery | 0.103 | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 |
| random | 0.241 | 0.154 | 0.897 | 1.000 | 1.897 | 146.638 | 0.030 |
| fixed_retry | 0.517 | 0.462 | 1.724 | 2.000 | 2.724 | 278.259 | 0.039 |
| dpo_pm | 0.517 | 0.462 | 0.897 | 1.000 | 1.897 | 146.638 | 0.041 |

## Split: clean

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 12 | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| random | 12 | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| fixed_retry | 12 | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| dpo_pm | 12 | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |

## Split: new_tool_same_family

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 8 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| random | 8 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |
| fixed_retry | 8 | 0.000 | 0.000 | 3.000 | 0.000 | 4.000 |
| dpo_pm | 8 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |

## Split: seen_template_unseen_params

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 72 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| random | 72 | 0.167 | 0.167 | 1.000 | 1.000 | 2.000 |
| fixed_retry | 72 | 0.500 | 0.500 | 1.833 | 2.000 | 2.833 |
| dpo_pm | 72 | 0.500 | 0.500 | 1.000 | 1.000 | 2.000 |

## Split: seen_tool_new_error_message

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 24 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| random | 24 | 0.167 | 0.167 | 1.000 | 1.000 | 2.000 |
| fixed_retry | 24 | 0.500 | 0.500 | 1.833 | 2.000 | 2.833 |
| dpo_pm | 24 | 0.500 | 0.500 | 1.000 | 1.000 | 2.000 |

## Failure Type: clean

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 12 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| random | 12 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| fixed_retry | 12 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| dpo_pm | 12 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## Failure Type: division_by_zero

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 16 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| random | 16 | 0.438 | 0.438 | 1.000 | 1.000 | 2.000 |
| fixed_retry | 16 | 1.000 | 1.000 | 2.000 | 2.000 | 3.000 |
| dpo_pm | 16 | 1.000 | 1.000 | 1.000 | 1.000 | 2.000 |

## Failure Type: file_not_found

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 4 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| random | 4 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |
| fixed_retry | 4 | 0.000 | 0.000 | 3.000 | 0.000 | 4.000 |
| dpo_pm | 4 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |

## Failure Type: invalid_expression

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 4 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| random | 4 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |
| fixed_retry | 4 | 0.000 | 0.000 | 3.000 | 0.000 | 4.000 |
| dpo_pm | 4 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |

## Failure Type: invalid_json

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 16 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| random | 16 | 0.312 | 0.312 | 1.000 | 1.000 | 2.000 |
| fixed_retry | 16 | 1.000 | 1.000 | 2.000 | 2.000 | 3.000 |
| dpo_pm | 16 | 1.000 | 1.000 | 1.000 | 1.000 | 2.000 |

## Failure Type: not_found

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 16 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| random | 16 | 0.250 | 0.250 | 1.000 | 1.000 | 2.000 |
| fixed_retry | 16 | 1.000 | 1.000 | 2.000 | 2.000 | 3.000 |
| dpo_pm | 16 | 1.000 | 1.000 | 1.000 | 1.000 | 2.000 |

## Failure Type: permission_denied

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 16 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| random | 16 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |
| fixed_retry | 16 | 0.000 | 0.000 | 3.000 | 0.000 | 4.000 |
| dpo_pm | 16 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |

## Failure Type: validation_error

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 32 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| random | 32 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |
| fixed_retry | 32 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |
| dpo_pm | 32 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |

## Failure Family: clean

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 12 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| random | 12 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| fixed_retry | 12 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| dpo_pm | 12 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## Failure Family: malformed_input

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 20 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| random | 20 | 0.250 | 0.250 | 1.000 | 1.000 | 2.000 |
| fixed_retry | 20 | 0.800 | 0.800 | 2.200 | 2.000 | 3.200 |
| dpo_pm | 20 | 0.800 | 0.800 | 1.000 | 1.000 | 2.000 |

## Failure Family: permission_error

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 16 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| random | 16 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |
| fixed_retry | 16 | 0.000 | 0.000 | 3.000 | 0.000 | 4.000 |
| dpo_pm | 16 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |

## Failure Family: schema_error

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 32 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| random | 32 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |
| fixed_retry | 32 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |
| dpo_pm | 32 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |

## Failure Family: semantic_param_error

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 16 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| random | 16 | 0.438 | 0.438 | 1.000 | 1.000 | 2.000 |
| fixed_retry | 16 | 1.000 | 1.000 | 2.000 | 2.000 | 3.000 |
| dpo_pm | 16 | 1.000 | 1.000 | 1.000 | 1.000 | 2.000 |

## Failure Family: unavailable_resource

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 20 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| random | 20 | 0.200 | 0.200 | 1.000 | 1.000 | 2.000 |
| fixed_retry | 20 | 0.800 | 0.800 | 2.200 | 2.000 | 3.200 |
| dpo_pm | 20 | 0.800 | 0.800 | 1.000 | 1.000 | 2.000 |
