# DPO Controlled Smoke v1

Positioning: fixed candidate-ranking smoke test; not a broad generalization result.

Contexts: 32 (24 recoverable, 8 unrecoverable)
Candidate pools: 56
Manifest SHA256: `0c0bc7fa26d5a0968ce220c60b6e2c4484bc7ce4882c6fdf099c4cd77425b772`

## all

| scorer | pools | top-1 success | pairwise success>failure | first-success rank | give-up rate | abstention accuracy |
|---|---:|---:|---:|---:|---:|---:|
| base_raw | 56 | 0.500 | 0.792 | 1.625 | 0.000 | 0.000 |
| base_penalized | 56 | 0.500 | 0.792 | 1.625 | 0.000 | 0.000 |
| dpo_raw | 56 | 0.750 | 0.875 | 1.375 | 0.000 | 0.000 |
| dpo_penalized | 56 | 0.750 | 0.875 | 1.375 | 0.000 | 0.000 |
| dpo_reward | 56 | 0.375 | 0.694 | 1.917 | 0.000 | 0.000 |

## canonical

| scorer | pools | top-1 success | pairwise success>failure | first-success rank | give-up rate | abstention accuracy |
|---|---:|---:|---:|---:|---:|---:|
| base_raw | 24 | 0.500 | 0.833 | 1.500 | 0.000 | 0.000 |
| base_penalized | 24 | 0.500 | 0.833 | 1.500 | 0.000 | 0.000 |
| dpo_raw | 24 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 |
| dpo_penalized | 24 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 |
| dpo_reward | 24 | 0.750 | 0.917 | 1.250 | 0.000 | 0.000 |

## paraphrased

| scorer | pools | top-1 success | pairwise success>failure | first-success rank | give-up rate | abstention accuracy |
|---|---:|---:|---:|---:|---:|---:|
| base_raw | 24 | 0.500 | 0.750 | 1.750 | 0.000 | 0.000 |
| base_penalized | 24 | 0.500 | 0.750 | 1.750 | 0.000 | 0.000 |
| dpo_raw | 24 | 0.500 | 0.750 | 1.750 | 0.000 | 0.000 |
| dpo_penalized | 24 | 0.500 | 0.750 | 1.750 | 0.000 | 0.000 |
| dpo_reward | 24 | 0.000 | 0.472 | 2.583 | 0.000 | 0.000 |

## unrecoverable_controls

| scorer | pools | top-1 success | pairwise success>failure | first-success rank | give-up rate | abstention accuracy |
|---|---:|---:|---:|---:|---:|---:|
| base_raw | 8 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| base_penalized | 8 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| dpo_raw | 8 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| dpo_penalized | 8 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| dpo_reward | 8 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## Paired Top-1 Comparisons

| comparison | disagreements | left-only success | right-only success | left-only correct abstention | right-only correct abstention |
|---|---:|---:|---:|---:|---:|
| dpo_raw_vs_base_raw | 18 | 12 | 0 | 0 | 0 |
| base_penalized_vs_base_raw | 0 | 0 | 0 | 0 | 0 |
| dpo_penalized_vs_base_penalized | 18 | 12 | 0 | 0 | 0 |
| dpo_reward_vs_base_raw | 38 | 12 | 18 | 0 | 0 |
