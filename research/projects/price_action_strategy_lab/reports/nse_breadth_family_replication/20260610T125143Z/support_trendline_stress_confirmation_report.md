# Support Trendline Stress Confirmation

## Aggregate

| variant | cost_bps | return_pct | cagr_pct | ann_vol_pct | ann_sharpe | max_drawdown_pct | negative_fold_rate | worst_fold_sharpe | latest_fold_sharpe | average_exposure | turnover |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 10.000 | 16.703 | 8.029 | 7.240 | 1.103 | -18.342 | 0.500 | -22.837 | -1.380 | 1.000 | 0.581 |
| breadth_soft_aggressive | 10.000 | 11.309 | 5.503 | 7.876 | 0.719 | -26.580 | 0.500 | -22.837 | -1.380 | 1.025 | 0.600 |
| breadth_drawdown_only | 10.000 | 11.309 | 5.503 | 7.876 | 0.719 | -26.580 | 0.500 | -22.837 | -1.380 | 1.025 | 0.600 |
| baseline | 25.000 | 6.890 | 3.388 | 7.232 | 0.497 | -21.849 | 0.542 | -23.510 | -2.130 | 1.000 | 0.581 |
| breadth_soft_aggressive | 25.000 | 3.608 | 1.788 | 7.676 | 0.269 | -29.131 | 0.542 | -23.510 | -2.130 | 1.000 | 0.585 |
| breadth_drawdown_only | 25.000 | 3.608 | 1.788 | 7.676 | 0.269 | -29.131 | 0.542 | -23.510 | -2.130 | 1.000 | 0.585 |
| baseline | 50.000 | -7.670 | -3.911 | 7.221 | -0.517 | -28.768 | 0.583 | -24.602 | -3.376 | 1.000 | 0.581 |
| breadth_soft_aggressive | 50.000 | -4.323 | -2.185 | 7.461 | -0.259 | -30.471 | 0.583 | -24.602 | -3.376 | 0.951 | 0.557 |
| breadth_drawdown_only | 50.000 | -4.323 | -2.185 | 7.461 | -0.259 | -30.471 | 0.583 | -24.602 | -3.376 | 0.951 | 0.557 |

## Tail

| variant | cost_bps | mean_delta_vs_baseline | left_tail_delta | right_tail_retention | top_decile_retention | bottom_decile_improvement | best_fold_damage | worst_fold_improvement | ci_low | ci_high | paired_t_stat | paired_p_value | bh_p_value |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 10.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| breadth_soft_aggressive | 10.000 | -0.167 | -0.437 | 1.115 | 1.198 | 0.067 | 1.310 | 3.940 | -0.760 | 0.422 | -0.451 | 0.656 | 1.000 |
| breadth_drawdown_only | 10.000 | -0.167 | -0.437 | 1.115 | 1.198 | 0.067 | 1.310 | 3.940 | -0.760 | 0.422 | -0.451 | 0.656 | 1.000 |
| baseline | 25.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| breadth_soft_aggressive | 25.000 | -0.112 | -0.113 | 1.100 | 1.197 | 0.803 | 1.260 | 3.976 | -0.647 | 0.428 | -0.332 | 0.743 | 1.000 |
| breadth_drawdown_only | 25.000 | -0.112 | -0.113 | 1.100 | 1.197 | 0.803 | 1.260 | 3.976 | -0.647 | 0.428 | -0.332 | 0.743 | 1.000 |
| baseline | 50.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| breadth_soft_aggressive | 50.000 | 0.153 | 0.893 | 1.101 | 1.196 | 2.754 | 1.177 | 4.036 | -0.451 | 0.764 | 0.398 | 0.694 | 1.000 |
| breadth_drawdown_only | 50.000 | 0.153 | 0.893 | 1.101 | 1.196 | 2.754 | 1.177 | 4.036 | -0.451 | 0.764 | 0.398 | 0.694 | 1.000 |

## Event Split

| variant | cost_bps | split | fold_count | mean_delta | net_delta | average_exposure |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 10.000 | known_stress | 6 | 0.000 | 0.000 | 1.000 |
| baseline | 10.000 | unmatched | 18 | 0.000 | 0.000 | 1.000 |
| baseline | 10.000 | all | 24 | 0.000 | 0.000 | 1.000 |
| breadth_soft_aggressive | 10.000 | known_stress | 6 | -0.305 | -1.830 | 1.179 |
| breadth_soft_aggressive | 10.000 | unmatched | 18 | -0.121 | -2.182 | 0.974 |
| breadth_soft_aggressive | 10.000 | all | 24 | -0.167 | -4.012 | 1.025 |
| breadth_drawdown_only | 10.000 | known_stress | 6 | -0.305 | -1.830 | 1.179 |
| breadth_drawdown_only | 10.000 | unmatched | 18 | -0.121 | -2.182 | 0.974 |
| breadth_drawdown_only | 10.000 | all | 24 | -0.167 | -4.012 | 1.025 |
| baseline | 25.000 | known_stress | 6 | 0.000 | 0.000 | 1.000 |
| baseline | 25.000 | unmatched | 18 | 0.000 | 0.000 | 1.000 |
| baseline | 25.000 | all | 24 | 0.000 | 0.000 | 1.000 |
| breadth_soft_aggressive | 25.000 | known_stress | 6 | 0.028 | 0.169 | 1.104 |
| breadth_soft_aggressive | 25.000 | unmatched | 18 | -0.159 | -2.854 | 0.966 |
| breadth_soft_aggressive | 25.000 | all | 24 | -0.112 | -2.685 | 1.000 |
| breadth_drawdown_only | 25.000 | known_stress | 6 | 0.028 | 0.169 | 1.104 |
| breadth_drawdown_only | 25.000 | unmatched | 18 | -0.159 | -2.854 | 0.966 |
| breadth_drawdown_only | 25.000 | all | 24 | -0.112 | -2.685 | 1.000 |
| baseline | 50.000 | known_stress | 6 | 0.000 | 0.000 | 1.000 |
| baseline | 50.000 | unmatched | 18 | 0.000 | 0.000 | 1.000 |
| baseline | 50.000 | all | 24 | 0.000 | 0.000 | 1.000 |
| breadth_soft_aggressive | 50.000 | known_stress | 6 | 0.945 | 5.668 | 0.962 |
| breadth_soft_aggressive | 50.000 | unmatched | 18 | -0.110 | -1.987 | 0.948 |
| breadth_soft_aggressive | 50.000 | all | 24 | 0.153 | 3.681 | 0.951 |
| breadth_drawdown_only | 50.000 | known_stress | 6 | 0.945 | 5.668 | 0.962 |
| breadth_drawdown_only | 50.000 | unmatched | 18 | -0.110 | -1.987 | 0.948 |
| breadth_drawdown_only | 50.000 | all | 24 | 0.153 | 3.681 | 0.951 |

## Trade Diagnostics

| fold | variant | cost_bps | event_label | accepted_winner | accepted_loser | reduced_winner | reduced_loser | increased_winner | increased_loser | accepted_winner_pnl | accepted_loser_pnl | loss_reduced_from_reduced_losers | profit_reduced_from_reduced_winners | profit_added_from_increased_winners | loss_added_from_increased_losers | net_blocker_value |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 333 | baseline | 10.000 | unmatched | 161 | 159 | 0 | 0 | 0 | 0 | 6.925 | -6.573 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 333 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 161 | 159 | 0.000 | 0.000 | 0.000 | 0.000 | 1.731 | 1.643 | 0.088 |
| 333 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 161 | 159 | 0.000 | 0.000 | 0.000 | 0.000 | 1.731 | 1.643 | 0.088 |
| 334 | baseline | 10.000 | unmatched | 204 | 119 | 0 | 0 | 0 | 0 | 12.560 | -3.682 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 334 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 204 | 119 | 0.000 | 0.000 | 0.000 | 0.000 | 3.140 | 0.920 | 2.220 |
| 334 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 204 | 119 | 0.000 | 0.000 | 0.000 | 0.000 | 3.140 | 0.920 | 2.220 |
| 335 | baseline | 10.000 | unmatched | 120 | 213 | 0 | 0 | 0 | 0 | 6.622 | -7.476 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 335 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 120 | 213 | 0.000 | 0.000 | 0.000 | 0.000 | 1.656 | 1.869 | -0.213 |
| 335 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 120 | 213 | 0.000 | 0.000 | 0.000 | 0.000 | 1.656 | 1.869 | -0.213 |
| 336 | baseline | 10.000 | unmatched | 203 | 104 | 0 | 0 | 0 | 0 | 12.143 | -3.403 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 336 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 203 | 104 | 0.000 | 0.000 | 0.000 | 0.000 | 3.036 | 0.851 | 2.185 |
| 336 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 203 | 104 | 0.000 | 0.000 | 0.000 | 0.000 | 3.036 | 0.851 | 2.185 |
| 337 | baseline | 10.000 | unmatched | 146 | 192 | 0 | 0 | 0 | 0 | 4.879 | -7.754 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 337 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 146 | 192 | 0.000 | 0.000 | 0.000 | 0.000 | 1.220 | 1.938 | -0.719 |
| 337 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 146 | 192 | 0.000 | 0.000 | 0.000 | 0.000 | 1.220 | 1.938 | -0.719 |
| 338 | baseline | 10.000 | unmatched | 137 | 200 | 0 | 0 | 0 | 0 | 6.631 | -6.935 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 338 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 137 | 200 | 0.000 | 0.000 | 0.000 | 0.000 | 1.658 | 1.734 | -0.076 |
| 338 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 137 | 200 | 0.000 | 0.000 | 0.000 | 0.000 | 1.658 | 1.734 | -0.076 |
| 339 | baseline | 10.000 | unmatched | 220 | 112 | 0 | 0 | 0 | 0 | 11.676 | -3.577 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 339 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 220 | 112 | 0.000 | 0.000 | 0.000 | 0.000 | 2.919 | 0.894 | 2.025 |
| 339 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 220 | 112 | 0.000 | 0.000 | 0.000 | 0.000 | 2.919 | 0.894 | 2.025 |
| 340 | baseline | 10.000 | early_2025_broad_correction_fpi_outflows | 89 | 235 | 0 | 0 | 0 | 0 | 3.915 | -8.147 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 340 | breadth_soft_aggressive | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 0 | 0 | 89 | 235 | 0.000 | 0.000 | 0.000 | 0.000 | 0.979 | 2.037 | -1.058 |
| 340 | breadth_drawdown_only | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 0 | 0 | 89 | 235 | 0.000 | 0.000 | 0.000 | 0.000 | 0.979 | 2.037 | -1.058 |
| 341 | baseline | 10.000 | early_2025_broad_correction_fpi_outflows | 131 | 203 | 0 | 0 | 0 | 0 | 4.384 | -8.038 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 341 | breadth_soft_aggressive | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 0 | 0 | 131 | 203 | 0.000 | 0.000 | 0.000 | 0.000 | 1.096 | 2.010 | -0.914 |
| 341 | breadth_drawdown_only | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 0 | 0 | 131 | 203 | 0.000 | 0.000 | 0.000 | 0.000 | 1.096 | 2.010 | -0.914 |
| 342 | baseline | 10.000 | early_2025_broad_correction_fpi_outflows | 86 | 257 | 0 | 0 | 0 | 0 | 2.580 | -13.354 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 342 | breadth_soft_aggressive | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 19 | 125 | 67 | 132 | 0.000 | 0.000 | 5.771 | 0.569 | 0.455 | 1.415 | 4.243 |
| 342 | breadth_drawdown_only | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 19 | 125 | 67 | 132 | 0.000 | 0.000 | 5.771 | 0.569 | 0.455 | 1.415 | 4.243 |
| 343 | baseline | 10.000 | unmatched | 197 | 123 | 0 | 0 | 0 | 0 | 9.113 | -5.216 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 343 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 172 | 104 | 25 | 19 | 0.000 | 0.000 | 3.447 | 5.818 | 0.339 | 0.155 | -2.188 |
| 343 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 172 | 104 | 25 | 19 | 0.000 | 0.000 | 3.447 | 5.818 | 0.339 | 0.155 | -2.188 |
| 344 | baseline | 10.000 | unmatched | 218 | 99 | 0 | 0 | 0 | 0 | 10.152 | -3.995 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 344 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 201 | 99 | 17 | 0 | 0.000 | 0.000 | 2.996 | 7.011 | 0.201 | 0.000 | -3.813 |
| 344 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 201 | 99 | 17 | 0 | 0.000 | 0.000 | 2.996 | 7.011 | 0.201 | 0.000 | -3.813 |
| 345 | baseline | 10.000 | unmatched | 198 | 139 | 0 | 0 | 0 | 0 | 6.888 | -3.371 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 345 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 198 | 139 | 0 | 0 | 0.000 | 0.000 | 2.529 | 5.166 | 0.000 | 0.000 | -2.638 |
| 345 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 198 | 139 | 0 | 0 | 0.000 | 0.000 | 2.529 | 5.166 | 0.000 | 0.000 | -2.638 |
| 346 | baseline | 10.000 | unmatched | 191 | 161 | 0 | 0 | 0 | 0 | 7.324 | -3.912 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 346 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 191 | 161 | 0 | 0 | 0.000 | 0.000 | 2.934 | 5.493 | 0.000 | 0.000 | -2.559 |
| 346 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 191 | 161 | 0 | 0 | 0.000 | 0.000 | 2.934 | 5.493 | 0.000 | 0.000 | -2.559 |
| 347 | baseline | 10.000 | july_2025_broad_based_selling | 108 | 247 | 0 | 0 | 0 | 0 | 2.634 | -8.634 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 347 | breadth_soft_aggressive | 10.000 | july_2025_broad_based_selling | 0 | 0 | 0 | 0 | 108 | 247 | 0.000 | 0.000 | 0.000 | 0.000 | 0.659 | 2.158 | -1.500 |
| 347 | breadth_drawdown_only | 10.000 | july_2025_broad_based_selling | 0 | 0 | 0 | 0 | 108 | 247 | 0.000 | 0.000 | 0.000 | 0.000 | 0.659 | 2.158 | -1.500 |
| 348 | baseline | 10.000 | unmatched | 224 | 132 | 0 | 0 | 0 | 0 | 8.378 | -2.735 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 348 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 224 | 132 | 0.000 | 0.000 | 0.000 | 0.000 | 2.095 | 0.684 | 1.411 |
| 348 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 224 | 132 | 0.000 | 0.000 | 0.000 | 0.000 | 2.095 | 0.684 | 1.411 |
| 349 | baseline | 10.000 | unmatched | 163 | 190 | 0 | 0 | 0 | 0 | 6.920 | -6.224 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 349 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 163 | 190 | 0.000 | 0.000 | 0.000 | 0.000 | 1.730 | 1.556 | 0.174 |
| 349 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 163 | 190 | 0.000 | 0.000 | 0.000 | 0.000 | 1.730 | 1.556 | 0.174 |
| 350 | baseline | 10.000 | unmatched | 190 | 162 | 0 | 0 | 0 | 0 | 7.130 | -5.110 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 350 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 190 | 162 | 0.000 | 0.000 | 0.000 | 0.000 | 1.782 | 1.277 | 0.505 |
| 350 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 190 | 162 | 0.000 | 0.000 | 0.000 | 0.000 | 1.782 | 1.277 | 0.505 |
| 351 | baseline | 10.000 | unmatched | 168 | 187 | 0 | 0 | 0 | 0 | 7.939 | -7.769 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 351 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 168 | 187 | 0.000 | 0.000 | 0.000 | 0.000 | 1.985 | 1.942 | 0.042 |
| 351 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 168 | 187 | 0.000 | 0.000 | 0.000 | 0.000 | 1.985 | 1.942 | 0.042 |
| 352 | baseline | 10.000 | unmatched | 139 | 201 | 0 | 0 | 0 | 0 | 4.040 | -7.106 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 352 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 139 | 201 | 0.000 | 0.000 | 0.000 | 0.000 | 1.010 | 1.777 | -0.767 |
| 352 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 139 | 201 | 0.000 | 0.000 | 0.000 | 0.000 | 1.010 | 1.777 | -0.767 |

## Decision

Reject: missing target diagnostic rows.
