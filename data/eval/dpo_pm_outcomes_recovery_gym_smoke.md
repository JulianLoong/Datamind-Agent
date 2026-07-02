# recovery_gym Results

repeats: 1

Note: controlled synthetic benchmarks validate the recovery pipeline and ranking behavior; split-level results should be used when discussing generalization.

| baseline | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls | avg_recovery_tokens | avg_recovery_latency_ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| no_recovery | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 |
| random | 0.062 | 0.062 | 1.000 | 1.000 | 2.000 | 163.250 | 0.060 |
| fixed_retry | 0.562 | 0.562 | 1.812 | 2.000 | 2.812 | 293.438 | 0.057 |
| dpo_pm | 0.562 | 0.562 | 1.000 | 1.000 | 2.000 | 163.250 | 0.064 |

## Split: seen_template_unseen_params

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 16 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| random | 16 | 0.062 | 0.062 | 1.000 | 1.000 | 2.000 |
| fixed_retry | 16 | 0.562 | 0.562 | 1.812 | 2.000 | 2.812 |
| dpo_pm | 16 | 0.562 | 0.562 | 1.000 | 1.000 | 2.000 |

## Failure Type: division_by_zero

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| random | 3 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |
| fixed_retry | 3 | 1.000 | 1.000 | 2.000 | 2.000 | 3.000 |
| dpo_pm | 3 | 1.000 | 1.000 | 1.000 | 1.000 | 2.000 |

## Failure Type: invalid_json

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| random | 3 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |
| fixed_retry | 3 | 1.000 | 1.000 | 2.000 | 2.000 | 3.000 |
| dpo_pm | 3 | 1.000 | 1.000 | 1.000 | 1.000 | 2.000 |

## Failure Type: not_found

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| random | 3 | 0.333 | 0.333 | 1.000 | 1.000 | 2.000 |
| fixed_retry | 3 | 1.000 | 1.000 | 2.000 | 2.000 | 3.000 |
| dpo_pm | 3 | 1.000 | 1.000 | 1.000 | 1.000 | 2.000 |

## Failure Type: permission_denied

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 2 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| random | 2 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |
| fixed_retry | 2 | 0.000 | 0.000 | 3.000 | 0.000 | 4.000 |
| dpo_pm | 2 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |

## Failure Type: validation_error

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 5 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| random | 5 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |
| fixed_retry | 5 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |
| dpo_pm | 5 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |

## Failure Family: malformed_input

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| random | 3 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |
| fixed_retry | 3 | 1.000 | 1.000 | 2.000 | 2.000 | 3.000 |
| dpo_pm | 3 | 1.000 | 1.000 | 1.000 | 1.000 | 2.000 |

## Failure Family: permission_error

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 2 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| random | 2 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |
| fixed_retry | 2 | 0.000 | 0.000 | 3.000 | 0.000 | 4.000 |
| dpo_pm | 2 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |

## Failure Family: schema_error

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 5 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| random | 5 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |
| fixed_retry | 5 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |
| dpo_pm | 5 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |

## Failure Family: semantic_param_error

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| random | 3 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |
| fixed_retry | 3 | 1.000 | 1.000 | 2.000 | 2.000 | 3.000 |
| dpo_pm | 3 | 1.000 | 1.000 | 1.000 | 1.000 | 2.000 |

## Failure Family: unavailable_resource

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| random | 3 | 0.333 | 0.333 | 1.000 | 1.000 | 2.000 |
| fixed_retry | 3 | 1.000 | 1.000 | 2.000 | 2.000 | 3.000 |
| dpo_pm | 3 | 1.000 | 1.000 | 1.000 | 1.000 | 2.000 |
