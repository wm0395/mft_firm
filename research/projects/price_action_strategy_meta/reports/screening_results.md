# Price Action Screening Results

## Protocol

- Universe: `nifty500_high_vol_top100` and `expanded_high_vol_top100`.
- Horizon: `1d` and `5d` forward returns.
- Primary mask: repo-native `high_vol_mask` intersected with `active_mask`.
- Long-short construction: top and bottom quintiles of each signal cross-section.
- Cost stress: `0`, `5`, `10`, and `25` bps with turnover-based deductions.
- Non-directional overlays, intraday-only helpers, and loop-heavy profile tools are listed separately and not forced into this pass.

## Family Summary

| family | strategies | mean_rank_ic | mean_gross_bps | mean_net_10_bps | positive_net_10_rate | positive_ic_rate |
| --- | --- | --- | --- | --- | --- | --- |
| reversal_exhaustion | 8 | 0.016 | 7.100 | -6.781 | 0.375 | 0.750 |
| volume_confirmation | 8 | -0.012 | -4.977 | -13.166 | 0.062 | 0.125 |
| trend_following | 6 | -0.022 | -14.113 | -22.262 | 0.000 | 0.000 |
| breakout_continuation | 3 | -0.010 | -6.474 | -31.366 | 0.000 | 0.333 |
| gap_reaction | 2 | 0.000 | -0.151 | -31.873 | 0.000 | 0.500 |
| structure_levels | 2 | -0.027 | -13.957 | -33.507 | 0.000 | 0.000 |

## Stable Winners

_No rows._

## Stable Losers

| strategy | family | universes | horizons | mean_rank_ic | mean_net_10_bps | min_net_10_bps | max_net_10_bps |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pivot_relative_position | structure_levels | 2 | 2 | -0.029 | -42.369 | -60.783 | -24.790 |
| failed_reversal_score | reversal_exhaustion | 2 | 2 | -0.022 | -41.599 | -57.170 | -27.841 |
| keltner_breakout_20 | breakout_continuation | 2 | 2 | -0.024 | -40.413 | -56.346 | -28.691 |
| breakout_20 | breakout_continuation | 2 | 2 | -0.020 | -32.165 | -49.062 | -18.415 |
| gap_continuation_score | gap_reaction | 2 | 2 | -0.004 | -31.781 | -38.139 | -25.455 |
| macd_histogram_12_26_9 | trend_following | 2 | 2 | -0.029 | -31.180 | -47.431 | -16.340 |
| dpo_mean_reversion_20 | reversal_exhaustion | 2 | 2 | -0.014 | -27.347 | -34.497 | -21.111 |
| force_index_13 | volume_confirmation | 2 | 2 | -0.031 | -25.882 | -36.571 | -16.536 |
| multi_timeframe_confirmation | trend_following | 2 | 2 | -0.020 | -25.551 | -31.890 | -22.115 |
| support_resistance_position_20 | structure_levels | 2 | 2 | -0.025 | -24.645 | -35.652 | -16.958 |
| directional_spread_14 | trend_following | 2 | 2 | -0.028 | -24.132 | -31.291 | -17.226 |
| hybrid_confirmation | volume_confirmation | 2 | 2 | -0.021 | -22.942 | -34.245 | -13.324 |
| trix_histogram_15_9 | trend_following | 2 | 2 | -0.017 | -20.227 | -28.047 | -12.096 |
| vortex_spread_14 | trend_following | 2 | 2 | -0.021 | -20.030 | -25.946 | -16.200 |
| chaikin_oscillator_3_10 | volume_confirmation | 2 | 2 | -0.013 | -14.016 | -20.085 | -10.151 |
| trend_volume_composite | volume_confirmation | 2 | 2 | -0.018 | -13.454 | -18.511 | -10.699 |
| adx_directional_14 | trend_following | 2 | 2 | -0.017 | -12.448 | -13.559 | -11.227 |
| obv_slope_20 | volume_confirmation | 2 | 2 | -0.017 | -10.633 | -12.963 | -8.304 |
| chaikin_money_flow_20 | volume_confirmation | 2 | 2 | -0.005 | -9.895 | -16.282 | -6.430 |
| price_volume_trend_20 | volume_confirmation | 2 | 2 | -0.016 | -8.792 | -9.790 | -7.805 |

## nifty500_high_vol_top100 / 1d

Top 5 by `net_mean_bps_10`:

| family | strategy | rank_ic_mean | gross_mean_bps | net_mean_bps_10 | turnover | gross_win_rate |
| --- | --- | --- | --- | --- | --- | --- |
| reversal_exhaustion | rsi_mean_reversion_14 | 0.027 | 7.725 | -1.328 | 0.453 | 0.328 |
| reversal_exhaustion | cmo_mean_reversion_14 | 0.022 | 7.835 | -2.038 | 0.494 | 0.335 |
| volume_confirmation | mfi_mean_reversion_14 | 0.023 | 5.174 | -3.256 | 0.421 | 0.336 |
| reversal_exhaustion | cci_mean_reversion_20 | 0.026 | 7.124 | -3.304 | 0.521 | 0.341 |
| reversal_exhaustion | bollinger_percent_b_mean_reversion_20 | 0.027 | 6.635 | -5.270 | 0.595 | 0.335 |

Bottom 5 by `net_mean_bps_10`:

| family | strategy | rank_ic_mean | gross_mean_bps | net_mean_bps_10 | turnover | gross_win_rate |
| --- | --- | --- | --- | --- | --- | --- |
| gap_reaction | gap_fade_score | -0.001 | -6.492 | -38.209 | 1.586 | 0.312 |
| breakout_continuation | keltner_breakout_20 | -0.021 | -19.882 | -37.115 | 0.862 | 0.146 |
| reversal_exhaustion | failed_reversal_score | -0.017 | -2.800 | -30.428 | 1.381 | 0.314 |
| structure_levels | pivot_relative_position | -0.022 | 1.622 | -25.636 | 1.363 | 0.318 |
| gap_reaction | gap_continuation_score | 0.001 | 6.264 | -25.455 | 1.586 | 0.339 |

## nifty500_high_vol_top100 / 5d

Top 5 by `net_mean_bps_10`:

| family | strategy | rank_ic_mean | gross_mean_bps | net_mean_bps_10 | turnover | gross_win_rate |
| --- | --- | --- | --- | --- | --- | --- |
| reversal_exhaustion | bollinger_percent_b_mean_reversion_20 | 0.036 | 29.547 | 17.632 | 0.596 | 0.362 |
| reversal_exhaustion | cci_mean_reversion_20 | 0.033 | 27.247 | 16.809 | 0.522 | 0.354 |
| reversal_exhaustion | stochastic_mean_reversion_14 | 0.032 | 25.631 | 11.826 | 0.690 | 0.355 |
| reversal_exhaustion | williams_r_mean_reversion_14 | 0.032 | 25.631 | 11.826 | 0.690 | 0.355 |
| reversal_exhaustion | rsi_mean_reversion_14 | 0.028 | 18.051 | 8.987 | 0.453 | 0.337 |

Bottom 5 by `net_mean_bps_10`:

| family | strategy | rank_ic_mean | gross_mean_bps | net_mean_bps_10 | turnover | gross_win_rate |
| --- | --- | --- | --- | --- | --- | --- |
| structure_levels | pivot_relative_position | -0.038 | -33.527 | -60.783 | 1.363 | 0.289 |
| reversal_exhaustion | failed_reversal_score | -0.030 | -29.541 | -57.170 | 1.381 | 0.296 |
| breakout_continuation | keltner_breakout_20 | -0.027 | -39.109 | -56.346 | 0.862 | 0.146 |
| breakout_continuation | breakout_20 | -0.028 | -23.638 | -49.062 | 1.271 | 0.230 |
| trend_following | macd_histogram_12_26_9 | -0.034 | -41.278 | -47.431 | 0.308 | 0.273 |

## expanded_high_vol_top100 / 1d

Top 5 by `net_mean_bps_10`:

| family | strategy | rank_ic_mean | gross_mean_bps | net_mean_bps_10 | turnover | gross_win_rate |
| --- | --- | --- | --- | --- | --- | --- |
| reversal_exhaustion | cmo_mean_reversion_14 | 0.023 | 7.857 | -2.165 | 0.501 | 0.339 |
| reversal_exhaustion | rsi_mean_reversion_14 | 0.027 | 6.597 | -2.502 | 0.455 | 0.340 |
| volume_confirmation | mfi_mean_reversion_14 | 0.026 | 5.933 | -2.678 | 0.431 | 0.341 |
| reversal_exhaustion | cci_mean_reversion_20 | 0.027 | 5.877 | -4.600 | 0.524 | 0.345 |
| volume_confirmation | chaikin_money_flow_20 | -0.007 | 1.123 | -6.430 | 0.378 | 0.315 |

Bottom 5 by `net_mean_bps_10`:

| family | strategy | rank_ic_mean | gross_mean_bps | net_mean_bps_10 | turnover | gross_win_rate |
| --- | --- | --- | --- | --- | --- | --- |
| gap_reaction | gap_fade_score | -0.000 | -5.638 | -37.369 | 1.587 | 0.321 |
| breakout_continuation | failed_breakout_score_20 | 0.015 | -0.771 | -33.022 | 1.613 | 0.193 |
| breakout_continuation | keltner_breakout_20 | -0.021 | -12.002 | -28.691 | 0.834 | 0.156 |
| reversal_exhaustion | failed_reversal_score | -0.015 | -0.244 | -27.841 | 1.380 | 0.326 |
| gap_reaction | gap_continuation_score | 0.000 | 5.187 | -26.530 | 1.586 | 0.333 |

## expanded_high_vol_top100 / 5d

Top 5 by `net_mean_bps_10`:

| family | strategy | rank_ic_mean | gross_mean_bps | net_mean_bps_10 | turnover | gross_win_rate |
| --- | --- | --- | --- | --- | --- | --- |
| reversal_exhaustion | bollinger_percent_b_mean_reversion_20 | 0.033 | 24.923 | 13.011 | 0.596 | 0.354 |
| reversal_exhaustion | cci_mean_reversion_20 | 0.031 | 22.961 | 12.471 | 0.524 | 0.352 |
| reversal_exhaustion | stochastic_mean_reversion_14 | 0.028 | 18.852 | 5.106 | 0.687 | 0.346 |
| reversal_exhaustion | williams_r_mean_reversion_14 | 0.028 | 18.852 | 5.106 | 0.687 | 0.346 |
| volume_confirmation | mfi_mean_reversion_14 | 0.025 | 13.733 | 5.104 | 0.431 | 0.348 |

Bottom 5 by `net_mean_bps_10`:

| family | strategy | rank_ic_mean | gross_mean_bps | net_mean_bps_10 | turnover | gross_win_rate |
| --- | --- | --- | --- | --- | --- | --- |
| structure_levels | pivot_relative_position | -0.036 | -30.980 | -58.267 | 1.364 | 0.292 |
| reversal_exhaustion | failed_reversal_score | -0.028 | -23.360 | -50.958 | 1.380 | 0.301 |
| trend_following | macd_histogram_12_26_9 | -0.032 | -37.258 | -43.509 | 0.313 | 0.279 |
| breakout_continuation | keltner_breakout_20 | -0.026 | -22.804 | -39.502 | 0.835 | 0.159 |
| breakout_continuation | breakout_20 | -0.026 | -13.314 | -38.747 | 1.272 | 0.234 |

## Not Screened In This Pass

- `opening_range_breakout`: session-dependent intraday data is not present in the daily panel.
- `volume_profile_levels`, `support_resistance_trendlines`: structure/profile helpers that need a separate pass.
- `supertrend`, `parabolic_sar`: directional helpers that are too slow for the pooled screen pass here.
- `atr_position_size`, `pyramiding_ladder`: sizing overlays, not standalone directional strategies.
- `bollinger_squeeze`, `choppiness_index`, `mass_index`, `volume_profile_regime`: gate-only helpers rather than standalone directional scores.
