# DPO Pairwise Margin Diagnostic

Positioning: candidate-level adapter-on/off diagnostic; not an end-to-end generalization result.

Pairs: 192 across 64 error contexts
Give-up sensitivity penalty: -5.0

## success_over_failure

Pairs: 128 | Contexts: 64

| scorer | accuracy | accuracy 95% CI | mean margin | margin 95% CI | median margin | ties |
|---|---:|---:|---:|---:|---:|---:|
| base_raw | 0.738 | [0.676, 0.797] | 0.2085 | [0.1667, 0.2480] | 0.2188 | 0.008 |
| base_penalized | 0.738 | [0.676, 0.797] | 2.7085 | [2.6667, 2.7480] | 2.7617 | 0.008 |
| dpo_raw | 1.000 | [1.000, 1.000] | 3.8942 | [3.8636, 3.9238] | 3.9844 | 0.000 |
| dpo_penalized | 1.000 | [1.000, 1.000] | 6.3942 | [6.3636, 6.4238] | 6.4844 | 0.000 |
| dpo_reward | 1.000 | [1.000, 1.000] | 144.9297 | [144.1328, 145.7168] | 139.8750 | 0.000 |

| paired comparison | delta accuracy | accuracy delta 95% CI | delta mean margin | margin delta 95% CI |
|---|---:|---:|---:|---:|
| dpo_raw_minus_base_raw | 0.262 | [0.203, 0.324] | 3.6857 | [3.6700, 3.7008] |
| base_penalized_minus_base_raw | 0.000 | [0.000, 0.000] | 2.5000 | [2.5000, 2.5000] |
| dpo_penalized_minus_base_penalized | 0.262 | [0.203, 0.324] | 3.6857 | [3.6700, 3.7008] |

## executable_failure_over_give_up

Pairs: 64 | Contexts: 64

| scorer | accuracy | accuracy 95% CI | mean margin | margin 95% CI | median margin | ties |
|---|---:|---:|---:|---:|---:|---:|
| base_raw | 1.000 | [1.000, 1.000] | 0.4946 | [0.4518, 0.5350] | 0.5312 | 0.000 |
| base_penalized | 1.000 | [1.000, 1.000] | 5.4946 | [5.4518, 5.5350] | 5.5312 | 0.000 |
| dpo_raw | 1.000 | [1.000, 1.000] | 5.0635 | [4.9824, 5.1411] | 5.1406 | 0.000 |
| dpo_penalized | 1.000 | [1.000, 1.000] | 10.0635 | [9.9824, 10.1411] | 10.1406 | 0.000 |
| dpo_reward | 1.000 | [1.000, 1.000] | 138.0938 | [137.0703, 139.0898] | 138.7500 | 0.000 |

| paired comparison | delta accuracy | accuracy delta 95% CI | delta mean margin | margin delta 95% CI |
|---|---:|---:|---:|---:|
| dpo_raw_minus_base_raw | 0.000 | [0.000, 0.000] | 4.5688 | [4.5265, 4.6095] |
| base_penalized_minus_base_raw | 0.000 | [0.000, 0.000] | 5.0000 | [5.0000, 5.0000] |
| dpo_penalized_minus_base_penalized | 0.000 | [0.000, 0.000] | 4.5688 | [4.5265, 4.6095] |

## all

Pairs: 192 | Contexts: 64

| scorer | accuracy | accuracy 95% CI | mean margin | margin 95% CI | median margin | ties |
|---|---:|---:|---:|---:|---:|---:|
| base_raw | 0.826 | [0.784, 0.865] | 0.3039 | [0.2745, 0.3339] | 0.3281 | 0.005 |
| base_penalized | 0.826 | [0.784, 0.865] | 3.6372 | [3.6078, 3.6672] | 5.3164 | 0.005 |
| dpo_raw | 1.000 | [1.000, 1.000] | 4.2840 | [4.2527, 4.3151] | 5.1406 | 0.000 |
| dpo_penalized | 1.000 | [1.000, 1.000] | 7.6173 | [7.5861, 7.6484] | 10.1406 | 0.000 |
| dpo_reward | 1.000 | [1.000, 1.000] | 142.6510 | [141.8464, 143.4349] | 138.7500 | 0.000 |

| paired comparison | delta accuracy | accuracy delta 95% CI | delta mean margin | margin delta 95% CI |
|---|---:|---:|---:|---:|
| dpo_raw_minus_base_raw | 0.174 | [0.135, 0.216] | 3.9801 | [3.9646, 3.9952] |
| base_penalized_minus_base_raw | 0.000 | [0.000, 0.000] | 3.3333 | [3.3333, 3.3333] |
| dpo_penalized_minus_base_penalized | 0.174 | [0.135, 0.216] | 3.9801 | [3.9646, 3.9952] |

## Acceptance Checks

- DPO raw improves the primary subset: `True`
- DPO with the same penalty improves the primary subset: `True`
- DPO implicit reward has a positive primary margin: `True`
