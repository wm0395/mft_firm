# Narrow Falsification Report

## Tail Diagnostics

| hypothesis_id | cost_bps | fold_count | mean_delta_vs_baseline_pct | delta_ci_low_pct | delta_ci_high_pct | paired_t_stat | paired_p_value | left_tail_delta_pct | right_tail_retention | worst_fold_improvement_pct | best_fold_damage_pct | bh_p_value | decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| doji_gap_fade_low_soft_aggressive | 10.000 | 24 | 0.864 | -0.012 | 1.781 | 1.560 | 0.132 | 3.846 | 0.783 | 6.158 | -3.376 | 0.478 | reject_right_tail_loss |
| doji_gap_fade_low_drawdown_only | 10.000 | 24 | 0.694 | -0.324 | 1.700 | 1.098 | 0.284 | 4.174 | 0.672 | 6.767 | -4.280 | 0.619 | reject_right_tail_loss |
| inside_outside_vol_expansion_high_drawdown_only | 10.000 | 24 | -0.354 | -0.912 | 0.140 | -1.053 | 0.303 | 1.026 | 0.774 | 1.336 | -0.875 | 0.619 | reject_right_tail_loss |
| oscillator_family_gap_fade_low_soft_aggressive | 10.000 | 24 | 0.046 | -0.588 | 0.772 | 0.111 | 0.912 | 1.877 | 0.919 | 6.785 | 0.709 | 0.977 | reject_right_tail_loss |
| support_trendline_vol_expansion_high_soft_aggressive | 10.000 | 24 | 0.190 | -0.438 | 0.786 | 0.512 | 0.613 | 0.988 | 0.951 | 0.841 | 1.137 | 0.836 | research_only_not_significant |
| doji_gap_fade_low_soft_aggressive | 25.000 | 24 | 1.073 | 0.188 | 1.986 | 1.932 | 0.066 | 4.008 | 0.792 | 6.400 | -3.246 | 0.329 | reject_right_tail_loss |
| doji_gap_fade_low_drawdown_only | 25.000 | 24 | 0.920 | -0.093 | 1.923 | 1.454 | 0.159 | 4.351 | 0.679 | 7.019 | -4.120 | 0.478 | reject_right_tail_loss |
| inside_outside_vol_expansion_high_drawdown_only | 25.000 | 24 | -0.003 | -0.596 | 0.581 | -0.008 | 0.994 | 1.921 | 0.778 | 4.283 | -0.829 | 0.994 | reject_right_tail_loss |
| oscillator_family_gap_fade_low_soft_aggressive | 25.000 | 24 | 0.085 | -0.554 | 0.812 | 0.204 | 0.840 | 1.925 | 0.921 | 6.886 | 0.747 | 0.970 | reject_right_tail_loss |
| support_trendline_vol_expansion_high_soft_aggressive | 25.000 | 24 | 0.246 | -0.378 | 0.846 | 0.665 | 0.513 | 1.046 | 0.953 | 0.834 | 1.112 | 0.836 | research_only_not_significant |
| doji_gap_fade_low_soft_aggressive | 50.000 | 24 | 1.391 | 0.454 | 2.331 | 2.384 | 0.026 | 4.453 | 0.762 | 6.801 | -3.030 | 0.329 | reject_right_tail_loss |
| doji_gap_fade_low_drawdown_only | 50.000 | 24 | 1.351 | 0.294 | 2.392 | 2.054 | 0.051 | 5.007 | 0.670 | 7.435 | -3.857 | 0.329 | reject_right_tail_loss |
| inside_outside_vol_expansion_high_drawdown_only | 50.000 | 24 | 0.243 | -0.418 | 0.940 | 0.565 | 0.577 | 2.718 | 0.709 | 4.652 | -0.752 | 0.836 | reject_right_tail_loss |
| oscillator_family_gap_fade_low_soft_aggressive | 50.000 | 24 | 0.116 | -0.552 | 0.843 | 0.272 | 0.788 | 2.140 | 0.904 | 7.055 | 0.809 | 0.970 | reject_right_tail_loss |
| support_trendline_vol_expansion_high_soft_aggressive | 50.000 | 24 | 0.362 | -0.245 | 0.949 | 0.995 | 0.330 | 1.222 | 0.958 | 0.822 | 1.070 | 0.619 | research_only_not_significant |

## Aggregate Metrics

| hypothesis_id | cost_bps | fold_count | baseline_return_pct | variant_return_pct | delta_return_pct | negative_fold_rate | worst_fold_sharpe | latest_fold_sharpe | avg_exposure_multiplier |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| doji_gap_fade_low_soft_aggressive | 10.000 | 24 | -12.169 | 8.567 | 20.736 | 0.583 | -26.471 | -3.207 | 0.621 |
| doji_gap_fade_low_drawdown_only | 10.000 | 24 | -12.169 | 4.484 | 16.653 | 0.583 | -26.471 | -3.572 | 0.553 |
| inside_outside_vol_expansion_high_drawdown_only | 10.000 | 24 | 30.389 | 21.904 | -8.485 | 0.458 | -20.836 | 8.924 | 0.793 |
| oscillator_family_gap_fade_low_soft_aggressive | 10.000 | 24 | 23.746 | 24.854 | 1.108 | 0.500 | -21.511 | -0.450 | 0.766 |
| support_trendline_vol_expansion_high_soft_aggressive | 10.000 | 24 | 13.781 | 18.341 | 4.559 | 0.417 | -23.464 | 0.748 | 0.745 |
| doji_gap_fade_low_soft_aggressive | 25.000 | 24 | -22.483 | 3.267 | 25.751 | 0.583 | -27.471 | -3.917 | 0.605 |
| doji_gap_fade_low_drawdown_only | 25.000 | 24 | -22.483 | -0.399 | 22.084 | 0.583 | -27.471 | -4.319 | 0.543 |
| inside_outside_vol_expansion_high_drawdown_only | 25.000 | 24 | 16.382 | 16.313 | -0.069 | 0.500 | -16.385 | 7.885 | 0.732 |
| oscillator_family_gap_fade_low_soft_aggressive | 25.000 | 24 | 19.563 | 21.597 | 2.033 | 0.500 | -22.093 | -1.006 | 0.763 |
| support_trendline_vol_expansion_high_soft_aggressive | 25.000 | 24 | 8.722 | 14.621 | 5.899 | 0.500 | -23.978 | 0.081 | 0.733 |
| doji_gap_fade_low_soft_aggressive | 50.000 | 24 | -39.580 | -6.191 | 33.388 | 0.625 | -29.058 | -5.330 | 0.571 |
| doji_gap_fade_low_drawdown_only | 50.000 | 24 | -39.580 | -7.164 | 32.416 | 0.625 | -29.058 | -5.538 | 0.514 |
| inside_outside_vol_expansion_high_drawdown_only | 50.000 | 24 | -6.794 | -0.961 | 5.834 | 0.667 | -17.180 | 6.063 | 0.681 |
| oscillator_family_gap_fade_low_soft_aggressive | 50.000 | 24 | 12.608 | 15.392 | 2.784 | 0.542 | -23.034 | -1.889 | 0.749 |
| support_trendline_vol_expansion_high_soft_aggressive | 50.000 | 24 | 0.314 | 8.991 | 8.678 | 0.542 | -24.832 | -0.936 | 0.727 |

## Gate Stability

| hypothesis_id | cost_bps | fold_count | threshold_mean | threshold_std | multiplier_down_mean | multiplier_up_mean | activation_rate | avg_exposure_multiplier |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| doji_gap_fade_low_soft_aggressive | 10.000 | 24 | 0.256 | 0.027 | 0.271 | 1.213 | 1.000 | 0.621 |
| doji_gap_fade_low_drawdown_only | 10.000 | 24 | 0.256 | 0.027 | 0.292 | 1.000 | 0.625 | 0.553 |
| inside_outside_vol_expansion_high_drawdown_only | 10.000 | 24 | 0.104 | 0.038 | 0.583 | 1.000 | 0.482 | 0.793 |
| oscillator_family_gap_fade_low_soft_aggressive | 10.000 | 24 | 0.267 | 0.029 | 0.406 | 1.231 | 1.000 | 0.766 |
| support_trendline_vol_expansion_high_soft_aggressive | 10.000 | 24 | 0.116 | 0.040 | 0.344 | 1.200 | 1.000 | 0.745 |
| doji_gap_fade_low_soft_aggressive | 25.000 | 24 | 0.252 | 0.024 | 0.271 | 1.213 | 1.000 | 0.605 |
| doji_gap_fade_low_drawdown_only | 25.000 | 24 | 0.253 | 0.024 | 0.292 | 1.000 | 0.639 | 0.543 |
| inside_outside_vol_expansion_high_drawdown_only | 25.000 | 24 | 0.106 | 0.040 | 0.500 | 1.000 | 0.482 | 0.732 |
| oscillator_family_gap_fade_low_soft_aggressive | 25.000 | 24 | 0.267 | 0.029 | 0.396 | 1.231 | 1.000 | 0.763 |
| support_trendline_vol_expansion_high_soft_aggressive | 25.000 | 24 | 0.118 | 0.040 | 0.344 | 1.188 | 1.000 | 0.733 |
| doji_gap_fade_low_soft_aggressive | 50.000 | 24 | 0.247 | 0.021 | 0.260 | 1.200 | 1.000 | 0.571 |
| doji_gap_fade_low_drawdown_only | 50.000 | 24 | 0.247 | 0.021 | 0.271 | 1.000 | 0.667 | 0.514 |
| inside_outside_vol_expansion_high_drawdown_only | 50.000 | 24 | 0.117 | 0.043 | 0.417 | 1.000 | 0.540 | 0.681 |
| oscillator_family_gap_fade_low_soft_aggressive | 50.000 | 24 | 0.267 | 0.029 | 0.375 | 1.225 | 1.000 | 0.749 |
| support_trendline_vol_expansion_high_soft_aggressive | 50.000 | 24 | 0.119 | 0.040 | 0.344 | 1.181 | 1.000 | 0.727 |

White Reality Check / Hansen SPA are not implemented in this sprint.