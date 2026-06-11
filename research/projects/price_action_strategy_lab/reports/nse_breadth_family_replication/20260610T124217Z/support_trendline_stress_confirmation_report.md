# Support Trendline Stress Confirmation

## Aggregate

| variant | cost_bps | return_pct | cagr_pct | ann_vol_pct | ann_sharpe | max_drawdown_pct | negative_fold_rate | worst_fold_sharpe | latest_fold_sharpe | average_exposure | turnover |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 10.000 | 25.957 | 12.231 | 7.383 | 1.600 | -21.476 | 0.458 | -19.015 | 2.908 | 1.000 | 0.649 |
| breadth_soft_aggressive | 10.000 | 27.886 | 13.087 | 8.793 | 1.443 | -24.932 | 0.417 | -19.015 | 2.908 | 1.023 | 0.662 |
| breadth_drawdown_only | 10.000 | 27.886 | 13.087 | 8.793 | 1.443 | -24.932 | 0.417 | -19.015 | 2.908 | 1.023 | 0.662 |
| baseline | 25.000 | 14.179 | 6.855 | 7.385 | 0.935 | -23.488 | 0.542 | -19.821 | 2.106 | 1.000 | 0.649 |
| breadth_soft_aggressive | 25.000 | 20.887 | 9.949 | 8.655 | 1.139 | -26.370 | 0.500 | -19.647 | 2.106 | 1.008 | 0.652 |
| breadth_drawdown_only | 25.000 | 20.887 | 9.949 | 8.655 | 1.139 | -26.370 | 0.500 | -19.647 | 2.106 | 1.008 | 0.652 |
| baseline | 50.000 | -3.059 | -1.541 | 7.391 | -0.173 | -32.256 | 0.542 | -21.539 | 0.778 | 1.000 | 0.649 |
| breadth_soft_aggressive | 50.000 | 1.267 | 0.632 | 8.402 | 0.117 | -35.033 | 0.583 | -20.672 | 0.778 | 0.948 | 0.614 |
| breadth_drawdown_only | 50.000 | 1.267 | 0.632 | 8.402 | 0.117 | -35.033 | 0.583 | -20.672 | 0.778 | 0.948 | 0.614 |

## Tail

| variant | cost_bps | mean_delta_vs_baseline | left_tail_delta | right_tail_retention | top_decile_retention | bottom_decile_improvement | best_fold_damage | worst_fold_improvement | ci_low | ci_high | paired_t_stat | paired_p_value | bh_p_value |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 10.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| breadth_soft_aggressive | 10.000 | 0.133 | -1.102 | 1.262 | 1.264 | -1.368 | 2.804 | -2.243 | -0.374 | 0.620 | 0.428 | 0.673 | 1.000 |
| breadth_drawdown_only | 10.000 | 0.133 | -1.102 | 1.262 | 1.264 | -1.368 | 2.804 | -2.243 | -0.374 | 0.620 | 0.428 | 0.673 | 1.000 |
| baseline | 25.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| breadth_soft_aggressive | 25.000 | 0.294 | -0.503 | 1.262 | 1.263 | -0.075 | 2.691 | -2.324 | -0.231 | 0.809 | 0.906 | 0.374 | 1.000 |
| breadth_drawdown_only | 25.000 | 0.294 | -0.503 | 1.262 | 1.263 | -0.075 | 2.691 | -2.324 | -0.231 | 0.809 | 0.906 | 0.374 | 1.000 |
| baseline | 50.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| breadth_soft_aggressive | 50.000 | 0.229 | -0.502 | 1.223 | 1.262 | -0.123 | 2.504 | -2.457 | -0.255 | 0.703 | 0.748 | 0.462 | 1.000 |
| breadth_drawdown_only | 50.000 | 0.229 | -0.502 | 1.223 | 1.262 | -0.123 | 2.504 | -2.457 | -0.255 | 0.703 | 0.748 | 0.462 | 1.000 |

## Event Split

| variant | cost_bps | split | fold_count | mean_delta | net_delta | average_exposure |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 10.000 | known_stress | 6 | 0.000 | 0.000 | 1.000 |
| baseline | 10.000 | unmatched | 18 | 0.000 | 0.000 | 1.000 |
| baseline | 10.000 | all | 24 | 0.000 | 0.000 | 1.000 |
| breadth_soft_aggressive | 10.000 | known_stress | 6 | -0.611 | -3.663 | 1.033 |
| breadth_soft_aggressive | 10.000 | unmatched | 18 | 0.381 | 6.851 | 1.020 |
| breadth_soft_aggressive | 10.000 | all | 24 | 0.133 | 3.188 | 1.023 |
| breadth_drawdown_only | 10.000 | known_stress | 6 | -0.611 | -3.663 | 1.033 |
| breadth_drawdown_only | 10.000 | unmatched | 18 | 0.381 | 6.851 | 1.020 |
| breadth_drawdown_only | 10.000 | all | 24 | 0.133 | 3.188 | 1.023 |
| baseline | 25.000 | known_stress | 6 | 0.000 | 0.000 | 1.000 |
| baseline | 25.000 | unmatched | 18 | 0.000 | 0.000 | 1.000 |
| baseline | 25.000 | all | 24 | 0.000 | 0.000 | 1.000 |
| breadth_soft_aggressive | 25.000 | known_stress | 6 | 0.066 | 0.394 | 0.973 |
| breadth_soft_aggressive | 25.000 | unmatched | 18 | 0.370 | 6.661 | 1.020 |
| breadth_soft_aggressive | 25.000 | all | 24 | 0.294 | 7.055 | 1.008 |
| breadth_drawdown_only | 25.000 | known_stress | 6 | 0.066 | 0.394 | 0.973 |
| breadth_drawdown_only | 25.000 | unmatched | 18 | 0.370 | 6.661 | 1.020 |
| breadth_drawdown_only | 25.000 | all | 24 | 0.294 | 7.055 | 1.008 |
| baseline | 50.000 | known_stress | 6 | 0.000 | 0.000 | 1.000 |
| baseline | 50.000 | unmatched | 18 | 0.000 | 0.000 | 1.000 |
| baseline | 50.000 | all | 24 | 0.000 | 0.000 | 1.000 |
| breadth_soft_aggressive | 50.000 | known_stress | 6 | 0.091 | 0.546 | 0.973 |
| breadth_soft_aggressive | 50.000 | unmatched | 18 | 0.274 | 4.940 | 0.940 |
| breadth_soft_aggressive | 50.000 | all | 24 | 0.229 | 5.485 | 0.948 |
| breadth_drawdown_only | 50.000 | known_stress | 6 | 0.091 | 0.546 | 0.973 |
| breadth_drawdown_only | 50.000 | unmatched | 18 | 0.274 | 4.940 | 0.940 |
| breadth_drawdown_only | 50.000 | all | 24 | 0.229 | 5.485 | 0.948 |

## Trade Diagnostics

| fold | variant | cost_bps | event_label | accepted_winner | accepted_loser | reduced_winner | reduced_loser | increased_winner | increased_loser | accepted_winner_pnl | accepted_loser_pnl | loss_reduced_from_reduced_losers | profit_reduced_from_reduced_winners | profit_added_from_increased_winners | loss_added_from_increased_losers | net_blocker_value |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 333 | baseline | 10.000 | unmatched | 155 | 115 | 0 | 0 | 0 | 0 | 13.041 | -4.085 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 333 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 155 | 115 | 0.000 | 0.000 | 0.000 | 0.000 | 3.260 | 1.021 | 2.239 |
| 333 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 155 | 115 | 0.000 | 0.000 | 0.000 | 0.000 | 3.260 | 1.021 | 2.239 |
| 334 | baseline | 10.000 | unmatched | 196 | 123 | 0 | 0 | 0 | 0 | 13.810 | -3.475 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 334 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 196 | 123 | 0.000 | 0.000 | 0.000 | 0.000 | 3.452 | 0.869 | 2.584 |
| 334 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 196 | 123 | 0.000 | 0.000 | 0.000 | 0.000 | 3.452 | 0.869 | 2.584 |
| 335 | baseline | 10.000 | unmatched | 137 | 166 | 0 | 0 | 0 | 0 | 8.463 | -7.848 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 335 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 137 | 166 | 0.000 | 0.000 | 0.000 | 0.000 | 2.116 | 1.962 | 0.154 |
| 335 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 137 | 166 | 0.000 | 0.000 | 0.000 | 0.000 | 2.116 | 1.962 | 0.154 |
| 336 | baseline | 10.000 | unmatched | 189 | 120 | 0 | 0 | 0 | 0 | 14.207 | -4.435 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 336 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 189 | 120 | 0.000 | 0.000 | 0.000 | 0.000 | 3.552 | 1.109 | 2.443 |
| 336 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 189 | 120 | 0.000 | 0.000 | 0.000 | 0.000 | 3.552 | 1.109 | 2.443 |
| 337 | baseline | 10.000 | unmatched | 144 | 167 | 0 | 0 | 0 | 0 | 6.253 | -6.626 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 337 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 144 | 167 | 0.000 | 0.000 | 0.000 | 0.000 | 1.563 | 1.657 | -0.093 |
| 337 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 144 | 167 | 0.000 | 0.000 | 0.000 | 0.000 | 1.563 | 1.657 | -0.093 |
| 338 | baseline | 10.000 | unmatched | 109 | 156 | 0 | 0 | 0 | 0 | 6.020 | -10.517 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 338 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 109 | 156 | 0.000 | 0.000 | 0.000 | 0.000 | 1.505 | 2.629 | -1.124 |
| 338 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 109 | 156 | 0.000 | 0.000 | 0.000 | 0.000 | 1.505 | 2.629 | -1.124 |
| 339 | baseline | 10.000 | unmatched | 131 | 148 | 0 | 0 | 0 | 0 | 4.686 | -8.460 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 339 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 131 | 148 | 0.000 | 0.000 | 0.000 | 0.000 | 1.171 | 2.115 | -0.944 |
| 339 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 131 | 148 | 0.000 | 0.000 | 0.000 | 0.000 | 1.171 | 2.115 | -0.944 |
| 340 | baseline | 10.000 | early_2025_broad_correction_fpi_outflows | 102 | 185 | 0 | 0 | 0 | 0 | 5.685 | -8.398 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 340 | breadth_soft_aggressive | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 0 | 0 | 102 | 185 | 0.000 | 0.000 | 0.000 | 0.000 | 1.421 | 2.099 | -0.678 |
| 340 | breadth_drawdown_only | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 0 | 0 | 102 | 185 | 0.000 | 0.000 | 0.000 | 0.000 | 1.421 | 2.099 | -0.678 |
| 341 | baseline | 10.000 | early_2025_broad_correction_fpi_outflows | 142 | 101 | 0 | 0 | 0 | 0 | 3.225 | -5.439 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 341 | breadth_soft_aggressive | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 0 | 0 | 142 | 101 | 0.000 | 0.000 | 0.000 | 0.000 | 0.323 | 0.544 | -0.221 |
| 341 | breadth_drawdown_only | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 0 | 0 | 142 | 101 | 0.000 | 0.000 | 0.000 | 0.000 | 0.323 | 0.544 | -0.221 |
| 342 | baseline | 10.000 | early_2025_broad_correction_fpi_outflows | 114 | 156 | 0 | 0 | 0 | 0 | 1.475 | -8.911 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 342 | breadth_soft_aggressive | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 0 | 0 | 114 | 156 | 0.000 | 0.000 | 0.000 | 0.000 | 0.147 | 0.891 | -0.744 |
| 342 | breadth_drawdown_only | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 0 | 0 | 114 | 156 | 0.000 | 0.000 | 0.000 | 0.000 | 0.147 | 0.891 | -0.744 |
| 343 | baseline | 10.000 | unmatched | 192 | 109 | 0 | 0 | 0 | 0 | 6.534 | -4.505 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 343 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 171 | 93 | 21 | 16 | 0.000 | 0.000 | 2.739 | 4.422 | 0.064 | 0.085 | -1.705 |
| 343 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 171 | 93 | 21 | 16 | 0.000 | 0.000 | 2.739 | 4.422 | 0.064 | 0.085 | -1.705 |
| 344 | baseline | 10.000 | unmatched | 174 | 146 | 0 | 0 | 0 | 0 | 5.297 | -5.269 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 344 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 166 | 146 | 8 | 0 | 0.000 | 0.000 | 3.952 | 3.701 | 0.036 | 0.000 | 0.287 |
| 344 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 166 | 146 | 8 | 0 | 0.000 | 0.000 | 3.952 | 3.701 | 0.036 | 0.000 | 0.287 |
| 345 | baseline | 10.000 | unmatched | 191 | 140 | 0 | 0 | 0 | 0 | 8.361 | -4.057 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 345 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 191 | 140 | 0 | 0 | 0.000 | 0.000 | 3.042 | 6.271 | 0.000 | 0.000 | -3.228 |
| 345 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 191 | 140 | 0 | 0 | 0.000 | 0.000 | 3.042 | 6.271 | 0.000 | 0.000 | -3.228 |
| 346 | baseline | 10.000 | unmatched | 177 | 158 | 0 | 0 | 0 | 0 | 5.356 | -4.719 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 346 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 177 | 158 | 0 | 0 | 0.000 | 0.000 | 3.539 | 4.017 | 0.000 | 0.000 | -0.478 |
| 346 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 177 | 158 | 0 | 0 | 0.000 | 0.000 | 3.539 | 4.017 | 0.000 | 0.000 | -0.478 |
| 347 | baseline | 10.000 | july_2025_broad_based_selling | 139 | 174 | 0 | 0 | 0 | 0 | 5.742 | -6.053 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 347 | breadth_soft_aggressive | 10.000 | july_2025_broad_based_selling | 0 | 0 | 139 | 174 | 0 | 0 | 0.000 | 0.000 | 4.540 | 4.306 | 0.000 | 0.000 | 0.234 |
| 347 | breadth_drawdown_only | 10.000 | july_2025_broad_based_selling | 0 | 0 | 139 | 174 | 0 | 0 | 0.000 | 0.000 | 4.540 | 4.306 | 0.000 | 0.000 | 0.234 |
| 348 | baseline | 10.000 | unmatched | 179 | 109 | 0 | 0 | 0 | 0 | 5.931 | -3.872 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 348 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 179 | 109 | 0.000 | 0.000 | 0.000 | 0.000 | 0.593 | 0.387 | 0.206 |
| 348 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 179 | 109 | 0.000 | 0.000 | 0.000 | 0.000 | 0.593 | 0.387 | 0.206 |
| 349 | baseline | 10.000 | unmatched | 200 | 133 | 0 | 0 | 0 | 0 | 9.356 | -7.686 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 349 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 200 | 133 | 0.000 | 0.000 | 0.000 | 0.000 | 2.339 | 1.922 | 0.418 |
| 349 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 200 | 133 | 0.000 | 0.000 | 0.000 | 0.000 | 2.339 | 1.922 | 0.418 |
| 350 | baseline | 10.000 | unmatched | 159 | 163 | 0 | 0 | 0 | 0 | 3.766 | -6.786 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 350 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 159 | 163 | 0.000 | 0.000 | 0.000 | 0.000 | 0.941 | 1.697 | -0.755 |
| 350 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 159 | 163 | 0.000 | 0.000 | 0.000 | 0.000 | 0.941 | 1.697 | -0.755 |
| 351 | baseline | 10.000 | unmatched | 216 | 129 | 0 | 0 | 0 | 0 | 11.621 | -3.745 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 351 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 216 | 129 | 0.000 | 0.000 | 0.000 | 0.000 | 2.905 | 0.936 | 1.969 |
| 351 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 216 | 129 | 0.000 | 0.000 | 0.000 | 0.000 | 2.905 | 0.936 | 1.969 |
| 352 | baseline | 10.000 | unmatched | 186 | 134 | 0 | 0 | 0 | 0 | 10.263 | -4.647 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 352 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 186 | 134 | 0.000 | 0.000 | 0.000 | 0.000 | 2.566 | 1.162 | 1.404 |
| 352 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 186 | 134 | 0.000 | 0.000 | 0.000 | 0.000 | 2.566 | 1.162 | 1.404 |

## Decision

Reject: missing target diagnostic rows.
