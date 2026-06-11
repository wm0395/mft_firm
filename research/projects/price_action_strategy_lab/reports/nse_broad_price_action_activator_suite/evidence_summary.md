# Evidence Metrics Summary

- Alpha count: 25
- Top-10 candidates: 10
- Soft throttle improves return: 20
- Soft throttle improves Sharpe: 19
- Soft throttle reduces drawdown: 21
- Top-10 passing all in-sample gates: 5

## Variant Metrics

| scope | alpha | variant | obs | return_pct | cagr_pct | ann_vol_pct | ann_sharpe | latest_1m_rolling_sharpe | negative_1m_sharpe_windows | negative_1m_sharpe_rate | mean_negative_1m_sharpe | worst_1m_sharpe | max_drawdown_pct | fold_count | latest_fold_sharpe | negative_fold_rate | worst_fold_sharpe | avg_exposure_multiplier | active_day_pct | return_per_active_day_bps | turnover | positive_windows_reduced | negative_windows_reduced |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| in_sample_2yr | aggregate_equal_weight | baseline | 504.000 | 19.868 | 9.484 | 5.085 | 1.807 | -2.888 | 188.000 | 0.388 | -12.092 | -53.054 | -15.312 |  |  |  |  |  |  |  |  |  |  |
| in_sample_2yr | aggregate_equal_weight | hard_gate | 504.000 | 13.791 | 6.673 | 1.967 | 3.295 | -0.414 | 146.000 | 0.302 | -4.864 | -13.948 | -2.083 |  |  |  |  |  |  |  |  |  |  |
| in_sample_2yr | aggregate_equal_weight | soft_conservative | 504.000 | 16.839 | 8.092 | 3.267 | 2.398 | -2.570 | 179.000 | 0.370 | -11.214 | -45.413 | -8.402 |  |  |  |  |  |  |  |  |  |  |
| in_sample_2yr | aggregate_equal_weight | soft_aggressive | 504.000 | 24.796 | 11.712 | 4.854 | 2.306 | -1.440 | 176.000 | 0.364 | -11.432 | -43.565 | -12.408 |  |  |  |  |  |  |  |  |  |  |
| in_sample_2yr | aggregate_equal_weight | drawdown_only_throttle | 504.000 | 20.400 | 9.727 | 4.677 | 2.009 | -2.032 | 180.000 | 0.372 | -12.057 | -49.067 | -13.227 |  |  |  |  |  |  |  |  |  |  |
| walk_forward |  | baseline |  | 25.007 | 11.807 | 5.158 | 2.190 |  |  |  |  |  | -15.271 | 24.000 | 4.621 | 0.375 | -26.261 | 1.000 | 100.000 | 4.482 | 0.037 | 0.000 | 0.000 |
| walk_forward |  | hard_gate |  | 11.929 | 5.797 | 2.635 | 2.152 |  |  |  |  |  | -4.972 | 24.000 | 4.995 | 0.458 | -21.479 | 0.294 | 93.452 | 2.259 | 0.010 | 11.000 | 11.000 |
| walk_forward |  | soft_conservative |  | 18.330 | 8.780 | 3.634 | 2.334 |  |  |  |  |  | -9.508 | 24.000 | 4.955 | 0.375 | -26.002 | 0.647 | 100.000 | 3.366 | 0.024 | 13.000 | 9.000 |
| walk_forward |  | soft_aggressive |  | 23.566 | 11.160 | 4.839 | 2.211 |  |  |  |  |  | -12.854 | 24.000 | 4.666 | 0.333 | -25.262 | 0.891 | 100.000 | 4.246 | 0.033 | 12.000 | 4.000 |
| walk_forward |  | drawdown_only_throttle |  | 24.455 | 11.559 | 4.607 | 2.398 |  |  |  |  |  | -13.031 | 24.000 | 4.022 | 0.375 | -25.228 | 0.874 | 100.000 | 4.384 | 0.032 | 13.000 | 9.000 |

## Top 10 Candidates

| alpha | soft_return_rank | baseline_return_rank | soft_return_pct | baseline_return_pct | soft_return_delta_pct | soft_return_retention | soft_sharpe | baseline_sharpe | soft_sharpe_delta | soft_max_dd_pct | baseline_max_dd_pct | soft_drawdown_improvement_pct | soft_latest_1m_sharpe | soft_negative_1m_rate | hard_return_pct | hard_sharpe | soft_avg_exposure | soft_active_day_pct | soft_turnover | soft_positive_windows_reduced | soft_negative_windows_reduced | candidate_tier | soft_beats_baseline_return | soft_beats_baseline_sharpe | soft_reduces_drawdown | passes_all_in_sample_gates |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| relative_volume_breakout_20 | 1 | 2 | 66.333 | 70.302 | -3.969 | 0.944 | 3.391 | 3.493 | -0.102 | -9.844 | -14.590 | 4.746 | 3.427 | 0.368 | 45.705 | 3.162 | 0.812 | 100.000 | 0.038 | 145 | 71 | core_return_engine | False | False | True | False |
| breakout_20 | 2 | 1 | 65.463 | 71.539 | -6.077 | 0.915 | 3.457 | 3.577 | -0.120 | -14.578 | -14.597 | 0.019 | 1.831 | 0.341 | 6.709 | 1.721 | 0.938 | 100.000 | 0.043 | 29 | 27 | core_return_engine | False | False | True | False |
| keltner_breakout_20 | 3 | 3 | 57.384 | 54.966 | 2.418 | 1.044 | 2.608 | 2.543 | 0.066 | -17.536 | -18.276 | 0.740 | 0.715 | 0.488 | 29.641 | 2.579 | 0.893 | 100.000 | 0.026 | 66 | 50 | core_return_engine | True | True | True | True |
| trend_volume_composite | 4 | 4 | 55.062 | 50.762 | 4.299 | 1.085 | 3.143 | 2.943 | 0.200 | -15.734 | -16.376 | 0.641 | -5.786 | 0.467 | 9.417 | 1.753 | 0.948 | 100.000 | 0.014 | 22 | 30 | core_return_engine | True | True | True | True |
| failed_breakout_score_20 | 5 | 7 | 52.842 | 44.680 | 8.162 | 1.183 | 1.863 | 1.687 | 0.176 | -15.603 | -17.792 | 2.189 | 3.150 | 0.395 | 20.383 | 1.577 | 0.948 | 100.000 | 0.062 | 28 | 24 | core_return_engine | True | True | True | True |
| support_resistance_position_20 | 6 | 5 | 49.732 | 50.105 | -0.374 | 0.993 | 2.966 | 3.034 | -0.068 | -18.235 | -18.218 | -0.017 | -0.423 | 0.417 | 11.955 | 2.237 | 0.949 | 100.000 | 0.025 | 40 | 9 | validation_candidate | False | False | False | False |
| hybrid_confirmation | 7 | 6 | 41.984 | 46.305 | -4.321 | 0.907 | 3.278 | 2.847 | 0.431 | -9.993 | -17.192 | 7.199 | -3.850 | 0.413 | 25.798 | 3.059 | 0.796 | 100.000 | 0.029 | 109 | 100 | validation_candidate | False | True | True | False |
| inverse_fisher_rsi_reversal_10 | 8 | 9 | 37.163 | 28.379 | 8.784 | 1.310 | 1.896 | 1.549 | 0.347 | -16.893 | -19.576 | 2.682 | -7.286 | 0.444 | 19.287 | 2.063 | 0.948 | 100.000 | 0.025 | 27 | 25 | validation_candidate | True | True | True | True |
| multi_timeframe_confirmation | 9 | 8 | 35.271 | 34.406 | 0.864 | 1.025 | 2.890 | 2.907 | -0.017 | -13.356 | -13.349 | -0.006 | 4.812 | 0.322 | 10.640 | 2.627 | 0.949 | 100.000 | 0.024 | 45 | 4 | validation_candidate | True | False | False | False |
| inside_outside_bar_score | 10 | 10 | 34.157 | 26.952 | 7.205 | 1.267 | 1.722 | 1.378 | 0.344 | -15.287 | -18.882 | 3.595 | 4.807 | 0.434 | 12.082 | 1.732 | 0.948 | 100.000 | 0.089 | 26 | 26 | validation_candidate | True | True | True | True |

## Limitations

- Current walk-forward evidence is one latest fold only.
- Multi-fold OOS is still required to prove stability.
