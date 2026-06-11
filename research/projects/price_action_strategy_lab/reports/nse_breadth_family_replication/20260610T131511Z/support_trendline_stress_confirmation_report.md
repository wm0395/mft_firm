# Support Trendline Stress Confirmation

## Aggregate

| variant | cost_bps | return_pct | cagr_pct | ann_vol_pct | ann_sharpe | max_drawdown_pct | negative_fold_rate | worst_fold_sharpe | latest_fold_sharpe | average_exposure | turnover |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 10.000 | 62.584 | 27.508 | 6.917 | 3.550 | -18.208 | 0.417 | -21.949 | 5.275 | 1.000 | 0.247 |
| breadth_soft_aggressive | 10.000 | 76.388 | 32.811 | 8.350 | 3.442 | -22.238 | 0.417 | -21.949 | 5.275 | 1.048 | 0.257 |
| breadth_drawdown_only | 10.000 | 58.182 | 25.770 | 6.692 | 3.461 | -18.208 | 0.417 | -21.949 | 5.275 | 0.850 | 0.208 |
| baseline | 25.000 | 56.639 | 25.155 | 6.921 | 3.278 | -18.453 | 0.417 | -22.269 | 4.902 | 1.000 | 0.247 |
| breadth_soft_aggressive | 25.000 | 69.679 | 30.261 | 8.349 | 3.210 | -22.528 | 0.417 | -22.269 | 4.902 | 1.048 | 0.257 |
| breadth_drawdown_only | 25.000 | 53.285 | 23.808 | 6.693 | 3.226 | -18.453 | 0.417 | -22.269 | 4.902 | 0.850 | 0.208 |
| baseline | 50.000 | 47.209 | 21.330 | 6.930 | 2.826 | -18.858 | 0.417 | -22.792 | 4.279 | 1.000 | 0.247 |
| breadth_soft_aggressive | 50.000 | 59.656 | 26.355 | 8.319 | 2.855 | -23.010 | 0.417 | -22.792 | 4.279 | 1.036 | 0.254 |
| breadth_drawdown_only | 50.000 | 45.457 | 20.606 | 6.694 | 2.833 | -18.858 | 0.417 | -22.792 | 4.279 | 0.850 | 0.208 |

## Tail

| variant | cost_bps | mean_delta_vs_baseline | left_tail_delta | right_tail_retention | top_decile_retention | bottom_decile_improvement | best_fold_damage | worst_fold_improvement | ci_low | ci_high | paired_t_stat | paired_p_value | bh_p_value |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 10.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| breadth_soft_aggressive | 10.000 | 0.419 | -0.912 | 1.263 | 1.264 | -1.338 | 2.803 | -2.207 | -0.085 | 0.917 | 1.318 | 0.201 | 0.605 |
| breadth_drawdown_only | 10.000 | -0.118 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | -0.378 | 0.056 | -0.843 | 0.408 | 0.899 |
| baseline | 25.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| breadth_soft_aggressive | 25.000 | 0.411 | -0.949 | 1.263 | 1.264 | -1.372 | 2.758 | -2.237 | -0.089 | 0.904 | 1.314 | 0.202 | 0.605 |
| breadth_drawdown_only | 25.000 | -0.094 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | -0.340 | 0.089 | -0.686 | 0.499 | 0.899 |
| baseline | 50.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| breadth_soft_aggressive | 50.000 | 0.412 | -0.904 | 1.262 | 1.263 | -1.215 | 2.682 | -2.287 | -0.076 | 0.884 | 1.368 | 0.185 | 0.605 |
| breadth_drawdown_only | 50.000 | -0.053 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | -0.284 | 0.131 | -0.402 | 0.691 | 1.000 |

## Event Split

| variant | cost_bps | split | fold_count | mean_delta | net_delta | average_exposure |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 10.000 | known_stress | 6 | 0.000 | 0.000 | 1.000 |
| baseline | 10.000 | unmatched | 18 | 0.000 | 0.000 | 1.000 |
| baseline | 10.000 | all | 24 | 0.000 | 0.000 | 1.000 |
| breadth_soft_aggressive | 10.000 | known_stress | 6 | -0.583 | -3.499 | 1.083 |
| breadth_soft_aggressive | 10.000 | unmatched | 18 | 0.753 | 13.553 | 1.037 |
| breadth_soft_aggressive | 10.000 | all | 24 | 0.419 | 10.055 | 1.048 |
| breadth_drawdown_only | 10.000 | known_stress | 6 | 0.166 | 0.999 | 0.875 |
| breadth_drawdown_only | 10.000 | unmatched | 18 | -0.213 | -3.837 | 0.841 |
| breadth_drawdown_only | 10.000 | all | 24 | -0.118 | -2.838 | 0.850 |
| baseline | 25.000 | known_stress | 6 | 0.000 | 0.000 | 1.000 |
| baseline | 25.000 | unmatched | 18 | 0.000 | 0.000 | 1.000 |
| baseline | 25.000 | all | 24 | 0.000 | 0.000 | 1.000 |
| breadth_soft_aggressive | 25.000 | known_stress | 6 | -0.593 | -3.557 | 1.083 |
| breadth_soft_aggressive | 25.000 | unmatched | 18 | 0.746 | 13.424 | 1.037 |
| breadth_soft_aggressive | 25.000 | all | 24 | 0.411 | 9.868 | 1.048 |
| breadth_drawdown_only | 25.000 | known_stress | 6 | 0.184 | 1.106 | 0.875 |
| breadth_drawdown_only | 25.000 | unmatched | 18 | -0.186 | -3.357 | 0.841 |
| breadth_drawdown_only | 25.000 | all | 24 | -0.094 | -2.251 | 0.850 |
| baseline | 50.000 | known_stress | 6 | 0.000 | 0.000 | 1.000 |
| baseline | 50.000 | unmatched | 18 | 0.000 | 0.000 | 1.000 |
| baseline | 50.000 | all | 24 | 0.000 | 0.000 | 1.000 |
| breadth_soft_aggressive | 50.000 | known_stress | 6 | -0.502 | -3.012 | 1.058 |
| breadth_soft_aggressive | 50.000 | unmatched | 18 | 0.717 | 12.906 | 1.028 |
| breadth_soft_aggressive | 50.000 | all | 24 | 0.412 | 9.893 | 1.036 |
| breadth_drawdown_only | 50.000 | known_stress | 6 | 0.214 | 1.283 | 0.875 |
| breadth_drawdown_only | 50.000 | unmatched | 18 | -0.142 | -2.558 | 0.841 |
| breadth_drawdown_only | 50.000 | all | 24 | -0.053 | -1.275 | 0.850 |

## Trade Diagnostics

| fold | variant | cost_bps | event_label | accepted_winner | accepted_loser | reduced_winner | reduced_loser | increased_winner | increased_loser | accepted_winner_pnl | accepted_loser_pnl | loss_reduced_from_reduced_losers | profit_reduced_from_reduced_winners | profit_added_from_increased_winners | loss_added_from_increased_losers | net_blocker_value |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 333 | baseline | 10.000 | unmatched | 173 | 123 | 0 | 0 | 0 | 0 | 15.329 | -5.142 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 333 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 173 | 123 | 0.000 | 0.000 | 0.000 | 0.000 | 3.832 | 1.286 | 2.547 |
| 333 | breadth_drawdown_only | 10.000 | unmatched | 173 | 123 | 0 | 0 | 0 | 0 | 15.329 | -5.142 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 334 | baseline | 10.000 | unmatched | 208 | 114 | 0 | 0 | 0 | 0 | 12.560 | -3.742 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 334 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 208 | 114 | 0.000 | 0.000 | 0.000 | 0.000 | 3.140 | 0.936 | 2.204 |
| 334 | breadth_drawdown_only | 10.000 | unmatched | 208 | 114 | 0 | 0 | 0 | 0 | 12.560 | -3.742 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 335 | baseline | 10.000 | unmatched | 164 | 156 | 0 | 0 | 0 | 0 | 13.796 | -5.794 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 335 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 164 | 156 | 0.000 | 0.000 | 0.000 | 0.000 | 3.449 | 1.449 | 2.000 |
| 335 | breadth_drawdown_only | 10.000 | unmatched | 164 | 156 | 0 | 0 | 0 | 0 | 13.796 | -5.794 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 336 | baseline | 10.000 | unmatched | 208 | 103 | 0 | 0 | 0 | 0 | 13.818 | -4.126 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 336 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 208 | 103 | 0.000 | 0.000 | 0.000 | 0.000 | 3.455 | 1.032 | 2.423 |
| 336 | breadth_drawdown_only | 10.000 | unmatched | 208 | 103 | 0 | 0 | 0 | 0 | 13.818 | -4.126 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 337 | baseline | 10.000 | unmatched | 150 | 158 | 0 | 0 | 0 | 0 | 7.716 | -7.015 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 337 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 150 | 158 | 0.000 | 0.000 | 0.000 | 0.000 | 1.929 | 1.754 | 0.175 |
| 337 | breadth_drawdown_only | 10.000 | unmatched | 150 | 158 | 0 | 0 | 0 | 0 | 7.716 | -7.015 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 338 | baseline | 10.000 | unmatched | 153 | 163 | 0 | 0 | 0 | 0 | 8.306 | -8.890 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 338 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 153 | 163 | 0.000 | 0.000 | 0.000 | 0.000 | 2.077 | 2.223 | -0.146 |
| 338 | breadth_drawdown_only | 10.000 | unmatched | 153 | 163 | 0 | 0 | 0 | 0 | 8.306 | -8.890 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 339 | baseline | 10.000 | unmatched | 143 | 165 | 0 | 0 | 0 | 0 | 5.246 | -8.473 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 339 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 143 | 165 | 0.000 | 0.000 | 0.000 | 0.000 | 1.311 | 2.118 | -0.807 |
| 339 | breadth_drawdown_only | 10.000 | unmatched | 143 | 165 | 0 | 0 | 0 | 0 | 5.246 | -8.473 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 340 | baseline | 10.000 | early_2025_broad_correction_fpi_outflows | 125 | 201 | 0 | 0 | 0 | 0 | 6.610 | -8.162 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 340 | breadth_soft_aggressive | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 0 | 0 | 125 | 201 | 0.000 | 0.000 | 0.000 | 0.000 | 1.652 | 2.040 | -0.388 |
| 340 | breadth_drawdown_only | 10.000 | early_2025_broad_correction_fpi_outflows | 125 | 201 | 0 | 0 | 0 | 0 | 6.610 | -8.162 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 341 | baseline | 10.000 | early_2025_broad_correction_fpi_outflows | 197 | 121 | 0 | 0 | 0 | 0 | 4.043 | -5.470 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 341 | breadth_soft_aggressive | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 0 | 0 | 197 | 121 | 0.000 | 0.000 | 0.000 | 0.000 | 1.011 | 1.368 | -0.357 |
| 341 | breadth_drawdown_only | 10.000 | early_2025_broad_correction_fpi_outflows | 197 | 121 | 0 | 0 | 0 | 0 | 4.043 | -5.470 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 342 | baseline | 10.000 | early_2025_broad_correction_fpi_outflows | 161 | 165 | 0 | 0 | 0 | 0 | 2.122 | -6.174 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 342 | breadth_soft_aggressive | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 0 | 0 | 161 | 165 | 0.000 | 0.000 | 0.000 | 0.000 | 0.531 | 1.544 | -1.013 |
| 342 | breadth_drawdown_only | 10.000 | early_2025_broad_correction_fpi_outflows | 161 | 165 | 0 | 0 | 0 | 0 | 2.122 | -6.174 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 343 | baseline | 10.000 | unmatched | 217 | 113 | 0 | 0 | 0 | 0 | 5.529 | -3.888 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 343 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 183 | 98 | 34 | 15 | 0.000 | 0.000 | 2.452 | 3.393 | 0.100 | 0.062 | -0.903 |
| 343 | breadth_drawdown_only | 10.000 | unmatched | 34 | 15 | 183 | 98 | 0 | 0 | 1.005 | -0.619 | 2.452 | 3.393 | 0.000 | 0.000 | -0.942 |
| 344 | baseline | 10.000 | unmatched | 213 | 131 | 0 | 0 | 0 | 0 | 5.649 | -4.597 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 344 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 197 | 131 | 16 | 0 | 0.000 | 0.000 | 3.448 | 3.531 | 0.094 | 0.000 | 0.011 |
| 344 | breadth_drawdown_only | 10.000 | unmatched | 16 | 0 | 197 | 131 | 0 | 0 | 0.941 | 0.000 | 3.448 | 3.531 | 0.000 | 0.000 | -0.083 |
| 345 | baseline | 10.000 | unmatched | 219 | 124 | 0 | 0 | 0 | 0 | 8.066 | -3.956 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 345 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 219 | 124 | 0 | 0 | 0.000 | 0.000 | 2.967 | 6.049 | 0.000 | 0.000 | -3.082 |
| 345 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 219 | 124 | 0 | 0 | 0.000 | 0.000 | 2.967 | 6.049 | 0.000 | 0.000 | -3.082 |
| 346 | baseline | 10.000 | unmatched | 180 | 163 | 0 | 0 | 0 | 0 | 4.879 | -4.893 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 346 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 180 | 163 | 0 | 0 | 0.000 | 0.000 | 3.670 | 3.659 | 0.000 | 0.000 | 0.010 |
| 346 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 180 | 163 | 0 | 0 | 0.000 | 0.000 | 3.670 | 3.659 | 0.000 | 0.000 | 0.010 |
| 347 | baseline | 10.000 | july_2025_broad_based_selling | 149 | 187 | 0 | 0 | 0 | 0 | 4.883 | -6.126 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 347 | breadth_soft_aggressive | 10.000 | july_2025_broad_based_selling | 0 | 0 | 149 | 187 | 0 | 0 | 0.000 | 0.000 | 4.595 | 3.662 | 0.000 | 0.000 | 0.932 |
| 347 | breadth_drawdown_only | 10.000 | july_2025_broad_based_selling | 0 | 0 | 149 | 187 | 0 | 0 | 0.000 | 0.000 | 4.595 | 3.662 | 0.000 | 0.000 | 0.932 |
| 348 | baseline | 10.000 | unmatched | 222 | 120 | 0 | 0 | 0 | 0 | 6.262 | -3.829 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 348 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 222 | 120 | 0.000 | 0.000 | 0.000 | 0.000 | 1.566 | 0.957 | 0.608 |
| 348 | breadth_drawdown_only | 10.000 | unmatched | 222 | 120 | 0 | 0 | 0 | 0 | 6.262 | -3.829 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 349 | baseline | 10.000 | unmatched | 237 | 108 | 0 | 0 | 0 | 0 | 10.983 | -8.107 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 349 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 237 | 108 | 0.000 | 0.000 | 0.000 | 0.000 | 2.746 | 2.027 | 0.719 |
| 349 | breadth_drawdown_only | 10.000 | unmatched | 237 | 108 | 0 | 0 | 0 | 0 | 10.983 | -8.107 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 350 | baseline | 10.000 | unmatched | 162 | 151 | 0 | 0 | 0 | 0 | 4.531 | -6.563 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 350 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 162 | 151 | 0.000 | 0.000 | 0.000 | 0.000 | 1.133 | 1.641 | -0.508 |
| 350 | breadth_drawdown_only | 10.000 | unmatched | 162 | 151 | 0 | 0 | 0 | 0 | 4.531 | -6.563 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 351 | baseline | 10.000 | unmatched | 197 | 119 | 0 | 0 | 0 | 0 | 12.586 | -3.993 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 351 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 197 | 119 | 0.000 | 0.000 | 0.000 | 0.000 | 3.147 | 0.998 | 2.148 |
| 351 | breadth_drawdown_only | 10.000 | unmatched | 197 | 119 | 0 | 0 | 0 | 0 | 12.586 | -3.993 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 352 | baseline | 10.000 | unmatched | 237 | 108 | 0 | 0 | 0 | 0 | 11.424 | -3.766 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 352 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 237 | 108 | 0.000 | 0.000 | 0.000 | 0.000 | 2.856 | 0.941 | 1.914 |
| 352 | breadth_drawdown_only | 10.000 | unmatched | 237 | 108 | 0 | 0 | 0 | 0 | 11.424 | -3.766 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## Decision

Reject: missing target diagnostic rows.
