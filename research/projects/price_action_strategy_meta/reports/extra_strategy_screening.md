# Extra Strategy Screening

## Protocol

- This supplemental pass screens the extra first-principles strategies only.
- Each universe is reduced to its top 100 high-vol names so the extra screen matches the base screen and the regime scan.
- The extra pool now includes trend, reversal, structure, and regime helpers such as supertrend, parabolic SAR, Aroon, Ichimoku, KST, inverse Fisher RSI, mass index, trendlines, volume profile, and choppiness.
- Universe and horizon settings match the base screen so the comparison is apples-to-apples.
- The goal is to isolate whether the expanded extras add any durable edge before they are treated as gate inputs.

## Family Summary

| family | strategies | mean_rank_ic | mean_gross_bps | mean_net_10_bps | positive_net_10_rate | positive_ic_rate |
| --- | --- | --- | --- | --- | --- | --- |
| trend_following | 8 | -0.019 | -21.996 | -30.822 | 0.000 | 0.062 |
| volume_confirmation | 1 | -0.026 | -25.623 | -35.453 | 0.000 | 0.000 |
| structure_levels | 2 | -0.034 | -23.294 | -37.419 | 0.000 | 0.000 |
| reversal_exhaustion | 4 | 0.014 | -36.151 | -48.050 | 0.250 | 0.375 |
| gap_reaction | 1 | -0.014 | -52.365 | -77.954 | 0.000 | 0.000 |
| breakout_continuation | 2 | -0.024 | -67.686 | -90.180 | 0.000 | 0.000 |

## Stable Winners

| strategy | family | universes | horizons | mean_rank_ic | mean_net_10_bps | min_net_10_bps | max_net_10_bps |
| --- | --- | --- | --- | --- | --- | --- | --- |
| fisher_transform_reversal_10 | reversal_exhaustion | 2 | 2 | 0.034 | 31.080 | 7.937 | 54.224 |
| inverse_fisher_rsi_reversal_10 | reversal_exhaustion | 2 | 2 | 0.047 | 23.628 | 2.831 | 44.425 |

## Stable Losers

| strategy | family | universes | horizons | mean_rank_ic | mean_net_10_bps | min_net_10_bps | max_net_10_bps |
| --- | --- | --- | --- | --- | --- | --- | --- |
| relative_volume_breakout_20 | breakout_continuation | 2 | 2 | -0.033 | -90.180 | -141.797 | -38.564 |
| opening_gap_regime_score | gap_reaction | 2 | 2 | -0.014 | -77.954 | -95.456 | -60.453 |
| ultimate_oscillator_reversal | reversal_exhaustion | 2 | 2 | -0.034 | -54.652 | -82.719 | -26.585 |
| chandelier_trend | trend_following | 2 | 2 | -0.034 | -52.291 | -76.235 | -28.347 |
| support_trendline_position_20 | structure_levels | 2 | 2 | -0.032 | -41.778 | -60.468 | -23.089 |
| kst_momentum_9 | trend_following | 2 | 2 | -0.040 | -41.107 | -62.882 | -19.333 |
| ease_of_movement_14 | volume_confirmation | 2 | 2 | -0.026 | -35.453 | -53.621 | -17.286 |
| volume_profile_position_20 | structure_levels | 2 | 2 | -0.036 | -33.059 | -54.061 | -12.058 |
| ichimoku_kijun_spread_26 | trend_following | 2 | 2 | -0.020 | -32.128 | -51.376 | -12.879 |
| aroon_oscillator_25 | trend_following | 2 | 2 | -0.023 | -23.747 | -32.794 | -14.700 |
| choppiness_inverse_14 | trend_following | 2 | 2 | -0.010 | -13.714 | -14.759 | -12.669 |

## nifty500_high_vol_top100 / 1d

Top 5 by `net_mean_bps_10`:

_No rows._

Bottom 5 by `net_mean_bps_10`:

_No rows._

## nifty500_high_vol_top100 / 5d

Top 5 by `net_mean_bps_10`:

_No rows._

Bottom 5 by `net_mean_bps_10`:

_No rows._

## expanded_high_vol_top100 / 1d

Top 5 by `net_mean_bps_10`:

_No rows._

Bottom 5 by `net_mean_bps_10`:

_No rows._

## expanded_high_vol_top100 / 5d

Top 5 by `net_mean_bps_10`:

_No rows._

Bottom 5 by `net_mean_bps_10`:

_No rows._
