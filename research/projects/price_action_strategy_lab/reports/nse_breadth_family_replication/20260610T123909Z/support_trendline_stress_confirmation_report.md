# Support Trendline Stress Confirmation

## Aggregate

| variant | cost_bps | return_pct | cagr_pct | ann_vol_pct | ann_sharpe | max_drawdown_pct | negative_fold_rate | worst_fold_sharpe | latest_fold_sharpe | average_exposure | turnover |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 10.000 | 44.029 | 20.012 | 11.329 | 1.667 | -17.755 | 0.417 | -13.139 | -2.718 | 1.000 | 0.641 |
| breadth_soft_aggressive | 10.000 | 38.985 | 17.892 | 12.866 | 1.344 | -17.233 | 0.417 | -13.139 | -2.718 | 1.103 | 0.723 |
| breadth_drawdown_only | 10.000 | 38.985 | 17.892 | 12.866 | 1.344 | -17.233 | 0.417 | -13.139 | -2.718 | 1.103 | 0.723 |
| baseline | 25.000 | 30.741 | 14.342 | 11.327 | 1.240 | -18.946 | 0.458 | -14.323 | -3.220 | 1.000 | 0.641 |
| breadth_soft_aggressive | 25.000 | 19.814 | 9.459 | 12.700 | 0.775 | -19.562 | 0.458 | -14.323 | -3.220 | 1.032 | 0.690 |
| breadth_drawdown_only | 25.000 | 19.814 | 9.459 | 12.700 | 0.775 | -19.562 | 0.458 | -14.323 | -3.220 | 1.032 | 0.690 |
| baseline | 50.000 | 11.256 | 5.478 | 11.330 | 0.527 | -20.908 | 0.500 | -16.275 | -4.027 | 1.000 | 0.641 |
| breadth_soft_aggressive | 50.000 | -0.781 | -0.391 | 12.550 | 0.031 | -23.178 | 0.500 | -16.275 | -4.027 | 1.013 | 0.678 |
| breadth_drawdown_only | 50.000 | -0.781 | -0.391 | 12.550 | 0.031 | -23.178 | 0.500 | -16.275 | -4.027 | 1.013 | 0.678 |

## Tail

| variant | cost_bps | mean_delta_vs_baseline | left_tail_delta | right_tail_retention | top_decile_retention | bottom_decile_improvement | best_fold_damage | worst_fold_improvement | ci_low | ci_high | paired_t_stat | paired_p_value | bh_p_value |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 10.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| breadth_soft_aggressive | 10.000 | -0.112 | -0.698 | 0.979 | 1.262 | -0.323 | 2.762 | 2.024 | -0.899 | 0.569 | -0.246 | 0.808 | 1.000 |
| breadth_drawdown_only | 10.000 | -0.112 | -0.698 | 0.979 | 1.262 | -0.323 | 2.762 | 2.024 | -0.899 | 0.569 | -0.246 | 0.808 | 1.000 |
| baseline | 25.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| breadth_soft_aggressive | 25.000 | -0.335 | -0.771 | 0.979 | 1.262 | -0.365 | 2.630 | 2.092 | -1.113 | 0.380 | -0.710 | 0.485 | 1.000 |
| breadth_drawdown_only | 25.000 | -0.335 | -0.771 | 0.979 | 1.262 | -0.365 | 2.630 | 2.092 | -1.113 | 0.380 | -0.710 | 0.485 | 1.000 |
| baseline | 50.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| breadth_soft_aggressive | 50.000 | -0.461 | -0.732 | 0.923 | 1.158 | -0.111 | 2.414 | 2.203 | -1.138 | 0.170 | -1.113 | 0.277 | 1.000 |
| breadth_drawdown_only | 50.000 | -0.461 | -0.732 | 0.923 | 1.158 | -0.111 | 2.414 | 2.203 | -1.138 | 0.170 | -1.113 | 0.277 | 1.000 |

## Event Split

| variant | cost_bps | split | fold_count | mean_delta | net_delta | average_exposure |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 10.000 | known_stress | 6 | 0.000 | 0.000 | 1.000 |
| baseline | 10.000 | unmatched | 18 | 0.000 | 0.000 | 1.000 |
| baseline | 10.000 | all | 24 | 0.000 | 0.000 | 1.000 |
| breadth_soft_aggressive | 10.000 | known_stress | 6 | -0.423 | -2.536 | 1.179 |
| breadth_soft_aggressive | 10.000 | unmatched | 18 | -0.009 | -0.159 | 1.077 |
| breadth_soft_aggressive | 10.000 | all | 24 | -0.112 | -2.695 | 1.103 |
| breadth_drawdown_only | 10.000 | known_stress | 6 | -0.423 | -2.536 | 1.179 |
| breadth_drawdown_only | 10.000 | unmatched | 18 | -0.009 | -0.159 | 1.077 |
| breadth_drawdown_only | 10.000 | all | 24 | -0.112 | -2.695 | 1.103 |
| baseline | 25.000 | known_stress | 6 | 0.000 | 0.000 | 1.000 |
| baseline | 25.000 | unmatched | 18 | 0.000 | 0.000 | 1.000 |
| baseline | 25.000 | all | 24 | 0.000 | 0.000 | 1.000 |
| breadth_soft_aggressive | 25.000 | known_stress | 6 | -0.495 | -2.971 | 1.179 |
| breadth_soft_aggressive | 25.000 | unmatched | 18 | -0.282 | -5.077 | 0.983 |
| breadth_soft_aggressive | 25.000 | all | 24 | -0.335 | -8.048 | 1.032 |
| breadth_drawdown_only | 25.000 | known_stress | 6 | -0.495 | -2.971 | 1.179 |
| breadth_drawdown_only | 25.000 | unmatched | 18 | -0.282 | -5.077 | 0.983 |
| breadth_drawdown_only | 25.000 | all | 24 | -0.335 | -8.048 | 1.032 |
| baseline | 50.000 | known_stress | 6 | 0.000 | 0.000 | 1.000 |
| baseline | 50.000 | unmatched | 18 | 0.000 | 0.000 | 1.000 |
| baseline | 50.000 | all | 24 | 0.000 | 0.000 | 1.000 |
| breadth_soft_aggressive | 50.000 | known_stress | 6 | -0.453 | -2.721 | 1.154 |
| breadth_soft_aggressive | 50.000 | unmatched | 18 | -0.464 | -8.344 | 0.966 |
| breadth_soft_aggressive | 50.000 | all | 24 | -0.461 | -11.065 | 1.013 |
| breadth_drawdown_only | 50.000 | known_stress | 6 | -0.453 | -2.721 | 1.154 |
| breadth_drawdown_only | 50.000 | unmatched | 18 | -0.464 | -8.344 | 0.966 |
| breadth_drawdown_only | 50.000 | all | 24 | -0.461 | -11.065 | 1.013 |

## Trade Diagnostics

| fold | variant | cost_bps | event_label | accepted_winner | accepted_loser | reduced_winner | reduced_loser | increased_winner | increased_loser | accepted_winner_pnl | accepted_loser_pnl | loss_reduced_from_reduced_losers | profit_reduced_from_reduced_winners | profit_added_from_increased_winners | loss_added_from_increased_losers | net_blocker_value |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 333 | baseline | 10.000 | unmatched | 38 | 27 | 0 | 0 | 0 | 0 | 4.916 | -8.715 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 333 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 38 | 27 | 0.000 | 0.000 | 0.000 | 0.000 | 1.229 | 2.179 | -0.950 |
| 333 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 38 | 27 | 0.000 | 0.000 | 0.000 | 0.000 | 1.229 | 2.179 | -0.950 |
| 334 | baseline | 10.000 | unmatched | 42 | 6 | 0 | 0 | 0 | 0 | 7.059 | -4.415 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 334 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 42 | 6 | 0.000 | 0.000 | 0.000 | 0.000 | 1.765 | 1.104 | 0.661 |
| 334 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 42 | 6 | 0.000 | 0.000 | 0.000 | 0.000 | 1.765 | 1.104 | 0.661 |
| 335 | baseline | 10.000 | unmatched | 37 | 44 | 0 | 0 | 0 | 0 | 10.356 | -5.594 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 335 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 37 | 44 | 0.000 | 0.000 | 0.000 | 0.000 | 2.589 | 1.398 | 1.191 |
| 335 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 37 | 44 | 0.000 | 0.000 | 0.000 | 0.000 | 2.589 | 1.398 | 1.191 |
| 336 | baseline | 10.000 | unmatched | 35 | 4 | 0 | 0 | 0 | 0 | 10.210 | -0.823 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 336 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 35 | 4 | 0.000 | 0.000 | 0.000 | 0.000 | 2.553 | 0.206 | 2.347 |
| 336 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 35 | 4 | 0.000 | 0.000 | 0.000 | 0.000 | 2.553 | 0.206 | 2.347 |
| 337 | baseline | 10.000 | unmatched | 32 | 28 | 0 | 0 | 0 | 0 | 5.738 | -5.908 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 337 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 32 | 28 | 0.000 | 0.000 | 0.000 | 0.000 | 1.434 | 1.477 | -0.043 |
| 337 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 32 | 28 | 0.000 | 0.000 | 0.000 | 0.000 | 1.434 | 1.477 | -0.043 |
| 338 | baseline | 10.000 | unmatched | 63 | 63 | 0 | 0 | 0 | 0 | 6.328 | -9.563 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 338 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 63 | 63 | 0.000 | 0.000 | 0.000 | 0.000 | 1.582 | 2.391 | -0.809 |
| 338 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 63 | 63 | 0.000 | 0.000 | 0.000 | 0.000 | 1.582 | 2.391 | -0.809 |
| 339 | baseline | 10.000 | unmatched | 47 | 7 | 0 | 0 | 0 | 0 | 10.433 | -0.530 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 339 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 47 | 7 | 0.000 | 0.000 | 0.000 | 0.000 | 2.608 | 0.132 | 2.476 |
| 339 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 47 | 7 | 0.000 | 0.000 | 0.000 | 0.000 | 2.608 | 0.132 | 2.476 |
| 340 | baseline | 10.000 | early_2025_broad_correction_fpi_outflows | 18 | 46 | 0 | 0 | 0 | 0 | 4.653 | -5.898 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 340 | breadth_soft_aggressive | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 0 | 0 | 18 | 46 | 0.000 | 0.000 | 0.000 | 0.000 | 1.163 | 1.474 | -0.311 |
| 340 | breadth_drawdown_only | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 0 | 0 | 18 | 46 | 0.000 | 0.000 | 0.000 | 0.000 | 1.163 | 1.474 | -0.311 |
| 341 | baseline | 10.000 | early_2025_broad_correction_fpi_outflows | 46 | 73 | 0 | 0 | 0 | 0 | 5.208 | -10.350 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 341 | breadth_soft_aggressive | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 0 | 0 | 46 | 73 | 0.000 | 0.000 | 0.000 | 0.000 | 1.302 | 2.588 | -1.286 |
| 341 | breadth_drawdown_only | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 0 | 0 | 46 | 73 | 0.000 | 0.000 | 0.000 | 0.000 | 1.302 | 2.588 | -1.286 |
| 342 | baseline | 10.000 | early_2025_broad_correction_fpi_outflows | 28 | 115 | 0 | 0 | 0 | 0 | 4.063 | -13.633 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 342 | breadth_soft_aggressive | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 4 | 32 | 24 | 83 | 0.000 | 0.000 | 5.272 | 1.881 | 0.389 | 1.651 | 2.129 |
| 342 | breadth_drawdown_only | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 4 | 32 | 24 | 83 | 0.000 | 0.000 | 5.272 | 1.881 | 0.389 | 1.651 | 2.129 |
| 343 | baseline | 10.000 | unmatched | 27 | 31 | 0 | 0 | 0 | 0 | 6.066 | -4.395 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 343 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 22 | 28 | 5 | 3 | 0.000 | 0.000 | 2.977 | 4.096 | 0.151 | 0.107 | -1.074 |
| 343 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 22 | 28 | 5 | 3 | 0.000 | 0.000 | 2.977 | 4.096 | 0.151 | 0.107 | -1.074 |
| 344 | baseline | 10.000 | unmatched | 30 | 12 | 0 | 0 | 0 | 0 | 11.487 | -4.072 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 344 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 18 | 12 | 12 | 0 | 0.000 | 0.000 | 3.054 | 7.866 | 0.250 | 0.000 | -4.563 |
| 344 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 18 | 12 | 12 | 0 | 0.000 | 0.000 | 3.054 | 7.866 | 0.250 | 0.000 | -4.563 |
| 345 | baseline | 10.000 | unmatched | 27 | 5 | 0 | 0 | 0 | 0 | 9.782 | -0.586 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 345 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 27 | 5 | 0 | 0 | 0.000 | 0.000 | 0.439 | 7.337 | 0.000 | 0.000 | -6.898 |
| 345 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 27 | 5 | 0 | 0 | 0.000 | 0.000 | 0.439 | 7.337 | 0.000 | 0.000 | -6.898 |
| 346 | baseline | 10.000 | unmatched | 41 | 19 | 0 | 0 | 0 | 0 | 8.476 | -2.267 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 346 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 41 | 19 | 0.000 | 0.000 | 0.000 | 0.000 | 0.848 | 0.227 | 0.621 |
| 346 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 41 | 19 | 0.000 | 0.000 | 0.000 | 0.000 | 0.848 | 0.227 | 0.621 |
| 347 | baseline | 10.000 | july_2025_broad_based_selling | 30 | 77 | 0 | 0 | 0 | 0 | 2.644 | -7.887 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 347 | breadth_soft_aggressive | 10.000 | july_2025_broad_based_selling | 0 | 0 | 0 | 0 | 30 | 77 | 0.000 | 0.000 | 0.000 | 0.000 | 0.661 | 1.972 | -1.311 |
| 347 | breadth_drawdown_only | 10.000 | july_2025_broad_based_selling | 0 | 0 | 0 | 0 | 30 | 77 | 0.000 | 0.000 | 0.000 | 0.000 | 0.661 | 1.972 | -1.311 |
| 348 | baseline | 10.000 | unmatched | 67 | 42 | 0 | 0 | 0 | 0 | 7.033 | -2.609 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 348 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 67 | 42 | 0.000 | 0.000 | 0.000 | 0.000 | 1.758 | 0.652 | 1.106 |
| 348 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 67 | 42 | 0.000 | 0.000 | 0.000 | 0.000 | 1.758 | 0.652 | 1.106 |
| 349 | baseline | 10.000 | unmatched | 42 | 27 | 0 | 0 | 0 | 0 | 13.310 | -2.922 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 349 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 42 | 27 | 0.000 | 0.000 | 0.000 | 0.000 | 3.327 | 0.731 | 2.597 |
| 349 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 42 | 27 | 0.000 | 0.000 | 0.000 | 0.000 | 3.327 | 0.731 | 2.597 |
| 350 | baseline | 10.000 | unmatched | 36 | 21 | 0 | 0 | 0 | 0 | 9.872 | -5.458 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 350 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 36 | 21 | 0.000 | 0.000 | 0.000 | 0.000 | 2.468 | 1.365 | 1.104 |
| 350 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 36 | 21 | 0.000 | 0.000 | 0.000 | 0.000 | 2.468 | 1.365 | 1.104 |
| 351 | baseline | 10.000 | unmatched | 28 | 29 | 0 | 0 | 0 | 0 | 8.247 | -9.463 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 351 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 28 | 29 | 0.000 | 0.000 | 0.000 | 0.000 | 2.062 | 2.366 | -0.304 |
| 351 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 28 | 29 | 0.000 | 0.000 | 0.000 | 0.000 | 2.062 | 2.366 | -0.304 |
| 352 | baseline | 10.000 | unmatched | 35 | 18 | 0 | 0 | 0 | 0 | 3.589 | -3.259 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 352 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 35 | 18 | 0.000 | 0.000 | 0.000 | 0.000 | 0.897 | 0.815 | 0.083 |
| 352 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 35 | 18 | 0.000 | 0.000 | 0.000 | 0.000 | 0.897 | 0.815 | 0.083 |

## Decision

Reject: missing target diagnostic rows.
