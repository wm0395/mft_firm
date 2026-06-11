# Support Trendline Stress Confirmation

## Aggregate

| variant | cost_bps | return_pct | cagr_pct | ann_vol_pct | ann_sharpe | max_drawdown_pct | negative_fold_rate | worst_fold_sharpe | latest_fold_sharpe | average_exposure | turnover |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 10.000 | 10.452 | 5.096 | 7.264 | 0.721 | -26.794 | 0.458 | -23.334 | 3.340 | 1.000 | 0.333 |
| breadth_risk_off_high | 10.000 | 20.656 | 9.843 | 7.997 | 1.214 | -26.597 | 0.500 | -20.082 | 3.340 | 0.996 | 0.334 |
| baseline | 25.000 | 5.024 | 2.481 | 7.260 | 0.374 | -28.835 | 0.542 | -23.822 | 2.693 | 1.000 | 0.333 |
| breadth_risk_off_high | 25.000 | 12.168 | 5.910 | 7.832 | 0.772 | -28.300 | 0.542 | -20.377 | 2.693 | 0.948 | 0.319 |
| baseline | 50.000 | -3.437 | -1.734 | 7.256 | -0.205 | -32.110 | 0.583 | -24.640 | 1.598 | 1.000 | 0.333 |
| breadth_risk_off_high | 50.000 | 3.854 | 1.909 | 7.669 | 0.285 | -31.435 | 0.625 | -21.277 | 1.598 | 0.942 | 0.317 |
| baseline | 75.000 | -11.218 | -5.776 | 7.253 | -0.784 | -36.000 | 0.583 | -25.461 | 0.487 | 1.000 | 0.333 |
| breadth_risk_off_high | 75.000 | -3.159 | -1.592 | 7.615 | -0.173 | -34.577 | 0.625 | -22.553 | 0.487 | 0.935 | 0.315 |

## Tail

| variant | cost_bps | mean_delta_vs_baseline | left_tail_delta | right_tail_retention | top_decile_retention | bottom_decile_improvement | best_fold_damage | worst_fold_improvement | ci_low | ci_high | paired_t_stat | paired_p_value | bh_p_value |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 10.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| breadth_risk_off_high | 10.000 | 0.387 | 0.682 | 1.117 | 1.211 | 0.885 | 1.137 | 4.513 | -0.249 | 0.997 | 0.977 | 0.339 | 0.934 |
| baseline | 25.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| breadth_risk_off_high | 25.000 | 0.284 | 0.685 | 1.084 | 1.158 | 0.874 | 1.112 | 4.551 | -0.351 | 0.884 | 0.740 | 0.467 | 0.934 |
| baseline | 50.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| breadth_risk_off_high | 50.000 | 0.311 | 0.692 | 1.087 | 1.158 | 0.856 | 1.070 | 4.615 | -0.310 | 0.917 | 0.816 | 0.423 | 0.934 |
| baseline | 75.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| breadth_risk_off_high | 75.000 | 0.365 | 0.853 | 1.089 | 1.157 | 1.148 | 1.029 | 4.677 | -0.238 | 0.957 | 0.973 | 0.341 | 0.934 |

## Event Split

| variant | cost_bps | split | fold_count | mean_delta | net_delta | average_exposure |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 10.000 | known_stress | 6 | 0.000 | 0.000 | 1.000 |
| baseline | 10.000 | unmatched | 18 | 0.000 | 0.000 | 1.000 |
| baseline | 10.000 | all | 24 | 0.000 | 0.000 | 1.000 |
| breadth_risk_off_high | 10.000 | known_stress | 6 | 0.878 | 5.267 | 0.998 |
| breadth_risk_off_high | 10.000 | unmatched | 18 | 0.223 | 4.014 | 0.995 |
| breadth_risk_off_high | 10.000 | all | 24 | 0.387 | 9.281 | 0.996 |
| baseline | 25.000 | known_stress | 6 | 0.000 | 0.000 | 1.000 |
| baseline | 25.000 | unmatched | 18 | 0.000 | 0.000 | 1.000 |
| baseline | 25.000 | all | 24 | 0.000 | 0.000 | 1.000 |
| breadth_risk_off_high | 25.000 | known_stress | 6 | 0.877 | 5.262 | 0.998 |
| breadth_risk_off_high | 25.000 | unmatched | 18 | 0.086 | 1.542 | 0.931 |
| breadth_risk_off_high | 25.000 | all | 24 | 0.284 | 6.804 | 0.948 |
| baseline | 50.000 | known_stress | 6 | 0.000 | 0.000 | 1.000 |
| baseline | 50.000 | unmatched | 18 | 0.000 | 0.000 | 1.000 |
| baseline | 50.000 | all | 24 | 0.000 | 0.000 | 1.000 |
| breadth_risk_off_high | 50.000 | known_stress | 6 | 0.932 | 5.591 | 0.973 |
| breadth_risk_off_high | 50.000 | unmatched | 18 | 0.104 | 1.868 | 0.931 |
| breadth_risk_off_high | 50.000 | all | 24 | 0.311 | 7.459 | 0.942 |
| baseline | 75.000 | known_stress | 6 | 0.000 | 0.000 | 1.000 |
| baseline | 75.000 | unmatched | 18 | 0.000 | 0.000 | 1.000 |
| baseline | 75.000 | all | 24 | 0.000 | 0.000 | 1.000 |
| breadth_risk_off_high | 75.000 | known_stress | 6 | 1.094 | 6.562 | 0.948 |
| breadth_risk_off_high | 75.000 | unmatched | 18 | 0.122 | 2.196 | 0.931 |
| breadth_risk_off_high | 75.000 | all | 24 | 0.365 | 8.758 | 0.935 |

## Trade Diagnostics

| fold | variant | cost_bps | event_label | accepted_winner | accepted_loser | reduced_winner | reduced_loser | increased_winner | increased_loser | accepted_winner_pnl | accepted_loser_pnl | loss_reduced_from_reduced_losers | profit_reduced_from_reduced_winners | profit_added_from_increased_winners | loss_added_from_increased_losers | net_blocker_value |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 333 | baseline | 10.000 | unmatched | 169 | 137 | 0 | 0 | 0 | 0 | 10.535 | -6.500 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 333 | breadth_risk_off_high | 10.000 | unmatched | 0 | 0 | 0 | 0 | 169 | 137 | 0.000 | 0.000 | 0.000 | 0.000 | 2.634 | 1.625 | 1.009 |
| 334 | baseline | 10.000 | unmatched | 192 | 131 | 0 | 0 | 0 | 0 | 15.982 | -5.639 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 334 | breadth_risk_off_high | 10.000 | unmatched | 0 | 0 | 0 | 0 | 192 | 131 | 0.000 | 0.000 | 0.000 | 0.000 | 3.996 | 1.410 | 2.586 |
| 335 | baseline | 10.000 | unmatched | 156 | 170 | 0 | 0 | 0 | 0 | 12.124 | -8.248 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 335 | breadth_risk_off_high | 10.000 | unmatched | 0 | 0 | 0 | 0 | 156 | 170 | 0.000 | 0.000 | 0.000 | 0.000 | 3.031 | 2.062 | 0.969 |
| 336 | baseline | 10.000 | unmatched | 197 | 122 | 0 | 0 | 0 | 0 | 12.619 | -4.498 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 336 | breadth_risk_off_high | 10.000 | unmatched | 0 | 0 | 0 | 0 | 197 | 122 | 0.000 | 0.000 | 0.000 | 0.000 | 3.155 | 1.124 | 2.030 |
| 337 | baseline | 10.000 | unmatched | 116 | 196 | 0 | 0 | 0 | 0 | 7.246 | -9.428 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 337 | breadth_risk_off_high | 10.000 | unmatched | 0 | 0 | 0 | 0 | 116 | 196 | 0.000 | 0.000 | 0.000 | 0.000 | 1.812 | 2.357 | -0.545 |
| 338 | baseline | 10.000 | unmatched | 110 | 213 | 0 | 0 | 0 | 0 | 7.641 | -12.050 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 338 | breadth_risk_off_high | 10.000 | unmatched | 0 | 0 | 0 | 0 | 110 | 213 | 0.000 | 0.000 | 0.000 | 0.000 | 1.910 | 3.012 | -1.102 |
| 339 | baseline | 10.000 | unmatched | 153 | 152 | 0 | 0 | 0 | 0 | 6.807 | -7.401 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 339 | breadth_risk_off_high | 10.000 | unmatched | 0 | 0 | 0 | 0 | 153 | 152 | 0.000 | 0.000 | 0.000 | 0.000 | 1.702 | 1.850 | -0.149 |
| 340 | baseline | 10.000 | early_2025_broad_correction_fpi_outflows | 142 | 186 | 0 | 0 | 0 | 0 | 8.298 | -8.160 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 340 | breadth_risk_off_high | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 0 | 0 | 142 | 186 | 0.000 | 0.000 | 0.000 | 0.000 | 2.074 | 2.040 | 0.034 |
| 341 | baseline | 10.000 | early_2025_broad_correction_fpi_outflows | 140 | 183 | 0 | 0 | 0 | 0 | 2.766 | -7.828 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 341 | breadth_risk_off_high | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 0 | 0 | 140 | 183 | 0.000 | 0.000 | 0.000 | 0.000 | 0.691 | 1.957 | -1.266 |
| 342 | baseline | 10.000 | early_2025_broad_correction_fpi_outflows | 85 | 246 | 0 | 0 | 0 | 0 | 2.011 | -14.453 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 342 | breadth_risk_off_high | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 26 | 113 | 59 | 133 | 0.000 | 0.000 | 5.867 | 0.421 | 0.145 | 0.663 | 4.928 |
| 343 | baseline | 10.000 | unmatched | 181 | 150 | 0 | 0 | 0 | 0 | 7.431 | -6.102 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 343 | breadth_risk_off_high | 10.000 | unmatched | 0 | 0 | 159 | 122 | 22 | 28 | 0.000 | 0.000 | 3.756 | 4.904 | 0.089 | 0.109 | -1.168 |
| 344 | baseline | 10.000 | unmatched | 196 | 148 | 0 | 0 | 0 | 0 | 9.058 | -5.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 344 | breadth_risk_off_high | 10.000 | unmatched | 0 | 0 | 181 | 146 | 15 | 2 | 0.000 | 0.000 | 4.013 | 5.922 | 0.116 | 0.007 | -1.800 |
| 345 | baseline | 10.000 | unmatched | 204 | 134 | 0 | 0 | 0 | 0 | 10.159 | -4.676 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 345 | breadth_risk_off_high | 10.000 | unmatched | 0 | 0 | 204 | 134 | 0 | 0 | 0.000 | 0.000 | 3.507 | 7.619 | 0.000 | 0.000 | -4.112 |
| 346 | baseline | 10.000 | unmatched | 152 | 199 | 0 | 0 | 0 | 0 | 4.198 | -7.070 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 346 | breadth_risk_off_high | 10.000 | unmatched | 0 | 0 | 152 | 199 | 0 | 0 | 0.000 | 0.000 | 5.302 | 3.149 | 0.000 | 0.000 | 2.154 |
| 347 | baseline | 10.000 | july_2025_broad_based_selling | 113 | 234 | 0 | 0 | 0 | 0 | 4.252 | -9.281 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 347 | breadth_risk_off_high | 10.000 | july_2025_broad_based_selling | 0 | 0 | 113 | 234 | 0 | 0 | 0.000 | 0.000 | 6.961 | 3.189 | 0.000 | 0.000 | 3.771 |
| 348 | baseline | 10.000 | unmatched | 166 | 179 | 0 | 0 | 0 | 0 | 5.364 | -5.166 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 348 | breadth_risk_off_high | 10.000 | unmatched | 0 | 0 | 0 | 0 | 166 | 179 | 0.000 | 0.000 | 0.000 | 0.000 | 0.536 | 0.517 | 0.020 |
| 349 | baseline | 10.000 | unmatched | 159 | 187 | 0 | 0 | 0 | 0 | 8.288 | -9.220 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 349 | breadth_risk_off_high | 10.000 | unmatched | 0 | 0 | 0 | 0 | 159 | 187 | 0.000 | 0.000 | 0.000 | 0.000 | 0.829 | 0.922 | -0.093 |
| 350 | baseline | 10.000 | unmatched | 133 | 186 | 0 | 0 | 0 | 0 | 3.625 | -8.874 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 350 | breadth_risk_off_high | 10.000 | unmatched | 0 | 0 | 0 | 0 | 133 | 186 | 0.000 | 0.000 | 0.000 | 0.000 | 0.362 | 0.887 | -0.525 |
| 351 | baseline | 10.000 | unmatched | 200 | 121 | 0 | 0 | 0 | 0 | 15.557 | -5.130 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 351 | breadth_risk_off_high | 10.000 | unmatched | 0 | 0 | 0 | 0 | 200 | 121 | 0.000 | 0.000 | 0.000 | 0.000 | 1.556 | 0.513 | 1.043 |
| 352 | baseline | 10.000 | unmatched | 170 | 175 | 0 | 0 | 0 | 0 | 7.357 | -6.821 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 352 | breadth_risk_off_high | 10.000 | unmatched | 0 | 0 | 0 | 0 | 170 | 175 | 0.000 | 0.000 | 0.000 | 0.000 | 0.736 | 0.682 | 0.054 |
| 353 | baseline | 10.000 | feb_2026_it_global_tech_selloff | 109 | 126 | 0 | 0 | 0 | 0 | 7.626 | -9.084 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 353 | breadth_risk_off_high | 10.000 | feb_2026_it_global_tech_selloff | 0 | 0 | 0 | 0 | 109 | 126 | 0.000 | 0.000 | 0.000 | 0.000 | 1.907 | 2.271 | -0.364 |
| 354 | baseline | 10.000 | feb_2026_it_global_tech_selloff | 118 | 201 | 0 | 0 | 0 | 0 | 4.434 | -9.982 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 354 | breadth_risk_off_high | 10.000 | feb_2026_it_global_tech_selloff | 0 | 0 | 0 | 0 | 118 | 201 | 0.000 | 0.000 | 0.000 | 0.000 | 1.108 | 2.495 | -1.387 |
| 355 | baseline | 10.000 | unmatched | 228 | 114 | 0 | 0 | 0 | 0 | 15.500 | -5.102 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 355 | breadth_risk_off_high | 10.000 | unmatched | 0 | 0 | 0 | 0 | 228 | 114 | 0.000 | 0.000 | 0.000 | 0.000 | 3.875 | 1.276 | 2.600 |
| 356 | baseline | 10.000 | unmatched | 123 | 161 | 0 | 0 | 0 | 0 | 7.650 | -6.569 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 356 | breadth_risk_off_high | 10.000 | unmatched | 0 | 0 | 0 | 0 | 123 | 161 | 0.000 | 0.000 | 0.000 | 0.000 | 1.912 | 1.642 | 0.270 |
| 333 | baseline | 25.000 | unmatched | 169 | 137 | 0 | 0 | 0 | 0 | 10.535 | -6.500 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 333 | breadth_risk_off_high | 25.000 | unmatched | 0 | 0 | 0 | 0 | 169 | 137 | 0.000 | 0.000 | 0.000 | 0.000 | 2.634 | 1.625 | 1.009 |
| 334 | baseline | 25.000 | unmatched | 192 | 131 | 0 | 0 | 0 | 0 | 15.982 | -5.639 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 334 | breadth_risk_off_high | 25.000 | unmatched | 0 | 0 | 0 | 0 | 192 | 131 | 0.000 | 0.000 | 0.000 | 0.000 | 3.996 | 1.410 | 2.586 |
| 335 | baseline | 25.000 | unmatched | 156 | 170 | 0 | 0 | 0 | 0 | 12.124 | -8.248 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 335 | breadth_risk_off_high | 25.000 | unmatched | 0 | 0 | 0 | 0 | 156 | 170 | 0.000 | 0.000 | 0.000 | 0.000 | 3.031 | 2.062 | 0.969 |
| 336 | baseline | 25.000 | unmatched | 197 | 122 | 0 | 0 | 0 | 0 | 12.619 | -4.498 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 336 | breadth_risk_off_high | 25.000 | unmatched | 0 | 0 | 0 | 0 | 197 | 122 | 0.000 | 0.000 | 0.000 | 0.000 | 3.155 | 1.124 | 2.030 |
| 337 | baseline | 25.000 | unmatched | 116 | 196 | 0 | 0 | 0 | 0 | 7.246 | -9.428 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 337 | breadth_risk_off_high | 25.000 | unmatched | 0 | 0 | 0 | 0 | 116 | 196 | 0.000 | 0.000 | 0.000 | 0.000 | 1.812 | 2.357 | -0.545 |
| 338 | baseline | 25.000 | unmatched | 110 | 213 | 0 | 0 | 0 | 0 | 7.641 | -12.050 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 338 | breadth_risk_off_high | 25.000 | unmatched | 0 | 0 | 0 | 0 | 110 | 213 | 0.000 | 0.000 | 0.000 | 0.000 | 1.910 | 3.012 | -1.102 |

## Decision

Reject: missing target diagnostic rows.
