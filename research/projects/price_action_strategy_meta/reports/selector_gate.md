# Selector Gate

## Protocol

- Train/test cutoff date: `2017-02-14`
- Horizon: `5d` only; that is where the first-pass screen found the durable positive pocket.
- Split: first `70%` of dates train, remaining `30%` test.
- Selector job: choose one strategy or abstain.
- Confidence gate: a strategy must match at least two regime dimensions, clear a score threshold derived from positive train-set regime cells, and be supported by multiple strategies on the same day.
- Costs: 10 bps already embedded in the strategy return series.

## Candidate Scan

| policy | min_mean_net_bps | min_win_rate | min_tstat | min_obs | min_matches | min_score | min_support | train_precision | train_coverage | train_active_days | train_mean_net_bps | test_precision | test_coverage | test_active_days | test_mean_net_bps | test_portfolio_mean_net_bps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 40.000 | 0.550 | 1.500 | 250 | 3 | 3.000 | 2 | 0.582 | 0.220 | 2348.000 | 67.699 | 0.543 | 0.135 | 619.000 | 49.832 | 6.735 |
| loose | 20.000 | 0.520 | 1.000 | 50 | 2 | 2.000 | 1 | 0.548 | 0.492 | 5258.000 | 43.987 | 0.499 | 0.487 | 2231.000 | -12.669 | -6.171 |
| high_conf | 30.000 | 0.540 | 1.250 | 100 | 2 | 2.500 | 2 | 0.547 | 0.478 | 5106.000 | 37.750 | 0.487 | 0.486 | 2228.000 | -16.273 | -7.916 |
| balanced | 25.000 | 0.530 | 1.000 | 100 | 2 | 2.250 | 2 | 0.547 | 0.491 | 5244.000 | 42.189 | 0.502 | 0.487 | 2231.000 | -14.552 | -7.088 |

## Chosen Policy

- Chosen policy: `strict`
- Train precision: `0.582`
- Train coverage: `0.220`
- Test precision: `0.543`
- Test coverage: `0.135`
- Test active days: `619`
- Min support: `2` strategies

| universe | strategy | family | dimension | state | mean_net_bps | win_rate | tstat | obs | weight |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| expanded | bollinger_percent_b_mean_reversion_20 | reversal_exhaustion | breadth_state | bullish | 60.548 | 0.557 | 5.017 | 748 | 2.860 |
| expanded | bollinger_percent_b_mean_reversion_20 | reversal_exhaustion | gap_state | up_gap_shock | 71.068 | 0.579 | 3.266 | 259 | 2.527 |
| expanded | bollinger_percent_b_mean_reversion_20 | reversal_exhaustion | liquidity_state | normal_liquidity | 42.922 | 0.556 | 6.210 | 1968 | 2.982 |
| expanded | bollinger_percent_b_mean_reversion_20 | reversal_exhaustion | risk_state | mixed | 48.230 | 0.552 | 6.011 | 2124 | 2.985 |
| expanded | bollinger_percent_b_mean_reversion_20 | reversal_exhaustion | trend_state | sideways | 62.085 | 0.573 | 6.172 | 1053 | 3.164 |
| expanded | bollinger_percent_b_mean_reversion_20 | reversal_exhaustion | trend_state | bear | 63.542 | 0.613 | 3.717 | 385 | 2.565 |
| expanded | bollinger_percent_b_mean_reversion_20 | reversal_exhaustion | vol_state | high_vol | 90.770 | 0.591 | 7.896 | 1043 | 3.882 |
| expanded | fisher_transform_reversal_10 | reversal_exhaustion | breadth_state | bullish | 46.693 | 0.557 | 4.595 | 748 | 2.616 |
| expanded | fisher_transform_reversal_10 | reversal_exhaustion | gap_state | up_gap_shock | 65.189 | 0.560 | 3.122 | 259 | 2.432 |
| expanded | fisher_transform_reversal_10 | reversal_exhaustion | trend_state | sideways | 54.551 | 0.565 | 6.002 | 1053 | 3.046 |
| expanded | fisher_transform_reversal_10 | reversal_exhaustion | trend_state | bear | 70.178 | 0.582 | 3.353 | 385 | 2.540 |
| expanded | fisher_transform_reversal_10 | reversal_exhaustion | vol_state | high_vol | 74.938 | 0.585 | 6.906 | 1043 | 3.476 |
| expanded | mfi_mean_reversion_14 | volume_confirmation | trend_state | bear | 48.845 | 0.556 | 2.806 | 387 | 2.190 |
| expanded | stochastic_mean_reversion_14 | reversal_exhaustion | breadth_state | bearish | 42.902 | 0.554 | 2.917 | 587 | 2.158 |
| expanded | stochastic_mean_reversion_14 | reversal_exhaustion | gap_state | up_gap_shock | 61.667 | 0.591 | 2.958 | 259 | 2.356 |
| expanded | stochastic_mean_reversion_14 | reversal_exhaustion | liquidity_state | normal_liquidity | 40.381 | 0.555 | 5.896 | 1968 | 2.878 |
| expanded | stochastic_mean_reversion_14 | reversal_exhaustion | trend_state | sideways | 60.983 | 0.578 | 6.437 | 1053 | 3.219 |
| expanded | stochastic_mean_reversion_14 | reversal_exhaustion | trend_state | bear | 72.479 | 0.592 | 3.908 | 385 | 2.702 |
| expanded | stochastic_mean_reversion_14 | reversal_exhaustion | vol_state | high_vol | 76.451 | 0.604 | 6.279 | 1043 | 3.334 |
| expanded | williams_r_mean_reversion_14 | reversal_exhaustion | breadth_state | bearish | 42.902 | 0.554 | 2.917 | 587 | 2.158 |

## Test Backtest

| universe | active_days | coverage | precision | active_mean_net_bps | portfolio_mean_net_bps | portfolio_median_net_bps | portfolio_sharpe_like | portfolio_max_drawdown_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| combined | 619.000 | 0.135 | 0.543 | 49.832 | 6.735 | 0.000 | 2.966 | -81.119 |
| expanded | 197.000 | 0.086 | 0.579 | 74.358 | 6.397 | 0.000 | 2.573 | -26.501 |
| nifty500 | 422.000 | 0.184 | 0.526 | 38.383 | 7.073 | 0.000 | 1.861 | -81.119 |

Comparison against the combined always-on baseline:

| universe | best_always_on | best_always_on_mean_net_bps | always_flat_mean_net_bps | always_flat_precision | test_mean_net_bps |
| --- | --- | --- | --- | --- | --- |
| nifty500 | breakout_20 | 22.586 | 0.000 | nan | 6.510 |
| expanded | chandelier_trend | 43.993 | 0.000 | nan | 4.784 |
| combined | per-universe_best | 5.647 | 0.000 | nan | 5.647 |

## Class Context

| regime_state | obs | mean_net_bps | median_net_bps | win_rate | tstat | universe | horizon | sector | regime_dimension |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| up_gap_shock | 577 | 136.441 | 69.548 | 0.549 | 3.008 | expanded | 5 | Metals & Mining | gap_state |
| up_gap_shock | 616 | 128.705 | 77.119 | 0.552 | 3.027 | nifty500 | 5 | Metals & Mining | gap_state |
| risk_on | 822 | 124.703 | 111.195 | 0.609 | 7.211 | nifty500 | 5 | Capital Goods | risk_state |
| bullish | 1478 | 122.089 | 96.104 | 0.592 | 8.773 | nifty500 | 5 | Capital Goods | breadth_state |
| risk_on | 772 | 121.359 | 95.418 | 0.584 | 5.659 | expanded | 5 | Capital Goods | risk_state |

| regime_state | obs | mean_net_bps | median_net_bps | win_rate | tstat | universe | horizon | liquidity_class | regime_dimension |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bullish | 1561 | 95.508 | 77.507 | 0.597 | 8.388 | nifty500 | 5 | low | breadth_state |
| bullish | 1575 | 94.677 | 96.526 | 0.603 | 8.281 | nifty500 | 5 | very_low | breadth_state |
| bullish | 1531 | 91.088 | 91.015 | 0.600 | 8.234 | nifty500 | 5 | mid | breadth_state |
| high_vol | 1633 | 89.657 | 123.218 | 0.582 | 5.228 | nifty500 | 5 | very_low | vol_state |
| bullish | 1533 | 87.450 | 82.950 | 0.594 | 7.377 | expanded | 5 | low | breadth_state |

## Takeaway

- The gate is intentionally sparse: it should abstain unless several regime dimensions agree and the train-set edge is strong.
- If the out-of-sample precision does not stay above the always-on baseline, this policy should stay research-only.