# Alpha Regime Falsification Report

## Status Counts

| falsification_status | count |
| --- | --- |
| falsified_right_tail_loss | 35 |
| not_significant | 13 |

## Top Rows

| alpha | variant | indicator | side | falsification_status | failure_reasons | hypothesis_score | mean_delta_vs_baseline_pct | delta_ci_low_pct | paired_p_value | left_tail_delta_pct | right_tail_retention | max_drawdown_delta_pct | top_indicator_rate | selection_count | left_tail_count | right_tail_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| doji_reversal_score | soft_aggressive | gap_fade | low | falsified_right_tail_loss | right_tail<95%,ci_low<=0,pvalue>=0.05,top_indicator_rate<50% | 3.6463 | 0.4052 | -0.0320 | 0.1771 | 2.0907 | 0.9177 | 0.7287 | 0.2917 | 7 | 2 | 2 |
| doji_reversal_score | drawdown_only_throttle | gap_fade | low | falsified_right_tail_loss | right_tail<95%,ci_low<=0,pvalue>=0.05,top_indicator_rate<50% | 2.8342 | 0.3186 | -0.0528 | 0.2062 | 1.5546 | 0.9173 | 0.6274 | 0.2917 | 7 | 2 | 2 |
| bollinger_percent_b_mean_reversion_20 | soft_aggressive | gap_fade | low | falsified_right_tail_loss | right_tail<95%,ci_low<=0,pvalue>=0.05,top_indicator_rate<50% | 2.1782 | 0.1398 | -0.2697 | 0.5749 | 1.3278 | 0.9339 | 0.4891 | 0.2917 | 7 | 1 | 2 |
| inside_outside_bar_score | drawdown_only_throttle | volatility_expansion | high | falsified_right_tail_loss | right_tail<95%,ci_low<=0,pvalue>=0.05,top_indicator_rate<50% | 2.1074 | 0.1638 | -0.1486 | 0.4237 | 1.2680 | 0.9185 | 0.4709 | 0.3333 | 5 | 2 | 0 |
| support_trendline_position_20 | drawdown_only_throttle | volatility_expansion | high | falsified_right_tail_loss | right_tail<95%,ci_low<=0,pvalue>=0.05,top_indicator_rate<50% | 1.8687 | 0.1204 | -0.1314 | 0.4517 | 1.0699 | 0.9462 | 0.4272 | 0.2917 | 7 | 2 | 2 |
| hammer_shooting_star_score | drawdown_only_throttle | volatility_expansion | high | falsified_right_tail_loss | right_tail<95%,ci_low<=0,pvalue>=0.05,top_indicator_rate<50% | 1.7204 | 0.0979 | -0.2134 | 0.6199 | 1.0973 | 0.9239 | 0.4065 | 0.2500 | 6 | 3 | 1 |
| failed_reversal_score | drawdown_only_throttle | gap_fade | low | falsified_right_tail_loss | right_tail<95%,ci_low<=0,pvalue>=0.05,top_indicator_rate<50% | 1.6623 | -0.0758 | -0.4831 | 0.7688 | 1.2278 | 0.8983 | 0.5163 | 0.2500 | 6 | 3 | 0 |
| inverse_fisher_rsi_reversal_10 | drawdown_only_throttle | volatility_expansion | high | falsified_right_tail_loss | right_tail<95%,ci_low<=0,pvalue>=0.05,top_indicator_rate<50% | 1.6246 | 0.0610 | -0.3092 | 0.8004 | 1.1410 | 0.8783 | 0.5026 | 0.2917 | 7 | 2 | 0 |
| inside_outside_bar_score | soft_aggressive | volatility_expansion | high | falsified_right_tail_loss | right_tail<95%,ci_low<=0,pvalue>=0.05,top_indicator_rate<50% | 1.5418 | 0.1298 | -0.2357 | 0.5753 | 0.9446 | 0.9095 | 0.3329 | 0.3333 | 5 | 2 | 0 |
| bollinger_percent_b_mean_reversion_20 | drawdown_only_throttle | gap_fade | low | falsified_right_tail_loss | right_tail<95%,ci_low<=0,pvalue>=0.05,top_indicator_rate<50% | 1.4914 | 0.0321 | -0.2883 | 0.8718 | 1.0407 | 0.9107 | 0.3979 | 0.2917 | 7 | 1 | 2 |
| parabolic_sar_trend | drawdown_only_throttle | volatility_expansion | high | falsified_right_tail_loss | right_tail<95%,ci_low<=0,pvalue>=0.05,top_indicator_rate<50% | 1.4885 | 0.1247 | -0.1736 | 0.5196 | 0.8704 | 0.8887 | 0.4680 | 0.2917 | 6 | 2 | 2 |
| fisher_transform_reversal_10 | drawdown_only_throttle | gap_fade | low | falsified_right_tail_loss | right_tail<95%,ci_low<=0,pvalue>=0.05,top_indicator_rate<50% | 1.4479 | 0.0747 | -0.2022 | 0.6785 | 0.8366 | 0.9407 | 0.3739 | 0.2500 | 6 | 1 | 1 |
| piercing_dark_cloud_score | drawdown_only_throttle | volatility_compression | high | falsified_right_tail_loss | right_tail<95%,ci_low<=0,pvalue>=0.05,top_indicator_rate<50% | 1.2778 | 0.1292 | -0.1127 | 0.4005 | 0.7662 | 0.8917 | 0.3824 | 0.2083 | 3 | 3 | 0 |
| chandelier_trend | drawdown_only_throttle | gap_fade | low | falsified_right_tail_loss | right_tail<95%,ci_low<=0,pvalue>=0.05,top_indicator_rate<50% | 1.2674 | 0.0451 | -0.2097 | 0.7790 | 0.7585 | 0.9134 | 0.4193 | 0.2917 | 7 | 3 | 1 |
| inverse_fisher_rsi_reversal_10 | soft_aggressive | volatility_expansion | high | falsified_right_tail_loss | right_tail<95%,ci_low<=0,pvalue>=0.05,top_indicator_rate<50% | 1.1777 | 0.0316 | -0.3952 | 0.9091 | 0.8115 | 0.8654 | 0.4956 | 0.2917 | 7 | 2 | 0 |
| trend_volume_composite | drawdown_only_throttle | gap_fade | low | falsified_right_tail_loss | right_tail<95%,ci_low<=0,pvalue>=0.05,top_indicator_rate<50% | 1.1537 | -0.2521 | -0.5706 | 0.2146 | 0.6820 | 0.9353 | 0.3638 | 0.3333 | 8 | 2 | 1 |
| parabolic_sar_trend | soft_aggressive | volatility_expansion | high | falsified_right_tail_loss | right_tail<95%,ci_low<=0,pvalue>=0.05,top_indicator_rate<50% | 1.0821 | 0.0465 | -0.3397 | 0.8501 | 0.7415 | 0.9076 | 0.2712 | 0.2917 | 6 | 2 | 2 |
| hybrid_confirmation | drawdown_only_throttle | volatility_compression | high | falsified_right_tail_loss | right_tail<95%,ci_low<=0,pvalue>=0.05,top_indicator_rate<50% | 0.9750 | -0.2043 | -0.5380 | 0.3201 | 0.7319 | 0.9063 | 0.3138 | 0.2083 | 4 | 1 | 1 |
| failed_breakout_score_20 | drawdown_only_throttle | gap_fade | low | falsified_right_tail_loss | right_tail<95%,ci_low<=0,pvalue>=0.05,top_indicator_rate<50% | 0.9182 | -0.2824 | -0.7009 | 0.2898 | 0.6973 | 0.8803 | 0.3541 | 0.2917 | 7 | 2 | 1 |
| failed_breakout_score_20 | soft_aggressive | gap_fade | low | falsified_right_tail_loss | right_tail<95%,ci_low<=0,pvalue>=0.05,top_indicator_rate<50% | 0.8264 | -0.3535 | -0.9972 | 0.3763 | 0.5736 | 0.8907 | 0.3443 | 0.2917 | 7 | 2 | 1 |

## Acceptance Contract

- Right-tail retention must be at least 95%.
- Bootstrap lower CI and paired p-value must both clear significance.
- Top indicator rate must be at least 50% before promotion.
- Rows failing these tests remain research-only or rejected.