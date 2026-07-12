# recovery_gym Results

repeats: 1

Note: controlled synthetic benchmarks validate the recovery pipeline and ranking behavior; split-level results should be used when discussing generalization.

| baseline | failure_tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| llm_greedy | 68 | 0.368 | 1.000 | 661.971 |
| llm_self_pick | 68 | 0.706 | 1.000 | 1166.147 |
| base_model | 68 | 0.691 | 1.000 | 839.500 |
| dpo_pm | 68 | 0.706 | 1.000 | 839.500 |

## Split: clean

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| llm_greedy | 12 | 0.000 | 0.000 | 0.000 |
| llm_self_pick | 12 | 0.000 | 0.000 | 0.000 |
| base_model | 12 | 0.000 | 0.000 | 0.000 |
| dpo_pm | 12 | 0.000 | 0.000 | 0.000 |

## Split: new_tool_same_family

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| llm_greedy | 4 | 0.750 | 1.000 | 608.000 |
| llm_self_pick | 4 | 1.000 | 1.000 | 1045.750 |
| base_model | 4 | 1.000 | 1.000 | 765.500 |
| dpo_pm | 4 | 1.000 | 1.000 | 765.500 |

## Split: seen_template_unseen_params

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| llm_greedy | 48 | 0.333 | 1.000 | 661.625 |
| llm_self_pick | 48 | 0.667 | 1.000 | 1168.750 |
| base_model | 48 | 0.646 | 1.000 | 841.333 |
| dpo_pm | 48 | 0.667 | 1.000 | 841.333 |

## Split: seen_tool_new_error_message

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| llm_greedy | 16 | 0.375 | 1.000 | 676.500 |
| llm_self_pick | 16 | 0.750 | 1.000 | 1188.438 |
| base_model | 16 | 0.750 | 1.000 | 852.500 |
| dpo_pm | 16 | 0.750 | 1.000 | 852.500 |

## Failure Type: clean

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| llm_greedy | 12 | 0.000 | 0.000 | 0.000 |
| llm_self_pick | 12 | 0.000 | 0.000 | 0.000 |
| base_model | 12 | 0.000 | 0.000 | 0.000 |
| dpo_pm | 12 | 0.000 | 0.000 | 0.000 |

## Failure Type: invalid_json

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| llm_greedy | 16 | 0.312 | 1.000 | 667.750 |
| llm_self_pick | 16 | 0.625 | 1.000 | 1165.312 |
| base_model | 16 | 0.625 | 1.000 | 815.875 |
| dpo_pm | 16 | 0.625 | 1.000 | 815.875 |

## Failure Type: validation_error

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| llm_greedy | 52 | 0.385 | 1.000 | 660.192 |
| llm_self_pick | 52 | 0.731 | 1.000 | 1166.404 |
| base_model | 52 | 0.712 | 1.000 | 846.769 |
| dpo_pm | 52 | 0.731 | 1.000 | 846.769 |

## Failure Family: clean

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| llm_greedy | 12 | 0.000 | 0.000 | 0.000 |
| llm_self_pick | 12 | 0.000 | 0.000 | 0.000 |
| base_model | 12 | 0.000 | 0.000 | 0.000 |
| dpo_pm | 12 | 0.000 | 0.000 | 0.000 |

## Failure Family: malformed_input

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| llm_greedy | 16 | 0.312 | 1.000 | 667.750 |
| llm_self_pick | 16 | 0.625 | 1.000 | 1165.312 |
| base_model | 16 | 0.625 | 1.000 | 815.875 |
| dpo_pm | 16 | 0.625 | 1.000 | 815.875 |

## Failure Family: schema_error

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| llm_greedy | 52 | 0.385 | 1.000 | 660.192 |
| llm_self_pick | 52 | 0.731 | 1.000 | 1166.404 |
| base_model | 52 | 0.712 | 1.000 | 846.769 |
| dpo_pm | 52 | 0.731 | 1.000 | 846.769 |
