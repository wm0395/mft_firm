# Regime Analysis

## Protocol

- Strategy pool: a curated subset of fast, representative base-screen strategies plus breakout, trend, reversal, gap, structure, and participation extras.
- Each universe is reduced to its top 100 high-vol names before the regime scan so the panel matches the first-pass screen and stays tractable.
- Regime axes: volatility, trend, breadth, gap shock, liquidity, drawdown, and combined risk state.
- News effects are proxied by gap shocks because no local headline feed exists in the repository.
- Cost stress uses `10bps` net returns for the regime summaries.

## Strategy Correlations

| universe | horizon | family | strategy | corr_vol_score | corr_trend_score | corr_breadth_score | corr_gap_score | corr_liquidity_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nifty500 | 1 | breakout_continuation | failed_breakout_score_20 | -0.108 | -0.059 | -0.070 | 0.128 | -0.040 |
| nifty500 | 1 | gap_reaction | opening_gap_regime_score | -0.178 | 0.105 | 0.171 | 0.105 | -0.021 |
| nifty500 | 1 | trend_following | chandelier_trend | 0.071 | 0.092 | 0.009 | 0.077 | -0.019 |
| nifty500 | 5 | gap_reaction | opening_gap_regime_score | 0.214 | -0.232 | -0.055 | 0.063 | 0.035 |
| nifty500 | 5 | trend_following | chandelier_trend | 0.141 | 0.083 | 0.010 | 0.063 | 0.021 |
| nifty500 | 5 | breakout_continuation | keltner_breakout_20 | 0.014 | 0.109 | 0.077 | 0.053 | 0.106 |
| nifty500 | 5 | trend_following | aroon_oscillator_25 | -0.011 | 0.046 | -0.016 | -0.052 | 0.146 |
| nifty500 | 1 | reversal_exhaustion | williams_r_mean_reversion_14 | 0.070 | -0.129 | -0.064 | 0.043 | -0.012 |
| nifty500 | 1 | reversal_exhaustion | stochastic_mean_reversion_14 | 0.070 | -0.129 | -0.064 | 0.043 | -0.012 |
| nifty500 | 5 | breakout_continuation | failed_breakout_score_20 | 0.005 | -0.077 | -0.150 | 0.043 | 0.005 |

## High-Confidence Gate Candidates

_No rows._

## Market State Highlights

Top family/state pairs on 5-day horizon:

| family | strategy | regime_state | mean_net_bps | win_rate | obs |
| --- | --- | --- | --- | --- | --- |
| reversal_exhaustion | stochastic_mean_reversion_14 | bear | 192.569 | 0.697 | 99 |
| reversal_exhaustion | williams_r_mean_reversion_14 | bear | 192.569 | 0.697 | 99 |
| reversal_exhaustion | inverse_fisher_rsi_reversal_10 | bear | 163.183 | 0.747 | 99 |
| reversal_exhaustion | fisher_transform_reversal_10 | bear | 148.958 | 0.727 | 99 |
| reversal_exhaustion | bollinger_percent_b_mean_reversion_20 | bear | 136.042 | 0.667 | 99 |
| volume_confirmation | mfi_mean_reversion_14 | sideways | 83.440 | 0.597 | 419 |
| gap_reaction | opening_gap_regime_score | sideways | 70.077 | 0.538 | 26 |
| trend_following | choppiness_inverse_14 | bear | 59.331 | 0.566 | 99 |
| breakout_continuation | failed_breakout_score_20 | sideways | 47.694 | 0.562 | 89 |
| trend_following | aroon_oscillator_25 | bull | -3.079 | 0.477 | 556 |
| trend_following | elder_ray_trend | bull | -5.816 | 0.491 | 556 |
| trend_following | trix_histogram_15_9 | bull | -5.991 | 0.516 | 556 |
| gap_reaction | gap_fade_score | sideways | -6.107 | 0.496 | 419 |
| gap_reaction | gap_continuation_score | bear | -16.938 | 0.485 | 99 |
| reversal_exhaustion | failed_reversal_score | bull | -21.115 | 0.492 | 531 |
| volume_confirmation | chaikin_money_flow_20 | bull | -22.720 | 0.495 | 513 |
| trend_following | kst_momentum_9 | bull | -23.751 | 0.498 | 556 |
| reversal_exhaustion | ultimate_oscillator_reversal | bull | -23.946 | 0.459 | 556 |
| volume_confirmation | price_volume_trend_20 | bull | -24.578 | 0.460 | 556 |
| structure_levels | support_trendline_position_20 | bull | -26.788 | 0.475 | 556 |

## Sectors

| regime_state | obs | mean_net_bps | median_net_bps | win_rate | tstat | universe | horizon | sector | regime_dimension |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| risk_off | 89 | 435.680 | 157.326 | 0.562 | 3.021 | expanded | 5 | Construction | risk_state |
| risk_off | 104 | 311.420 | 272.033 | 0.615 | 2.907 | expanded | 5 | Chemicals | risk_state |
| risk_off | 49 | 283.754 | 212.948 | 0.612 | 2.593 | nifty500 | 5 | Healthcare | risk_state |
| risk_off | 20 | 278.291 | 172.999 | 0.550 | 1.854 | expanded | 5 | Healthcare | risk_state |
| risk_on | 108 | 277.547 | 120.612 | 0.574 | 3.569 | expanded | 5 | Healthcare | risk_state |
| risk_off | 147 | 255.651 | 129.916 | 0.571 | 3.262 | nifty500 | 5 | Capital Goods | risk_state |
| risk_on | 132 | 243.642 | 94.255 | 0.583 | 2.919 | expanded | 5 | Construction | risk_state |
| down_gap_shock | 269 | 238.397 | -20.631 | 0.476 | 0.996 | nifty500 | 5 | Metals & Mining | gap_state |
| risk_off | 165 | 223.482 | 155.630 | 0.600 | 4.034 | nifty500 | 5 | Financial Services | risk_state |
| risk_on | 76 | 193.526 | 175.932 | 0.618 | 3.232 | expanded | 5 | Oil Gas & Consumable Fuels | risk_state |

## Liquidity Classes

| regime_state | obs | mean_net_bps | median_net_bps | win_rate | tstat | universe | horizon | liquidity_class | regime_dimension |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| risk_on | 166 | 195.253 | 112.477 | 0.669 | 5.482 | expanded | 5 | very_low | risk_state |
| risk_off | 98 | 193.577 | 185.879 | 0.582 | 2.140 | expanded | 5 | very_low | risk_state |
| risk_on | 269 | 189.082 | 192.422 | 0.714 | 8.263 | nifty500 | 5 | very_low | risk_state |
| bullish | 458 | 173.211 | 114.184 | 0.609 | 5.637 | nifty500 | 5 | very_high | breadth_state |
| bullish | 253 | 170.663 | 66.436 | 0.585 | 4.291 | expanded | 5 | mid | breadth_state |
| risk_on | 275 | 169.449 | 148.935 | 0.636 | 6.637 | nifty500 | 5 | very_high | risk_state |
| bullish | 446 | 162.205 | 163.292 | 0.657 | 8.115 | nifty500 | 5 | very_low | breadth_state |
| bullish | 280 | 160.420 | 99.533 | 0.639 | 5.463 | expanded | 5 | very_low | breadth_state |
| bullish | 280 | 146.962 | 89.914 | 0.604 | 3.829 | expanded | 5 | high | breadth_state |
| risk_off | 208 | 145.056 | 122.790 | 0.591 | 3.473 | expanded | 5 | high | risk_state |

## Takeaway

- The report is designed to surface where signals align with the market state, not to promote every positive pocket as deployable.
- The next step is a walk-forward selector that only activates the historically consistent regime-state combinations.
