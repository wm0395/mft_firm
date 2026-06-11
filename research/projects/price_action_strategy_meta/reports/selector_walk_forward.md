# Walk-Forward Gate

## Protocol

- Horizon: `5d`.
- Split sizes: train `1260`, test `252`, step `1260`.
- Split families: walk-forward, purged lookahead `5`, and embargo `5`.
- Strategy pool: the base screen plus the supplemental first-principles extras, so the fold refit sees the broader trend, reversal, structure, and regime set.
- The selector is refit on each training fold using the same candidate scan as the gate prototype, then filtered by the consensus support floor.
- Family alignment bonus: reversal is favored in high-vol, bear, risk-off, gap-shock, and deep-drawdown states; trend is favored in bull and risk-on states; low-liquidity states are penalized.
- This is the missing leakage-control layer for the selector gate.

## Split Summary

| split_type | folds | train_precision | test_precision | test_coverage | test_mean_net_bps | baseline_mean_net_bps | lift_vs_baseline_bps |
| --- | --- | --- | --- | --- | --- | --- | --- |
| embargo | 5 | 0.635 | 0.714 | 0.008 | 0.412 | 2.367 | -1.955 |
| purged | 5 | 0.635 | 0.714 | 0.008 | 0.412 | 2.538 | -2.126 |
| walk_forward | 5 | 0.635 | 0.714 | 0.008 | 0.412 | 2.538 | -2.126 |

## Fold Detail

| split_type | fold | policy | train_start | train_end | test_start | test_end | train_precision | train_coverage | train_mean_net_bps | test_precision | test_coverage | test_mean_net_bps | baseline_mean_net_bps | lift_vs_baseline_bps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| embargo | 1 | abstain | 1996-01-01 | 2000-10-27 | 2000-11-06 | 2001-10-23 | nan | 0.000 | 0.000 | nan | 0.000 | 0.000 | 0.000 | 0.000 |
| embargo | 2 | abstain | 2000-10-30 | 2005-09-02 | 2005-09-13 | 2006-09-18 | nan | 0.000 | 0.000 | nan | 0.000 | 0.000 | 1.478 | -1.478 |
| embargo | 3 | abstain | 2005-09-05 | 2010-10-12 | 2010-10-20 | 2011-10-24 | nan | 0.000 | 0.000 | nan | 0.000 | 0.000 | 2.953 | -2.953 |
| embargo | 4 | abstain | 2010-10-13 | 2015-11-20 | 2015-12-01 | 2016-12-08 | nan | 0.000 | 0.000 | nan | 0.000 | 0.000 | 0.305 | -0.305 |
| embargo | 5 | strict | 2015-11-23 | 2020-12-30 | 2021-01-07 | 2022-01-12 | 0.635 | 0.213 | 24.929 | 0.714 | 0.042 | 2.060 | 7.099 | -5.039 |
| purged | 1 | abstain | 1996-01-01 | 2000-10-20 | 2000-10-30 | 2001-10-16 | nan | 0.000 | 0.000 | nan | 0.000 | 0.000 | 0.000 | 0.000 |
| purged | 2 | abstain | 2000-10-30 | 2005-08-26 | 2005-09-05 | 2006-09-11 | nan | 0.000 | 0.000 | nan | 0.000 | 0.000 | 1.478 | -1.478 |
| purged | 3 | abstain | 2005-09-05 | 2010-10-05 | 2010-10-13 | 2011-10-17 | nan | 0.000 | 0.000 | nan | 0.000 | 0.000 | 3.810 | -3.810 |
| purged | 4 | abstain | 2010-10-13 | 2015-11-13 | 2015-11-23 | 2016-12-01 | nan | 0.000 | 0.000 | nan | 0.000 | 0.000 | 0.305 | -0.305 |
| purged | 5 | strict | 2015-11-23 | 2020-12-22 | 2020-12-31 | 2022-01-05 | 0.635 | 0.214 | 25.028 | 0.714 | 0.042 | 2.060 | 7.099 | -5.039 |
| walk_forward | 1 | abstain | 1996-01-01 | 2000-10-27 | 2000-10-30 | 2001-10-16 | nan | 0.000 | 0.000 | nan | 0.000 | 0.000 | 0.000 | 0.000 |
| walk_forward | 2 | abstain | 2000-10-30 | 2005-09-02 | 2005-09-05 | 2006-09-11 | nan | 0.000 | 0.000 | nan | 0.000 | 0.000 | 1.478 | -1.478 |
| walk_forward | 3 | abstain | 2005-09-05 | 2010-10-12 | 2010-10-13 | 2011-10-17 | nan | 0.000 | 0.000 | nan | 0.000 | 0.000 | 3.810 | -3.810 |
| walk_forward | 4 | abstain | 2010-10-13 | 2015-11-20 | 2015-11-23 | 2016-12-01 | nan | 0.000 | 0.000 | nan | 0.000 | 0.000 | 0.305 | -0.305 |
| walk_forward | 5 | strict | 2015-11-23 | 2020-12-30 | 2020-12-31 | 2022-01-05 | 0.635 | 0.213 | 24.929 | 0.714 | 0.042 | 2.060 | 7.099 | -5.039 |

## Regime Holdout

| split_type | regime_dimension | regime_state | mean_net_bps | precision | coverage | active_obs | total_obs | tstat |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| embargo | gap_state | down_gap_shock | 139.492 | 1.000 | 0.007 | 1 | 184 | nan |
| purged | gap_state | down_gap_shock | 139.492 | 1.000 | 0.007 | 1 | 183 | nan |
| walk_forward | gap_state | down_gap_shock | 139.492 | 1.000 | 0.007 | 1 | 183 | nan |
| embargo | liquidity_state | normal_liquidity | 112.589 | 0.750 | 0.014 | 12 | 735 | 1.544 |
| purged | liquidity_state | normal_liquidity | 112.589 | 0.750 | 0.014 | 12 | 735 | 1.544 |
| walk_forward | liquidity_state | normal_liquidity | 112.589 | 0.750 | 0.014 | 12 | 735 | 1.544 |
| walk_forward | gap_state | calm | 66.661 | 0.737 | 0.010 | 19 | 1927 | 1.231 |
| purged | gap_state | calm | 66.661 | 0.737 | 0.010 | 19 | 1927 | 1.231 |
| embargo | gap_state | calm | 66.661 | 0.737 | 0.010 | 19 | 1919 | 1.231 |
| embargo | risk_state | mixed | 49.441 | 0.714 | 0.009 | 21 | 2348 | 0.930 |
| embargo | vol_state | low_vol | 49.441 | 0.714 | 0.029 | 21 | 971 | 0.930 |
| embargo | trend_state | bull | 49.441 | 0.714 | 0.011 | 21 | 1169 | 0.930 |
| embargo | breadth_state | neutral | 49.441 | 0.714 | 0.011 | 21 | 1356 | 0.930 |
| embargo | drawdown_state | shallow_drawdown | 49.441 | 0.714 | 0.011 | 21 | 777 | 0.930 |
| walk_forward | trend_state | bull | 49.441 | 0.714 | 0.011 | 21 | 1183 | 0.930 |
| walk_forward | vol_state | low_vol | 49.441 | 0.714 | 0.029 | 21 | 1001 | 0.930 |
| purged | breadth_state | neutral | 49.441 | 0.714 | 0.011 | 21 | 1355 | 0.930 |
| purged | drawdown_state | shallow_drawdown | 49.441 | 0.714 | 0.011 | 21 | 799 | 0.930 |
| walk_forward | breadth_state | neutral | 49.441 | 0.714 | 0.011 | 21 | 1355 | 0.930 |
| purged | risk_state | mixed | 49.441 | 0.714 | 0.009 | 21 | 2354 | 0.930 |

## Takeaway

- All three split families remain below the combined always-on baseline on average.
- Only fold 5 activates; folds 1-4 abstain, so the scan is not persistent across time.
- Embargo remains negative on fold 5, so the selector stays research-only.