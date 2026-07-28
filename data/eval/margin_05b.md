# DPO Pairwise Margin Diagnostic

Positioning: candidate-level adapter-on/off diagnostic; not an end-to-end generalization result.

Pairs: 219 across 77 error contexts
Give-up sensitivity penalty: -5.0

## success_over_failure

Pairs: 154 | Contexts: 77

| scorer | accuracy | accuracy 95% CI | mean margin | margin 95% CI | median margin | ties |
|---|---:|---:|---:|---:|---:|---:|
| base_raw | 0.708 | [0.623, 0.786] | 0.1501 | [0.0593, 0.2316] | 0.1016 | 0.000 |
| base_penalized | 0.708 | [0.623, 0.786] | 2.2605 | [1.9546, 2.5312] | 0.1016 | 0.000 |
| dpo_raw | 1.000 | [1.000, 1.000] | 3.2380 | [2.9342, 3.5094] | 1.6719 | 0.000 |
| dpo_penalized | 1.000 | [1.000, 1.000] | 5.3484 | [4.8344, 5.8055] | 1.6719 | 0.000 |
| dpo_reward | 1.000 | [1.000, 1.000] | 123.4253 | [115.6429, 130.5584] | 100.2500 | 0.000 |

| paired comparison | delta accuracy | accuracy delta 95% CI | delta mean margin | margin delta 95% CI |
|---|---:|---:|---:|---:|
| dpo_raw_minus_base_raw | 0.292 | [0.214, 0.377] | 3.0879 | [2.8741, 3.2795] |
| base_penalized_minus_base_raw | 0.000 | [0.000, 0.000] | 2.1104 | [1.8831, 2.3052] |
| dpo_penalized_minus_base_penalized | 0.292 | [0.214, 0.377] | 3.0879 | [2.8741, 3.2795] |

## executable_failure_over_give_up

Pairs: 65 | Contexts: 65

| scorer | accuracy | accuracy 95% CI | mean margin | margin 95% CI | median margin | ties |
|---|---:|---:|---:|---:|---:|---:|
| base_raw | 1.000 | [1.000, 1.000] | 0.5684 | [0.5142, 0.6202] | 0.6250 | 0.000 |
| base_penalized | 1.000 | [1.000, 1.000] | 5.5684 | [5.5142, 5.6202] | 5.6250 | 0.000 |
| dpo_raw | 1.000 | [1.000, 1.000] | 4.5781 | [4.4502, 4.7007] | 4.6875 | 0.000 |
| dpo_penalized | 1.000 | [1.000, 1.000] | 9.5781 | [9.4502, 9.7007] | 9.6875 | 0.000 |
| dpo_reward | 1.000 | [1.000, 1.000] | 106.2154 | [104.8692, 107.5462] | 104.5000 | 0.000 |

| paired comparison | delta accuracy | accuracy delta 95% CI | delta mean margin | margin delta 95% CI |
|---|---:|---:|---:|---:|
| dpo_raw_minus_base_raw | 0.000 | [0.000, 0.000] | 4.0097 | [3.9317, 4.0841] |
| base_penalized_minus_base_raw | 0.000 | [0.000, 0.000] | 5.0000 | [5.0000, 5.0000] |
| dpo_penalized_minus_base_penalized | 0.000 | [0.000, 0.000] | 4.0097 | [3.9317, 4.0841] |

## all

Pairs: 219 | Contexts: 77

| scorer | accuracy | accuracy 95% CI | mean margin | margin 95% CI | median margin | ties |
|---|---:|---:|---:|---:|---:|---:|
| base_raw | 0.795 | [0.728, 0.855] | 0.2742 | [0.1950, 0.3431] | 0.2812 | 0.000 |
| base_penalized | 0.795 | [0.728, 0.855] | 3.2423 | [2.9475, 3.4878] | 5.2812 | 0.000 |
| dpo_raw | 1.000 | [1.000, 1.000] | 3.6357 | [3.3791, 3.8531] | 4.5625 | 0.000 |
| dpo_penalized | 1.000 | [1.000, 1.000] | 6.6038 | [6.1360, 6.9970] | 9.5625 | 0.000 |
| dpo_reward | 1.000 | [1.000, 1.000] | 118.3174 | [113.0000, 123.0033] | 103.5000 | 0.000 |

| paired comparison | delta accuracy | accuracy delta 95% CI | delta mean margin | margin delta 95% CI |
|---|---:|---:|---:|---:|
| dpo_raw_minus_base_raw | 0.205 | [0.145, 0.272] | 3.3615 | [3.1824, 3.5128] |
| base_penalized_minus_base_raw | 0.000 | [0.000, 0.000] | 2.9680 | [2.7358, 3.1556] |
| dpo_penalized_minus_base_penalized | 0.205 | [0.145, 0.272] | 3.3615 | [3.1824, 3.5128] |

## Acceptance Checks

- DPO raw improves the primary subset: `True`
- DPO with the same penalty improves the primary subset: `True`
- DPO implicit reward has a positive primary margin: `True`
