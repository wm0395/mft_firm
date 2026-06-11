# Observable Regime Gate

## Protocol

- Universe: `nifty500` only for the minimal classifier test.
- Stress rule: at least 2 of 3 are true: `high_vol`, `bearish breadth`, `drawdown <= -10%`.
- Family under test: `reversal_exhaustion` only.
- Strategy choice is train-only within each universe and split fold.
- Costs: 10 bps are already embedded in the daily strategy returns.
- Validation includes holdout, walk-forward, purged, and embargo splits.

## Split Summary

| split_type | fold | universe | family | strategy | train_active_days | train_precision | train_mean_net_bps | test_active_days | test_precision | test_coverage | test_mean_net_bps | baseline_mean_net_bps | lift_vs_baseline_bps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| walk_forward | 1 | nifty500 | reversal_exhaustion | None | 0 | nan | nan | 0 | nan | 0.000 | 0.000 | 0.000 | 0.000 |
| purged | 1 | nifty500 | reversal_exhaustion | None | 0 | nan | nan | 0 | nan | 0.000 | 0.000 | 0.000 | 0.000 |
| embargo | 1 | nifty500 | reversal_exhaustion | None | 0 | nan | nan | 0 | nan | 0.000 | 0.000 | 0.000 | 0.000 |
| walk_forward | 3 | nifty500 | reversal_exhaustion | fisher_transform_reversal_10 | 21 | 0.714 | 247.047 | 4 | 0.750 | 0.016 | 2.456 | 4.039 | -1.583 |
| purged | 3 | nifty500 | reversal_exhaustion | fisher_transform_reversal_10 | 21 | 0.714 | 247.047 | 4 | 0.750 | 0.016 | 2.456 | 4.039 | -1.583 |
| embargo | 3 | nifty500 | reversal_exhaustion | fisher_transform_reversal_10 | 21 | 0.714 | 247.047 | 5 | 0.800 | 0.020 | 4.322 | 5.905 | -1.583 |
| holdout | 0 | nifty500 | reversal_exhaustion | fisher_transform_reversal_10 | 74 | 0.662 | 146.760 | 261 | 0.667 | 0.114 | 15.278 | 19.607 | -4.329 |
| walk_forward | 2 | nifty500 | reversal_exhaustion | None | 0 | nan | nan | 0 | nan | 0.000 | 0.000 | 9.315 | -9.315 |
| purged | 2 | nifty500 | reversal_exhaustion | None | 0 | nan | nan | 0 | nan | 0.000 | 0.000 | 9.315 | -9.315 |
| embargo | 2 | nifty500 | reversal_exhaustion | None | 0 | nan | nan | 0 | nan | 0.000 | 0.000 | 9.315 | -9.315 |
| embargo | 5 | nifty500 | reversal_exhaustion | stochastic_mean_reversion_14 | 217 | 0.687 | 195.958 | 0 | nan | 0.000 | 0.000 | 16.608 | -16.608 |
| walk_forward | 5 | nifty500 | reversal_exhaustion | stochastic_mean_reversion_14 | 217 | 0.687 | 195.958 | 0 | nan | 0.000 | 0.000 | 16.608 | -16.608 |
| purged | 5 | nifty500 | reversal_exhaustion | stochastic_mean_reversion_14 | 217 | 0.687 | 195.958 | 0 | nan | 0.000 | 0.000 | 16.608 | -16.608 |
| walk_forward | 4 | nifty500 | reversal_exhaustion | ultimate_oscillator_reversal | 21 | 0.619 | 89.209 | 27 | 0.148 | 0.107 | -30.185 | 0.610 | -30.795 |
| purged | 4 | nifty500 | reversal_exhaustion | ultimate_oscillator_reversal | 21 | 0.619 | 89.209 | 27 | 0.148 | 0.107 | -30.185 | 0.610 | -30.795 |
| embargo | 4 | nifty500 | reversal_exhaustion | ultimate_oscillator_reversal | 21 | 0.619 | 89.209 | 29 | 0.172 | 0.115 | -31.855 | 0.610 | -32.465 |

## Candidate Scan

| strategy | family | train_signal_days | train_signal_mean_net_bps | train_signal_precision | split_type | fold | universe | chosen_strategy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fisher_transform_reversal_10 | reversal_exhaustion | 21 | 247.047 | 0.714 | purged | 3 | nifty500 | fisher_transform_reversal_10 |
| fisher_transform_reversal_10 | reversal_exhaustion | 21 | 247.047 | 0.714 | walk_forward | 3 | nifty500 | fisher_transform_reversal_10 |
| fisher_transform_reversal_10 | reversal_exhaustion | 21 | 247.047 | 0.714 | embargo | 3 | nifty500 | fisher_transform_reversal_10 |
| inverse_fisher_rsi_reversal_10 | reversal_exhaustion | 21 | 203.909 | 0.714 | purged | 3 | nifty500 | fisher_transform_reversal_10 |
| inverse_fisher_rsi_reversal_10 | reversal_exhaustion | 21 | 203.909 | 0.714 | walk_forward | 3 | nifty500 | fisher_transform_reversal_10 |
| inverse_fisher_rsi_reversal_10 | reversal_exhaustion | 21 | 203.909 | 0.714 | embargo | 3 | nifty500 | fisher_transform_reversal_10 |
| stochastic_mean_reversion_14 | reversal_exhaustion | 217 | 195.958 | 0.687 | purged | 5 | nifty500 | stochastic_mean_reversion_14 |
| williams_r_mean_reversion_14 | reversal_exhaustion | 217 | 195.958 | 0.687 | purged | 5 | nifty500 | stochastic_mean_reversion_14 |
| williams_r_mean_reversion_14 | reversal_exhaustion | 217 | 195.958 | 0.687 | embargo | 5 | nifty500 | stochastic_mean_reversion_14 |
| stochastic_mean_reversion_14 | reversal_exhaustion | 217 | 195.958 | 0.687 | embargo | 5 | nifty500 | stochastic_mean_reversion_14 |
| stochastic_mean_reversion_14 | reversal_exhaustion | 217 | 195.958 | 0.687 | walk_forward | 5 | nifty500 | stochastic_mean_reversion_14 |
| williams_r_mean_reversion_14 | reversal_exhaustion | 217 | 195.958 | 0.687 | walk_forward | 5 | nifty500 | stochastic_mean_reversion_14 |
| bollinger_percent_b_mean_reversion_20 | reversal_exhaustion | 21 | 190.474 | 0.714 | purged | 3 | nifty500 | fisher_transform_reversal_10 |
| bollinger_percent_b_mean_reversion_20 | reversal_exhaustion | 21 | 190.474 | 0.714 | embargo | 3 | nifty500 | fisher_transform_reversal_10 |
| bollinger_percent_b_mean_reversion_20 | reversal_exhaustion | 21 | 190.474 | 0.714 | walk_forward | 3 | nifty500 | fisher_transform_reversal_10 |
| fisher_transform_reversal_10 | reversal_exhaustion | 217 | 188.868 | 0.714 | embargo | 5 | nifty500 | stochastic_mean_reversion_14 |
| fisher_transform_reversal_10 | reversal_exhaustion | 217 | 188.868 | 0.714 | purged | 5 | nifty500 | stochastic_mean_reversion_14 |
| fisher_transform_reversal_10 | reversal_exhaustion | 217 | 188.868 | 0.714 | walk_forward | 5 | nifty500 | stochastic_mean_reversion_14 |
| williams_r_mean_reversion_14 | reversal_exhaustion | 21 | 188.588 | 0.667 | walk_forward | 3 | nifty500 | fisher_transform_reversal_10 |
| stochastic_mean_reversion_14 | reversal_exhaustion | 21 | 188.588 | 0.667 | embargo | 3 | nifty500 | fisher_transform_reversal_10 |

## Interpretation

- This is the memo's minimal classifier test: a causal stress rule with no composite scoring.
- If it fails embargo, the correct conclusion is that the current selector remains research-only.

## Decision

- `SUSPECT_OVERFIT`
- The causal 2-of-3 stress gate does not beat the always-on baseline on holdout or embargo, so it is not a deployable activation rule.