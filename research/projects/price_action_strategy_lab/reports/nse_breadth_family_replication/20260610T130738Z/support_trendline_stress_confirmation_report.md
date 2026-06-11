# Support Trendline Stress Confirmation

## Aggregate

| variant | cost_bps | return_pct | cagr_pct | ann_vol_pct | ann_sharpe | max_drawdown_pct | negative_fold_rate | worst_fold_sharpe | latest_fold_sharpe | average_exposure | turnover |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 10.000 | 18.682 | 8.941 | 7.705 | 1.150 | -19.402 | 0.458 | -22.210 | 0.871 | 1.000 | 0.333 |
| breadth_soft_aggressive | 10.000 | 12.286 | 5.965 | 8.522 | 0.722 | -22.469 | 0.458 | -19.851 | 0.871 | 1.018 | 0.345 |
| breadth_drawdown_only | 10.000 | 12.286 | 5.965 | 8.522 | 0.722 | -22.469 | 0.458 | -19.851 | 0.871 | 1.018 | 0.345 |
| baseline | 25.000 | 12.850 | 6.231 | 7.703 | 0.823 | -19.954 | 0.458 | -22.564 | 0.209 | 1.000 | 0.333 |
| breadth_soft_aggressive | 25.000 | 6.576 | 3.236 | 8.521 | 0.416 | -24.826 | 0.458 | -20.442 | 0.209 | 1.018 | 0.345 |
| breadth_drawdown_only | 25.000 | 6.576 | 3.236 | 8.521 | 0.416 | -24.826 | 0.458 | -20.442 | 0.209 | 1.018 | 0.345 |
| baseline | 50.000 | 3.759 | 1.862 | 7.700 | 0.278 | -20.985 | 0.500 | -23.146 | -0.889 | 1.000 | 0.333 |
| breadth_soft_aggressive | 50.000 | 2.956 | 1.467 | 8.333 | 0.216 | -24.914 | 0.500 | -21.376 | -0.889 | 0.970 | 0.329 |
| breadth_drawdown_only | 50.000 | 2.956 | 1.467 | 8.333 | 0.216 | -24.914 | 0.500 | -21.376 | -0.889 | 0.970 | 0.329 |

## Tail

| variant | cost_bps | mean_delta_vs_baseline | left_tail_delta | right_tail_retention | top_decile_retention | bottom_decile_improvement | best_fold_damage | worst_fold_improvement | ci_low | ci_high | paired_t_stat | paired_p_value | bh_p_value |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 10.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| breadth_soft_aggressive | 10.000 | -0.203 | -0.421 | 1.105 | 1.201 | -0.191 | 1.229 | 2.733 | -0.773 | 0.372 | -0.566 | 0.577 | 1.000 |
| breadth_drawdown_only | 10.000 | -0.203 | -0.421 | 1.105 | 1.201 | -0.191 | 1.229 | 2.733 | -0.773 | 0.372 | -0.566 | 0.577 | 1.000 |
| baseline | 25.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| breadth_soft_aggressive | 25.000 | -0.210 | -0.453 | 1.106 | 1.200 | -0.217 | 1.199 | 2.753 | -0.755 | 0.351 | -0.601 | 0.554 | 1.000 |
| breadth_drawdown_only | 25.000 | -0.210 | -0.453 | 1.106 | 1.200 | -0.217 | 1.199 | 2.753 | -0.755 | 0.351 | -0.601 | 0.554 | 1.000 |
| baseline | 50.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| breadth_soft_aggressive | 50.000 | -0.020 | 0.468 | 1.085 | 1.200 | 0.155 | 1.150 | 2.786 | -0.587 | 0.547 | -0.054 | 0.957 | 1.000 |
| breadth_drawdown_only | 50.000 | -0.020 | 0.468 | 1.085 | 1.200 | 0.155 | 1.150 | 2.786 | -0.587 | 0.547 | -0.054 | 0.957 | 1.000 |

## Event Split

| variant | cost_bps | split | fold_count | mean_delta | net_delta | average_exposure |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 10.000 | known_stress | 6 | 0.000 | 0.000 | 1.000 |
| baseline | 10.000 | unmatched | 18 | 0.000 | 0.000 | 1.000 |
| baseline | 10.000 | all | 24 | 0.000 | 0.000 | 1.000 |
| breadth_soft_aggressive | 10.000 | known_stress | 6 | -0.207 | -1.241 | 1.154 |
| breadth_soft_aggressive | 10.000 | unmatched | 18 | -0.202 | -3.634 | 0.973 |
| breadth_soft_aggressive | 10.000 | all | 24 | -0.203 | -4.875 | 1.018 |
| breadth_drawdown_only | 10.000 | known_stress | 6 | -0.207 | -1.241 | 1.154 |
| breadth_drawdown_only | 10.000 | unmatched | 18 | -0.202 | -3.634 | 0.973 |
| breadth_drawdown_only | 10.000 | all | 24 | -0.203 | -4.875 | 1.018 |
| baseline | 25.000 | known_stress | 6 | 0.000 | 0.000 | 1.000 |
| baseline | 25.000 | unmatched | 18 | 0.000 | 0.000 | 1.000 |
| baseline | 25.000 | all | 24 | 0.000 | 0.000 | 1.000 |
| breadth_soft_aggressive | 25.000 | known_stress | 6 | -0.243 | -1.460 | 1.154 |
| breadth_soft_aggressive | 25.000 | unmatched | 18 | -0.199 | -3.587 | 0.973 |
| breadth_soft_aggressive | 25.000 | all | 24 | -0.210 | -5.047 | 1.018 |
| breadth_drawdown_only | 25.000 | known_stress | 6 | -0.243 | -1.460 | 1.154 |
| breadth_drawdown_only | 25.000 | unmatched | 18 | -0.199 | -3.587 | 0.973 |
| breadth_drawdown_only | 25.000 | all | 24 | -0.210 | -5.047 | 1.018 |
| baseline | 50.000 | known_stress | 6 | 0.000 | 0.000 | 1.000 |
| baseline | 50.000 | unmatched | 18 | 0.000 | 0.000 | 1.000 |
| baseline | 50.000 | all | 24 | 0.000 | 0.000 | 1.000 |
| breadth_soft_aggressive | 50.000 | known_stress | 6 | 0.671 | 4.028 | 0.987 |
| breadth_soft_aggressive | 50.000 | unmatched | 18 | -0.250 | -4.503 | 0.965 |
| breadth_soft_aggressive | 50.000 | all | 24 | -0.020 | -0.475 | 0.970 |
| breadth_drawdown_only | 50.000 | known_stress | 6 | 0.671 | 4.028 | 0.987 |
| breadth_drawdown_only | 50.000 | unmatched | 18 | -0.250 | -4.503 | 0.965 |
| breadth_drawdown_only | 50.000 | all | 24 | -0.020 | -0.475 | 0.970 |

## Trade Diagnostics

| fold | variant | cost_bps | event_label | accepted_winner | accepted_loser | reduced_winner | reduced_loser | increased_winner | increased_loser | accepted_winner_pnl | accepted_loser_pnl | loss_reduced_from_reduced_losers | profit_reduced_from_reduced_winners | profit_added_from_increased_winners | loss_added_from_increased_losers | net_blocker_value |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 333 | baseline | 10.000 | unmatched | 158 | 157 | 0 | 0 | 0 | 0 | 5.335 | -7.230 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 333 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 158 | 157 | 0.000 | 0.000 | 0.000 | 0.000 | 1.334 | 1.807 | -0.474 |
| 333 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 158 | 157 | 0.000 | 0.000 | 0.000 | 0.000 | 1.334 | 1.807 | -0.474 |
| 334 | baseline | 10.000 | unmatched | 208 | 122 | 0 | 0 | 0 | 0 | 13.519 | -4.458 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 334 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 208 | 122 | 0.000 | 0.000 | 0.000 | 0.000 | 3.380 | 1.115 | 2.265 |
| 334 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 208 | 122 | 0.000 | 0.000 | 0.000 | 0.000 | 3.380 | 1.115 | 2.265 |
| 335 | baseline | 10.000 | unmatched | 143 | 187 | 0 | 0 | 0 | 0 | 6.195 | -7.014 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 335 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 143 | 187 | 0.000 | 0.000 | 0.000 | 0.000 | 1.549 | 1.753 | -0.205 |
| 335 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 143 | 187 | 0.000 | 0.000 | 0.000 | 0.000 | 1.549 | 1.753 | -0.205 |
| 336 | baseline | 10.000 | unmatched | 220 | 110 | 0 | 0 | 0 | 0 | 11.626 | -3.027 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 336 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 220 | 110 | 0.000 | 0.000 | 0.000 | 0.000 | 2.907 | 0.757 | 2.150 |
| 336 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 220 | 110 | 0.000 | 0.000 | 0.000 | 0.000 | 2.907 | 0.757 | 2.150 |
| 337 | baseline | 10.000 | unmatched | 153 | 172 | 0 | 0 | 0 | 0 | 5.551 | -8.558 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 337 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 153 | 172 | 0.000 | 0.000 | 0.000 | 0.000 | 1.388 | 2.140 | -0.752 |
| 337 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 153 | 172 | 0.000 | 0.000 | 0.000 | 0.000 | 1.388 | 2.140 | -0.752 |
| 338 | baseline | 10.000 | unmatched | 157 | 179 | 0 | 0 | 0 | 0 | 7.171 | -9.724 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 338 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 157 | 179 | 0.000 | 0.000 | 0.000 | 0.000 | 1.793 | 2.431 | -0.638 |
| 338 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 157 | 179 | 0.000 | 0.000 | 0.000 | 0.000 | 1.793 | 2.431 | -0.638 |
| 339 | baseline | 10.000 | unmatched | 217 | 105 | 0 | 0 | 0 | 0 | 11.238 | -3.689 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 339 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 217 | 105 | 0.000 | 0.000 | 0.000 | 0.000 | 2.810 | 0.922 | 1.887 |
| 339 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 217 | 105 | 0.000 | 0.000 | 0.000 | 0.000 | 2.810 | 0.922 | 1.887 |
| 340 | baseline | 10.000 | early_2025_broad_correction_fpi_outflows | 89 | 249 | 0 | 0 | 0 | 0 | 4.183 | -9.712 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 340 | breadth_soft_aggressive | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 0 | 0 | 89 | 249 | 0.000 | 0.000 | 0.000 | 0.000 | 1.046 | 2.428 | -1.382 |
| 340 | breadth_drawdown_only | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 0 | 0 | 89 | 249 | 0.000 | 0.000 | 0.000 | 0.000 | 1.046 | 2.428 | -1.382 |
| 341 | baseline | 10.000 | early_2025_broad_correction_fpi_outflows | 148 | 182 | 0 | 0 | 0 | 0 | 5.013 | -7.332 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 341 | breadth_soft_aggressive | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 0 | 0 | 148 | 182 | 0.000 | 0.000 | 0.000 | 0.000 | 1.253 | 1.833 | -0.580 |
| 341 | breadth_drawdown_only | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 0 | 0 | 148 | 182 | 0.000 | 0.000 | 0.000 | 0.000 | 1.253 | 1.833 | -0.580 |
| 342 | baseline | 10.000 | early_2025_broad_correction_fpi_outflows | 84 | 248 | 0 | 0 | 0 | 0 | 2.712 | -14.916 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 342 | breadth_soft_aggressive | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 27 | 110 | 57 | 138 | 0.000 | 0.000 | 5.152 | 0.599 | 0.478 | 2.012 | 3.019 |
| 342 | breadth_drawdown_only | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 27 | 110 | 57 | 138 | 0.000 | 0.000 | 5.152 | 0.599 | 0.478 | 2.012 | 3.019 |
| 343 | baseline | 10.000 | unmatched | 195 | 136 | 0 | 0 | 0 | 0 | 9.793 | -5.453 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 343 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 166 | 115 | 29 | 21 | 0.000 | 0.000 | 3.500 | 6.297 | 0.140 | 0.079 | -2.737 |
| 343 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 166 | 115 | 29 | 21 | 0.000 | 0.000 | 3.500 | 6.297 | 0.140 | 0.079 | -2.737 |
| 344 | baseline | 10.000 | unmatched | 233 | 119 | 0 | 0 | 0 | 0 | 11.133 | -4.089 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 344 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 217 | 118 | 16 | 1 | 0.000 | 0.000 | 3.054 | 7.444 | 0.121 | 0.002 | -4.271 |
| 344 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 217 | 118 | 16 | 1 | 0.000 | 0.000 | 3.054 | 7.444 | 0.121 | 0.002 | -4.271 |
| 345 | baseline | 10.000 | unmatched | 220 | 132 | 0 | 0 | 0 | 0 | 5.682 | -3.987 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 345 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 220 | 132 | 0 | 0 | 0.000 | 0.000 | 2.990 | 4.261 | 0.000 | 0.000 | -1.271 |
| 345 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 220 | 132 | 0 | 0 | 0.000 | 0.000 | 2.990 | 4.261 | 0.000 | 0.000 | -1.271 |
| 346 | baseline | 10.000 | unmatched | 212 | 142 | 0 | 0 | 0 | 0 | 7.734 | -4.039 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 346 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 212 | 142 | 0 | 0 | 0.000 | 0.000 | 3.029 | 5.801 | 0.000 | 0.000 | -2.772 |
| 346 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 212 | 142 | 0 | 0 | 0.000 | 0.000 | 3.029 | 5.801 | 0.000 | 0.000 | -2.772 |
| 347 | baseline | 10.000 | july_2025_broad_based_selling | 115 | 236 | 0 | 0 | 0 | 0 | 2.149 | -7.063 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 347 | breadth_soft_aggressive | 10.000 | july_2025_broad_based_selling | 0 | 0 | 0 | 0 | 115 | 236 | 0.000 | 0.000 | 0.000 | 0.000 | 0.215 | 0.706 | -0.491 |
| 347 | breadth_drawdown_only | 10.000 | july_2025_broad_based_selling | 0 | 0 | 0 | 0 | 115 | 236 | 0.000 | 0.000 | 0.000 | 0.000 | 0.215 | 0.706 | -0.491 |
| 348 | baseline | 10.000 | unmatched | 233 | 120 | 0 | 0 | 0 | 0 | 9.782 | -2.759 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 348 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 233 | 120 | 0.000 | 0.000 | 0.000 | 0.000 | 2.445 | 0.690 | 1.756 |
| 348 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 233 | 120 | 0.000 | 0.000 | 0.000 | 0.000 | 2.445 | 0.690 | 1.756 |
| 349 | baseline | 10.000 | unmatched | 180 | 174 | 0 | 0 | 0 | 0 | 6.295 | -5.675 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 349 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 180 | 174 | 0.000 | 0.000 | 0.000 | 0.000 | 1.574 | 1.419 | 0.155 |
| 349 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 180 | 174 | 0.000 | 0.000 | 0.000 | 0.000 | 1.574 | 1.419 | 0.155 |
| 350 | baseline | 10.000 | unmatched | 172 | 148 | 0 | 0 | 0 | 0 | 8.978 | -5.654 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 350 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 172 | 148 | 0.000 | 0.000 | 0.000 | 0.000 | 2.244 | 1.414 | 0.831 |
| 350 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 172 | 148 | 0.000 | 0.000 | 0.000 | 0.000 | 2.244 | 1.414 | 0.831 |
| 351 | baseline | 10.000 | unmatched | 148 | 191 | 0 | 0 | 0 | 0 | 7.820 | -8.973 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 351 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 148 | 191 | 0.000 | 0.000 | 0.000 | 0.000 | 1.955 | 2.243 | -0.288 |
| 351 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 148 | 191 | 0.000 | 0.000 | 0.000 | 0.000 | 1.955 | 2.243 | -0.288 |
| 352 | baseline | 10.000 | unmatched | 151 | 190 | 0 | 0 | 0 | 0 | 4.230 | -6.976 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 352 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 151 | 190 | 0.000 | 0.000 | 0.000 | 0.000 | 1.058 | 1.744 | -0.686 |
| 352 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 151 | 190 | 0.000 | 0.000 | 0.000 | 0.000 | 1.058 | 1.744 | -0.686 |

## Decision

Reject: missing target diagnostic rows.
