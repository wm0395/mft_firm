# Support Trendline Stress Confirmation

## Aggregate

| variant | cost_bps | return_pct | cagr_pct | ann_vol_pct | ann_sharpe | max_drawdown_pct | negative_fold_rate | worst_fold_sharpe | latest_fold_sharpe | average_exposure | turnover |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 10.000 | 23.334 | 11.056 | 7.838 | 1.377 | -19.116 | 0.458 | -19.917 | 1.480 | 1.000 | 0.291 |
| breadth_soft_aggressive | 10.000 | 14.259 | 6.892 | 8.570 | 0.820 | -21.143 | 0.458 | -18.336 | 1.480 | 1.025 | 0.303 |
| breadth_drawdown_only | 10.000 | 13.618 | 6.592 | 7.085 | 0.936 | -17.106 | 0.458 | -18.336 | 1.480 | 0.836 | 0.247 |
| baseline | 25.000 | 18.032 | 8.643 | 7.838 | 1.097 | -19.608 | 0.458 | -20.284 | 0.944 | 1.000 | 0.291 |
| breadth_soft_aggressive | 25.000 | 8.935 | 4.372 | 8.552 | 0.543 | -23.412 | 0.458 | -18.651 | 0.944 | 1.025 | 0.303 |
| breadth_drawdown_only | 25.000 | 9.451 | 4.619 | 7.083 | 0.673 | -18.929 | 0.458 | -18.651 | 0.944 | 0.836 | 0.247 |
| baseline | 50.000 | 9.695 | 4.736 | 7.841 | 0.629 | -20.423 | 0.458 | -20.894 | 0.062 | 1.000 | 0.291 |
| breadth_soft_aggressive | 50.000 | 0.626 | 0.313 | 8.449 | 0.079 | -26.244 | 0.458 | -19.633 | 0.062 | 1.013 | 0.299 |
| breadth_drawdown_only | 50.000 | 2.841 | 1.411 | 7.082 | 0.233 | -21.878 | 0.458 | -19.633 | 0.062 | 0.836 | 0.247 |

## Tail

| variant | cost_bps | mean_delta_vs_baseline | left_tail_delta | right_tail_retention | top_decile_retention | bottom_decile_improvement | best_fold_damage | worst_fold_improvement | ci_low | ci_high | paired_t_stat | paired_p_value | bh_p_value |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 10.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| breadth_soft_aggressive | 10.000 | -0.299 | -0.469 | 1.080 | 0.947 | 0.001 | 1.353 | 3.123 | -0.914 | 0.310 | -0.782 | 0.442 | 0.664 |
| breadth_drawdown_only | 10.000 | -0.381 | 0.746 | 0.895 | 0.817 | 1.492 | 0.000 | 4.476 | -0.949 | 0.174 | -1.096 | 0.284 | 0.664 |
| baseline | 25.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| breadth_soft_aggressive | 25.000 | -0.315 | -0.497 | 1.076 | 0.940 | -0.018 | 1.325 | 3.143 | -0.927 | 0.292 | -0.831 | 0.414 | 0.664 |
| breadth_drawdown_only | 25.000 | -0.353 | 0.754 | 0.895 | 0.818 | 1.508 | 0.000 | 4.523 | -0.910 | 0.190 | -1.033 | 0.312 | 0.664 |
| baseline | 50.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| breadth_soft_aggressive | 50.000 | -0.346 | -0.421 | 1.049 | 0.940 | 0.194 | 1.278 | 3.175 | -0.920 | 0.220 | -0.977 | 0.339 | 0.664 |
| breadth_drawdown_only | 50.000 | -0.307 | 0.767 | 0.894 | 0.818 | 1.534 | 0.000 | 4.601 | -0.849 | 0.220 | -0.922 | 0.366 | 0.664 |

## Event Split

| variant | cost_bps | split | fold_count | mean_delta | net_delta | average_exposure |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 10.000 | known_stress | 6 | 0.000 | 0.000 | 1.000 |
| baseline | 10.000 | unmatched | 18 | 0.000 | 0.000 | 1.000 |
| baseline | 10.000 | all | 24 | 0.000 | 0.000 | 1.000 |
| breadth_soft_aggressive | 10.000 | known_stress | 6 | -0.250 | -1.503 | 1.179 |
| breadth_soft_aggressive | 10.000 | unmatched | 18 | -0.316 | -5.684 | 0.974 |
| breadth_soft_aggressive | 10.000 | all | 24 | -0.299 | -7.187 | 1.025 |
| breadth_drawdown_only | 10.000 | known_stress | 6 | 0.746 | 4.476 | 0.946 |
| breadth_drawdown_only | 10.000 | unmatched | 18 | -0.757 | -13.626 | 0.800 |
| breadth_drawdown_only | 10.000 | all | 24 | -0.381 | -9.150 | 0.836 |
| baseline | 25.000 | known_stress | 6 | 0.000 | 0.000 | 1.000 |
| baseline | 25.000 | unmatched | 18 | 0.000 | 0.000 | 1.000 |
| baseline | 25.000 | all | 24 | 0.000 | 0.000 | 1.000 |
| breadth_soft_aggressive | 25.000 | known_stress | 6 | -0.284 | -1.705 | 1.179 |
| breadth_soft_aggressive | 25.000 | unmatched | 18 | -0.326 | -5.862 | 0.974 |
| breadth_soft_aggressive | 25.000 | all | 24 | -0.315 | -7.567 | 1.025 |
| breadth_drawdown_only | 25.000 | known_stress | 6 | 0.754 | 4.523 | 0.946 |
| breadth_drawdown_only | 25.000 | unmatched | 18 | -0.722 | -13.002 | 0.800 |
| breadth_drawdown_only | 25.000 | all | 24 | -0.353 | -8.479 | 0.836 |
| baseline | 50.000 | known_stress | 6 | 0.000 | 0.000 | 1.000 |
| baseline | 50.000 | unmatched | 18 | 0.000 | 0.000 | 1.000 |
| baseline | 50.000 | all | 24 | 0.000 | 0.000 | 1.000 |
| breadth_soft_aggressive | 50.000 | known_stress | 6 | -0.218 | -1.307 | 1.154 |
| breadth_soft_aggressive | 50.000 | unmatched | 18 | -0.389 | -6.998 | 0.966 |
| breadth_soft_aggressive | 50.000 | all | 24 | -0.346 | -8.305 | 1.013 |
| breadth_drawdown_only | 50.000 | known_stress | 6 | 0.767 | 4.601 | 0.946 |
| breadth_drawdown_only | 50.000 | unmatched | 18 | -0.665 | -11.965 | 0.800 |
| breadth_drawdown_only | 50.000 | all | 24 | -0.307 | -7.364 | 0.836 |

## Trade Diagnostics

| fold | variant | cost_bps | event_label | accepted_winner | accepted_loser | reduced_winner | reduced_loser | increased_winner | increased_loser | accepted_winner_pnl | accepted_loser_pnl | loss_reduced_from_reduced_losers | profit_reduced_from_reduced_winners | profit_added_from_increased_winners | loss_added_from_increased_losers | net_blocker_value |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 333 | baseline | 10.000 | unmatched | 148 | 162 | 0 | 0 | 0 | 0 | 6.239 | -7.857 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 333 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 148 | 162 | 0.000 | 0.000 | 0.000 | 0.000 | 1.560 | 1.964 | -0.405 |
| 333 | breadth_drawdown_only | 10.000 | unmatched | 148 | 162 | 0 | 0 | 0 | 0 | 6.239 | -7.857 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 334 | baseline | 10.000 | unmatched | 211 | 119 | 0 | 0 | 0 | 0 | 13.496 | -5.568 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 334 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 211 | 119 | 0.000 | 0.000 | 0.000 | 0.000 | 3.374 | 1.392 | 1.982 |
| 334 | breadth_drawdown_only | 10.000 | unmatched | 211 | 119 | 0 | 0 | 0 | 0 | 13.496 | -5.568 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 335 | baseline | 10.000 | unmatched | 134 | 197 | 0 | 0 | 0 | 0 | 6.417 | -7.032 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 335 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 134 | 197 | 0.000 | 0.000 | 0.000 | 0.000 | 1.604 | 1.758 | -0.154 |
| 335 | breadth_drawdown_only | 10.000 | unmatched | 134 | 197 | 0 | 0 | 0 | 0 | 6.417 | -7.032 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 336 | baseline | 10.000 | unmatched | 206 | 123 | 0 | 0 | 0 | 0 | 10.520 | -3.704 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 336 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 206 | 123 | 0.000 | 0.000 | 0.000 | 0.000 | 2.630 | 0.926 | 1.704 |
| 336 | breadth_drawdown_only | 10.000 | unmatched | 206 | 123 | 0 | 0 | 0 | 0 | 10.520 | -3.704 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 337 | baseline | 10.000 | unmatched | 130 | 193 | 0 | 0 | 0 | 0 | 5.239 | -9.413 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 337 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 130 | 193 | 0.000 | 0.000 | 0.000 | 0.000 | 1.310 | 2.353 | -1.043 |
| 337 | breadth_drawdown_only | 10.000 | unmatched | 130 | 193 | 0 | 0 | 0 | 0 | 5.239 | -9.413 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 338 | baseline | 10.000 | unmatched | 150 | 185 | 0 | 0 | 0 | 0 | 9.116 | -9.317 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 338 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 150 | 185 | 0.000 | 0.000 | 0.000 | 0.000 | 2.279 | 2.329 | -0.050 |
| 338 | breadth_drawdown_only | 10.000 | unmatched | 150 | 185 | 0 | 0 | 0 | 0 | 9.116 | -9.317 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 339 | baseline | 10.000 | unmatched | 225 | 94 | 0 | 0 | 0 | 0 | 12.799 | -4.827 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 339 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 225 | 94 | 0.000 | 0.000 | 0.000 | 0.000 | 3.200 | 1.207 | 1.993 |
| 339 | breadth_drawdown_only | 10.000 | unmatched | 225 | 94 | 0 | 0 | 0 | 0 | 12.799 | -4.827 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 340 | baseline | 10.000 | early_2025_broad_correction_fpi_outflows | 97 | 241 | 0 | 0 | 0 | 0 | 5.087 | -9.614 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 340 | breadth_soft_aggressive | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 0 | 0 | 97 | 241 | 0.000 | 0.000 | 0.000 | 0.000 | 1.272 | 2.403 | -1.132 |
| 340 | breadth_drawdown_only | 10.000 | early_2025_broad_correction_fpi_outflows | 97 | 241 | 0 | 0 | 0 | 0 | 5.087 | -9.614 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 341 | baseline | 10.000 | early_2025_broad_correction_fpi_outflows | 146 | 186 | 0 | 0 | 0 | 0 | 5.418 | -7.714 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 341 | breadth_soft_aggressive | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 0 | 0 | 146 | 186 | 0.000 | 0.000 | 0.000 | 0.000 | 1.355 | 1.928 | -0.574 |
| 341 | breadth_drawdown_only | 10.000 | early_2025_broad_correction_fpi_outflows | 146 | 186 | 0 | 0 | 0 | 0 | 5.418 | -7.714 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 342 | baseline | 10.000 | early_2025_broad_correction_fpi_outflows | 81 | 253 | 0 | 0 | 0 | 0 | 2.889 | -15.111 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 342 | breadth_soft_aggressive | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 25 | 116 | 56 | 137 | 0.000 | 0.000 | 5.621 | 0.747 | 0.473 | 1.904 | 3.444 |
| 342 | breadth_drawdown_only | 10.000 | early_2025_broad_correction_fpi_outflows | 56 | 137 | 25 | 116 | 0 | 0 | 1.893 | -7.616 | 5.621 | 0.747 | 0.000 | 0.000 | 4.875 |
| 343 | baseline | 10.000 | unmatched | 184 | 150 | 0 | 0 | 0 | 0 | 10.382 | -5.539 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 343 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 159 | 124 | 25 | 26 | 0.000 | 0.000 | 3.497 | 6.759 | 0.342 | 0.219 | -3.139 |
| 343 | breadth_drawdown_only | 10.000 | unmatched | 25 | 26 | 159 | 124 | 0 | 0 | 1.370 | -0.876 | 3.497 | 6.759 | 0.000 | 0.000 | -3.262 |
| 344 | baseline | 10.000 | unmatched | 238 | 115 | 0 | 0 | 0 | 0 | 11.839 | -3.666 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 344 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 221 | 115 | 17 | 0 | 0.000 | 0.000 | 2.750 | 7.906 | 0.324 | 0.000 | -4.832 |
| 344 | breadth_drawdown_only | 10.000 | unmatched | 17 | 0 | 221 | 115 | 0 | 0 | 1.297 | 0.000 | 2.750 | 7.906 | 0.000 | 0.000 | -5.157 |
| 345 | baseline | 10.000 | unmatched | 207 | 144 | 0 | 0 | 0 | 0 | 7.199 | -4.379 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 345 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 207 | 144 | 0 | 0 | 0.000 | 0.000 | 3.284 | 5.399 | 0.000 | 0.000 | -2.115 |
| 345 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 207 | 144 | 0 | 0 | 0.000 | 0.000 | 3.284 | 5.399 | 0.000 | 0.000 | -2.115 |
| 346 | baseline | 10.000 | unmatched | 195 | 155 | 0 | 0 | 0 | 0 | 7.912 | -4.437 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 346 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 195 | 155 | 0 | 0 | 0.000 | 0.000 | 3.328 | 5.934 | 0.000 | 0.000 | -2.607 |
| 346 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 195 | 155 | 0 | 0 | 0.000 | 0.000 | 3.328 | 5.934 | 0.000 | 0.000 | -2.607 |
| 347 | baseline | 10.000 | july_2025_broad_based_selling | 109 | 243 | 0 | 0 | 0 | 0 | 2.945 | -7.461 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 347 | breadth_soft_aggressive | 10.000 | july_2025_broad_based_selling | 0 | 0 | 0 | 0 | 109 | 243 | 0.000 | 0.000 | 0.000 | 0.000 | 0.736 | 1.865 | -1.129 |
| 347 | breadth_drawdown_only | 10.000 | july_2025_broad_based_selling | 109 | 243 | 0 | 0 | 0 | 0 | 2.945 | -7.461 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 348 | baseline | 10.000 | unmatched | 236 | 116 | 0 | 0 | 0 | 0 | 9.345 | -2.673 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 348 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 236 | 116 | 0.000 | 0.000 | 0.000 | 0.000 | 2.336 | 0.668 | 1.668 |
| 348 | breadth_drawdown_only | 10.000 | unmatched | 236 | 116 | 0 | 0 | 0 | 0 | 9.345 | -2.673 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 349 | baseline | 10.000 | unmatched | 159 | 195 | 0 | 0 | 0 | 0 | 6.413 | -5.585 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 349 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 159 | 195 | 0.000 | 0.000 | 0.000 | 0.000 | 1.603 | 1.396 | 0.207 |
| 349 | breadth_drawdown_only | 10.000 | unmatched | 159 | 195 | 0 | 0 | 0 | 0 | 6.413 | -5.585 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 350 | baseline | 10.000 | unmatched | 175 | 145 | 0 | 0 | 0 | 0 | 10.214 | -5.609 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 350 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 175 | 145 | 0.000 | 0.000 | 0.000 | 0.000 | 2.554 | 1.402 | 1.151 |
| 350 | breadth_drawdown_only | 10.000 | unmatched | 175 | 145 | 0 | 0 | 0 | 0 | 10.214 | -5.609 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 351 | baseline | 10.000 | unmatched | 134 | 185 | 0 | 0 | 0 | 0 | 7.171 | -9.887 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 351 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 134 | 185 | 0.000 | 0.000 | 0.000 | 0.000 | 1.793 | 2.472 | -0.679 |
| 351 | breadth_drawdown_only | 10.000 | unmatched | 134 | 185 | 0 | 0 | 0 | 0 | 7.171 | -9.887 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 352 | baseline | 10.000 | unmatched | 156 | 185 | 0 | 0 | 0 | 0 | 4.332 | -6.382 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 352 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 156 | 185 | 0.000 | 0.000 | 0.000 | 0.000 | 1.083 | 1.596 | -0.513 |
| 352 | breadth_drawdown_only | 10.000 | unmatched | 156 | 185 | 0 | 0 | 0 | 0 | 4.332 | -6.382 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## Decision

Reject: missing target diagnostic rows.
