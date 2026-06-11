# Support Trendline Stress Confirmation

## Aggregate

| variant | cost_bps | return_pct | cagr_pct | ann_vol_pct | ann_sharpe | max_drawdown_pct | negative_fold_rate | worst_fold_sharpe | latest_fold_sharpe | average_exposure | turnover |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 10.000 | 10.452 | 5.096 | 7.264 | 0.721 | -26.794 | 0.458 | -23.334 | 3.340 | 1.000 | 0.333 |
| volatility_expansion_high | 10.000 | 15.774 | 7.599 | 7.029 | 1.077 | -25.791 | 0.417 | -23.464 | 0.748 | 0.745 | 0.259 |
| breadth_risk_off_high | 10.000 | 20.656 | 9.843 | 7.997 | 1.214 | -26.597 | 0.500 | -20.082 | 3.340 | 0.996 | 0.334 |
| vol_and_breadth | 10.000 | 20.118 | 9.598 | 8.008 | 1.185 | -26.924 | 0.500 | -20.082 | 3.340 | 0.997 | 0.334 |
| baseline | 25.000 | 5.024 | 2.481 | 7.260 | 0.374 | -28.835 | 0.542 | -23.822 | 2.693 | 1.000 | 0.333 |
| volatility_expansion_high | 25.000 | 11.593 | 5.637 | 6.979 | 0.821 | -27.132 | 0.500 | -23.978 | 0.081 | 0.733 | 0.254 |
| breadth_risk_off_high | 25.000 | 12.168 | 5.910 | 7.832 | 0.772 | -28.300 | 0.542 | -20.377 | 2.693 | 0.948 | 0.319 |
| vol_and_breadth | 25.000 | 11.663 | 5.671 | 7.843 | 0.742 | -28.623 | 0.542 | -20.377 | 2.693 | 0.950 | 0.320 |
| baseline | 50.000 | -3.437 | -1.734 | 7.256 | -0.205 | -32.110 | 0.583 | -24.640 | 1.598 | 1.000 | 0.333 |
| volatility_expansion_high | 50.000 | 5.582 | 2.753 | 6.932 | 0.426 | -28.960 | 0.542 | -24.832 | -0.936 | 0.727 | 0.252 |
| breadth_risk_off_high | 50.000 | 3.854 | 1.909 | 7.669 | 0.285 | -31.435 | 0.625 | -21.277 | 1.598 | 0.942 | 0.317 |
| vol_and_breadth | 50.000 | 3.379 | 1.676 | 7.680 | 0.255 | -31.749 | 0.625 | -21.277 | 1.598 | 0.943 | 0.318 |
| baseline | 75.000 | -11.218 | -5.776 | 7.253 | -0.784 | -36.000 | 0.583 | -25.461 | 0.487 | 1.000 | 0.333 |
| volatility_expansion_high | 75.000 | -4.750 | -2.404 | 6.607 | -0.335 | -30.726 | 0.583 | -25.680 | -1.840 | 0.691 | 0.242 |
| breadth_risk_off_high | 75.000 | -3.159 | -1.592 | 7.615 | -0.173 | -34.577 | 0.625 | -22.553 | 0.487 | 0.935 | 0.315 |
| vol_and_breadth | 75.000 | -3.610 | -1.821 | 7.626 | -0.203 | -34.881 | 0.625 | -22.553 | 0.487 | 0.937 | 0.315 |

## Tail

| variant | cost_bps | mean_delta_vs_baseline | left_tail_delta | right_tail_retention | top_decile_retention | bottom_decile_improvement | best_fold_damage | worst_fold_improvement | ci_low | ci_high | paired_t_stat | paired_p_value | bh_p_value |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 10.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| volatility_expansion_high | 10.000 | 0.190 | 0.988 | 0.951 | 1.146 | 0.359 | 1.137 | 0.841 | -0.438 | 0.786 | 0.512 | 0.613 | 0.818 |
| breadth_risk_off_high | 10.000 | 0.387 | 0.682 | 1.117 | 1.211 | 0.885 | 1.137 | 4.513 | -0.249 | 0.997 | 0.977 | 0.339 | 0.746 |
| vol_and_breadth | 10.000 | 0.368 | 0.608 | 1.117 | 1.211 | 0.885 | 1.137 | 4.513 | -0.262 | 0.954 | 0.946 | 0.354 | 0.746 |
| baseline | 25.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| volatility_expansion_high | 25.000 | 0.246 | 1.046 | 0.953 | 1.146 | 0.359 | 1.112 | 0.834 | -0.378 | 0.846 | 0.665 | 0.513 | 0.746 |
| breadth_risk_off_high | 25.000 | 0.284 | 0.685 | 1.084 | 1.158 | 0.874 | 1.112 | 4.551 | -0.351 | 0.884 | 0.740 | 0.467 | 0.746 |
| vol_and_breadth | 25.000 | 0.265 | 0.611 | 1.084 | 1.158 | 0.874 | 1.112 | 4.551 | -0.368 | 0.861 | 0.705 | 0.488 | 0.746 |
| baseline | 50.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| volatility_expansion_high | 50.000 | 0.362 | 1.222 | 0.958 | 1.145 | 0.630 | 1.070 | 0.822 | -0.245 | 0.949 | 0.995 | 0.330 | 0.746 |
| breadth_risk_off_high | 50.000 | 0.311 | 0.692 | 1.087 | 1.158 | 0.856 | 1.070 | 4.615 | -0.310 | 0.917 | 0.816 | 0.423 | 0.746 |
| vol_and_breadth | 50.000 | 0.292 | 0.616 | 1.087 | 1.158 | 0.856 | 1.070 | 4.615 | -0.316 | 0.888 | 0.783 | 0.442 | 0.746 |
| baseline | 75.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| volatility_expansion_high | 75.000 | 0.257 | 1.430 | 0.838 | 0.957 | 0.965 | -1.118 | 0.810 | -0.316 | 0.847 | 0.725 | 0.476 | 0.746 |
| breadth_risk_off_high | 75.000 | 0.365 | 0.853 | 1.089 | 1.157 | 1.148 | 1.029 | 4.677 | -0.238 | 0.957 | 0.973 | 0.341 | 0.746 |
| vol_and_breadth | 75.000 | 0.346 | 0.777 | 1.089 | 1.157 | 1.148 | 1.029 | 4.677 | -0.246 | 0.924 | 0.944 | 0.355 | 0.746 |

## Event Split

| variant | cost_bps | split | fold_count | mean_delta | net_delta | average_exposure |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 10.000 | known_stress | 6 | 0.000 | 0.000 | 1.000 |
| baseline | 10.000 | unmatched | 18 | 0.000 | 0.000 | 1.000 |
| baseline | 10.000 | all | 24 | 0.000 | 0.000 | 1.000 |
| volatility_expansion_high | 10.000 | known_stress | 6 | 1.411 | 8.465 | 0.688 |
| volatility_expansion_high | 10.000 | unmatched | 18 | -0.217 | -3.905 | 0.764 |
| volatility_expansion_high | 10.000 | all | 24 | 0.190 | 4.559 | 0.745 |
| breadth_risk_off_high | 10.000 | known_stress | 6 | 0.878 | 5.267 | 0.998 |
| breadth_risk_off_high | 10.000 | unmatched | 18 | 0.223 | 4.014 | 0.995 |
| breadth_risk_off_high | 10.000 | all | 24 | 0.387 | 9.281 | 0.996 |
| vol_and_breadth | 10.000 | known_stress | 6 | 0.805 | 4.828 | 1.004 |
| vol_and_breadth | 10.000 | unmatched | 18 | 0.223 | 4.014 | 0.995 |
| vol_and_breadth | 10.000 | all | 24 | 0.368 | 8.841 | 0.997 |
| baseline | 25.000 | known_stress | 6 | 0.000 | 0.000 | 1.000 |
| baseline | 25.000 | unmatched | 18 | 0.000 | 0.000 | 1.000 |
| baseline | 25.000 | all | 24 | 0.000 | 0.000 | 1.000 |
| volatility_expansion_high | 25.000 | known_stress | 6 | 1.500 | 8.999 | 0.676 |
| volatility_expansion_high | 25.000 | unmatched | 18 | -0.172 | -3.101 | 0.752 |
| volatility_expansion_high | 25.000 | all | 24 | 0.246 | 5.899 | 0.733 |
| breadth_risk_off_high | 25.000 | known_stress | 6 | 0.877 | 5.262 | 0.998 |
| breadth_risk_off_high | 25.000 | unmatched | 18 | 0.086 | 1.542 | 0.931 |
| breadth_risk_off_high | 25.000 | all | 24 | 0.284 | 6.804 | 0.948 |
| vol_and_breadth | 25.000 | known_stress | 6 | 0.803 | 4.818 | 1.004 |
| vol_and_breadth | 25.000 | unmatched | 18 | 0.086 | 1.542 | 0.931 |
| vol_and_breadth | 25.000 | all | 24 | 0.265 | 6.360 | 0.950 |
| baseline | 50.000 | known_stress | 6 | 0.000 | 0.000 | 1.000 |
| baseline | 50.000 | unmatched | 18 | 0.000 | 0.000 | 1.000 |
| baseline | 50.000 | all | 24 | 0.000 | 0.000 | 1.000 |
| volatility_expansion_high | 50.000 | known_stress | 6 | 1.592 | 9.550 | 0.676 |
| volatility_expansion_high | 50.000 | unmatched | 18 | -0.048 | -0.872 | 0.744 |
| volatility_expansion_high | 50.000 | all | 24 | 0.362 | 8.678 | 0.727 |
| breadth_risk_off_high | 50.000 | known_stress | 6 | 0.932 | 5.591 | 0.973 |
| breadth_risk_off_high | 50.000 | unmatched | 18 | 0.104 | 1.868 | 0.931 |
| breadth_risk_off_high | 50.000 | all | 24 | 0.311 | 7.459 | 0.942 |
| vol_and_breadth | 50.000 | known_stress | 6 | 0.857 | 5.140 | 0.979 |
| vol_and_breadth | 50.000 | unmatched | 18 | 0.104 | 1.868 | 0.931 |
| vol_and_breadth | 50.000 | all | 24 | 0.292 | 7.008 | 0.943 |
| baseline | 75.000 | known_stress | 6 | 0.000 | 0.000 | 1.000 |
| baseline | 75.000 | unmatched | 18 | 0.000 | 0.000 | 1.000 |
| baseline | 75.000 | all | 24 | 0.000 | 0.000 | 1.000 |
| volatility_expansion_high | 75.000 | known_stress | 6 | 1.683 | 10.098 | 0.676 |
| volatility_expansion_high | 75.000 | unmatched | 18 | -0.219 | -3.937 | 0.697 |
| volatility_expansion_high | 75.000 | all | 24 | 0.257 | 6.161 | 0.691 |
| breadth_risk_off_high | 75.000 | known_stress | 6 | 1.094 | 6.562 | 0.948 |
| breadth_risk_off_high | 75.000 | unmatched | 18 | 0.122 | 2.196 | 0.931 |
| breadth_risk_off_high | 75.000 | all | 24 | 0.365 | 8.758 | 0.935 |
| vol_and_breadth | 75.000 | known_stress | 6 | 1.017 | 6.104 | 0.954 |
| vol_and_breadth | 75.000 | unmatched | 18 | 0.122 | 2.196 | 0.931 |
| vol_and_breadth | 75.000 | all | 24 | 0.346 | 8.300 | 0.937 |

## Trade Diagnostics

| fold | variant | cost_bps | event_label | accepted_winner | accepted_loser | reduced_winner | reduced_loser | increased_winner | increased_loser | accepted_winner_pnl | accepted_loser_pnl | loss_reduced_from_reduced_losers | profit_reduced_from_reduced_winners | profit_added_from_increased_winners | loss_added_from_increased_losers | net_blocker_value |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 333 | baseline | 10.000 | unmatched | 169 | 137 | 0 | 0 | 0 | 0 | 10.535 | -6.500 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 333 | volatility_expansion_high | 10.000 | unmatched | 0 | 0 | 169 | 137 | 0 | 0 | 0.000 | 0.000 | 3.250 | 5.268 | 0.000 | 0.000 | -2.018 |
| 333 | breadth_risk_off_high | 10.000 | unmatched | 0 | 0 | 0 | 0 | 169 | 137 | 0.000 | 0.000 | 0.000 | 0.000 | 2.634 | 1.625 | 1.009 |
| 333 | vol_and_breadth | 10.000 | unmatched | 0 | 0 | 0 | 0 | 169 | 137 | 0.000 | 0.000 | 0.000 | 0.000 | 2.634 | 1.625 | 1.009 |
| 334 | baseline | 10.000 | unmatched | 192 | 131 | 0 | 0 | 0 | 0 | 15.982 | -5.639 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 334 | volatility_expansion_high | 10.000 | unmatched | 0 | 0 | 55 | 35 | 137 | 96 | 0.000 | 0.000 | 0.773 | 2.113 | 2.939 | 1.023 | 0.576 |
| 334 | breadth_risk_off_high | 10.000 | unmatched | 0 | 0 | 0 | 0 | 192 | 131 | 0.000 | 0.000 | 0.000 | 0.000 | 3.996 | 1.410 | 2.586 |
| 334 | vol_and_breadth | 10.000 | unmatched | 0 | 0 | 0 | 0 | 192 | 131 | 0.000 | 0.000 | 0.000 | 0.000 | 3.996 | 1.410 | 2.586 |
| 335 | baseline | 10.000 | unmatched | 156 | 170 | 0 | 0 | 0 | 0 | 12.124 | -8.248 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 335 | volatility_expansion_high | 10.000 | unmatched | 0 | 0 | 156 | 170 | 0 | 0 | 0.000 | 0.000 | 4.124 | 6.062 | 0.000 | 0.000 | -1.938 |
| 335 | breadth_risk_off_high | 10.000 | unmatched | 0 | 0 | 0 | 0 | 156 | 170 | 0.000 | 0.000 | 0.000 | 0.000 | 3.031 | 2.062 | 0.969 |
| 335 | vol_and_breadth | 10.000 | unmatched | 0 | 0 | 0 | 0 | 156 | 170 | 0.000 | 0.000 | 0.000 | 0.000 | 3.031 | 2.062 | 0.969 |
| 336 | baseline | 10.000 | unmatched | 197 | 122 | 0 | 0 | 0 | 0 | 12.619 | -4.498 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 336 | volatility_expansion_high | 10.000 | unmatched | 0 | 0 | 91 | 63 | 106 | 59 | 0.000 | 0.000 | 1.217 | 3.225 | 1.543 | 0.516 | -0.981 |
| 336 | breadth_risk_off_high | 10.000 | unmatched | 0 | 0 | 0 | 0 | 197 | 122 | 0.000 | 0.000 | 0.000 | 0.000 | 3.155 | 1.124 | 2.030 |
| 336 | vol_and_breadth | 10.000 | unmatched | 0 | 0 | 0 | 0 | 197 | 122 | 0.000 | 0.000 | 0.000 | 0.000 | 3.155 | 1.124 | 2.030 |
| 337 | baseline | 10.000 | unmatched | 116 | 196 | 0 | 0 | 0 | 0 | 7.246 | -9.428 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 337 | volatility_expansion_high | 10.000 | unmatched | 0 | 0 | 33 | 40 | 83 | 156 | 0.000 | 0.000 | 1.032 | 1.178 | 1.223 | 1.841 | -0.765 |
| 337 | breadth_risk_off_high | 10.000 | unmatched | 0 | 0 | 0 | 0 | 116 | 196 | 0.000 | 0.000 | 0.000 | 0.000 | 1.812 | 2.357 | -0.545 |
| 337 | vol_and_breadth | 10.000 | unmatched | 0 | 0 | 0 | 0 | 116 | 196 | 0.000 | 0.000 | 0.000 | 0.000 | 1.812 | 2.357 | -0.545 |
| 338 | baseline | 10.000 | unmatched | 110 | 213 | 0 | 0 | 0 | 0 | 7.641 | -12.050 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 338 | volatility_expansion_high | 10.000 | unmatched | 0 | 0 | 1 | 14 | 109 | 199 | 0.000 | 0.000 | 0.497 | 0.022 | 1.899 | 2.764 | -0.389 |
| 338 | breadth_risk_off_high | 10.000 | unmatched | 0 | 0 | 0 | 0 | 110 | 213 | 0.000 | 0.000 | 0.000 | 0.000 | 1.910 | 3.012 | -1.102 |
| 338 | vol_and_breadth | 10.000 | unmatched | 0 | 0 | 0 | 0 | 110 | 213 | 0.000 | 0.000 | 0.000 | 0.000 | 1.910 | 3.012 | -1.102 |
| 339 | baseline | 10.000 | unmatched | 153 | 152 | 0 | 0 | 0 | 0 | 6.807 | -7.401 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 339 | volatility_expansion_high | 10.000 | unmatched | 0 | 0 | 32 | 24 | 121 | 128 | 0.000 | 0.000 | 0.553 | 0.798 | 1.302 | 1.574 | -0.517 |
| 339 | breadth_risk_off_high | 10.000 | unmatched | 0 | 0 | 0 | 0 | 153 | 152 | 0.000 | 0.000 | 0.000 | 0.000 | 1.702 | 1.850 | -0.149 |
| 339 | vol_and_breadth | 10.000 | unmatched | 0 | 0 | 0 | 0 | 153 | 152 | 0.000 | 0.000 | 0.000 | 0.000 | 1.702 | 1.850 | -0.149 |
| 340 | baseline | 10.000 | early_2025_broad_correction_fpi_outflows | 142 | 186 | 0 | 0 | 0 | 0 | 8.298 | -8.160 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 340 | volatility_expansion_high | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 142 | 186 | 0 | 0 | 0.000 | 0.000 | 4.080 | 4.149 | 0.000 | 0.000 | -0.069 |
| 340 | breadth_risk_off_high | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 0 | 0 | 142 | 186 | 0.000 | 0.000 | 0.000 | 0.000 | 2.074 | 2.040 | 0.034 |
| 340 | vol_and_breadth | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 0 | 0 | 142 | 186 | 0.000 | 0.000 | 0.000 | 0.000 | 2.074 | 2.040 | 0.034 |
| 341 | baseline | 10.000 | early_2025_broad_correction_fpi_outflows | 140 | 183 | 0 | 0 | 0 | 0 | 2.766 | -7.828 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 341 | volatility_expansion_high | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 69 | 103 | 71 | 80 | 0.000 | 0.000 | 2.428 | 0.560 | 0.411 | 0.743 | 1.536 |
| 341 | breadth_risk_off_high | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 0 | 0 | 140 | 183 | 0.000 | 0.000 | 0.000 | 0.000 | 0.691 | 1.957 | -1.266 |
| 341 | vol_and_breadth | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 0 | 0 | 140 | 183 | 0.000 | 0.000 | 0.000 | 0.000 | 0.691 | 1.957 | -1.266 |
| 342 | baseline | 10.000 | early_2025_broad_correction_fpi_outflows | 85 | 246 | 0 | 0 | 0 | 0 | 2.011 | -14.453 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 342 | volatility_expansion_high | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 3 | 29 | 82 | 217 | 0.000 | 0.000 | 1.953 | 0.021 | 0.198 | 1.185 | 0.945 |
| 342 | breadth_risk_off_high | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 26 | 113 | 59 | 133 | 0.000 | 0.000 | 5.867 | 0.421 | 0.145 | 0.663 | 4.928 |
| 342 | vol_and_breadth | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 26 | 113 | 59 | 133 | 0.000 | 0.000 | 5.867 | 0.421 | 0.145 | 0.663 | 4.928 |
| 343 | baseline | 10.000 | unmatched | 181 | 150 | 0 | 0 | 0 | 0 | 7.431 | -6.102 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 343 | volatility_expansion_high | 10.000 | unmatched | 0 | 0 | 78 | 72 | 103 | 78 | 0.000 | 0.000 | 1.859 | 2.575 | 0.400 | 0.362 | -0.678 |
| 343 | breadth_risk_off_high | 10.000 | unmatched | 0 | 0 | 159 | 122 | 22 | 28 | 0.000 | 0.000 | 3.756 | 4.904 | 0.089 | 0.109 | -1.168 |
| 343 | vol_and_breadth | 10.000 | unmatched | 0 | 0 | 159 | 122 | 22 | 28 | 0.000 | 0.000 | 3.756 | 4.904 | 0.089 | 0.109 | -1.168 |
| 344 | baseline | 10.000 | unmatched | 196 | 148 | 0 | 0 | 0 | 0 | 9.058 | -5.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 344 | volatility_expansion_high | 10.000 | unmatched | 0 | 0 | 82 | 48 | 114 | 100 | 0.000 | 0.000 | 1.428 | 3.271 | 0.470 | 0.351 | -1.725 |
| 344 | breadth_risk_off_high | 10.000 | unmatched | 0 | 0 | 181 | 146 | 15 | 2 | 0.000 | 0.000 | 4.013 | 5.922 | 0.116 | 0.007 | -1.800 |
| 344 | vol_and_breadth | 10.000 | unmatched | 0 | 0 | 181 | 146 | 15 | 2 | 0.000 | 0.000 | 4.013 | 5.922 | 0.116 | 0.007 | -1.800 |
| 345 | baseline | 10.000 | unmatched | 204 | 134 | 0 | 0 | 0 | 0 | 10.159 | -4.676 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 345 | volatility_expansion_high | 10.000 | unmatched | 0 | 0 | 204 | 134 | 0 | 0 | 0.000 | 0.000 | 3.507 | 7.619 | 0.000 | 0.000 | -4.112 |
| 345 | breadth_risk_off_high | 10.000 | unmatched | 0 | 0 | 204 | 134 | 0 | 0 | 0.000 | 0.000 | 3.507 | 7.619 | 0.000 | 0.000 | -4.112 |
| 345 | vol_and_breadth | 10.000 | unmatched | 0 | 0 | 204 | 134 | 0 | 0 | 0.000 | 0.000 | 3.507 | 7.619 | 0.000 | 0.000 | -4.112 |
| 346 | baseline | 10.000 | unmatched | 152 | 199 | 0 | 0 | 0 | 0 | 4.198 | -7.070 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 346 | volatility_expansion_high | 10.000 | unmatched | 0 | 0 | 152 | 199 | 0 | 0 | 0.000 | 0.000 | 5.302 | 3.149 | 0.000 | 0.000 | 2.154 |
| 346 | breadth_risk_off_high | 10.000 | unmatched | 0 | 0 | 152 | 199 | 0 | 0 | 0.000 | 0.000 | 5.302 | 3.149 | 0.000 | 0.000 | 2.154 |
| 346 | vol_and_breadth | 10.000 | unmatched | 0 | 0 | 152 | 199 | 0 | 0 | 0.000 | 0.000 | 5.302 | 3.149 | 0.000 | 0.000 | 2.154 |
| 347 | baseline | 10.000 | july_2025_broad_based_selling | 113 | 234 | 0 | 0 | 0 | 0 | 4.252 | -9.281 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 347 | volatility_expansion_high | 10.000 | july_2025_broad_based_selling | 0 | 0 | 113 | 234 | 0 | 0 | 0.000 | 0.000 | 6.961 | 3.189 | 0.000 | 0.000 | 3.771 |
| 347 | breadth_risk_off_high | 10.000 | july_2025_broad_based_selling | 0 | 0 | 113 | 234 | 0 | 0 | 0.000 | 0.000 | 6.961 | 3.189 | 0.000 | 0.000 | 3.771 |
| 347 | vol_and_breadth | 10.000 | july_2025_broad_based_selling | 0 | 0 | 110 | 221 | 3 | 13 | 0.000 | 0.000 | 6.482 | 3.100 | 0.012 | 0.064 | 3.329 |

## Decision

Research-only lead: AND condition passes first stress-overlay screen.
