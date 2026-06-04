# Walk-Forward Gate

## Protocol

- Horizon: `5d`.
- Split sizes: train `1260`, test `252`, step `1260`.
- Split families: walk-forward, purged lookahead `5`, and embargo `5`.
- The selector is refit on each training fold using the same candidate scan as the gate prototype, then filtered by the consensus support floor.
- This is the missing leakage-control layer for the selector gate.

## Split Summary

| split_type | folds | train_precision | test_precision | test_coverage | test_mean_net_bps | baseline_mean_net_bps | lift_vs_baseline_bps |
| --- | --- | --- | --- | --- | --- | --- | --- |
| purged | 5 | 0.611 | 0.534 | 0.224 | 10.919 | 26.907 | -15.988 |
| embargo | 5 | 0.610 | 0.509 | 0.168 | 5.912 | 26.982 | -21.070 |
| walk_forward | 5 | 0.610 | 0.506 | 0.169 | 5.771 | 26.907 | -21.136 |

## Fold Detail

| split_type | fold | policy | train_start | train_end | test_start | test_end | train_precision | train_coverage | train_mean_net_bps | test_precision | test_coverage | test_mean_net_bps | baseline_mean_net_bps | lift_vs_baseline_bps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| embargo | 1 | abstain | 1996-01-01 | 2000-10-27 | 2000-11-06 | 2001-10-23 | nan | 0.000 | 0.000 | nan | 0.000 | 0.000 | 0.000 | 0.000 |
| embargo | 2 | high_conf | 2000-10-30 | 2005-09-02 | 2005-09-13 | 2006-09-18 | 0.582 | 0.089 | 10.197 | 0.496 | 0.536 | 11.960 | 20.920 | -8.961 |
| embargo | 3 | ultra_strict_3 | 2005-09-05 | 2010-10-12 | 2010-10-20 | 2011-10-24 | 0.654 | 0.119 | 16.851 | 0.448 | 0.058 | -0.930 | 35.194 | -36.124 |
| embargo | 4 | strict | 2010-10-13 | 2015-11-20 | 2015-12-01 | 2016-12-08 | 0.603 | 0.081 | 6.923 | 0.660 | 0.099 | 25.583 | 61.730 | -36.147 |
| embargo | 5 | high_conf | 2015-11-23 | 2020-12-30 | 2021-01-07 | 2022-01-12 | 0.602 | 0.368 | 36.845 | 0.432 | 0.147 | -7.053 | 17.068 | -24.120 |
| purged | 1 | abstain | 1996-01-01 | 2000-10-20 | 2000-10-30 | 2001-10-16 | nan | 0.000 | 0.000 | nan | 0.000 | 0.000 | 0.000 | 0.000 |
| purged | 2 | balanced | 2000-10-30 | 2005-08-26 | 2005-09-05 | 2006-09-11 | 0.578 | 0.140 | 13.948 | 0.526 | 0.728 | 16.100 | 21.222 | -5.122 |
| purged | 3 | ultra_strict_3 | 2005-09-05 | 2010-10-05 | 2010-10-13 | 2011-10-17 | 0.654 | 0.120 | 16.918 | 0.464 | 0.056 | -0.675 | 34.889 | -35.564 |
| purged | 4 | strict | 2010-10-13 | 2015-11-13 | 2015-11-23 | 2016-12-01 | 0.605 | 0.080 | 7.373 | 0.623 | 0.105 | 23.786 | 59.895 | -36.109 |
| purged | 5 | loose | 2015-11-23 | 2020-12-22 | 2020-12-31 | 2022-01-05 | 0.605 | 0.546 | 51.507 | 0.521 | 0.232 | 15.384 | 18.529 | -3.146 |
| walk_forward | 1 | abstain | 1996-01-01 | 2000-10-27 | 2000-10-30 | 2001-10-16 | nan | 0.000 | 0.000 | nan | 0.000 | 0.000 | 0.000 | 0.000 |
| walk_forward | 2 | high_conf | 2000-10-30 | 2005-09-02 | 2005-09-05 | 2006-09-11 | 0.582 | 0.089 | 10.197 | 0.504 | 0.536 | 12.798 | 21.222 | -8.424 |
| walk_forward | 3 | ultra_strict_3 | 2005-09-05 | 2010-10-12 | 2010-10-13 | 2011-10-17 | 0.654 | 0.119 | 16.851 | 0.464 | 0.056 | -0.675 | 34.889 | -35.564 |
| walk_forward | 4 | strict | 2010-10-13 | 2015-11-20 | 2015-11-23 | 2016-12-01 | 0.603 | 0.081 | 6.923 | 0.623 | 0.105 | 23.786 | 59.895 | -36.109 |
| walk_forward | 5 | high_conf | 2015-11-23 | 2020-12-30 | 2020-12-31 | 2022-01-05 | 0.602 | 0.368 | 36.845 | 0.432 | 0.147 | -7.053 | 18.529 | -25.582 |

## Regime Holdout

| split_type | regime_dimension | regime_state | mean_net_bps | precision | coverage | active_obs | total_obs | tstat |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| purged | risk_state | risk_off | 372.800 | 1.000 | 0.143 | 2 | 99 | 5.649 |
| purged | gap_state | up_gap_shock | 249.580 | 0.532 | 0.210 | 51 | 288 | 1.025 |
| walk_forward | risk_state | risk_on | 236.345 | 0.697 | 0.134 | 72 | 347 | 0.318 |
| embargo | risk_state | risk_on | 233.056 | 0.685 | 0.132 | 73 | 353 | 0.253 |
| walk_forward | breadth_state | bullish | 228.039 | 0.707 | 0.152 | 102 | 545 | 1.067 |
| purged | trend_state | bear | 177.324 | 0.727 | 0.159 | 14 | 408 | 2.626 |
| embargo | breadth_state | bullish | 166.931 | 0.583 | 0.158 | 104 | 545 | 1.035 |
| purged | breadth_state | bullish | 124.583 | 0.592 | 0.218 | 146 | 545 | 0.921 |
| purged | vol_state | high_vol | 104.806 | 0.651 | 0.314 | 258 | 702 | 1.410 |
| purged | breadth_state | neutral | 101.067 | 0.591 | 0.236 | 305 | 1206 | 1.112 |
| purged | liquidity_state | high_liquidity | 98.023 | 0.537 | 0.077 | 116 | 654 | 0.843 |
| walk_forward | gap_state | up_gap_shock | 90.770 | 0.536 | 0.112 | 27 | 288 | 0.970 |
| embargo | gap_state | up_gap_shock | 90.770 | 0.536 | 0.110 | 27 | 293 | 0.970 |
| purged | risk_state | risk_on | 82.624 | 0.531 | 0.172 | 93 | 347 | 0.727 |
| purged | vol_state | normal_vol | 79.133 | 0.509 | 0.182 | 155 | 955 | 0.334 |
| purged | trend_state | bull | 78.263 | 0.525 | 0.203 | 327 | 1062 | 0.091 |
| purged | risk_state | mixed | 77.780 | 0.574 | 0.234 | 470 | 2074 | 1.152 |
| walk_forward | trend_state | bull | 75.727 | 0.526 | 0.171 | 271 | 1062 | -0.111 |
| embargo | trend_state | bull | 74.901 | 0.523 | 0.171 | 271 | 1052 | -0.151 |
| purged | gap_state | calm | 62.938 | 0.531 | 0.227 | 495 | 2055 | 0.845 |

## Takeaway

- The gate is only meaningful if the lift over the combined always-on baseline persists across all split families.
- Regime holdout rows show whether the gate still concentrates activity in the same high-vol, bear, risk-off, and gap-shock states after leakage control.
- The adaptive threshold scan still needs positive leakage-controlled lift before the selector can move beyond research-only status.