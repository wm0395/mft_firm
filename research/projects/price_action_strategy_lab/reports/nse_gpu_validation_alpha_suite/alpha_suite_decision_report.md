# Alpha Suite Decision Report

- decision: research_only
- chosen_name: 
- chosen_alpha: inverse_fisher_rsi_reversal_10
- selected_scheme: embargo
- selector_score: -80.861
- lower_bps: -48.609
- fold_pass_rate: 0.667
- summary_rows: 540

- status: research_only
- reason: validation gates did not clear

| scheme | alpha | mode | horizon | cost_bps | fold_count | train_days | test_days | obs | active_days | coverage | gross_mean_bps | net_mean_bps | gross_std_bps | net_std_bps | turnover | win_rate | hit_rate | net_sharpe_like | hac_t_stat | max_drawdown_bps | lower_bps | upper_bps | break_even_cost_bps | fold_pass_rate | instability_bps | selector_score | primary_scheme | eligible | target_cost | cost_gap_bps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| embargo | inverse_fisher_rsi_reversal_10 | ranked_long_only | 1 | 0.000 | 6 | 756.000 | 63.000 | 359 | 359 | 0.950 | 11.098 | 11.098 | 292.222 | 292.222 | 0.245 | 0.461 | 0.461 | 0.656 | 0.450 | -3855.032 | -42.697 | 66.312 | 24.246 | 0.667 | 25.892 | -74.707 | True | True | False | -10.000 |
| embargo | inverse_fisher_rsi_reversal_10 | ranked_long_only | 1 | 5.000 | 6 | 756.000 | 63.000 | 359 | 359 | 0.950 | 11.098 | 8.517 | 292.222 | 292.182 | 0.245 | 0.453 | 0.453 | 0.510 | 0.370 | -3905.032 | -46.862 | 61.610 | 24.246 | 0.667 | 26.010 | -78.990 | True | True | False | -5.000 |
| embargo | inverse_fisher_rsi_reversal_10 | ranked_long_only | 1 | 10.000 | 6 | 756.000 | 63.000 | 359 | 359 | 0.950 | 11.098 | 5.936 | 292.222 | 292.168 | 0.245 | 0.451 | 0.451 | 0.364 | 0.288 | -3955.032 | -48.609 | 61.477 | 24.246 | 0.667 | 26.134 | -80.861 | True | True | True | 0.000 |
| embargo | fisher_transform_reversal_10 | ranked_long_only | 1 | 0.000 | 6 | 756.000 | 63.000 | 359 | 359 | 0.950 | 24.201 | 24.201 | 304.527 | 304.527 | 0.160 | 0.459 | 0.459 | 1.317 | 0.653 | -3464.296 | -42.968 | 93.365 | 69.553 | 0.833 | 34.781 | -81.751 | True | True | False | -10.000 |
| embargo | fisher_transform_reversal_10 | ranked_long_only | 1 | 10.000 | 6 | 756.000 | 63.000 | 359 | 359 | 0.950 | 24.201 | 20.830 | 304.527 | 304.207 | 0.160 | 0.453 | 0.453 | 1.136 | 0.566 | -3494.296 | -47.380 | 89.630 | 69.553 | 0.833 | 34.603 | -85.983 | True | True | True | 0.000 |
| embargo | fisher_transform_reversal_10 | ranked_long_only | 1 | 5.000 | 6 | 756.000 | 63.000 | 359 | 359 | 0.950 | 24.201 | 22.515 | 304.527 | 304.357 | 0.160 | 0.456 | 0.456 | 1.226 | 0.610 | -3479.296 | -47.539 | 92.735 | 69.553 | 0.833 | 34.692 | -86.232 | True | True | False | -5.000 |
| embargo | fisher_transform_reversal_10 | ranked_long_only | 1 | 25.000 | 6 | 756.000 | 63.000 | 359 | 359 | 0.950 | 24.201 | 15.773 | 304.527 | 303.887 | 0.160 | 0.450 | 0.450 | 0.864 | 0.434 | -3539.296 | -50.321 | 82.557 | 69.553 | 0.833 | 34.340 | -88.662 | True | True | False | 15.000 |
| embargo | inverse_fisher_rsi_reversal_10 | ranked_long_only | 1 | 25.000 | 6 | 756.000 | 63.000 | 359 | 359 | 0.950 | 11.098 | -1.806 | 292.222 | 292.278 | 0.245 | 0.445 | 0.445 | -0.072 | 0.042 | -4105.032 | -57.223 | 53.025 | 24.246 | 0.667 | 26.542 | -89.883 | True | True | False | 15.000 |
| embargo | bollinger_percent_b_mean_reversion_20 | ranked_long_only | 1 | 0.000 | 6 | 756.000 | 63.000 | 359 | 359 | 0.950 | 27.145 | 27.145 | 370.017 | 370.017 | 0.267 | 0.475 | 0.475 | 1.489 | 0.847 | -4464.267 | -47.916 | 111.570 | 51.049 | 0.667 | 37.137 | -91.733 | True | True | False | -10.000 |
| embargo | bollinger_percent_b_mean_reversion_20 | ranked_long_only | 1 | 5.000 | 6 | 756.000 | 63.000 | 359 | 359 | 0.950 | 27.145 | 24.327 | 370.017 | 369.857 | 0.267 | 0.470 | 0.470 | 1.352 | 0.780 | -4544.267 | -50.276 | 104.202 | 51.049 | 0.667 | 37.123 | -94.079 | True | True | False | -5.000 |
