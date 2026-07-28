# recovery_gym Results

repeats: 1

Note: controlled synthetic benchmarks validate the recovery pipeline and ranking behavior; split-level results should be used when discussing generalization.

| baseline | failure_tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| dpo_pm | 68 | 0.662 | 1.000 | 956.574 |

## Split: clean

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| dpo_pm | 12 | 0.000 | 0.000 | 0.000 |

## Split: new_tool_same_family

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| dpo_pm | 4 | 1.000 | 1.000 | 906.250 |

## Split: seen_template_unseen_params

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| dpo_pm | 48 | 0.646 | 1.000 | 959.750 |

## Split: seen_tool_new_error_message

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| dpo_pm | 16 | 0.625 | 1.000 | 959.625 |

## Failure Type: clean

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| dpo_pm | 12 | 0.000 | 0.000 | 0.000 |

## Failure Type: invalid_json

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| dpo_pm | 16 | 0.625 | 1.000 | 919.375 |

## Failure Type: validation_error

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| dpo_pm | 52 | 0.673 | 1.000 | 968.019 |

## Failure Family: clean

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| dpo_pm | 12 | 0.000 | 0.000 | 0.000 |

## Failure Family: malformed_input

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| dpo_pm | 16 | 0.625 | 1.000 | 919.375 |

## Failure Family: schema_error

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| dpo_pm | 52 | 0.673 | 1.000 | 968.019 |
