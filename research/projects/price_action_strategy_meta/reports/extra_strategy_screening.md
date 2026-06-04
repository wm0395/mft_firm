# Extra Strategy Screening

## Protocol

- This supplemental pass screens the extra first-principles strategies only.
- Universe and horizon settings match the base screen so the comparison is apples-to-apples.
- The goal is to isolate whether the expanded extras add any durable edge before they are treated as gate inputs.

## Family Summary

| family | strategies | mean_rank_ic | mean_gross_bps | mean_net_10_bps | positive_net_10_rate | positive_ic_rate |
| --- | --- | --- | --- | --- | --- | --- |
| breakout_continuation | 2 | -0.006 | 20.130 | -2.269 | 0.375 | 0.500 |
| reversal_exhaustion | 2 | -0.001 | -2.996 | -11.563 | 0.500 | 0.500 |
| trend_following | 2 | -0.013 | -9.495 | -20.890 | 0.000 | 0.000 |
| volume_confirmation | 1 | -0.018 | -12.870 | -21.985 | 0.000 | 0.000 |
| gap_reaction | 1 | -0.003 | 1.869 | -24.336 | 0.500 | 0.500 |

## Stable Winners

| strategy | family | universes | horizons | mean_rank_ic | mean_net_10_bps | min_net_10_bps | max_net_10_bps |
| --- | --- | --- | --- | --- | --- | --- | --- |
| fisher_transform_reversal_10 | reversal_exhaustion | 2 | 2 | 0.019 | 5.852 | 0.430 | 14.184 |

## Stable Losers

| strategy | family | universes | horizons | mean_rank_ic | mean_net_10_bps | min_net_10_bps | max_net_10_bps |
| --- | --- | --- | --- | --- | --- | --- | --- |
| relative_volume_breakout_20 | breakout_continuation | 2 | 2 | -0.022 | -36.937 | -55.616 | -20.602 |
| elder_ray_trend | trend_following | 2 | 2 | -0.005 | -29.978 | -43.987 | -18.103 |
| ultimate_oscillator_reversal | reversal_exhaustion | 2 | 2 | -0.021 | -28.979 | -43.316 | -18.377 |
| ease_of_movement_14 | volume_confirmation | 2 | 2 | -0.018 | -21.985 | -31.457 | -14.035 |
| chandelier_trend | trend_following | 2 | 2 | -0.021 | -11.803 | -14.085 | -8.215 |

## nifty500_high_vol_top100 / 1d

Top 5 by `net_mean_bps_10`:

| family | strategy | rank_ic_mean | gross_mean_bps | net_mean_bps_10 | turnover | gross_win_rate |
| --- | --- | --- | --- | --- | --- | --- |
| breakout_continuation | squeeze_breakout_20 | 0.006 | 155.030 | 136.697 | 0.917 | 0.001 |
| reversal_exhaustion | fisher_transform_reversal_10 | 0.019 | 7.903 | 1.606 | 0.315 | 0.338 |
| gap_reaction | opening_gap_regime_score | 0.003 | 27.586 | 1.285 | 1.315 | 0.052 |
| trend_following | chandelier_trend | -0.021 | -2.114 | -14.085 | 0.599 | 0.085 |
| volume_confirmation | ease_of_movement_14 | -0.014 | -7.503 | -16.544 | 0.452 | 0.303 |

Bottom 5 by `net_mean_bps_10`:

| family | strategy | rank_ic_mean | gross_mean_bps | net_mean_bps_10 | turnover | gross_win_rate |
| --- | --- | --- | --- | --- | --- | --- |
| breakout_continuation | relative_volume_breakout_20 | -0.017 | -0.198 | -25.835 | 1.282 | 0.255 |
| reversal_exhaustion | ultimate_oscillator_reversal | -0.020 | -11.552 | -22.293 | 0.537 | 0.300 |
| trend_following | elder_ray_trend | -0.004 | -7.590 | -18.103 | 0.526 | 0.313 |
| volume_confirmation | ease_of_movement_14 | -0.014 | -7.503 | -16.544 | 0.452 | 0.303 |
| trend_following | chandelier_trend | -0.021 | -2.114 | -14.085 | 0.599 | 0.085 |

## nifty500_high_vol_top100 / 5d

Top 5 by `net_mean_bps_10`:

| family | strategy | rank_ic_mean | gross_mean_bps | net_mean_bps_10 | turnover | gross_win_rate |
| --- | --- | --- | --- | --- | --- | --- |
| breakout_continuation | squeeze_breakout_20 | 0.014 | 156.994 | 138.660 | 0.917 | 0.001 |
| reversal_exhaustion | fisher_transform_reversal_10 | 0.021 | 20.493 | 14.184 | 0.316 | 0.344 |
| trend_following | chandelier_trend | -0.024 | -0.891 | -12.863 | 0.599 | 0.088 |
| volume_confirmation | ease_of_movement_14 | -0.021 | -22.407 | -31.457 | 0.453 | 0.292 |
| trend_following | elder_ray_trend | -0.005 | -28.866 | -39.390 | 0.526 | 0.310 |

Bottom 5 by `net_mean_bps_10`:

| family | strategy | rank_ic_mean | gross_mean_bps | net_mean_bps_10 | turnover | gross_win_rate |
| --- | --- | --- | --- | --- | --- | --- |
| gap_reaction | opening_gap_regime_score | -0.007 | -30.455 | -56.734 | 1.314 | 0.048 |
| breakout_continuation | relative_volume_breakout_20 | -0.030 | -29.982 | -55.616 | 1.282 | 0.237 |
| reversal_exhaustion | ultimate_oscillator_reversal | -0.026 | -32.568 | -43.316 | 0.537 | 0.291 |
| trend_following | elder_ray_trend | -0.005 | -28.866 | -39.390 | 0.526 | 0.310 |
| volume_confirmation | ease_of_movement_14 | -0.021 | -22.407 | -31.457 | 0.453 | 0.292 |

## expanded_high_vol_top100 / 1d

Top 5 by `net_mean_bps_10`:

| family | strategy | rank_ic_mean | gross_mean_bps | net_mean_bps_10 | turnover | gross_win_rate |
| --- | --- | --- | --- | --- | --- | --- |
| breakout_continuation | squeeze_breakout_20 | 0.008 | 84.411 | 64.411 | 1.000 | 0.001 |
| gap_reaction | opening_gap_regime_score | 0.001 | 27.866 | 1.739 | 1.306 | 0.052 |
| reversal_exhaustion | fisher_transform_reversal_10 | 0.018 | 6.874 | 0.430 | 0.322 | 0.341 |
| trend_following | chandelier_trend | -0.021 | 0.057 | -12.049 | 0.605 | 0.080 |
| volume_confirmation | ease_of_movement_14 | -0.016 | -4.857 | -14.035 | 0.459 | 0.312 |

Bottom 5 by `net_mean_bps_10`:

| family | strategy | rank_ic_mean | gross_mean_bps | net_mean_bps_10 | turnover | gross_win_rate |
| --- | --- | --- | --- | --- | --- | --- |
| breakout_continuation | relative_volume_breakout_20 | -0.016 | 5.022 | -20.602 | 1.281 | 0.253 |
| trend_following | elder_ray_trend | -0.005 | -7.452 | -18.431 | 0.549 | 0.316 |
| reversal_exhaustion | ultimate_oscillator_reversal | -0.017 | -7.614 | -18.377 | 0.538 | 0.308 |
| volume_confirmation | ease_of_movement_14 | -0.016 | -4.857 | -14.035 | 0.459 | 0.312 |
| trend_following | chandelier_trend | -0.021 | 0.057 | -12.049 | 0.605 | 0.080 |

## expanded_high_vol_top100 / 5d

Top 5 by `net_mean_bps_10`:

| family | strategy | rank_ic_mean | gross_mean_bps | net_mean_bps_10 | turnover | gross_win_rate |
| --- | --- | --- | --- | --- | --- | --- |
| reversal_exhaustion | fisher_transform_reversal_10 | 0.018 | 13.651 | 7.190 | 0.323 | 0.335 |
| trend_following | chandelier_trend | -0.020 | 3.895 | -8.215 | 0.606 | 0.085 |
| volume_confirmation | ease_of_movement_14 | -0.022 | -16.712 | -25.902 | 0.460 | 0.297 |
| reversal_exhaustion | ultimate_oscillator_reversal | -0.020 | -21.153 | -31.931 | 0.539 | 0.307 |
| gap_reaction | opening_gap_regime_score | -0.008 | -17.521 | -43.636 | 1.306 | 0.048 |

Bottom 5 by `net_mean_bps_10`:

| family | strategy | rank_ic_mean | gross_mean_bps | net_mean_bps_10 | turnover | gross_win_rate |
| --- | --- | --- | --- | --- | --- | --- |
| breakout_continuation | squeeze_breakout_20 | 0.017 | -190.170 | -210.170 | 1.000 | 0.000 |
| breakout_continuation | relative_volume_breakout_20 | -0.028 | -20.071 | -45.694 | 1.281 | 0.241 |
| trend_following | elder_ray_trend | -0.007 | -32.996 | -43.987 | 0.550 | 0.301 |
| gap_reaction | opening_gap_regime_score | -0.008 | -17.521 | -43.636 | 1.306 | 0.048 |
| reversal_exhaustion | ultimate_oscillator_reversal | -0.020 | -21.153 | -31.931 | 0.539 | 0.307 |
