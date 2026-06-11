# Support Trendline Breadth-Only Diagnostic

## Aggregate

| variant | cost_bps | return_pct | cagr_pct | ann_vol_pct | ann_sharpe | max_drawdown_pct | negative_fold_rate | worst_fold_sharpe | latest_fold_sharpe | average_exposure | turnover |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 10.000 | 10.452 | 5.096 | 7.264 | 0.721 | -26.794 | 0.458 | -23.334 | 3.340 | 1.000 | 0.333 |
| breadth_risk_off_high | 10.000 | 20.656 | 9.843 | 7.997 | 1.214 | -26.597 | 0.500 | -20.082 | 3.340 | 0.996 | 0.334 |

## Tail

| variant | cost_bps | mean_delta_vs_baseline | left_tail_delta | right_tail_retention | top_decile_retention | bottom_decile_improvement | best_fold_damage | worst_fold_improvement | ci_low | ci_high | paired_t_stat | paired_p_value | bh_p_value |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 10.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| breadth_risk_off_high | 10.000 | 0.387 | 0.682 | 1.117 | 1.211 | 0.885 | 1.137 | 4.513 | -0.249 | 0.997 | 0.977 | 0.339 | 0.678 |

## Event Split

| variant | cost_bps | split | fold_count | mean_delta | net_delta | average_exposure |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 10.000 | known_stress | 6 | 0.000 | 0.000 | 1.000 |
| baseline | 10.000 | unmatched | 18 | 0.000 | 0.000 | 1.000 |
| baseline | 10.000 | all | 24 | 0.000 | 0.000 | 1.000 |
| breadth_risk_off_high | 10.000 | known_stress | 6 | 0.878 | 5.267 | 0.998 |
| breadth_risk_off_high | 10.000 | unmatched | 18 | 0.223 | 4.014 | 0.995 |
| breadth_risk_off_high | 10.000 | all | 24 | 0.387 | 9.281 | 0.996 |

## Threshold Stability

| variant | cost_bps | fold_count | threshold_mean | threshold_std | selected_quantile_mean | selected_quantile_std | activation_rate | average_exposure |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| breadth_risk_off_high | 10.000 | 24 | 0.031 | 0.055 | 0.571 | 0.124 | 1.000 | 0.996 |

## Fold Concentration

| variant | cost_bps | fold_count | helped_folds | hurt_folds | top_1_fold_contribution | top_3_fold_contribution | excluding_best_fold_delta | excluding_worst_fold_delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| breadth_risk_off_high | 10.000 | 24 | 10 | 11 | 0.486 | 1.198 | 4.768 | 13.406 |

## Decision

Research lead: breadth_risk_off survives this focused diagnostic, still not deployable.
