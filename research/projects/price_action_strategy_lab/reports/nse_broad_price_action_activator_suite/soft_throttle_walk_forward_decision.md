# Soft Throttle Walk-Forward Decision

- decision: promote
- return_retention: 0.942
- sharpe_pass: True
- drawdown_pass: True
- worst_fold_pass: True
- return_pass: True

| variant | fold_count | return_pct | cagr_pct | ann_vol_pct | ann_sharpe | latest_fold_sharpe | negative_fold_rate | worst_fold_sharpe | max_drawdown_pct | avg_exposure_multiplier | active_day_pct | return_per_active_day_bps | turnover | positive_windows_reduced | negative_windows_reduced |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 24 | 25.007 | 11.807 | 5.158 | 2.190 | 4.621 | 0.375 | -26.261 | -15.271 | 1.000 | 100.000 | 4.482 | 0.037 | 0 | 0 |
| hard_gate | 24 | 11.929 | 5.797 | 2.635 | 2.152 | 4.995 | 0.458 | -21.479 | -4.972 | 0.294 | 93.452 | 2.259 | 0.010 | 11 | 11 |
| soft_conservative | 24 | 18.330 | 8.780 | 3.634 | 2.334 | 4.955 | 0.375 | -26.002 | -9.508 | 0.647 | 100.000 | 3.366 | 0.024 | 13 | 9 |
| soft_aggressive | 24 | 23.566 | 11.160 | 4.839 | 2.211 | 4.666 | 0.333 | -25.262 | -12.854 | 0.891 | 100.000 | 4.246 | 0.033 | 12 | 4 |
| drawdown_only_throttle | 24 | 24.455 | 11.559 | 4.607 | 2.398 | 4.022 | 0.375 | -25.228 | -13.031 | 0.874 | 100.000 | 4.384 | 0.032 | 13 | 9 |
