# DPO Pairwise Margin Diagnostic

Positioning: candidate-level adapter-on/off diagnostic; not an end-to-end generalization result.

Pairs: 219 across 77 error contexts
Give-up sensitivity penalty: -5.0

## success_over_failure

Pairs: 154 | Contexts: 77

| scorer | accuracy | accuracy 95% CI | mean margin | margin 95% CI | median margin | ties |
|---|---:|---:|---:|---:|---:|---:|
| base_raw | 0.740 | [0.656, 0.821] | 0.3384 | [0.2561, 0.4130] | 0.0938 | 0.013 |
| base_penalized | 0.740 | [0.656, 0.821] | 2.4488 | [2.1537, 2.7086] | 0.0938 | 0.013 |
| dpo_raw | 1.000 | [1.000, 1.000] | 3.0449 | [2.8305, 3.2433] | 1.8516 | 0.000 |
| dpo_penalized | 1.000 | [1.000, 1.000] | 5.1553 | [4.7353, 5.5311] | 1.8516 | 0.000 |
| dpo_reward | 1.000 | [1.000, 1.000] | 106.6526 | [101.4416, 111.7825] | 101.5000 | 0.000 |

| paired comparison | delta accuracy | accuracy delta 95% CI | delta mean margin | margin delta 95% CI |
|---|---:|---:|---:|---:|
| dpo_raw_minus_base_raw | 0.260 | [0.179, 0.344] | 2.7065 | [2.5647, 2.8413] |
| base_penalized_minus_base_raw | 0.000 | [0.000, 0.000] | 2.1104 | [1.8831, 2.3052] |
| dpo_penalized_minus_base_penalized | 0.260 | [0.179, 0.344] | 2.7065 | [2.5647, 2.8413] |

## executable_failure_over_give_up

Pairs: 65 | Contexts: 65

| scorer | accuracy | accuracy 95% CI | mean margin | margin 95% CI | median margin | ties |
|---|---:|---:|---:|---:|---:|---:|
| base_raw | 1.000 | [1.000, 1.000] | 0.9316 | [0.8742, 0.9864] | 1.0000 | 0.000 |
| base_penalized | 1.000 | [1.000, 1.000] | 5.9316 | [5.8742, 5.9864] | 6.0000 | 0.000 |
| dpo_raw | 1.000 | [1.000, 1.000] | 4.2099 | [4.1159, 4.3043] | 4.1562 | 0.000 |
| dpo_penalized | 1.000 | [1.000, 1.000] | 9.2099 | [9.1159, 9.3043] | 9.1562 | 0.000 |
| dpo_reward | 1.000 | [1.000, 1.000] | 80.6462 | [78.1846, 83.0154] | 82.0000 | 0.000 |

| paired comparison | delta accuracy | accuracy delta 95% CI | delta mean margin | margin delta 95% CI |
|---|---:|---:|---:|---:|
| dpo_raw_minus_base_raw | 0.000 | [0.000, 0.000] | 3.2782 | [3.2249, 3.3328] |
| base_penalized_minus_base_raw | 0.000 | [0.000, 0.000] | 5.0000 | [5.0000, 5.0000] |
| dpo_penalized_minus_base_penalized | 0.000 | [0.000, 0.000] | 3.2782 | [3.2249, 3.3328] |

## all

Pairs: 219 | Contexts: 77

| scorer | accuracy | accuracy 95% CI | mean margin | margin 95% CI | median margin | ties |
|---|---:|---:|---:|---:|---:|---:|
| base_raw | 0.817 | [0.750, 0.877] | 0.5145 | [0.4369, 0.5813] | 0.6172 | 0.009 |
| base_penalized | 0.817 | [0.750, 0.877] | 3.4825 | [3.1935, 3.7242] | 5.6172 | 0.009 |
| dpo_raw | 1.000 | [1.000, 1.000] | 3.3907 | [3.2129, 3.5451] | 3.9844 | 0.000 |
| dpo_penalized | 1.000 | [1.000, 1.000] | 6.3587 | [5.9626, 6.6883] | 8.9844 | 0.000 |
| dpo_reward | 1.000 | [1.000, 1.000] | 98.9338 | [95.6621, 102.1284] | 84.5000 | 0.000 |

| paired comparison | delta accuracy | accuracy delta 95% CI | delta mean margin | margin delta 95% CI |
|---|---:|---:|---:|---:|
| dpo_raw_minus_base_raw | 0.183 | [0.123, 0.250] | 2.8762 | [2.7652, 2.9736] |
| base_penalized_minus_base_raw | 0.000 | [0.000, 0.000] | 2.9680 | [2.7358, 3.1556] |
| dpo_penalized_minus_base_penalized | 0.183 | [0.123, 0.250] | 2.8762 | [2.7652, 2.9736] |

## Acceptance Checks

- DPO raw improves the primary subset: `True`
- DPO with the same penalty improves the primary subset: `True`
- DPO implicit reward has a positive primary margin: `True`
