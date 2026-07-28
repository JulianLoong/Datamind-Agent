# recovery_gym Results

repeats: 1

Note: controlled synthetic benchmarks validate the recovery pipeline and ranking behavior; split-level results should be used when discussing generalization.

| baseline | failure_tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| llm_self_pick | 68 | 0.691 | 1.000 | 1289.221 |

## Split: clean

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| llm_self_pick | 12 | 0.000 | 0.000 | 0.000 |

## Split: new_tool_same_family

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| llm_self_pick | 4 | 1.000 | 1.000 | 1228.500 |

## Split: seen_template_unseen_params

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| llm_self_pick | 48 | 0.688 | 1.000 | 1294.333 |

## Split: seen_tool_new_error_message

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| llm_self_pick | 16 | 0.625 | 1.000 | 1289.062 |

## Failure Type: clean

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| llm_self_pick | 12 | 0.000 | 0.000 | 0.000 |

## Failure Type: invalid_json

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| llm_self_pick | 16 | 0.625 | 1.000 | 1258.625 |

## Failure Type: validation_error

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| llm_self_pick | 52 | 0.712 | 1.000 | 1298.635 |

## Failure Family: clean

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| llm_self_pick | 12 | 0.000 | 0.000 | 0.000 |

## Failure Family: malformed_input

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| llm_self_pick | 16 | 0.625 | 1.000 | 1258.625 |

## Failure Family: schema_error

| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |
|---|---:|---:|---:|---:|
| llm_self_pick | 52 | 0.712 | 1.000 | 1298.635 |
