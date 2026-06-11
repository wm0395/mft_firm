# Selector Gate

## Protocol

- Train/test cutoff date: `2017-02-14`
- Horizon: `5d` only; that is where the first-pass screen found the durable positive pocket.
- Split: first `70%` of dates train, remaining `30%` test.
- Selector job: choose one strategy or abstain.
- Strategy pool: the base screen plus the supplemental first-principles extras, including trend, reversal, structure, and regime helpers.
- Confidence gate: a strategy must match at least two regime dimensions, clear a score threshold derived from positive train-set regime cells, and be supported by multiple strategies on the same day.
- Family alignment bonus: reversal is favored in high-vol, bear, risk-off, gap-shock, and deep-drawdown states; trend is favored in bull and risk-on states; low-liquidity states are penalized.
- Costs: 10 bps already embedded in the strategy return series.

## Candidate Scan

| policy | min_mean_net_bps | min_win_rate | min_tstat | min_obs | min_matches | min_score | min_support | train_precision | train_coverage | train_active_days | train_mean_net_bps | test_precision | test_coverage | test_active_days | test_mean_net_bps | test_portfolio_mean_net_bps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| loose | 20.000 | 0.520 | 1.000 | 50 | 2 | 2.000 | 1 | 0.591 | 0.025 | 269.000 | 78.265 | 0.549 | 0.176 | 805.000 | 34.758 | 6.109 |
| high_conf | 30.000 | 0.540 | 1.250 | 100 | 2 | 2.500 | 2 | 0.590 | 0.025 | 268.000 | 64.736 | 0.548 | 0.174 | 796.000 | 26.262 | 4.564 |
| balanced | 25.000 | 0.530 | 1.000 | 100 | 2 | 2.250 | 2 | 0.569 | 0.025 | 269.000 | 50.206 | 0.541 | 0.174 | 799.000 | 30.316 | 5.289 |

## Chosen Policy

- Chosen policy: `loose`
- Train precision: `0.591`
- Train coverage: `0.025`
- Test precision: `0.549`
- Test coverage: `0.176`
- Test active days: `805`
- Min support: `1` strategies

| universe | strategy | family | dimension | state | mean_net_bps | win_rate | tstat | obs | weight |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nifty500 | bollinger_percent_b_mean_reversion_20 | reversal_exhaustion | breadth_state | bearish | 62.487 | 0.592 | 1.471 | 71 | 1.993 |
| nifty500 | bollinger_percent_b_mean_reversion_20 | reversal_exhaustion | breadth_state | neutral | 39.624 | 0.562 | 1.444 | 169 | 1.757 |
| nifty500 | bollinger_percent_b_mean_reversion_20 | reversal_exhaustion | drawdown_state | deep_drawdown | 115.555 | 0.667 | 3.697 | 96 | 3.080 |
| nifty500 | bollinger_percent_b_mean_reversion_20 | reversal_exhaustion | drawdown_state | shallow_drawdown | 53.661 | 0.592 | 1.479 | 120 | 1.906 |
| nifty500 | bollinger_percent_b_mean_reversion_20 | reversal_exhaustion | gap_state | calm | 42.214 | 0.580 | 1.686 | 212 | 1.844 |
| nifty500 | bollinger_percent_b_mean_reversion_20 | reversal_exhaustion | liquidity_state | high_liquidity | 80.903 | 0.603 | 2.641 | 151 | 2.469 |
| nifty500 | bollinger_percent_b_mean_reversion_20 | reversal_exhaustion | risk_state | mixed | 55.446 | 0.576 | 2.449 | 255 | 2.167 |
| nifty500 | bollinger_percent_b_mean_reversion_20 | reversal_exhaustion | trend_state | sideways | 95.254 | 0.644 | 3.280 | 118 | 2.772 |
| nifty500 | bollinger_percent_b_mean_reversion_20 | reversal_exhaustion | trend_state | bull | 33.757 | 0.541 | 1.035 | 146 | 1.596 |
| nifty500 | bollinger_percent_b_mean_reversion_20 | reversal_exhaustion | vol_state | high_vol | 130.871 | 0.636 | 4.079 | 118 | 3.328 |
| nifty500 | bollinger_percent_b_mean_reversion_20 | reversal_exhaustion | vol_state | low_vol | 53.636 | 0.631 | 1.226 | 65 | 1.843 |
| nifty500 | choppiness_inverse_14 | trend_following | breadth_state | neutral | 54.379 | 0.568 | 2.253 | 169 | 2.107 |
| nifty500 | choppiness_inverse_14 | trend_following | breadth_state | bearish | 45.871 | 0.521 | 1.247 | 71 | 1.771 |
| nifty500 | choppiness_inverse_14 | trend_following | drawdown_state | deep_drawdown | 55.873 | 0.562 | 1.623 | 96 | 1.964 |
| nifty500 | choppiness_inverse_14 | trend_following | drawdown_state | shallow_drawdown | 43.165 | 0.550 | 1.389 | 120 | 1.779 |
| nifty500 | choppiness_inverse_14 | trend_following | gap_state | calm | 42.392 | 0.552 | 1.970 | 212 | 1.917 |
| nifty500 | choppiness_inverse_14 | trend_following | liquidity_state | high_liquidity | 72.945 | 0.589 | 2.608 | 151 | 2.381 |
| nifty500 | choppiness_inverse_14 | trend_following | risk_state | mixed | 50.935 | 0.553 | 2.550 | 255 | 2.147 |
| nifty500 | choppiness_inverse_14 | trend_following | trend_state | sideways | 65.879 | 0.576 | 2.298 | 118 | 2.233 |
| nifty500 | choppiness_inverse_14 | trend_following | vol_state | low_vol | 69.657 | 0.615 | 1.974 | 65 | 2.190 |

## Test Backtest

| universe | active_days | coverage | precision | active_mean_net_bps | portfolio_mean_net_bps | portfolio_median_net_bps | portfolio_sharpe_like | portfolio_max_drawdown_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| combined | 805.000 | 0.176 | 0.549 | 34.758 | 6.109 | 0.000 | 2.648 | -88.210 |
| expanded | 0.000 | 0.000 | nan | nan | 0.000 | 0.000 | nan | 0.000 |
| nifty500 | 805.000 | 0.352 | 0.549 | 34.758 | 12.218 | 0.000 | 2.650 | -88.210 |

Comparison against the combined always-on baseline:

| universe | best_always_on | best_always_on_mean_net_bps | always_flat_mean_net_bps | always_flat_precision | test_mean_net_bps |
| --- | --- | --- | --- | --- | --- |
| nifty500 | stochastic_mean_reversion_14 | 55.775 | 0.000 | nan | 19.607 |
| expanded | breakout_20 | nan | 0.000 | nan | 0.000 |
| combined | per-universe_best | 9.803 | 0.000 | nan | 9.803 |

## Class Context

| regime_state | obs | mean_net_bps | median_net_bps | win_rate | tstat | universe | horizon | sector | regime_dimension |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| risk_off | 89 | 435.680 | 157.326 | 0.562 | 3.021 | expanded | 5 | Construction | risk_state |
| risk_off | 104 | 311.420 | 272.033 | 0.615 | 2.907 | expanded | 5 | Chemicals | risk_state |
| risk_off | 49 | 283.754 | 212.948 | 0.612 | 2.593 | nifty500 | 5 | Healthcare | risk_state |
| risk_off | 20 | 278.291 | 172.999 | 0.550 | 1.854 | expanded | 5 | Healthcare | risk_state |
| risk_on | 108 | 277.547 | 120.612 | 0.574 | 3.569 | expanded | 5 | Healthcare | risk_state |

| regime_state | obs | mean_net_bps | median_net_bps | win_rate | tstat | universe | horizon | liquidity_class | regime_dimension |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| risk_on | 166 | 195.253 | 112.477 | 0.669 | 5.482 | expanded | 5 | very_low | risk_state |
| risk_off | 98 | 193.577 | 185.879 | 0.582 | 2.140 | expanded | 5 | very_low | risk_state |
| risk_on | 269 | 189.082 | 192.422 | 0.714 | 8.263 | nifty500 | 5 | very_low | risk_state |
| bullish | 458 | 173.211 | 114.184 | 0.609 | 5.637 | nifty500 | 5 | very_high | breadth_state |
| bullish | 253 | 170.663 | 66.436 | 0.585 | 4.291 | expanded | 5 | mid | breadth_state |

## Takeaway

- The chosen `loose` policy is sparse, but it still loses to the combined always-on baseline on the current holdout.
- The stricter `high_conf` policy is lower, and the looser scan variants still remain below the combined always-on baseline.
- Activity is concentrated in `nifty500` and a few rules, which is evidence of a narrow pocket rather than a durable all-regime selector.
- The gate stays research-only until holdout and embargo both clear the always-on baseline after costs.
