# Regime Analysis

## Protocol

- Strategy pool: a curated subset of fast, representative base-screen strategies plus breakout, trend, reversal, gap, structure, and participation extras.
- Each universe is reduced to its top 100 high-vol names before the regime scan so the panel matches the first-pass screen and stays tractable.
- Regime axes: volatility, trend, breadth, gap shock, liquidity, and combined risk state.
- News effects are proxied by gap shocks because no local headline feed exists in the repository.
- Cost stress uses `10bps` net returns for the regime summaries.

## Strategy Correlations

| universe | horizon | family | strategy | corr_vol_score | corr_trend_score | corr_breadth_score | corr_gap_score | corr_liquidity_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nifty500 | 5 | gap_reaction | opening_gap_regime_score | -0.029 | 0.058 | -0.074 | -0.121 | -0.038 |
| expanded | 1 | breakout_continuation | relative_volume_breakout_20 | -0.019 | 0.007 | 0.009 | 0.067 | 0.003 |
| nifty500 | 1 | breakout_continuation | relative_volume_breakout_20 | -0.019 | 0.002 | 0.033 | 0.066 | 0.018 |
| expanded | 5 | trend_following | chandelier_trend | -0.104 | 0.014 | -0.055 | -0.059 | 0.085 |
| nifty500 | 5 | trend_following | chandelier_trend | -0.107 | 0.027 | -0.069 | -0.057 | 0.054 |
| nifty500 | 1 | breakout_continuation | breakout_20 | -0.006 | -0.006 | 0.012 | 0.055 | 0.013 |
| expanded | 1 | breakout_continuation | breakout_20 | -0.008 | -0.001 | -0.003 | 0.053 | 0.005 |
| expanded | 5 | gap_reaction | opening_gap_regime_score | -0.002 | 0.080 | -0.000 | -0.053 | -0.105 |
| nifty500 | 5 | volume_confirmation | force_index_13 | -0.077 | -0.014 | 0.002 | -0.048 | 0.044 |
| nifty500 | 1 | gap_reaction | opening_gap_regime_score | 0.038 | 0.011 | -0.003 | 0.047 | -0.023 |

## High-Confidence Gate Candidates

| family | strategy | regime_dimension | regime_state | mean_net_bps | median_net_bps | win_rate | tstat | obs | universes | horizons |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| reversal_exhaustion | fisher_transform_reversal_10 | trend_state | bear | 47.406 | 43.928 | 0.568 | 3.242 | 2310 | 2 | 2 |
| reversal_exhaustion | fisher_transform_reversal_10 | risk_state | risk_off | 46.153 | 28.954 | 0.537 | 1.204 | 680 | 2 | 2 |
| reversal_exhaustion | bollinger_percent_b_mean_reversion_20 | vol_state | high_vol | 44.572 | 35.511 | 0.555 | 4.411 | 4995 | 2 | 2 |
| volume_confirmation | mfi_mean_reversion_14 | risk_state | risk_off | 43.058 | 39.706 | 0.545 | 1.363 | 680 | 2 | 2 |
| reversal_exhaustion | fisher_transform_reversal_10 | vol_state | high_vol | 41.206 | 39.597 | 0.561 | 4.884 | 4995 | 2 | 2 |
| breakout_continuation | keltner_breakout_20 | risk_state | risk_on | 40.439 | 42.962 | 0.536 | 0.691 | 346 | 2 | 2 |
| reversal_exhaustion | williams_r_mean_reversion_14 | vol_state | high_vol | 39.102 | 36.470 | 0.560 | 3.764 | 4995 | 2 | 2 |
| reversal_exhaustion | stochastic_mean_reversion_14 | vol_state | high_vol | 39.102 | 36.470 | 0.560 | 3.764 | 4995 | 2 | 2 |
| reversal_exhaustion | bollinger_percent_b_mean_reversion_20 | gap_state | up_gap_shock | 37.705 | 22.167 | 0.536 | 1.931 | 1302 | 2 | 2 |
| gap_reaction | opening_gap_regime_score | liquidity_state | low_liquidity | 36.118 | 9.631 | 0.524 | 0.735 | 145 | 2 | 2 |
| reversal_exhaustion | stochastic_mean_reversion_14 | risk_state | risk_off | 34.958 | 30.548 | 0.533 | 0.639 | 680 | 2 | 2 |
| reversal_exhaustion | williams_r_mean_reversion_14 | risk_state | risk_off | 34.958 | 30.548 | 0.533 | 0.639 | 680 | 2 | 2 |
| reversal_exhaustion | williams_r_mean_reversion_14 | trend_state | bear | 31.048 | 30.136 | 0.541 | 1.680 | 2310 | 2 | 2 |
| reversal_exhaustion | stochastic_mean_reversion_14 | trend_state | bear | 31.048 | 30.136 | 0.541 | 1.680 | 2310 | 2 | 2 |
| reversal_exhaustion | stochastic_mean_reversion_14 | gap_state | up_gap_shock | 30.827 | 20.624 | 0.539 | 1.639 | 1302 | 2 | 2 |
| reversal_exhaustion | williams_r_mean_reversion_14 | gap_state | up_gap_shock | 30.827 | 20.624 | 0.539 | 1.639 | 1302 | 2 | 2 |
| reversal_exhaustion | fisher_transform_reversal_10 | liquidity_state | low_liquidity | 30.127 | 11.879 | 0.523 | 1.186 | 1590 | 2 | 2 |
| volume_confirmation | mfi_mean_reversion_14 | liquidity_state | low_liquidity | 28.830 | 3.389 | 0.502 | 1.060 | 1594 | 2 | 2 |
| reversal_exhaustion | fisher_transform_reversal_10 | gap_state | up_gap_shock | 28.524 | 27.134 | 0.538 | 1.750 | 1302 | 2 | 2 |
| volume_confirmation | mfi_mean_reversion_14 | trend_state | bear | 28.460 | 26.502 | 0.537 | 2.081 | 2316 | 2 | 2 |

## Market State Highlights

Top family/state pairs on 5-day horizon:

| family | strategy | regime_state | mean_net_bps | win_rate | obs |
| --- | --- | --- | --- | --- | --- |
| reversal_exhaustion | fisher_transform_reversal_10 | bear | 85.321 | 0.617 | 582 |
| reversal_exhaustion | bollinger_percent_b_mean_reversion_20 | bear | 71.260 | 0.591 | 582 |
| reversal_exhaustion | williams_r_mean_reversion_14 | bear | 70.736 | 0.589 | 582 |
| reversal_exhaustion | stochastic_mean_reversion_14 | bear | 70.736 | 0.589 | 582 |
| volume_confirmation | mfi_mean_reversion_14 | bear | 59.090 | 0.578 | 583 |
| breakout_continuation | keltner_breakout_20 | bull | 47.985 | 0.517 | 391 |
| trend_following | chandelier_trend | sideways | 23.548 | 0.540 | 550 |
| breakout_continuation | failed_breakout_score_20 | bear | 9.349 | 0.518 | 282 |
| volume_confirmation | chaikin_money_flow_20 | bull | -2.091 | 0.514 | 1285 |
| volume_confirmation | trend_volume_composite | bull | -3.201 | 0.509 | 1705 |
| volume_confirmation | price_volume_trend_20 | sideways | -4.734 | 0.489 | 1692 |
| trend_following | vortex_spread_14 | bull | -7.377 | 0.512 | 1431 |
| reversal_exhaustion | ultimate_oscillator_reversal | bull | -10.676 | 0.485 | 1700 |
| breakout_continuation | relative_volume_breakout_20 | bull | -16.367 | 0.473 | 1001 |
| volume_confirmation | ease_of_movement_14 | bull | -19.276 | 0.459 | 1435 |
| gap_reaction | gap_fade_score | bull | -19.484 | 0.463 | 1435 |
| trend_following | trix_histogram_15_9 | sideways | -20.065 | 0.476 | 1692 |
| breakout_continuation | breakout_20 | bull | -20.230 | 0.469 | 962 |
| trend_following | elder_ray_trend | bear | -21.311 | 0.463 | 575 |
| gap_reaction | opening_gap_regime_score | bull | -24.772 | 0.478 | 186 |

## Sectors

| regime_state | obs | mean_net_bps | median_net_bps | win_rate | tstat | universe | horizon | sector | regime_dimension |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| up_gap_shock | 577 | 136.441 | 69.548 | 0.549 | 3.008 | expanded | 5 | Metals & Mining | gap_state |
| up_gap_shock | 616 | 128.705 | 77.119 | 0.552 | 3.027 | nifty500 | 5 | Metals & Mining | gap_state |
| risk_on | 822 | 124.703 | 111.195 | 0.609 | 7.211 | nifty500 | 5 | Capital Goods | risk_state |
| bullish | 1478 | 122.089 | 96.104 | 0.592 | 8.773 | nifty500 | 5 | Capital Goods | breadth_state |
| risk_on | 772 | 121.359 | 95.418 | 0.584 | 5.659 | expanded | 5 | Capital Goods | risk_state |
| bullish | 1456 | 120.273 | 103.676 | 0.573 | 7.169 | nifty500 | 5 | Metals & Mining | breadth_state |
| bullish | 1297 | 118.272 | 107.849 | 0.577 | 6.426 | expanded | 5 | Metals & Mining | breadth_state |
| bull | 2282 | 116.979 | 108.528 | 0.587 | 7.306 | expanded | 5 | Metals & Mining | trend_state |
| risk_on | 698 | 116.864 | 110.644 | 0.586 | 5.905 | expanded | 5 | Metals & Mining | risk_state |
| low_liquidity | 982 | 115.799 | 78.766 | 0.558 | 3.706 | nifty500 | 5 | Metals & Mining | liquidity_state |

## Liquidity Classes

| regime_state | obs | mean_net_bps | median_net_bps | win_rate | tstat | universe | horizon | liquidity_class | regime_dimension |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bullish | 1561 | 95.508 | 77.507 | 0.597 | 8.388 | nifty500 | 5 | low | breadth_state |
| bullish | 1575 | 94.677 | 96.526 | 0.603 | 8.281 | nifty500 | 5 | very_low | breadth_state |
| bullish | 1531 | 91.088 | 91.015 | 0.600 | 8.234 | nifty500 | 5 | mid | breadth_state |
| high_vol | 1633 | 89.657 | 123.218 | 0.582 | 5.228 | nifty500 | 5 | very_low | vol_state |
| bullish | 1533 | 87.450 | 82.950 | 0.594 | 7.377 | expanded | 5 | low | breadth_state |
| risk_on | 864 | 86.628 | 99.572 | 0.611 | 6.341 | nifty500 | 5 | mid | risk_state |
| risk_on | 721 | 86.311 | 101.309 | 0.607 | 5.411 | expanded | 5 | very_high | risk_state |
| bullish | 1563 | 86.161 | 91.968 | 0.605 | 6.915 | expanded | 5 | very_low | breadth_state |
| bullish | 1363 | 82.517 | 84.828 | 0.585 | 6.321 | expanded | 5 | very_high | breadth_state |
| bullish | 1502 | 81.758 | 72.634 | 0.573 | 6.472 | expanded | 5 | mid | breadth_state |

## Takeaway

- The report is designed to surface where signals align with the market state, not to promote every positive pocket as deployable.
- The next step is a walk-forward selector that only activates the historically consistent regime-state combinations.