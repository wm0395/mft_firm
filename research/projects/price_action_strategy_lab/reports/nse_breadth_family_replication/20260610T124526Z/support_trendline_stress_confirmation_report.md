# Support Trendline Stress Confirmation

## Aggregate

| variant | cost_bps | return_pct | cagr_pct | ann_vol_pct | ann_sharpe | max_drawdown_pct | negative_fold_rate | worst_fold_sharpe | latest_fold_sharpe | average_exposure | turnover |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 10.000 | 31.304 | 14.588 | 9.082 | 1.545 | -18.771 | 0.458 | -20.120 | 8.243 | 1.000 | 0.918 |
| breadth_soft_aggressive | 10.000 | 20.992 | 9.996 | 10.099 | 0.994 | -22.731 | 0.458 | -20.120 | 8.243 | 1.042 | 0.962 |
| breadth_drawdown_only | 10.000 | 20.992 | 9.996 | 10.099 | 0.994 | -22.731 | 0.458 | -20.120 | 8.243 | 1.042 | 0.962 |
| baseline | 25.000 | 14.296 | 6.909 | 9.083 | 0.781 | -21.966 | 0.458 | -21.316 | 7.236 | 1.000 | 0.918 |
| breadth_soft_aggressive | 25.000 | 6.889 | 3.387 | 9.725 | 0.391 | -28.095 | 0.458 | -21.316 | 7.236 | 0.988 | 0.914 |
| breadth_drawdown_only | 25.000 | 6.889 | 3.387 | 9.725 | 0.391 | -28.095 | 0.458 | -21.316 | 7.236 | 0.988 | 0.914 |
| baseline | 50.000 | -9.306 | -4.766 | 9.089 | -0.492 | -33.436 | 0.583 | -23.256 | 5.553 | 1.000 | 0.918 |
| breadth_soft_aggressive | 50.000 | -8.671 | -4.434 | 9.394 | -0.436 | -34.958 | 0.583 | -23.256 | 5.553 | 0.948 | 0.877 |
| breadth_drawdown_only | 50.000 | -8.671 | -4.434 | 9.394 | -0.436 | -34.958 | 0.583 | -23.256 | 5.553 | 0.948 | 0.877 |

## Tail

| variant | cost_bps | mean_delta_vs_baseline | left_tail_delta | right_tail_retention | top_decile_retention | bottom_decile_improvement | best_fold_damage | worst_fold_improvement | ci_low | ci_high | paired_t_stat | paired_p_value | bh_p_value |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 10.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| breadth_soft_aggressive | 10.000 | -0.296 | -1.088 | 0.991 | 0.985 | -1.725 | 3.340 | -1.995 | -0.972 | 0.316 | -0.740 | 0.467 | 1.000 |
| breadth_drawdown_only | 10.000 | -0.296 | -1.088 | 0.991 | 0.985 | -1.725 | 3.340 | -1.995 | -0.972 | 0.316 | -0.740 | 0.467 | 1.000 |
| baseline | 25.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| breadth_soft_aggressive | 25.000 | -0.246 | -0.641 | 0.962 | 0.937 | -1.444 | 3.151 | -2.114 | -0.847 | 0.315 | -0.679 | 0.504 | 1.000 |
| breadth_drawdown_only | 25.000 | -0.246 | -0.641 | 0.962 | 0.937 | -1.444 | 3.151 | -2.114 | -0.847 | 0.315 | -0.679 | 0.504 | 1.000 |
| baseline | 50.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| breadth_soft_aggressive | 50.000 | 0.038 | 0.439 | 0.969 | 0.942 | 0.637 | 2.840 | -0.930 | -0.539 | 0.572 | 0.107 | 0.916 | 1.000 |
| breadth_drawdown_only | 50.000 | 0.038 | 0.439 | 0.969 | 0.942 | 0.637 | 2.840 | -0.930 | -0.539 | 0.572 | 0.107 | 0.916 | 1.000 |

## Event Split

| variant | cost_bps | split | fold_count | mean_delta | net_delta | average_exposure |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 10.000 | known_stress | 6 | 0.000 | 0.000 | 1.000 |
| baseline | 10.000 | unmatched | 18 | 0.000 | 0.000 | 1.000 |
| baseline | 10.000 | all | 24 | 0.000 | 0.000 | 1.000 |
| breadth_soft_aggressive | 10.000 | known_stress | 6 | -1.088 | -6.530 | 1.225 |
| breadth_soft_aggressive | 10.000 | unmatched | 18 | -0.032 | -0.572 | 0.981 |
| breadth_soft_aggressive | 10.000 | all | 24 | -0.296 | -7.102 | 1.042 |
| breadth_drawdown_only | 10.000 | known_stress | 6 | -1.088 | -6.530 | 1.225 |
| breadth_drawdown_only | 10.000 | unmatched | 18 | -0.032 | -0.572 | 0.981 |
| breadth_drawdown_only | 10.000 | all | 24 | -0.296 | -7.102 | 1.042 |
| baseline | 25.000 | known_stress | 6 | 0.000 | 0.000 | 1.000 |
| baseline | 25.000 | unmatched | 18 | 0.000 | 0.000 | 1.000 |
| baseline | 25.000 | all | 24 | 0.000 | 0.000 | 1.000 |
| breadth_soft_aggressive | 25.000 | known_stress | 6 | -0.641 | -3.848 | 1.058 |
| breadth_soft_aggressive | 25.000 | unmatched | 18 | -0.114 | -2.059 | 0.965 |
| breadth_soft_aggressive | 25.000 | all | 24 | -0.246 | -5.907 | 0.988 |
| breadth_drawdown_only | 25.000 | known_stress | 6 | -0.641 | -3.848 | 1.058 |
| breadth_drawdown_only | 25.000 | unmatched | 18 | -0.114 | -2.059 | 0.965 |
| breadth_drawdown_only | 25.000 | all | 24 | -0.246 | -5.907 | 0.988 |
| baseline | 50.000 | known_stress | 6 | 0.000 | 0.000 | 1.000 |
| baseline | 50.000 | unmatched | 18 | 0.000 | 0.000 | 1.000 |
| baseline | 50.000 | all | 24 | 0.000 | 0.000 | 1.000 |
| breadth_soft_aggressive | 50.000 | known_stress | 6 | 0.438 | 2.629 | 0.948 |
| breadth_soft_aggressive | 50.000 | unmatched | 18 | -0.096 | -1.724 | 0.948 |
| breadth_soft_aggressive | 50.000 | all | 24 | 0.038 | 0.905 | 0.948 |
| breadth_drawdown_only | 50.000 | known_stress | 6 | 0.438 | 2.629 | 0.948 |
| breadth_drawdown_only | 50.000 | unmatched | 18 | -0.096 | -1.724 | 0.948 |
| breadth_drawdown_only | 50.000 | all | 24 | 0.038 | 0.905 | 0.948 |

## Trade Diagnostics

| fold | variant | cost_bps | event_label | accepted_winner | accepted_loser | reduced_winner | reduced_loser | increased_winner | increased_loser | accepted_winner_pnl | accepted_loser_pnl | loss_reduced_from_reduced_losers | profit_reduced_from_reduced_winners | profit_added_from_increased_winners | loss_added_from_increased_losers | net_blocker_value |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 333 | baseline | 10.000 | unmatched | 49 | 57 | 0 | 0 | 0 | 0 | 8.729 | -4.960 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 333 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 49 | 57 | 0.000 | 0.000 | 0.000 | 0.000 | 2.182 | 1.240 | 0.942 |
| 333 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 49 | 57 | 0.000 | 0.000 | 0.000 | 0.000 | 2.182 | 1.240 | 0.942 |
| 334 | baseline | 10.000 | unmatched | 86 | 42 | 0 | 0 | 0 | 0 | 14.719 | -2.465 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 334 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 86 | 42 | 0.000 | 0.000 | 0.000 | 0.000 | 3.680 | 0.616 | 3.063 |
| 334 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 86 | 42 | 0.000 | 0.000 | 0.000 | 0.000 | 3.680 | 0.616 | 3.063 |
| 335 | baseline | 10.000 | unmatched | 57 | 81 | 0 | 0 | 0 | 0 | 8.511 | -8.361 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 335 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 57 | 81 | 0.000 | 0.000 | 0.000 | 0.000 | 2.128 | 2.090 | 0.037 |
| 335 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 57 | 81 | 0.000 | 0.000 | 0.000 | 0.000 | 2.128 | 2.090 | 0.037 |
| 336 | baseline | 10.000 | unmatched | 77 | 44 | 0 | 0 | 0 | 0 | 11.333 | -4.162 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 336 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 77 | 44 | 0.000 | 0.000 | 0.000 | 0.000 | 2.833 | 1.040 | 1.793 |
| 336 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 77 | 44 | 0.000 | 0.000 | 0.000 | 0.000 | 2.833 | 1.040 | 1.793 |
| 337 | baseline | 10.000 | unmatched | 68 | 77 | 0 | 0 | 0 | 0 | 7.015 | -6.834 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 337 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 68 | 77 | 0.000 | 0.000 | 0.000 | 0.000 | 1.754 | 1.709 | 0.045 |
| 337 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 68 | 77 | 0.000 | 0.000 | 0.000 | 0.000 | 1.754 | 1.709 | 0.045 |
| 338 | baseline | 10.000 | unmatched | 62 | 57 | 0 | 0 | 0 | 0 | 6.753 | -7.204 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 338 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 62 | 57 | 0.000 | 0.000 | 0.000 | 0.000 | 1.688 | 1.801 | -0.113 |
| 338 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 62 | 57 | 0.000 | 0.000 | 0.000 | 0.000 | 1.688 | 1.801 | -0.113 |
| 339 | baseline | 10.000 | unmatched | 81 | 58 | 0 | 0 | 0 | 0 | 7.798 | -6.127 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 339 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 81 | 58 | 0.000 | 0.000 | 0.000 | 0.000 | 1.949 | 1.532 | 0.418 |
| 339 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 81 | 58 | 0.000 | 0.000 | 0.000 | 0.000 | 1.949 | 1.532 | 0.418 |
| 340 | baseline | 10.000 | early_2025_broad_correction_fpi_outflows | 44 | 79 | 0 | 0 | 0 | 0 | 5.975 | -6.576 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 340 | breadth_soft_aggressive | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 0 | 0 | 44 | 79 | 0.000 | 0.000 | 0.000 | 0.000 | 1.494 | 1.644 | -0.150 |
| 340 | breadth_drawdown_only | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 0 | 0 | 44 | 79 | 0.000 | 0.000 | 0.000 | 0.000 | 1.494 | 1.644 | -0.150 |
| 341 | baseline | 10.000 | early_2025_broad_correction_fpi_outflows | 54 | 72 | 0 | 0 | 0 | 0 | 3.020 | -7.946 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 341 | breadth_soft_aggressive | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 0 | 0 | 54 | 72 | 0.000 | 0.000 | 0.000 | 0.000 | 0.755 | 1.987 | -1.231 |
| 341 | breadth_drawdown_only | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 0 | 0 | 54 | 72 | 0.000 | 0.000 | 0.000 | 0.000 | 0.755 | 1.987 | -1.231 |
| 342 | baseline | 10.000 | early_2025_broad_correction_fpi_outflows | 39 | 79 | 0 | 0 | 0 | 0 | 2.478 | -10.406 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 342 | breadth_soft_aggressive | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 0 | 0 | 39 | 79 | 0.000 | 0.000 | 0.000 | 0.000 | 0.619 | 2.602 | -1.982 |
| 342 | breadth_drawdown_only | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 0 | 0 | 39 | 79 | 0.000 | 0.000 | 0.000 | 0.000 | 0.619 | 2.602 | -1.982 |
| 343 | baseline | 10.000 | unmatched | 82 | 53 | 0 | 0 | 0 | 0 | 7.578 | -7.921 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 343 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 71 | 47 | 11 | 6 | 0.000 | 0.000 | 5.027 | 5.366 | 0.042 | 0.122 | -0.419 |
| 343 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 71 | 47 | 11 | 6 | 0.000 | 0.000 | 5.027 | 5.366 | 0.042 | 0.122 | -0.419 |
| 344 | baseline | 10.000 | unmatched | 87 | 51 | 0 | 0 | 0 | 0 | 8.165 | -6.123 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 344 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 81 | 51 | 6 | 0 | 0.000 | 0.000 | 4.592 | 5.818 | 0.041 | 0.000 | -1.185 |
| 344 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 81 | 51 | 6 | 0 | 0.000 | 0.000 | 4.592 | 5.818 | 0.041 | 0.000 | -1.185 |
| 345 | baseline | 10.000 | unmatched | 86 | 46 | 0 | 0 | 0 | 0 | 11.926 | -3.390 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 345 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 86 | 46 | 0 | 0 | 0.000 | 0.000 | 2.542 | 8.945 | 0.000 | 0.000 | -6.402 |
| 345 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 86 | 46 | 0 | 0 | 0.000 | 0.000 | 2.542 | 8.945 | 0.000 | 0.000 | -6.402 |
| 346 | baseline | 10.000 | unmatched | 83 | 53 | 0 | 0 | 0 | 0 | 6.331 | -4.689 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 346 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 83 | 53 | 0 | 0 | 0.000 | 0.000 | 3.517 | 4.749 | 0.000 | 0.000 | -1.232 |
| 346 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 83 | 53 | 0 | 0 | 0.000 | 0.000 | 3.517 | 4.749 | 0.000 | 0.000 | -1.232 |
| 347 | baseline | 10.000 | july_2025_broad_based_selling | 58 | 85 | 0 | 0 | 0 | 0 | 4.839 | -6.477 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 347 | breadth_soft_aggressive | 10.000 | july_2025_broad_based_selling | 0 | 0 | 0 | 0 | 58 | 85 | 0.000 | 0.000 | 0.000 | 0.000 | 0.484 | 0.648 | -0.164 |
| 347 | breadth_drawdown_only | 10.000 | july_2025_broad_based_selling | 0 | 0 | 0 | 0 | 58 | 85 | 0.000 | 0.000 | 0.000 | 0.000 | 0.484 | 0.648 | -0.164 |
| 348 | baseline | 10.000 | unmatched | 89 | 71 | 0 | 0 | 0 | 0 | 5.781 | -4.245 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 348 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 89 | 71 | 0.000 | 0.000 | 0.000 | 0.000 | 1.445 | 1.061 | 0.384 |
| 348 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 89 | 71 | 0.000 | 0.000 | 0.000 | 0.000 | 1.445 | 1.061 | 0.384 |
| 349 | baseline | 10.000 | unmatched | 97 | 59 | 0 | 0 | 0 | 0 | 9.170 | -6.648 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 349 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 97 | 59 | 0.000 | 0.000 | 0.000 | 0.000 | 2.292 | 1.662 | 0.630 |
| 349 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 97 | 59 | 0.000 | 0.000 | 0.000 | 0.000 | 2.292 | 1.662 | 0.630 |
| 350 | baseline | 10.000 | unmatched | 75 | 53 | 0 | 0 | 0 | 0 | 4.936 | -5.426 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 350 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 75 | 53 | 0.000 | 0.000 | 0.000 | 0.000 | 1.234 | 1.357 | -0.123 |
| 350 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 75 | 53 | 0.000 | 0.000 | 0.000 | 0.000 | 1.234 | 1.357 | -0.123 |
| 351 | baseline | 10.000 | unmatched | 87 | 60 | 0 | 0 | 0 | 0 | 11.423 | -4.561 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 351 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 87 | 60 | 0.000 | 0.000 | 0.000 | 0.000 | 2.856 | 1.140 | 1.716 |
| 351 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 87 | 60 | 0.000 | 0.000 | 0.000 | 0.000 | 2.856 | 1.140 | 1.716 |
| 352 | baseline | 10.000 | unmatched | 80 | 61 | 0 | 0 | 0 | 0 | 8.707 | -6.583 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 352 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 80 | 61 | 0.000 | 0.000 | 0.000 | 0.000 | 2.177 | 1.646 | 0.531 |
| 352 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 0 | 0 | 80 | 61 | 0.000 | 0.000 | 0.000 | 0.000 | 2.177 | 1.646 | 0.531 |

## Decision

Reject: missing target diagnostic rows.
