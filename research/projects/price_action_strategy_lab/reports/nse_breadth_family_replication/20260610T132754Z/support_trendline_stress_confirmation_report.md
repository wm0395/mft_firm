# Support Trendline Stress Confirmation

## Aggregate

| variant | cost_bps | return_pct | cagr_pct | ann_vol_pct | ann_sharpe | max_drawdown_pct | negative_fold_rate | worst_fold_sharpe | latest_fold_sharpe | average_exposure | turnover |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 10.000 | -16.318 | -8.522 | 9.792 | -0.861 | -37.798 | 0.625 | -26.471 | -6.415 | 1.000 | 0.687 |
| breadth_soft_aggressive | 10.000 | -16.840 | -8.808 | 10.094 | -0.863 | -41.738 | 0.583 | -26.471 | -6.415 | 0.935 | 0.658 |
| breadth_drawdown_only | 10.000 | -13.165 | -6.815 | 8.730 | -0.765 | -36.776 | 0.583 | -26.471 | -6.415 | 0.805 | 0.566 |
| baseline | 25.000 | -24.581 | -13.156 | 9.797 | -1.391 | -42.568 | 0.625 | -27.471 | -7.332 | 1.000 | 0.687 |
| breadth_soft_aggressive | 25.000 | -24.165 | -12.917 | 10.008 | -1.332 | -45.519 | 0.583 | -27.471 | -7.332 | 0.923 | 0.649 |
| breadth_drawdown_only | 25.000 | -20.287 | -10.718 | 8.734 | -1.254 | -40.721 | 0.583 | -27.471 | -7.332 | 0.805 | 0.566 |
| baseline | 50.000 | -36.584 | -20.366 | 9.809 | -2.272 | -49.721 | 0.667 | -29.058 | -8.836 | 1.000 | 0.687 |
| breadth_soft_aggressive | 50.000 | -34.606 | -19.134 | 9.964 | -2.081 | -51.011 | 0.667 | -29.058 | -8.836 | 0.917 | 0.645 |
| breadth_drawdown_only | 50.000 | -30.886 | -16.865 | 8.748 | -2.067 | -46.759 | 0.667 | -29.058 | -8.836 | 0.805 | 0.566 |

## Tail

| variant | cost_bps | mean_delta_vs_baseline | left_tail_delta | right_tail_retention | top_decile_retention | bottom_decile_improvement | best_fold_damage | worst_fold_improvement | ci_low | ci_high | paired_t_stat | paired_p_value | bh_p_value |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 10.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| breadth_soft_aggressive | 10.000 | -0.021 | 0.870 | 0.948 | 1.150 | 0.509 | 1.519 | 4.493 | -0.797 | 0.768 | -0.044 | 0.965 | 1.000 |
| breadth_drawdown_only | 10.000 | 0.101 | 1.826 | 0.836 | 1.000 | 1.656 | 0.000 | 4.969 | -0.627 | 0.826 | 0.224 | 0.825 | 1.000 |
| baseline | 25.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| breadth_soft_aggressive | 25.000 | 0.027 | 0.881 | 0.952 | 1.149 | 0.490 | 1.465 | 4.557 | -0.739 | 0.813 | 0.055 | 0.956 | 1.000 |
| breadth_drawdown_only | 25.000 | 0.177 | 1.884 | 0.840 | 1.000 | 1.686 | 0.000 | 5.058 | -0.548 | 0.895 | 0.395 | 0.696 | 1.000 |
| baseline | 50.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| breadth_soft_aggressive | 50.000 | 0.126 | 1.129 | 0.960 | 1.148 | 0.918 | 1.377 | 4.663 | -0.615 | 0.915 | 0.265 | 0.793 | 1.000 |
| breadth_drawdown_only | 50.000 | 0.303 | 1.980 | 0.847 | 1.000 | 1.735 | 0.000 | 5.204 | -0.414 | 1.008 | 0.679 | 0.504 | 1.000 |

## Event Split

| variant | cost_bps | split | fold_count | mean_delta | net_delta | average_exposure |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 10.000 | known_stress | 6 | 0.000 | 0.000 | 1.000 |
| baseline | 10.000 | unmatched | 18 | 0.000 | 0.000 | 1.000 |
| baseline | 10.000 | all | 24 | 0.000 | 0.000 | 1.000 |
| breadth_soft_aggressive | 10.000 | known_stress | 6 | 1.305 | 7.830 | 0.923 |
| breadth_soft_aggressive | 10.000 | unmatched | 18 | -0.463 | -8.342 | 0.940 |
| breadth_soft_aggressive | 10.000 | all | 24 | -0.021 | -0.512 | 0.935 |
| breadth_drawdown_only | 10.000 | known_stress | 6 | 1.826 | 10.955 | 0.821 |
| breadth_drawdown_only | 10.000 | unmatched | 18 | -0.474 | -8.534 | 0.800 |
| breadth_drawdown_only | 10.000 | all | 24 | 0.101 | 2.421 | 0.805 |
| baseline | 25.000 | known_stress | 6 | 0.000 | 0.000 | 1.000 |
| baseline | 25.000 | unmatched | 18 | 0.000 | 0.000 | 1.000 |
| baseline | 25.000 | all | 24 | 0.000 | 0.000 | 1.000 |
| breadth_soft_aggressive | 25.000 | known_stress | 6 | 1.446 | 8.676 | 0.898 |
| breadth_soft_aggressive | 25.000 | unmatched | 18 | -0.446 | -8.035 | 0.931 |
| breadth_soft_aggressive | 25.000 | all | 24 | 0.027 | 0.641 | 0.923 |
| breadth_drawdown_only | 25.000 | known_stress | 6 | 1.884 | 11.304 | 0.821 |
| breadth_drawdown_only | 25.000 | unmatched | 18 | -0.392 | -7.061 | 0.800 |
| breadth_drawdown_only | 25.000 | all | 24 | 0.177 | 4.243 | 0.805 |
| baseline | 50.000 | known_stress | 6 | 0.000 | 0.000 | 1.000 |
| baseline | 50.000 | unmatched | 18 | 0.000 | 0.000 | 1.000 |
| baseline | 50.000 | all | 24 | 0.000 | 0.000 | 1.000 |
| breadth_soft_aggressive | 50.000 | known_stress | 6 | 1.491 | 8.948 | 0.898 |
| breadth_soft_aggressive | 50.000 | unmatched | 18 | -0.329 | -5.929 | 0.923 |
| breadth_soft_aggressive | 50.000 | all | 24 | 0.126 | 3.019 | 0.917 |
| breadth_drawdown_only | 50.000 | known_stress | 6 | 1.980 | 11.882 | 0.821 |
| breadth_drawdown_only | 50.000 | unmatched | 18 | -0.257 | -4.622 | 0.800 |
| breadth_drawdown_only | 50.000 | all | 24 | 0.303 | 7.260 | 0.805 |

## Trade Diagnostics

| fold | variant | cost_bps | event_label | accepted_winner | accepted_loser | reduced_winner | reduced_loser | increased_winner | increased_loser | accepted_winner_pnl | accepted_loser_pnl | loss_reduced_from_reduced_losers | profit_reduced_from_reduced_winners | profit_added_from_increased_winners | loss_added_from_increased_losers | net_blocker_value |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 333 | baseline | 10.000 | unmatched | 69 | 75 | 0 | 0 | 0 | 0 | 5.697 | -9.348 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 333 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 69 | 75 | 0.000 | 0.000 | 0.000 | 0.000 | 1.424 | 2.337 | -0.913 |
| 333 | breadth_drawdown_only | 10.000 | unmatched | 69 | 75 | 0 | 0 | 0 | 0 | 5.697 | -9.348 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 334 | baseline | 10.000 | unmatched | 78 | 43 | 0 | 0 | 0 | 0 | 14.860 | -4.714 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 334 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 78 | 43 | 0.000 | 0.000 | 0.000 | 0.000 | 3.715 | 1.179 | 2.536 |
| 334 | breadth_drawdown_only | 10.000 | unmatched | 78 | 43 | 0 | 0 | 0 | 0 | 14.860 | -4.714 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 335 | baseline | 10.000 | unmatched | 53 | 85 | 0 | 0 | 0 | 0 | 5.734 | -6.834 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 335 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 53 | 85 | 0.000 | 0.000 | 0.000 | 0.000 | 1.434 | 1.708 | -0.275 |
| 335 | breadth_drawdown_only | 10.000 | unmatched | 53 | 85 | 0 | 0 | 0 | 0 | 5.734 | -6.834 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 336 | baseline | 10.000 | unmatched | 76 | 34 | 0 | 0 | 0 | 0 | 17.097 | -4.874 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 336 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 76 | 34 | 0.000 | 0.000 | 0.000 | 0.000 | 1.710 | 0.487 | 1.222 |
| 336 | breadth_drawdown_only | 10.000 | unmatched | 76 | 34 | 0 | 0 | 0 | 0 | 17.097 | -4.874 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 337 | baseline | 10.000 | unmatched | 63 | 130 | 0 | 0 | 0 | 0 | 4.429 | -13.372 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 337 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 63 | 130 | 0.000 | 0.000 | 0.000 | 0.000 | 1.107 | 3.343 | -2.236 |
| 337 | breadth_drawdown_only | 10.000 | unmatched | 63 | 130 | 0 | 0 | 0 | 0 | 4.429 | -13.372 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 338 | baseline | 10.000 | unmatched | 76 | 97 | 0 | 0 | 0 | 0 | 8.875 | -15.530 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 338 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 76 | 97 | 0.000 | 0.000 | 0.000 | 0.000 | 2.219 | 3.882 | -1.664 |
| 338 | breadth_drawdown_only | 10.000 | unmatched | 76 | 97 | 0 | 0 | 0 | 0 | 8.875 | -15.530 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 339 | baseline | 10.000 | unmatched | 106 | 76 | 0 | 0 | 0 | 0 | 10.069 | -6.942 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 339 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 106 | 76 | 0.000 | 0.000 | 0.000 | 0.000 | 1.007 | 0.694 | 0.313 |
| 339 | breadth_drawdown_only | 10.000 | unmatched | 106 | 76 | 0 | 0 | 0 | 0 | 10.069 | -6.942 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 340 | baseline | 10.000 | early_2025_broad_correction_fpi_outflows | 40 | 106 | 0 | 0 | 0 | 0 | 5.351 | -9.800 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 340 | breadth_soft_aggressive | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 0 | 0 | 40 | 106 | 0.000 | 0.000 | 0.000 | 0.000 | 1.338 | 2.450 | -1.112 |
| 340 | breadth_drawdown_only | 10.000 | early_2025_broad_correction_fpi_outflows | 40 | 106 | 0 | 0 | 0 | 0 | 5.351 | -9.800 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 341 | baseline | 10.000 | early_2025_broad_correction_fpi_outflows | 80 | 105 | 0 | 0 | 0 | 0 | 4.621 | -9.180 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 341 | breadth_soft_aggressive | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 0 | 0 | 80 | 105 | 0.000 | 0.000 | 0.000 | 0.000 | 0.462 | 0.918 | -0.456 |
| 341 | breadth_drawdown_only | 10.000 | early_2025_broad_correction_fpi_outflows | 80 | 105 | 0 | 0 | 0 | 0 | 4.621 | -9.180 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 342 | baseline | 10.000 | early_2025_broad_correction_fpi_outflows | 59 | 120 | 0 | 0 | 0 | 0 | 4.117 | -16.131 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 342 | breadth_soft_aggressive | 10.000 | early_2025_broad_correction_fpi_outflows | 0 | 0 | 16 | 47 | 43 | 73 | 0.000 | 0.000 | 6.390 | 1.044 | 0.273 | 0.761 | 4.858 |
| 342 | breadth_drawdown_only | 10.000 | early_2025_broad_correction_fpi_outflows | 43 | 73 | 16 | 47 | 0 | 0 | 2.725 | -7.612 | 6.390 | 1.044 | 0.000 | 0.000 | 5.346 |
| 343 | baseline | 10.000 | unmatched | 68 | 65 | 0 | 0 | 0 | 0 | 7.853 | -7.682 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 343 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 63 | 59 | 5 | 6 | 0.000 | 0.000 | 5.110 | 4.852 | 0.138 | 0.087 | 0.309 |
| 343 | breadth_drawdown_only | 10.000 | unmatched | 5 | 6 | 63 | 59 | 0 | 0 | 1.384 | -0.869 | 5.110 | 4.852 | 0.000 | 0.000 | 0.258 |
| 344 | baseline | 10.000 | unmatched | 108 | 41 | 0 | 0 | 0 | 0 | 12.814 | -4.470 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 344 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 100 | 39 | 8 | 2 | 0.000 | 0.000 | 3.263 | 8.870 | 0.099 | 0.012 | -5.520 |
| 344 | breadth_drawdown_only | 10.000 | unmatched | 8 | 2 | 100 | 39 | 0 | 0 | 0.988 | -0.120 | 3.263 | 8.870 | 0.000 | 0.000 | -5.607 |
| 345 | baseline | 10.000 | unmatched | 77 | 49 | 0 | 0 | 0 | 0 | 9.998 | -5.194 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 345 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 77 | 49 | 0 | 0 | 0.000 | 0.000 | 3.896 | 7.499 | 0.000 | 0.000 | -3.603 |
| 345 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 77 | 49 | 0 | 0 | 0.000 | 0.000 | 3.896 | 7.499 | 0.000 | 0.000 | -3.603 |
| 346 | baseline | 10.000 | unmatched | 90 | 85 | 0 | 0 | 0 | 0 | 7.305 | -4.549 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 346 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 90 | 85 | 0 | 0 | 0.000 | 0.000 | 3.412 | 5.479 | 0.000 | 0.000 | -2.067 |
| 346 | breadth_drawdown_only | 10.000 | unmatched | 0 | 0 | 90 | 85 | 0 | 0 | 0.000 | 0.000 | 3.412 | 5.479 | 0.000 | 0.000 | -2.067 |
| 347 | baseline | 10.000 | july_2025_broad_based_selling | 39 | 131 | 0 | 0 | 0 | 0 | 1.894 | -10.019 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 347 | breadth_soft_aggressive | 10.000 | july_2025_broad_based_selling | 0 | 0 | 39 | 131 | 0 | 0 | 0.000 | 0.000 | 7.515 | 1.420 | 0.000 | 0.000 | 6.094 |
| 347 | breadth_drawdown_only | 10.000 | july_2025_broad_based_selling | 0 | 0 | 39 | 131 | 0 | 0 | 0.000 | 0.000 | 7.515 | 1.420 | 0.000 | 0.000 | 6.094 |
| 348 | baseline | 10.000 | unmatched | 97 | 68 | 0 | 0 | 0 | 0 | 9.712 | -4.149 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 348 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 97 | 68 | 0.000 | 0.000 | 0.000 | 0.000 | 0.971 | 0.415 | 0.556 |
| 348 | breadth_drawdown_only | 10.000 | unmatched | 97 | 68 | 0 | 0 | 0 | 0 | 9.712 | -4.149 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 349 | baseline | 10.000 | unmatched | 45 | 65 | 0 | 0 | 0 | 0 | 4.703 | -7.615 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 349 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 45 | 65 | 0.000 | 0.000 | 0.000 | 0.000 | 1.176 | 1.904 | -0.728 |
| 349 | breadth_drawdown_only | 10.000 | unmatched | 45 | 65 | 0 | 0 | 0 | 0 | 4.703 | -7.615 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 350 | baseline | 10.000 | unmatched | 60 | 71 | 0 | 0 | 0 | 0 | 6.090 | -6.080 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 350 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 60 | 71 | 0.000 | 0.000 | 0.000 | 0.000 | 1.523 | 1.520 | 0.002 |
| 350 | breadth_drawdown_only | 10.000 | unmatched | 60 | 71 | 0 | 0 | 0 | 0 | 6.090 | -6.080 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 351 | baseline | 10.000 | unmatched | 42 | 45 | 0 | 0 | 0 | 0 | 7.746 | -6.508 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 351 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 42 | 45 | 0.000 | 0.000 | 0.000 | 0.000 | 1.936 | 1.627 | 0.309 |
| 351 | breadth_drawdown_only | 10.000 | unmatched | 42 | 45 | 0 | 0 | 0 | 0 | 7.746 | -6.508 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 352 | baseline | 10.000 | unmatched | 42 | 102 | 0 | 0 | 0 | 0 | 2.543 | -9.198 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 352 | breadth_soft_aggressive | 10.000 | unmatched | 0 | 0 | 0 | 0 | 42 | 102 | 0.000 | 0.000 | 0.000 | 0.000 | 0.254 | 0.920 | -0.665 |
| 352 | breadth_drawdown_only | 10.000 | unmatched | 42 | 102 | 0 | 0 | 0 | 0 | 2.543 | -9.198 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## Decision

Reject: missing target diagnostic rows.
