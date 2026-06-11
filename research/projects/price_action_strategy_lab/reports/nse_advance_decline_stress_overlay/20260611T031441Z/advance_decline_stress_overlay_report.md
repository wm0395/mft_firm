# Advance-Decline Stress Overlay Report

Status: research-only falsification sprint.

## Metrics

| hypothesis_id | cost_bps | return_pct | baseline_return_pct | delta_return_pct | ann_sharpe | baseline_ann_sharpe | max_drawdown_pct | baseline_max_drawdown_pct | negative_fold_rate | worst_fold_sharpe | latest_fold_sharpe | turnover | average_exposure |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_25_alpha_stack:baseline | 10.000 | 24.356 | 24.356 | 0.000 | 1.891 | 1.891 | -7.498 | -7.498 | 0.375 | -26.261 | 4.621 | 0.371 | 1.000 |
| structure_level:baseline | 10.000 | 32.223 | 32.223 | 0.000 | 2.382 | 2.382 | -8.349 | -8.349 | 0.375 | -20.613 | 7.280 | 0.558 | 1.000 |
| core_structure:baseline | 10.000 | 30.576 | 30.576 | 0.000 | 2.143 | 2.143 | -8.551 | -8.551 | 0.458 | -22.281 | 4.845 | 0.410 | 1.000 |
| reversal_exhaustion:baseline | 10.000 | 17.912 | 17.912 | 0.000 | -0.296 | -0.296 | -11.142 | -11.142 | 0.542 | -29.090 | -1.505 | 0.377 | 1.000 |
| full_25_alpha_stack:advance_decline_ratio_lag1_low:soft_aggressive | 10.000 | 19.742 | 24.356 | -4.614 | 2.113 | 1.891 | -6.030 | -7.498 | 0.375 | -20.857 | 4.380 | 0.333 | 0.911 |
| full_25_alpha_stack:advance_decline_ratio_lag1_low:drawdown_only | 10.000 | 18.031 | 24.356 | -6.325 | 2.122 | 1.891 | -5.538 | -7.498 | 0.375 | -21.074 | 4.398 | 0.304 | 0.833 |
| full_25_alpha_stack:advance_decline_ratio_lag1_low:reduce_only | 10.000 | 20.123 | 24.356 | -4.234 | 2.132 | 1.891 | -6.005 | -7.498 | 0.375 | -23.337 | 4.548 | 0.327 | 0.889 |
| structure_level:advance_decline_ratio_lag1_low:soft_aggressive | 10.000 | 27.640 | 32.223 | -4.583 | 2.344 | 2.382 | -6.843 | -8.349 | 0.375 | -15.453 | 6.531 | 0.501 | 0.911 |
| structure_level:advance_decline_ratio_lag1_low:drawdown_only | 10.000 | 25.187 | 32.223 | -7.036 | 2.363 | 2.382 | -6.288 | -8.349 | 0.375 | -15.640 | 6.588 | 0.458 | 0.833 |
| structure_level:advance_decline_ratio_lag1_low:reduce_only | 10.000 | 27.512 | 32.223 | -4.711 | 2.483 | 2.382 | -6.824 | -8.349 | 0.375 | -17.612 | 7.062 | 0.491 | 0.889 |
| core_structure:advance_decline_ratio_lag1_low:soft_aggressive | 10.000 | 27.249 | 30.576 | -3.327 | 2.246 | 2.143 | -6.596 | -8.551 | 0.458 | -16.514 | 4.689 | 0.371 | 0.911 |
| core_structure:advance_decline_ratio_lag1_low:drawdown_only | 10.000 | 24.767 | 30.576 | -5.809 | 2.268 | 2.143 | -6.057 | -8.551 | 0.458 | -16.716 | 4.700 | 0.339 | 0.833 |
| core_structure:advance_decline_ratio_lag1_low:reduce_only | 10.000 | 26.679 | 30.576 | -3.897 | 2.397 | 2.143 | -6.730 | -8.551 | 0.458 | -18.888 | 4.796 | 0.363 | 0.889 |
| reversal_exhaustion:advance_decline_ratio_lag1_low:soft_aggressive | 10.000 | 12.938 | 17.912 | -4.974 | -0.119 | -0.296 | -9.882 | -11.142 | 0.542 | -22.561 | -2.520 | 0.336 | 0.911 |
| reversal_exhaustion:advance_decline_ratio_lag1_low:drawdown_only | 10.000 | 11.706 | 17.912 | -6.206 | -0.117 | -0.296 | -9.084 | -11.142 | 0.542 | -22.833 | -2.492 | 0.307 | 0.833 |
| reversal_exhaustion:advance_decline_ratio_lag1_low:reduce_only | 10.000 | 13.755 | 17.912 | -4.157 | -0.143 | -0.296 | -9.774 | -11.142 | 0.542 | -25.669 | -2.167 | 0.331 | 0.889 |
| full_25_alpha_stack:nifty_return_5d_lag1_low:soft_aggressive | 10.000 | 18.935 | 24.356 | -5.421 | 1.573 | 1.891 | -5.309 | -7.498 | 0.375 | -26.261 | 4.621 | 0.336 | 0.918 |
| full_25_alpha_stack:nifty_return_5d_lag1_low:drawdown_only | 10.000 | 17.324 | 24.356 | -7.032 | 1.588 | 1.891 | -4.917 | -7.498 | 0.375 | -26.261 | 4.621 | 0.307 | 0.839 |
| full_25_alpha_stack:nifty_return_5d_lag1_low:reduce_only | 10.000 | 19.641 | 24.356 | -4.716 | 1.704 | 1.891 | -5.784 | -7.498 | 0.375 | -26.261 | 4.621 | 0.329 | 0.893 |
| structure_level:nifty_return_5d_lag1_low:soft_aggressive | 10.000 | 28.990 | 32.223 | -3.233 | 2.163 | 2.382 | -6.059 | -8.349 | 0.417 | -14.942 | 7.280 | 0.507 | 0.918 |
| structure_level:nifty_return_5d_lag1_low:drawdown_only | 10.000 | 26.387 | 32.223 | -5.836 | 2.177 | 2.382 | -5.606 | -8.349 | 0.417 | -15.228 | 7.280 | 0.464 | 0.839 |
| structure_level:nifty_return_5d_lag1_low:reduce_only | 10.000 | 28.299 | 32.223 | -3.924 | 2.294 | 2.382 | -6.528 | -8.349 | 0.375 | -18.140 | 7.280 | 0.495 | 0.893 |
| core_structure:nifty_return_5d_lag1_low:soft_aggressive | 10.000 | 26.342 | 30.576 | -4.234 | 1.993 | 2.143 | -6.061 | -8.551 | 0.458 | -16.272 | 4.845 | 0.377 | 0.918 |
| core_structure:nifty_return_5d_lag1_low:drawdown_only | 10.000 | 23.973 | 30.576 | -6.603 | 2.015 | 2.143 | -5.583 | -8.551 | 0.458 | -16.761 | 4.845 | 0.345 | 0.839 |
| core_structure:nifty_return_5d_lag1_low:reduce_only | 10.000 | 26.138 | 30.576 | -4.438 | 2.186 | 2.143 | -6.304 | -8.551 | 0.458 | -20.771 | 4.845 | 0.367 | 0.893 |
| reversal_exhaustion:nifty_return_5d_lag1_low:soft_aggressive | 10.000 | 9.521 | 17.912 | -8.391 | -0.673 | -0.296 | -8.357 | -11.142 | 0.542 | -29.090 | -1.505 | 0.337 | 0.918 |
| reversal_exhaustion:nifty_return_5d_lag1_low:drawdown_only | 10.000 | 8.708 | 17.912 | -9.205 | -0.655 | -0.296 | -7.729 | -11.142 | 0.542 | -29.090 | -1.505 | 0.309 | 0.839 |
| reversal_exhaustion:nifty_return_5d_lag1_low:reduce_only | 10.000 | 11.719 | 17.912 | -6.193 | -0.511 | -0.296 | -8.879 | -11.142 | 0.542 | -29.090 | -1.505 | 0.332 | 0.893 |
| full_25_alpha_stack:advance_decline_ratio_5d_lag1_low:soft_aggressive | 10.000 | 18.787 | 24.356 | -5.569 | 1.833 | 1.891 | -5.567 | -7.498 | 0.375 | -20.231 | 4.621 | 0.333 | 0.909 |
| full_25_alpha_stack:advance_decline_ratio_5d_lag1_low:drawdown_only | 10.000 | 17.196 | 24.356 | -7.160 | 1.840 | 1.891 | -5.145 | -7.498 | 0.375 | -20.626 | 4.621 | 0.304 | 0.832 |

## Tail Diagnostics

| hypothesis_id | cost_bps | mean_delta_vs_baseline | left_tail_delta | right_tail_retention | top_decile_retention | bottom_decile_improvement | best_fold_damage | worst_fold_improvement | ci_low | ci_high | paired_t_stat | paired_p_value | bh_p_value |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_25_alpha_stack:baseline | 10.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| structure_level:baseline | 10.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| core_structure:baseline | 10.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| reversal_exhaustion:baseline | 10.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| full_25_alpha_stack:advance_decline_ratio_lag1_low:soft_aggressive | 10.000 | -0.192 | 0.520 | 0.833 | 0.850 | 0.915 | -2.108 | 1.822 | -0.470 | 0.076 | -1.117 | 0.275 | 0.739 |
| full_25_alpha_stack:advance_decline_ratio_lag1_low:drawdown_only | 10.000 | -0.264 | 0.831 | 0.763 | 0.777 | 1.320 | -2.615 | 2.249 | -0.596 | 0.075 | -1.238 | 0.228 | 0.739 |
| full_25_alpha_stack:advance_decline_ratio_lag1_low:reduce_only | 10.000 | -0.176 | 0.553 | 0.842 | 0.851 | 0.878 | -1.748 | 1.494 | -0.398 | 0.049 | -1.243 | 0.227 | 0.739 |
| structure_level:advance_decline_ratio_lag1_low:soft_aggressive | 10.000 | -0.191 | 0.503 | 0.854 | 0.879 | 1.105 | -1.332 | 0.915 | -0.489 | 0.094 | -1.041 | 0.309 | 0.739 |
| structure_level:advance_decline_ratio_lag1_low:drawdown_only | 10.000 | -0.293 | 0.839 | 0.781 | 0.802 | 1.553 | -2.052 | 1.511 | -0.656 | 0.073 | -1.266 | 0.218 | 0.739 |
| structure_level:advance_decline_ratio_lag1_low:reduce_only | 10.000 | -0.196 | 0.558 | 0.854 | 0.868 | 1.032 | -1.369 | 1.005 | -0.439 | 0.048 | -1.271 | 0.216 | 0.739 |
| core_structure:advance_decline_ratio_lag1_low:soft_aggressive | 10.000 | -0.139 | 0.865 | 0.874 | 0.883 | 1.052 | 0.035 | 2.322 | -0.461 | 0.195 | -0.673 | 0.507 | 0.739 |
| core_structure:advance_decline_ratio_lag1_low:drawdown_only | 10.000 | -0.242 | 1.176 | 0.798 | 0.805 | 1.491 | -0.899 | 2.754 | -0.645 | 0.182 | -0.933 | 0.361 | 0.739 |
| core_structure:advance_decline_ratio_lag1_low:reduce_only | 10.000 | -0.162 | 0.782 | 0.865 | 0.870 | 0.991 | -0.599 | 1.828 | -0.431 | 0.120 | -0.939 | 0.358 | 0.739 |
| reversal_exhaustion:advance_decline_ratio_lag1_low:soft_aggressive | 10.000 | -0.207 | 0.624 | 0.907 | 0.858 | 1.082 | -2.743 | 1.187 | -0.518 | 0.099 | -1.055 | 0.302 | 0.739 |
| reversal_exhaustion:advance_decline_ratio_lag1_low:drawdown_only | 10.000 | -0.259 | 1.100 | 0.827 | 0.784 | 1.686 | -3.610 | 2.016 | -0.665 | 0.149 | -0.997 | 0.329 | 0.739 |
| reversal_exhaustion:advance_decline_ratio_lag1_low:reduce_only | 10.000 | -0.173 | 0.732 | 0.885 | 0.856 | 1.121 | -2.410 | 1.340 | -0.444 | 0.098 | -1.001 | 0.327 | 0.739 |
| full_25_alpha_stack:nifty_return_5d_lag1_low:soft_aggressive | 10.000 | -0.226 | 0.677 | 0.771 | 0.776 | 1.151 | -1.030 | 2.200 | -0.585 | 0.134 | -1.002 | 0.327 | 0.739 |
| full_25_alpha_stack:nifty_return_5d_lag1_low:drawdown_only | 10.000 | -0.293 | 0.970 | 0.708 | 0.712 | 1.530 | -1.668 | 2.583 | -0.691 | 0.113 | -1.139 | 0.267 | 0.739 |
| full_25_alpha_stack:nifty_return_5d_lag1_low:reduce_only | 10.000 | -0.196 | 0.645 | 0.805 | 0.808 | 1.016 | -1.114 | 1.716 | -0.462 | 0.074 | -1.144 | 0.264 | 0.739 |
| structure_level:nifty_return_5d_lag1_low:soft_aggressive | 10.000 | -0.135 | 0.875 | 0.820 | 0.807 | 1.689 | -3.496 | 1.899 | -0.531 | 0.255 | -0.545 | 0.591 | 0.742 |
| structure_level:nifty_return_5d_lag1_low:drawdown_only | 10.000 | -0.243 | 1.169 | 0.751 | 0.739 | 2.071 | -3.952 | 2.384 | -0.685 | 0.217 | -0.849 | 0.404 | 0.739 |
| structure_level:nifty_return_5d_lag1_low:reduce_only | 10.000 | -0.163 | 0.777 | 0.834 | 0.825 | 1.376 | -2.645 | 1.584 | -0.459 | 0.143 | -0.856 | 0.401 | 0.739 |
| core_structure:nifty_return_5d_lag1_low:soft_aggressive | 10.000 | -0.176 | 0.839 | 0.829 | 0.802 | 1.333 | -1.628 | 3.054 | -0.573 | 0.236 | -0.681 | 0.503 | 0.739 |
| core_structure:nifty_return_5d_lag1_low:drawdown_only | 10.000 | -0.275 | 1.154 | 0.758 | 0.735 | 1.740 | -2.356 | 3.403 | -0.736 | 0.216 | -0.907 | 0.374 | 0.739 |
| core_structure:nifty_return_5d_lag1_low:reduce_only | 10.000 | -0.185 | 0.767 | 0.838 | 0.823 | 1.155 | -1.574 | 2.257 | -0.493 | 0.142 | -0.914 | 0.370 | 0.739 |
| reversal_exhaustion:nifty_return_5d_lag1_low:soft_aggressive | 10.000 | -0.350 | 0.651 | 0.821 | 0.730 | 1.330 | -6.127 | 2.705 | -0.898 | 0.152 | -1.058 | 0.301 | 0.739 |
| reversal_exhaustion:nifty_return_5d_lag1_low:drawdown_only | 10.000 | -0.384 | 1.125 | 0.751 | 0.671 | 1.908 | -6.580 | 3.366 | -0.993 | 0.179 | -1.039 | 0.310 | 0.739 |
| reversal_exhaustion:nifty_return_5d_lag1_low:reduce_only | 10.000 | -0.258 | 0.747 | 0.833 | 0.780 | 1.266 | -4.416 | 2.232 | -0.665 | 0.118 | -1.045 | 0.307 | 0.739 |
| full_25_alpha_stack:advance_decline_ratio_5d_lag1_low:soft_aggressive | 10.000 | -0.232 | 0.709 | 0.773 | 0.768 | 1.348 | -1.710 | 1.942 | -0.571 | 0.103 | -1.076 | 0.293 | 0.739 |
| full_25_alpha_stack:advance_decline_ratio_5d_lag1_low:drawdown_only | 10.000 | -0.298 | 0.998 | 0.710 | 0.706 | 1.704 | -2.265 | 2.355 | -0.684 | 0.088 | -1.184 | 0.249 | 0.739 |

## Targeting

| hypothesis_id | cost_bps | weak_folds_correctly_reduced | normal_folds_incorrectly_reduced | false_positive_fold_cost | false_negative_weak_fold_cost | stress_activation_rate | avg_exposure_weak_folds | avg_exposure_normal_folds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_25_alpha_stack:baseline | 10.000 | 0 | 0 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| structure_level:baseline | 10.000 | 0 | 0 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| core_structure:baseline | 10.000 | 0 | 0 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| reversal_exhaustion:baseline | 10.000 | 0 | 0 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| full_25_alpha_stack:advance_decline_ratio_lag1_low:soft_aggressive | 10.000 | 6 | 12 | -7.282 | 0.000 | 0.222 | 0.850 | 0.931 |
| full_25_alpha_stack:advance_decline_ratio_lag1_low:drawdown_only | 10.000 | 6 | 18 | -11.310 | 0.000 | 0.222 | 0.780 | 0.851 |
| full_25_alpha_stack:advance_decline_ratio_lag1_low:reduce_only | 10.000 | 6 | 18 | -7.551 | 0.000 | 0.222 | 0.853 | 0.901 |
| structure_level:advance_decline_ratio_lag1_low:soft_aggressive | 10.000 | 6 | 12 | -7.485 | 0.000 | 0.222 | 0.837 | 0.936 |
| structure_level:advance_decline_ratio_lag1_low:drawdown_only | 10.000 | 6 | 18 | -12.070 | 0.000 | 0.222 | 0.768 | 0.855 |
| structure_level:advance_decline_ratio_lag1_low:reduce_only | 10.000 | 6 | 18 | -8.059 | 0.000 | 0.222 | 0.845 | 0.903 |
| core_structure:advance_decline_ratio_lag1_low:soft_aggressive | 10.000 | 6 | 12 | -7.169 | 0.000 | 0.222 | 0.817 | 0.943 |
| core_structure:advance_decline_ratio_lag1_low:drawdown_only | 10.000 | 6 | 18 | -12.867 | 0.000 | 0.222 | 0.750 | 0.861 |
| core_structure:advance_decline_ratio_lag1_low:reduce_only | 10.000 | 6 | 18 | -8.591 | 0.000 | 0.222 | 0.833 | 0.907 |
| reversal_exhaustion:advance_decline_ratio_lag1_low:soft_aggressive | 10.000 | 6 | 12 | -8.042 | 0.000 | 0.222 | 0.877 | 0.922 |
| reversal_exhaustion:advance_decline_ratio_lag1_low:drawdown_only | 10.000 | 6 | 18 | -12.808 | 0.000 | 0.222 | 0.804 | 0.843 |
| reversal_exhaustion:advance_decline_ratio_lag1_low:reduce_only | 10.000 | 6 | 18 | -8.548 | 0.000 | 0.222 | 0.869 | 0.896 |
| full_25_alpha_stack:nifty_return_5d_lag1_low:soft_aggressive | 10.000 | 4 | 9 | -10.368 | -0.541 | 0.214 | 0.877 | 0.931 |
| full_25_alpha_stack:nifty_return_5d_lag1_low:drawdown_only | 10.000 | 4 | 14 | -12.852 | 0.000 | 0.214 | 0.804 | 0.851 |
| full_25_alpha_stack:nifty_return_5d_lag1_low:reduce_only | 10.000 | 4 | 14 | -8.585 | 0.000 | 0.214 | 0.869 | 0.901 |
| structure_level:nifty_return_5d_lag1_low:soft_aggressive | 10.000 | 4 | 9 | -9.701 | -0.476 | 0.214 | 0.796 | 0.958 |
| structure_level:nifty_return_5d_lag1_low:drawdown_only | 10.000 | 5 | 13 | -12.849 | 0.000 | 0.214 | 0.732 | 0.875 |
| structure_level:nifty_return_5d_lag1_low:reduce_only | 10.000 | 5 | 13 | -8.586 | 0.000 | 0.214 | 0.821 | 0.917 |
| core_structure:nifty_return_5d_lag1_low:soft_aggressive | 10.000 | 5 | 8 | -10.252 | -0.394 | 0.214 | 0.756 | 0.972 |
| core_structure:nifty_return_5d_lag1_low:drawdown_only | 10.000 | 6 | 12 | -13.529 | 0.000 | 0.214 | 0.696 | 0.887 |
| core_structure:nifty_return_5d_lag1_low:reduce_only | 10.000 | 6 | 12 | -9.040 | 0.000 | 0.214 | 0.798 | 0.925 |
| reversal_exhaustion:nifty_return_5d_lag1_low:soft_aggressive | 10.000 | 3 | 10 | -13.736 | -1.163 | 0.214 | 0.945 | 0.909 |
| reversal_exhaustion:nifty_return_5d_lag1_low:drawdown_only | 10.000 | 4 | 14 | -15.953 | 0.000 | 0.214 | 0.863 | 0.831 |
| reversal_exhaustion:nifty_return_5d_lag1_low:reduce_only | 10.000 | 4 | 14 | -10.674 | 0.000 | 0.214 | 0.909 | 0.888 |
| full_25_alpha_stack:advance_decline_ratio_5d_lag1_low:soft_aggressive | 10.000 | 5 | 12 | -10.502 | -0.331 | 0.224 | 0.884 | 0.918 |
| full_25_alpha_stack:advance_decline_ratio_5d_lag1_low:drawdown_only | 10.000 | 6 | 15 | -13.147 | 0.000 | 0.224 | 0.810 | 0.839 |