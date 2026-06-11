# Support Trendline Breadth-Only Diagnostic

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

## Threshold Stability

| variant | cost_bps | fold_count | threshold_mean | threshold_std | selected_quantile_mean | selected_quantile_std | activation_rate | average_exposure |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| breadth_risk_off_high | 10.000 | 24 | 0.031 | 0.055 | 0.571 | 0.124 | 1.000 | 0.996 |
| breadth_risk_off_high | 25.000 | 24 | 0.036 | 0.059 | 0.583 | 0.131 | 1.000 | 0.948 |
| breadth_risk_off_high | 50.000 | 24 | 0.036 | 0.059 | 0.583 | 0.131 | 1.000 | 0.942 |
| breadth_risk_off_high | 75.000 | 24 | 0.036 | 0.059 | 0.583 | 0.131 | 1.000 | 0.935 |

## Fold Concentration

| variant | cost_bps | fold_count | helped_folds | hurt_folds | top_1_fold_contribution | top_3_fold_contribution | excluding_best_fold_delta | excluding_worst_fold_delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| breadth_risk_off_high | 10.000 | 24 | 10 | 11 | 0.486 | 1.198 | 4.768 | 13.406 |
| breadth_risk_off_high | 25.000 | 24 | 9 | 12 | 0.669 | 1.650 | 2.253 | 10.753 |
| breadth_risk_off_high | 50.000 | 24 | 9 | 13 | 0.619 | 1.532 | 2.845 | 11.116 |
| breadth_risk_off_high | 75.000 | 24 | 9 | 12 | 0.534 | 1.356 | 4.081 | 12.124 |

## Decision

Research lead: breadth_risk_off survives this focused diagnostic, still not deployable.
