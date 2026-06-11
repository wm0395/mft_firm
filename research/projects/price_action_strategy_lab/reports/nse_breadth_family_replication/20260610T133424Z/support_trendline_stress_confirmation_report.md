# Support Trendline Stress Confirmation

## Aggregate

| variant | cost_bps | return_pct | cagr_pct | ann_vol_pct | ann_sharpe | max_drawdown_pct | negative_fold_rate | worst_fold_sharpe | latest_fold_sharpe | average_exposure | turnover |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 10.000 | 18.538 | 8.875 | 7.631 | 1.152 | -22.248 | 0.417 | -26.132 | 4.409 | 1.000 | 0.161 |
| breadth_soft_aggressive | 10.000 | 19.275 | 9.213 | 8.662 | 1.061 | -22.136 | 0.417 | -21.578 | 4.409 | 0.983 | 0.160 |
| breadth_drawdown_only | 10.000 | 16.625 | 7.993 | 6.988 | 1.135 | -18.378 | 0.417 | -21.578 | 4.409 | 0.805 | 0.131 |
| baseline | 25.000 | 15.689 | 7.559 | 7.632 | 0.993 | -22.758 | 0.417 | -26.335 | 3.937 | 1.000 | 0.161 |
| breadth_soft_aggressive | 25.000 | 16.433 | 7.904 | 8.660 | 0.922 | -22.736 | 0.417 | -21.845 | 3.937 | 0.983 | 0.160 |
| breadth_drawdown_only | 25.000 | 14.345 | 6.932 | 6.986 | 0.994 | -18.883 | 0.417 | -21.845 | 3.937 | 0.805 | 0.131 |
| baseline | 50.000 | 11.091 | 5.400 | 7.634 | 0.727 | -23.601 | 0.417 | -26.669 | 3.143 | 1.000 | 0.161 |
| breadth_soft_aggressive | 50.000 | 9.788 | 4.780 | 8.323 | 0.602 | -23.724 | 0.417 | -22.277 | 3.143 | 0.976 | 0.159 |
| breadth_drawdown_only | 50.000 | 10.644 | 5.187 | 6.983 | 0.759 | -19.717 | 0.417 | -22.277 | 3.143 | 0.805 | 0.131 |

## Tail

| variant | cost_bps | mean_delta_vs_baseline | left_tail_delta | right_tail_retention | top_decile_retention | bottom_decile_improvement | best_fold_damage | worst_fold_improvement | ci_low | ci_high | paired_t_stat | paired_p_value | bh_p_value |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 10.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| breadth_soft_aggressive | 10.000 | 0.057 | 0.385 | 1.137 | 1.264 | 1.883 | 3.648 | 3.122 | -0.590 | 0.709 | 0.140 | 0.890 | 1.000 |
| breadth_drawdown_only | 10.000 | -0.104 | 1.398 | 0.926 | 1.000 | 2.796 | 0.000 | 4.413 | -0.643 | 0.448 | -0.302 | 0.765 | 1.000 |
| baseline | 25.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| breadth_soft_aggressive | 25.000 | 0.057 | 0.385 | 1.137 | 1.264 | 1.908 | 3.619 | 3.139 | -0.585 | 0.703 | 0.142 | 0.888 | 1.000 |
| breadth_drawdown_only | 25.000 | -0.085 | 1.415 | 0.926 | 1.000 | 2.830 | 0.000 | 4.444 | -0.622 | 0.465 | -0.248 | 0.806 | 1.000 |
| baseline | 50.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| breadth_soft_aggressive | 50.000 | -0.031 | 0.387 | 1.094 | 1.193 | 1.948 | 1.417 | 3.168 | -0.631 | 0.567 | -0.083 | 0.935 | 1.000 |
| breadth_drawdown_only | 50.000 | -0.053 | 1.444 | 0.927 | 1.000 | 2.887 | 0.000 | 4.494 | -0.582 | 0.502 | -0.156 | 0.877 | 1.000 |

## Event Split

| variant | cost_bps | split | fold_count | mean_delta | net_delta | average_exposure |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 10.000 | known_stress | 6 | 0.000 | 0.000 | 1.000 |
| baseline | 10.000 | unmatched | 18 | 0.000 | 0.000 | 1.000 |
| baseline | 10.000 | all | 24 | 0.000 | 0.000 | 1.000 |
| breadth_soft_aggressive | 10.000 | known_stress | 6 | 0.700 | 4.203 | 1.012 |
| breadth_soft_aggressive | 10.000 | unmatched | 18 | -0.158 | -2.837 | 0.973 |
| breadth_soft_aggressive | 10.000 | all | 24 | 0.057 | 1.366 | 0.983 |
| breadth_drawdown_only | 10.000 | known_stress | 6 | 1.398 | 8.387 | 0.821 |
| breadth_drawdown_only | 10.000 | unmatched | 18 | -0.605 | -10.894 | 0.800 |
| breadth_drawdown_only | 10.000 | all | 24 | -0.104 | -2.507 | 0.805 |
| baseline | 25.000 | known_stress | 6 | 0.000 | 0.000 | 1.000 |
| baseline | 25.000 | unmatched | 18 | 0.000 | 0.000 | 1.000 |
| baseline | 25.000 | all | 24 | 0.000 | 0.000 | 1.000 |
| breadth_soft_aggressive | 25.000 | known_stress | 6 | 0.699 | 4.194 | 1.012 |
| breadth_soft_aggressive | 25.000 | unmatched | 18 | -0.156 | -2.814 | 0.973 |
| breadth_soft_aggressive | 25.000 | all | 24 | 0.057 | 1.380 | 0.983 |
| breadth_drawdown_only | 25.000 | known_stress | 6 | 1.415 | 8.490 | 0.821 |
| breadth_drawdown_only | 25.000 | unmatched | 18 | -0.585 | -10.538 | 0.800 |
| breadth_drawdown_only | 25.000 | all | 24 | -0.085 | -2.047 | 0.805 |
| baseline | 50.000 | known_stress | 6 | 0.000 | 0.000 | 1.000 |
| baseline | 50.000 | unmatched | 18 | 0.000 | 0.000 | 1.000 |
| baseline | 50.000 | all | 24 | 0.000 | 0.000 | 1.000 |
| breadth_soft_aggressive | 50.000 | known_stress | 6 | 0.697 | 4.180 | 1.012 |
| breadth_soft_aggressive | 50.000 | unmatched | 18 | -0.274 | -4.928 | 0.965 |
| breadth_soft_aggressive | 50.000 | all | 24 | -0.031 | -0.748 | 0.976 |
| breadth_drawdown_only | 50.000 | known_stress | 6 | 1.444 | 8.662 | 0.821 |
| breadth_drawdown_only | 50.000 | unmatched | 18 | -0.552 | -9.945 | 0.800 |
| breadth_drawdown_only | 50.000 | all | 24 | -0.053 | -1.283 | 0.805 |

## Trade Diagnostics

| fold | variant | cost_bps | event_label | accepted_winner | accepted_loser | reduced_winner | reduced_loser | increased_winner | increased_loser | accepted_winner_pnl | accepted_loser_pnl | loss_reduced_from_reduced_losers | profit_reduced_from_reduced_winners | profit_added_from_increased_winners | loss_added_from_increased_losers | net_blocker_value |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 333 | baseline | 10.000 | unmatched | 152 | 164 | 0 | 0 | 0 | 0 | 5.175 | -7.883 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 333 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 152 | 164 | 0.000 | 0.000 | 0.000 | 0.000 | 1.294 | 1.971 | -0.677 |
| 333 | breadth_drawdown_only | 10.000 | unmatched | 152 | 164 | 0 | 0 | 0 | 0 | 5.175 | -7.883 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 334 | baseline | 10.000 | unmatched | 206 | 123 | 0 | 0 | 0 | 0 | 12.349 | -4.758 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 334 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 206 | 123 | 0.000 | 0.000 | 0.000 | 0.000 | 3.087 | 1.189 | 1.898 |
| 334 | breadth_drawdown_only | 10.000 | unmatched | 206 | 123 | 0 | 0 | 0 | 0 | 12.349 | -4.758 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 335 | baseline | 10.000 | unmatched | 149 | 181 | 0 | 0 | 0 | 0 | 6.813 | -7.149 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 335 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 149 | 181 | 0.000 | 0.000 | 0.000 | 0.000 | 1.703 | 1.787 | -0.084 |
| 335 | breadth_drawdown_only | 10.000 | unmatched | 149 | 181 | 0 | 0 | 0 | 0 | 6.813 | -7.149 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 336 | baseline | 10.000 | unmatched | 223 | 105 | 0 | 0 | 0 | 0 | 12.555 | -2.996 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 336 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 223 | 105 | 0.000 | 0.000 | 0.000 | 0.000 | 3.139 | 0.749 | 2.390 |
| 336 | breadth_drawdown_only | 10.000 | unmatched | 223 | 105 | 0 | 0 | 0 | 0 | 12.555 | -2.996 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 337 | baseline | 10.000 | unmatched | 141 | 190 | 0 | 0 | 0 | 0 | 5.118 | -9.566 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 337 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 141 | 190 | 0.000 | 0.000 | 0.000 | 0.000 | 1.280 | 2.392 | -1.112 |
| 337 | breadth_drawdown_only | 10.000 | unmatched | 141 | 190 | 0 | 0 | 0 | 0 | 5.118 | -9.566 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 338 | baseline | 10.000 | unmatched | 136 | 198 | 0 | 0 | 0 | 0 | 5.900 | -10.784 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 338 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 136 | 198 | 0.000 | 0.000 | 0.000 | 0.000 | 1.475 | 2.696 | -1.221 |
| 338 | breadth_drawdown_only | 10.000 | unmatched | 136 | 198 | 0 | 0 | 0 | 0 | 5.900 | -10.784 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 339 | baseline | 10.000 | unmatched | 215 | 106 | 0 | 0 | 0 | 0 | 10.158 | -4.440 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 339 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 215 | 106 | 0.000 | 0.000 | 0.000 | 0.000 | 2.540 | 1.110 | 1.430 |
| 339 | breadth_drawdown_only | 10.000 | unmatched | 215 | 106 | 0 | 0 | 0 | 0 | 10.158 | -4.440 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 340 | baseline | 10.000 | early_2025_broad_correction_fpi_outflows | 105 | 233 | 0 | 0 | 0 | 0 | 4.793 | -9.231 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 340 | breadth_soft_aggressive | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 0 | 0 | 105 | 233 | 0.000 | 0.000 | 0.000 | 0.000 | 1.198 | 2.308 | -1.110 |
| 340 | breadth_drawdown_only | 10.000 | early_2025_broad_correction_fpi_outflows | 105 | 233 | 0 | 0 | 0 | 0 | 4.793 | -9.231 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 341 | baseline | 10.000 | early_2025_broad_correction_fpi_outflows | 135 | 196 | 0 | 0 | 0 | 0 | 4.596 | -8.396 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 341 | breadth_soft_aggressive | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 0 | 0 | 135 | 196 | 0.000 | 0.000 | 0.000 | 0.000 | 1.149 | 2.099 | -0.950 |
| 341 | breadth_drawdown_only | 10.000 | early_2025_broad_correction_fpi_outflows | 135 | 196 | 0 | 0 | 0 | 0 | 4.596 | -8.396 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 342 | baseline | 10.000 | early_2025_broad_correction_fpi_outflows | 81 | 254 | 0 | 0 | 0 | 0 | 2.832 | -14.748 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 342 | breadth_soft_aggressive | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 29 | 112 | 52 | 142 | 0.000 | 0.000 | 5.655 | 0.846 | 0.426 | 1.802 | 3.433 |
| 342 | breadth_drawdown_only | 10.000 | early_2025_broad_correction_fpi_outflows | 52 | 142 | 29 | 112 | 0 | 0 | 1.704 | -7.208 | 5.655 | 0.846 | 0.000 | 0.000 | 4.809 |
| 343 | baseline | 10.000 | unmatched | 200 | 135 | 0 | 0 | 0 | 0 | 11.264 | -5.683 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 343 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 170 | 114 | 30 | 21 | 0.000 | 0.000 | 3.579 | 7.235 | 0.162 | 0.091 | -3.586 |
| 343 | breadth_drawdown_only | 10.000 | unmatched | 30 | 21 | 170 | 114 | 0 | 0 | 1.617 | -0.912 | 3.579 | 7.235 | 0.000 | 0.000 | -3.657 |
| 344 | baseline | 10.000 | unmatched | 225 | 129 | 0 | 0 | 0 | 0 | 9.318 | -4.045 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 344 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 210 | 127 | 15 | 2 | 0.000 | 0.000 | 3.016 | 6.377 | 0.082 | 0.002 | -3.282 |
| 344 | breadth_drawdown_only | 10.000 | unmatched | 15 | 2 | 210 | 127 | 0 | 0 | 0.816 | -0.024 | 3.016 | 6.377 | 0.000 | 0.000 | -3.361 |
| 345 | baseline | 10.000 | unmatched | 221 | 127 | 0 | 0 | 0 | 0 | 6.271 | -3.838 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 345 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 221 | 127 | 0 | 0 | 0.000 | 0.000 | 2.878 | 4.703 | 0.000 | 0.000 | -1.825 |
| 345 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 221 | 127 | 0 | 0 | 0.000 | 0.000 | 2.878 | 4.703 | 0.000 | 0.000 | -1.825 |
| 346 | baseline | 10.000 | unmatched | 199 | 149 | 0 | 0 | 0 | 0 | 6.457 | -4.841 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 346 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 199 | 149 | 0 | 0 | 0.000 | 0.000 | 3.631 | 4.843 | 0.000 | 0.000 | -1.212 |
| 346 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 199 | 149 | 0 | 0 | 0.000 | 0.000 | 3.631 | 4.843 | 0.000 | 0.000 | -1.212 |
| 347 | baseline | 10.000 | july_2025_broad_based_selling | 103 | 249 | 0 | 0 | 0 | 0 | 1.908 | -7.307 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 347 | breadth_soft_aggressive | 10.000 | july_2025_broad_based_selling | 0 | 0 | 103 | 249 | 0 | 0 | 0.000 | 0.000 | 5.480 | 1.431 | 0.000 | 0.000 | 4.049 |
| 347 | breadth_drawdown_only | 10.000 | july_2025_broad_based_selling | 0 | 0 | 103 | 249 | 0 | 0 | 0.000 | 0.000 | 5.480 | 1.431 | 0.000 | 0.000 | 4.049 |
| 348 | baseline | 10.000 | unmatched | 226 | 126 | 0 | 0 | 0 | 0 | 10.463 | -3.103 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 348 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 226 | 126 | 0.000 | 0.000 | 0.000 | 0.000 | 1.046 | 0.310 | 0.736 |
| 348 | breadth_drawdown_only | 10.000 | unmatched | 226 | 126 | 0 | 0 | 0 | 0 | 10.463 | -3.103 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 349 | baseline | 10.000 | unmatched | 195 | 159 | 0 | 0 | 0 | 0 | 6.854 | -5.357 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 349 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 195 | 159 | 0.000 | 0.000 | 0.000 | 0.000 | 1.713 | 1.339 | 0.374 |
| 349 | breadth_drawdown_only | 10.000 | unmatched | 195 | 159 | 0 | 0 | 0 | 0 | 6.854 | -5.357 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 350 | baseline | 10.000 | unmatched | 170 | 151 | 0 | 0 | 0 | 0 | 8.836 | -5.362 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 350 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 170 | 151 | 0.000 | 0.000 | 0.000 | 0.000 | 2.209 | 1.341 | 0.868 |
| 350 | breadth_drawdown_only | 10.000 | unmatched | 170 | 151 | 0 | 0 | 0 | 0 | 8.836 | -5.362 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 351 | baseline | 10.000 | unmatched | 159 | 189 | 0 | 0 | 0 | 0 | 9.282 | -8.609 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 351 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 159 | 189 | 0.000 | 0.000 | 0.000 | 0.000 | 2.320 | 2.152 | 0.168 |
| 351 | breadth_drawdown_only | 10.000 | unmatched | 159 | 189 | 0 | 0 | 0 | 0 | 9.282 | -8.609 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 352 | baseline | 10.000 | unmatched | 129 | 211 | 0 | 0 | 0 | 0 | 3.830 | -7.918 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 352 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 129 | 211 | 0.000 | 0.000 | 0.000 | 0.000 | 0.958 | 1.980 | -1.022 |
| 352 | breadth_drawdown_only | 10.000 | unmatched | 129 | 211 | 0 | 0 | 0 | 0 | 3.830 | -7.918 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## Decision

Reject: missing target diagnostic rows.
