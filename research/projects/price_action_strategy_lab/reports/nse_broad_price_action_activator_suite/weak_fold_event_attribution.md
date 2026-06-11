# Weak Fold Event Attribution

## Worst Baseline Alpha Folds

| fold | alpha | test_start | test_end | return_pct | event_label | selected_indicator | selected_side |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 342 | support_trendline_position_20 | 2025-01-31 | 2025-03-02 | -11.8756 | early_2025_broad_correction_fpi_outflows | volume_acceptance | high |
| 342 | bollinger_percent_b_mean_reversion_20 | 2025-01-31 | 2025-03-02 | -11.6802 | early_2025_broad_correction_fpi_outflows | breadth_risk_off | high |
| 342 | stochastic_mean_reversion_14 | 2025-01-31 | 2025-03-02 | -11.6640 | early_2025_broad_correction_fpi_outflows | breadth_risk_off | high |
| 342 | williams_r_mean_reversion_14 | 2025-01-31 | 2025-03-02 | -11.6640 | early_2025_broad_correction_fpi_outflows | breadth_risk_off | high |
| 342 | doji_reversal_score | 2025-01-31 | 2025-03-02 | -11.6403 | early_2025_broad_correction_fpi_outflows | gap_fade | low |
| 342 | inverse_fisher_rsi_reversal_10 | 2025-01-31 | 2025-03-02 | -11.6255 | early_2025_broad_correction_fpi_outflows | volatility_expansion | high |
| 335 | engulfing_reversal_score | 2024-07-02 | 2024-07-31 | -11.5096 | unmatched | volatility_compression | high |
| 342 | fisher_transform_reversal_10 | 2025-01-31 | 2025-03-02 | -11.3393 | early_2025_broad_correction_fpi_outflows | breadth_risk_off | high |
| 342 | parabolic_sar_trend | 2025-01-31 | 2025-03-02 | -11.1292 | early_2025_broad_correction_fpi_outflows | breadth_risk_off | high |
| 354 | inverse_fisher_rsi_reversal_10 | 2026-02-08 | 2026-03-09 | -10.7733 | feb_2026_it_global_tech_selloff | relative_strength_leader | low |
| 342 | hammer_shooting_star_score | 2025-01-31 | 2025-03-02 | -10.4854 | early_2025_broad_correction_fpi_outflows | volatility_expansion | high |
| 354 | hybrid_confirmation | 2026-02-08 | 2026-03-09 | -10.1128 | feb_2026_it_global_tech_selloff | gap_continuation | low |
| 354 | hammer_shooting_star_score | 2026-02-08 | 2026-03-09 | -9.6594 | feb_2026_it_global_tech_selloff | relative_strength_leader | low |
| 340 | engulfing_reversal_score | 2024-12-03 | 2025-01-01 | -9.6450 | early_2025_broad_correction_fpi_outflows | volatility_expansion | high |
| 354 | failed_reversal_score | 2026-02-08 | 2026-03-09 | -9.5079 | feb_2026_it_global_tech_selloff | volatility_compression | low |
| 342 | failed_breakout_score_20 | 2025-01-31 | 2025-03-02 | -9.4972 | early_2025_broad_correction_fpi_outflows | breadth_risk_off | high |
| 354 | support_resistance_position_20 | 2026-02-08 | 2026-03-09 | -9.3479 | feb_2026_it_global_tech_selloff | relative_strength_leader | high |
| 354 | trend_volume_composite | 2026-02-08 | 2026-03-09 | -9.3171 | feb_2026_it_global_tech_selloff | gap_continuation | low |
| 354 | chandelier_trend | 2026-02-08 | 2026-03-09 | -9.1777 | feb_2026_it_global_tech_selloff | gap_continuation | low |
| 354 | doji_reversal_score | 2026-02-08 | 2026-03-09 | -9.1544 | feb_2026_it_global_tech_selloff | oscillator_extreme | low |
| 340 | piercing_dark_cloud_score | 2024-12-03 | 2025-01-01 | -9.0683 | early_2025_broad_correction_fpi_outflows | volatility_expansion | high |
| 337 | doji_reversal_score | 2024-09-02 | 2024-09-30 | -8.8246 | unmatched | volume_acceptance | low |
| 354 | bollinger_percent_b_mean_reversion_20 | 2026-02-08 | 2026-03-09 | -8.4629 | feb_2026_it_global_tech_selloff | volatility_compression | high |
| 354 | inside_outside_bar_score | 2026-02-08 | 2026-03-09 | -8.3987 | feb_2026_it_global_tech_selloff | relative_strength_leader | low |
| 341 | piercing_dark_cloud_score | 2025-01-02 | 2025-01-30 | -8.3281 | early_2025_broad_correction_fpi_outflows | volume_acceptance | low |

## Interpretation

- Event labels are explanatory hypotheses only, not model inputs.
- Any event-derived indicator must be timestamped, lagged, and tested OOS.
- Use this report to explain failures before adding new blockers.