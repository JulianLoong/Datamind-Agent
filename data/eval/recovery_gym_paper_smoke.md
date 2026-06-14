# recovery_gym Results

repeats: 1

Note: controlled synthetic benchmarks validate the recovery pipeline and ranking behavior; split-level results should be used when discussing generalization.

| baseline | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls | avg_recovery_tokens | avg_recovery_latency_ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| no_recovery | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 |
| fixed_retry | 0.625 | 0.625 | 1.875 | 2.000 | 2.875 | 303.000 | 0.043 |
| mock_pm | 0.625 | 0.625 | 1.000 | 1.000 | 2.000 | 163.125 | 0.018 |
| lightweight_pm | 0.625 | 0.625 | 1.000 | 1.000 | 2.000 | 163.125 | 0.019 |
| memory_lightweight_pm | 0.625 | 0.625 | 1.000 | 1.000 | 2.000 | 163.125 | 0.020 |

## Split: seen_template_unseen_params

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 8 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| fixed_retry | 8 | 0.625 | 0.625 | 1.875 | 2.000 | 2.875 |
| mock_pm | 8 | 0.625 | 0.625 | 1.000 | 1.000 | 2.000 |
| lightweight_pm | 8 | 0.625 | 0.625 | 1.000 | 1.000 | 2.000 |
| memory_lightweight_pm | 8 | 0.625 | 0.625 | 1.000 | 1.000 | 2.000 |

## Failure Type: division_by_zero

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 2 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| fixed_retry | 2 | 1.000 | 1.000 | 2.000 | 2.000 | 3.000 |
| mock_pm | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 2.000 |
| lightweight_pm | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 2.000 |
| memory_lightweight_pm | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 2.000 |

## Failure Type: invalid_json

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 2 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| fixed_retry | 2 | 1.000 | 1.000 | 2.000 | 2.000 | 3.000 |
| mock_pm | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 2.000 |
| lightweight_pm | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 2.000 |
| memory_lightweight_pm | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 2.000 |

## Failure Type: not_found

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 1 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| fixed_retry | 1 | 1.000 | 1.000 | 2.000 | 2.000 | 3.000 |
| mock_pm | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 2.000 |
| lightweight_pm | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 2.000 |
| memory_lightweight_pm | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 2.000 |

## Failure Type: permission_denied

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 1 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| fixed_retry | 1 | 0.000 | 0.000 | 3.000 | 0.000 | 4.000 |
| mock_pm | 1 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |
| lightweight_pm | 1 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |
| memory_lightweight_pm | 1 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |

## Failure Type: validation_error

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 2 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| fixed_retry | 2 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |
| mock_pm | 2 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |
| lightweight_pm | 2 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |
| memory_lightweight_pm | 2 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |

## Failure Family: malformed_input

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 2 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| fixed_retry | 2 | 1.000 | 1.000 | 2.000 | 2.000 | 3.000 |
| mock_pm | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 2.000 |
| lightweight_pm | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 2.000 |
| memory_lightweight_pm | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 2.000 |

## Failure Family: permission_error

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 1 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| fixed_retry | 1 | 0.000 | 0.000 | 3.000 | 0.000 | 4.000 |
| mock_pm | 1 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |
| lightweight_pm | 1 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |
| memory_lightweight_pm | 1 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |

## Failure Family: schema_error

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 2 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| fixed_retry | 2 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |
| mock_pm | 2 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |
| lightweight_pm | 2 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |
| memory_lightweight_pm | 2 | 0.000 | 0.000 | 1.000 | 0.000 | 2.000 |

## Failure Family: semantic_param_error

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 2 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| fixed_retry | 2 | 1.000 | 1.000 | 2.000 | 2.000 | 3.000 |
| mock_pm | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 2.000 |
| lightweight_pm | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 2.000 |
| memory_lightweight_pm | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 2.000 |

## Failure Family: unavailable_resource

| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |
|---|---:|---:|---:|---:|---:|---:|
| no_recovery | 1 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| fixed_retry | 1 | 1.000 | 1.000 | 2.000 | 2.000 | 3.000 |
| mock_pm | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 2.000 |
| lightweight_pm | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 2.000 |
| memory_lightweight_pm | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 2.000 |
