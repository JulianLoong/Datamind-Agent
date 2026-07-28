# DPO Pairwise Margin Diagnostic

Positioning: candidate-level adapter-on/off diagnostic; not an end-to-end generalization result.

Pairs: 219 across 77 error contexts
Give-up sensitivity penalty: -5.0

## success_over_failure

Pairs: 154 | Contexts: 77

| scorer | accuracy | accuracy 95% CI | mean margin | margin 95% CI | median margin | ties |
|---|---:|---:|---:|---:|---:|---:|
| base_raw | 0.708 | [0.623, 0.786] | 0.0904 | [0.0122, 0.1621] | 0.1250 | 0.000 |
| base_penalized | 0.708 | [0.623, 0.786] | 2.2007 | [1.9065, 2.4602] | 0.1250 | 0.000 |
| dpo_raw | 1.000 | [1.000, 1.000] | 2.9861 | [2.7326, 3.2121] | 2.1289 | 0.000 |
| dpo_penalized | 1.000 | [1.000, 1.000] | 5.0965 | [4.6289, 5.5088] | 2.1289 | 0.000 |
| dpo_reward | 1.000 | [1.000, 1.000] | 118.6786 | [112.6023, 124.2549] | 95.5000 | 0.000 |

| paired comparison | delta accuracy | accuracy delta 95% CI | delta mean margin | margin delta 95% CI |
|---|---:|---:|---:|---:|
| dpo_raw_minus_base_raw | 0.292 | [0.214, 0.377] | 2.8957 | [2.7195, 3.0546] |
| base_penalized_minus_base_raw | 0.000 | [0.000, 0.000] | 2.1104 | [1.8831, 2.3052] |
| dpo_penalized_minus_base_penalized | 0.292 | [0.214, 0.377] | 2.8957 | [2.7195, 3.0546] |

## executable_failure_over_give_up

Pairs: 65 | Contexts: 65

| scorer | accuracy | accuracy 95% CI | mean margin | margin 95% CI | median margin | ties |
|---|---:|---:|---:|---:|---:|---:|
| base_raw | 1.000 | [1.000, 1.000] | 0.4333 | [0.3909, 0.4734] | 0.4688 | 0.000 |
| base_penalized | 1.000 | [1.000, 1.000] | 5.4333 | [5.3909, 5.4734] | 5.4688 | 0.000 |
| dpo_raw | 1.000 | [1.000, 1.000] | 3.7385 | [3.6108, 3.8606] | 3.9219 | 0.000 |
| dpo_penalized | 1.000 | [1.000, 1.000] | 8.7385 | [8.6108, 8.8606] | 8.9219 | 0.000 |
| dpo_reward | 1.000 | [1.000, 1.000] | 85.9846 | [84.6346, 87.3231] | 88.2500 | 0.000 |

| paired comparison | delta accuracy | accuracy delta 95% CI | delta mean margin | margin delta 95% CI |
|---|---:|---:|---:|---:|
| dpo_raw_minus_base_raw | 0.000 | [0.000, 0.000] | 3.3052 | [3.2178, 3.3898] |
| base_penalized_minus_base_raw | 0.000 | [0.000, 0.000] | 5.0000 | [5.0000, 5.0000] |
| dpo_penalized_minus_base_penalized | 0.000 | [0.000, 0.000] | 3.3052 | [3.2178, 3.3898] |

## all

Pairs: 219 | Contexts: 77

| scorer | accuracy | accuracy 95% CI | mean margin | margin 95% CI | median margin | ties |
|---|---:|---:|---:|---:|---:|---:|
| base_raw | 0.795 | [0.728, 0.855] | 0.1921 | [0.1263, 0.2500] | 0.2344 | 0.000 |
| base_penalized | 0.795 | [0.728, 0.855] | 3.1602 | [2.8741, 3.3972] | 5.2344 | 0.000 |
| dpo_raw | 1.000 | [1.000, 1.000] | 3.2094 | [3.0081, 3.3825] | 3.7344 | 0.000 |
| dpo_penalized | 1.000 | [1.000, 1.000] | 6.1774 | [5.7567, 6.5260] | 8.7344 | 0.000 |
| dpo_reward | 1.000 | [1.000, 1.000] | 108.9749 | [105.1033, 112.3750] | 90.5000 | 0.000 |

| paired comparison | delta accuracy | accuracy delta 95% CI | delta mean margin | margin delta 95% CI |
|---|---:|---:|---:|---:|
| dpo_raw_minus_base_raw | 0.205 | [0.145, 0.272] | 3.0173 | [2.8797, 3.1360] |
| base_penalized_minus_base_raw | 0.000 | [0.000, 0.000] | 2.9680 | [2.7358, 3.1556] |
| dpo_penalized_minus_base_penalized | 0.205 | [0.145, 0.272] | 3.0173 | [2.8797, 3.1360] |

## Acceptance Checks

- DPO raw improves the primary subset: `True`
- DPO with the same penalty improves the primary subset: `True`
- DPO implicit reward has a positive primary margin: `True`
