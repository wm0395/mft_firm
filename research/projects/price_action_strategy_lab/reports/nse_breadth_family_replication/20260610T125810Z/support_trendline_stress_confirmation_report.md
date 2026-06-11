# Support Trendline Stress Confirmation

## Aggregate

| variant | cost_bps | return_pct | cagr_pct | ann_vol_pct | ann_sharpe | max_drawdown_pct | negative_fold_rate | worst_fold_sharpe | latest_fold_sharpe | average_exposure | turnover |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 10.000 | 29.134 | 13.637 | 8.318 | 1.579 | -19.560 | 0.500 | -26.145 | -4.849 | 1.000 | 0.253 |
| breadth_soft_aggressive | 10.000 | 14.570 | 7.037 | 9.368 | 0.773 | -29.993 | 0.500 | -26.145 | -4.849 | 1.042 | 0.262 |
| breadth_drawdown_only | 10.000 | 14.570 | 7.037 | 9.368 | 0.773 | -29.993 | 0.500 | -26.145 | -4.849 | 1.042 | 0.262 |
| baseline | 25.000 | 24.293 | 11.487 | 8.316 | 1.349 | -19.927 | 0.500 | -26.347 | -5.300 | 1.000 | 0.253 |
| breadth_soft_aggressive | 25.000 | 10.127 | 4.941 | 9.367 | 0.562 | -31.609 | 0.500 | -26.347 | -5.300 | 1.042 | 0.262 |
| breadth_drawdown_only | 25.000 | 10.127 | 4.941 | 9.367 | 0.562 | -31.609 | 0.500 | -26.347 | -5.300 | 1.042 | 0.262 |
| baseline | 50.000 | 16.625 | 7.993 | 8.314 | 0.966 | -20.535 | 0.542 | -26.677 | -6.044 | 1.000 | 0.253 |
| breadth_soft_aggressive | 50.000 | 13.840 | 6.696 | 8.964 | 0.768 | -27.369 | 0.542 | -26.677 | -6.044 | 1.012 | 0.254 |
| breadth_drawdown_only | 50.000 | 13.840 | 6.696 | 8.964 | 0.768 | -27.369 | 0.542 | -26.677 | -6.044 | 1.012 | 0.254 |

## Tail

| variant | cost_bps | mean_delta_vs_baseline | left_tail_delta | right_tail_retention | top_decile_retention | bottom_decile_improvement | best_fold_damage | worst_fold_improvement | ci_low | ci_high | paired_t_stat | paired_p_value | bh_p_value |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 10.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| breadth_soft_aggressive | 10.000 | -0.427 | -1.532 | 1.112 | 1.198 | -2.156 | 1.586 | -2.706 | -1.116 | 0.239 | -1.008 | 0.324 | 0.729 |
| breadth_drawdown_only | 10.000 | -0.427 | -1.532 | 1.112 | 1.198 | -2.156 | 1.586 | -2.706 | -1.116 | 0.239 | -1.008 | 0.324 | 0.729 |
| baseline | 25.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| breadth_soft_aggressive | 25.000 | -0.432 | -1.566 | 1.112 | 1.197 | -2.185 | 1.567 | -2.733 | -1.109 | 0.219 | -1.038 | 0.310 | 0.729 |
| breadth_drawdown_only | 25.000 | -0.432 | -1.566 | 1.112 | 1.197 | -2.185 | 1.567 | -2.733 | -1.109 | 0.219 | -1.038 | 0.310 | 0.729 |
| baseline | 50.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| breadth_soft_aggressive | 50.000 | -0.074 | -0.158 | 1.113 | 1.196 | 0.693 | 1.534 | 3.661 | -0.727 | 0.586 | -0.180 | 0.859 | 1.000 |
| breadth_drawdown_only | 50.000 | -0.074 | -0.158 | 1.113 | 1.196 | 0.693 | 1.534 | 3.661 | -0.727 | 0.586 | -0.180 | 0.859 | 1.000 |

## Event Split

| variant | cost_bps | split | fold_count | mean_delta | net_delta | average_exposure |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 10.000 | known_stress | 6 | 0.000 | 0.000 | 1.000 |
| baseline | 10.000 | unmatched | 18 | 0.000 | 0.000 | 1.000 |
| baseline | 10.000 | all | 24 | 0.000 | 0.000 | 1.000 |
| breadth_soft_aggressive | 10.000 | known_stress | 6 | -1.292 | -7.751 | 1.250 |
| breadth_soft_aggressive | 10.000 | unmatched | 18 | -0.138 | -2.486 | 0.973 |
| breadth_soft_aggressive | 10.000 | all | 24 | -0.427 | -10.236 | 1.042 |
| breadth_drawdown_only | 10.000 | known_stress | 6 | -1.292 | -7.751 | 1.250 |
| breadth_drawdown_only | 10.000 | unmatched | 18 | -0.138 | -2.486 | 0.973 |
| breadth_drawdown_only | 10.000 | all | 24 | -0.427 | -10.236 | 1.042 |
| baseline | 25.000 | known_stress | 6 | 0.000 | 0.000 | 1.000 |
| baseline | 25.000 | unmatched | 18 | 0.000 | 0.000 | 1.000 |
| baseline | 25.000 | all | 24 | 0.000 | 0.000 | 1.000 |
| breadth_soft_aggressive | 25.000 | known_stress | 6 | -1.328 | -7.966 | 1.250 |
| breadth_soft_aggressive | 25.000 | unmatched | 18 | -0.133 | -2.391 | 0.973 |
| breadth_soft_aggressive | 25.000 | all | 24 | -0.432 | -10.357 | 1.042 |
| breadth_drawdown_only | 25.000 | known_stress | 6 | -1.328 | -7.966 | 1.250 |
| breadth_drawdown_only | 25.000 | unmatched | 18 | -0.133 | -2.391 | 0.973 |
| breadth_drawdown_only | 25.000 | all | 24 | -0.432 | -10.357 | 1.042 |
| baseline | 50.000 | known_stress | 6 | 0.000 | 0.000 | 1.000 |
| baseline | 50.000 | unmatched | 18 | 0.000 | 0.000 | 1.000 |
| baseline | 50.000 | all | 24 | 0.000 | 0.000 | 1.000 |
| breadth_soft_aggressive | 50.000 | known_stress | 6 | 0.077 | 0.461 | 1.129 |
| breadth_soft_aggressive | 50.000 | unmatched | 18 | -0.124 | -2.233 | 0.973 |
| breadth_soft_aggressive | 50.000 | all | 24 | -0.074 | -1.771 | 1.012 |
| breadth_drawdown_only | 50.000 | known_stress | 6 | 0.077 | 0.461 | 1.129 |
| breadth_drawdown_only | 50.000 | unmatched | 18 | -0.124 | -2.233 | 0.973 |
| breadth_drawdown_only | 50.000 | all | 24 | -0.074 | -1.771 | 1.012 |

## Trade Diagnostics

| fold | variant | cost_bps | event_label | accepted_winner | accepted_loser | reduced_winner | reduced_loser | increased_winner | increased_loser | accepted_winner_pnl | accepted_loser_pnl | loss_reduced_from_reduced_losers | profit_reduced_from_reduced_winners | profit_added_from_increased_winners | loss_added_from_increased_losers | net_blocker_value |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 333 | baseline | 10.000 | unmatched | 151 | 164 | 0 | 0 | 0 | 0 | 6.012 | -7.343 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 333 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 151 | 164 | 0.000 | 0.000 | 0.000 | 0.000 | 1.503 | 1.836 | -0.333 |
| 333 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 151 | 164 | 0.000 | 0.000 | 0.000 | 0.000 | 1.503 | 1.836 | -0.333 |
| 334 | baseline | 10.000 | unmatched | 203 | 131 | 0 | 0 | 0 | 0 | 15.749 | -5.732 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 334 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 203 | 131 | 0.000 | 0.000 | 0.000 | 0.000 | 3.937 | 1.433 | 2.504 |
| 334 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 203 | 131 | 0.000 | 0.000 | 0.000 | 0.000 | 3.937 | 1.433 | 2.504 |
| 335 | baseline | 10.000 | unmatched | 131 | 199 | 0 | 0 | 0 | 0 | 6.685 | -6.420 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 335 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 131 | 199 | 0.000 | 0.000 | 0.000 | 0.000 | 1.671 | 1.605 | 0.066 |
| 335 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 131 | 199 | 0.000 | 0.000 | 0.000 | 0.000 | 1.671 | 1.605 | 0.066 |
| 336 | baseline | 10.000 | unmatched | 216 | 116 | 0 | 0 | 0 | 0 | 12.953 | -3.195 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 336 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 216 | 116 | 0.000 | 0.000 | 0.000 | 0.000 | 3.238 | 0.799 | 2.440 |
| 336 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 216 | 116 | 0.000 | 0.000 | 0.000 | 0.000 | 3.238 | 0.799 | 2.440 |
| 337 | baseline | 10.000 | unmatched | 134 | 203 | 0 | 0 | 0 | 0 | 5.638 | -9.138 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 337 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 134 | 203 | 0.000 | 0.000 | 0.000 | 0.000 | 1.410 | 2.285 | -0.875 |
| 337 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 134 | 203 | 0.000 | 0.000 | 0.000 | 0.000 | 1.410 | 2.285 | -0.875 |
| 338 | baseline | 10.000 | unmatched | 143 | 194 | 0 | 0 | 0 | 0 | 8.187 | -8.847 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 338 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 143 | 194 | 0.000 | 0.000 | 0.000 | 0.000 | 2.047 | 2.212 | -0.165 |
| 338 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 143 | 194 | 0.000 | 0.000 | 0.000 | 0.000 | 2.047 | 2.212 | -0.165 |
| 339 | baseline | 10.000 | unmatched | 231 | 97 | 0 | 0 | 0 | 0 | 12.972 | -3.682 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 339 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 231 | 97 | 0.000 | 0.000 | 0.000 | 0.000 | 3.243 | 0.921 | 2.322 |
| 339 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 231 | 97 | 0.000 | 0.000 | 0.000 | 0.000 | 3.243 | 0.921 | 2.322 |
| 340 | baseline | 10.000 | early_2025_broad_correction_fpi_outflows | 88 | 250 | 0 | 0 | 0 | 0 | 4.787 | -9.092 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 340 | breadth_soft_aggressive | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 0 | 0 | 88 | 250 | 0.000 | 0.000 | 0.000 | 0.000 | 1.197 | 2.273 | -1.076 |
| 340 | breadth_drawdown_only | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 0 | 0 | 88 | 250 | 0.000 | 0.000 | 0.000 | 0.000 | 1.197 | 2.273 | -1.076 |
| 341 | baseline | 10.000 | early_2025_broad_correction_fpi_outflows | 138 | 196 | 0 | 0 | 0 | 0 | 4.551 | -7.708 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 341 | breadth_soft_aggressive | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 0 | 0 | 138 | 196 | 0.000 | 0.000 | 0.000 | 0.000 | 1.138 | 1.927 | -0.789 |
| 341 | breadth_drawdown_only | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 0 | 0 | 138 | 196 | 0.000 | 0.000 | 0.000 | 0.000 | 1.138 | 1.927 | -0.789 |
| 342 | baseline | 10.000 | early_2025_broad_correction_fpi_outflows | 87 | 257 | 0 | 0 | 0 | 0 | 2.953 | -15.153 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 342 | breadth_soft_aggressive | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 0 | 0 | 87 | 257 | 0.000 | 0.000 | 0.000 | 0.000 | 0.738 | 3.788 | -3.050 |
| 342 | breadth_drawdown_only | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 0 | 0 | 87 | 257 | 0.000 | 0.000 | 0.000 | 0.000 | 0.738 | 3.788 | -3.050 |
| 343 | baseline | 10.000 | unmatched | 197 | 137 | 0 | 0 | 0 | 0 | 10.998 | -5.038 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 343 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 170 | 113 | 27 | 24 | 0.000 | 0.000 | 3.157 | 7.250 | 0.133 | 0.083 | -4.042 |
| 343 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 170 | 113 | 27 | 24 | 0.000 | 0.000 | 3.157 | 7.250 | 0.133 | 0.083 | -4.042 |
| 344 | baseline | 10.000 | unmatched | 234 | 117 | 0 | 0 | 0 | 0 | 11.384 | -3.776 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 344 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 218 | 116 | 16 | 1 | 0.000 | 0.000 | 2.819 | 7.718 | 0.109 | 0.002 | -4.792 |
| 344 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 218 | 116 | 16 | 1 | 0.000 | 0.000 | 2.819 | 7.718 | 0.109 | 0.002 | -4.792 |
| 345 | baseline | 10.000 | unmatched | 191 | 159 | 0 | 0 | 0 | 0 | 7.255 | -4.770 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 345 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 191 | 159 | 0 | 0 | 0.000 | 0.000 | 3.578 | 5.441 | 0.000 | 0.000 | -1.863 |
| 345 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 191 | 159 | 0 | 0 | 0.000 | 0.000 | 3.578 | 5.441 | 0.000 | 0.000 | -1.863 |
| 346 | baseline | 10.000 | unmatched | 186 | 163 | 0 | 0 | 0 | 0 | 8.519 | -4.610 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 346 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 186 | 163 | 0 | 0 | 0.000 | 0.000 | 3.458 | 6.389 | 0.000 | 0.000 | -2.932 |
| 346 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 186 | 163 | 0 | 0 | 0.000 | 0.000 | 3.458 | 6.389 | 0.000 | 0.000 | -2.932 |
| 347 | baseline | 10.000 | july_2025_broad_based_selling | 106 | 246 | 0 | 0 | 0 | 0 | 2.701 | -7.835 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 347 | breadth_soft_aggressive | 10.000 | july_2025_broad_based_selling | 0 | 0 | 0 | 0 | 106 | 246 | 0.000 | 0.000 | 0.000 | 0.000 | 0.675 | 1.959 | -1.284 |
| 347 | breadth_drawdown_only | 10.000 | july_2025_broad_based_selling | 0 | 0 | 0 | 0 | 106 | 246 | 0.000 | 0.000 | 0.000 | 0.000 | 0.675 | 1.959 | -1.284 |
| 348 | baseline | 10.000 | unmatched | 253 | 101 | 0 | 0 | 0 | 0 | 11.033 | -2.436 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 348 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 253 | 101 | 0.000 | 0.000 | 0.000 | 0.000 | 2.758 | 0.609 | 2.149 |
| 348 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 253 | 101 | 0.000 | 0.000 | 0.000 | 0.000 | 2.758 | 0.609 | 2.149 |
| 349 | baseline | 10.000 | unmatched | 166 | 189 | 0 | 0 | 0 | 0 | 6.543 | -7.457 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 349 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 166 | 189 | 0.000 | 0.000 | 0.000 | 0.000 | 1.636 | 1.864 | -0.229 |
| 349 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 166 | 189 | 0.000 | 0.000 | 0.000 | 0.000 | 1.636 | 1.864 | -0.229 |
| 350 | baseline | 10.000 | unmatched | 178 | 169 | 0 | 0 | 0 | 0 | 8.925 | -6.385 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 350 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 178 | 169 | 0.000 | 0.000 | 0.000 | 0.000 | 2.231 | 1.596 | 0.635 |
| 350 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 178 | 169 | 0.000 | 0.000 | 0.000 | 0.000 | 2.231 | 1.596 | 0.635 |
| 351 | baseline | 10.000 | unmatched | 151 | 200 | 0 | 0 | 0 | 0 | 8.277 | -9.330 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 351 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 151 | 200 | 0.000 | 0.000 | 0.000 | 0.000 | 2.069 | 2.333 | -0.263 |
| 351 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 151 | 200 | 0.000 | 0.000 | 0.000 | 0.000 | 2.069 | 2.333 | -0.263 |
| 352 | baseline | 10.000 | unmatched | 136 | 204 | 0 | 0 | 0 | 0 | 4.386 | -7.228 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 352 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 136 | 204 | 0.000 | 0.000 | 0.000 | 0.000 | 1.096 | 1.807 | -0.711 |
| 352 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 136 | 204 | 0.000 | 0.000 | 0.000 | 0.000 | 1.096 | 1.807 | -0.711 |

## Decision

Reject: missing target diagnostic rows.
