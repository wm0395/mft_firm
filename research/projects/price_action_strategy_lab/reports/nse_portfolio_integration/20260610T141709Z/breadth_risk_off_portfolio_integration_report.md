# Breadth Risk-Off Portfolio Integration

## Metrics

| variant | cost_bps | return_pct | ann_sharpe | max_drawdown_pct | negative_fold_rate | worst_fold_sharpe | latest_fold_sharpe | turnover |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_baseline | 10.000 | 24.356 | 1.891 | -7.498 | 0.375 | -26.261 | 4.621 | 0.371 |
| full_stack_structure_overlay | 10.000 | 24.787 | 1.866 | -7.901 | 0.375 | -27.019 | 4.148 | 0.377 |
| full_stack_core_structure_overlay | 10.000 | 25.195 | 1.919 | -7.743 | 0.375 | -26.998 | 4.685 | 0.372 |
| structure_family_only_baseline | 10.000 | 32.223 | 2.382 | -8.349 | 0.375 | -20.613 | 7.280 | 0.558 |
| structure_family_only_overlay | 10.000 | 34.581 | 2.462 | -10.332 | 0.375 | -21.454 | 5.270 | 0.587 |
| reversal_family_only_baseline | 10.000 | 17.912 | -0.296 | -11.142 | 0.542 | -29.090 | -1.505 | 0.377 |
| reversal_family_only_overlay_negative_control | 10.000 | 12.786 | -0.180 | -10.606 | 0.542 | -26.894 | -1.505 | 0.383 |
| full_baseline | 25.000 | 18.697 | 1.078 | -7.714 | 0.375 | -27.861 | 3.700 | 0.371 |
| full_stack_structure_overlay | 25.000 | 19.017 | 0.949 | -8.133 | 0.375 | -30.389 | 3.300 | 0.373 |
| full_stack_core_structure_overlay | 25.000 | 19.587 | 1.107 | -7.966 | 0.375 | -28.546 | 3.672 | 0.371 |
| structure_family_only_baseline | 25.000 | 23.708 | 1.424 | -8.668 | 0.375 | -21.517 | 6.090 | 0.558 |
| structure_family_only_overlay | 25.000 | 25.479 | 1.279 | -10.722 | 0.417 | -21.217 | 4.528 | 0.566 |
| reversal_family_only_baseline | 25.000 | 12.178 | -0.889 | -11.347 | 0.542 | -30.024 | -2.277 | 0.377 |
| reversal_family_only_overlay_negative_control | 25.000 | 8.011 | -0.716 | -10.659 | 0.542 | -27.561 | -2.277 | 0.378 |
| full_baseline | 50.000 | 9.294 | -0.270 | -8.074 | 0.375 | -30.397 | 2.170 | 0.371 |
| full_stack_structure_overlay | 50.000 | 9.747 | -0.367 | -8.460 | 0.375 | -32.546 | 1.972 | 0.370 |
| full_stack_core_structure_overlay | 50.000 | 10.156 | -0.223 | -8.337 | 0.375 | -30.991 | 2.227 | 0.370 |
| structure_family_only_baseline | 50.000 | 9.580 | -0.171 | -9.197 | 0.458 | -23.072 | 4.112 | 0.558 |
| structure_family_only_overlay | 50.000 | 11.977 | -0.102 | -11.088 | 0.500 | -22.028 | 3.958 | 0.550 |
| reversal_family_only_baseline | 50.000 | 2.651 | -1.873 | -11.686 | 0.542 | -31.520 | -3.550 | 0.377 |
| reversal_family_only_overlay_negative_control | 50.000 | 1.911 | -1.454 | -10.493 | 0.542 | -26.895 | -3.550 | 0.367 |

## Tail

| variant | cost_bps | mean_delta | left_tail_delta | right_tail_retention | top_decile_retention | bottom_decile_improvement | best_fold_damage | worst_fold_improvement | ci_low | ci_high | paired_t_stat | paired_p_value | bh_p_value |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_baseline | 10.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| full_stack_structure_overlay | 10.000 | 0.018 | -0.066 | 1.057 | 1.059 | -0.039 | 0.465 | -0.384 | -0.086 | 0.112 | 0.289 | 0.775 | 1.000 |
| full_stack_core_structure_overlay | 10.000 | 0.035 | -0.009 | 1.039 | 1.037 | 0.029 | 0.292 | -0.236 | -0.025 | 0.091 | 0.969 | 0.343 | 1.000 |
| structure_family_only_baseline | 10.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| structure_family_only_overlay | 10.000 | 0.098 | -0.397 | 1.112 | 1.263 | -0.727 | 2.539 | 0.605 | -0.429 | 0.573 | 0.314 | 0.756 | 1.000 |
| reversal_family_only_baseline | 10.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| reversal_family_only_overlay_negative_control | 10.000 | -0.214 | -0.416 | 1.096 | 1.199 | 0.153 | 1.694 | 2.234 | -0.771 | 0.345 | -0.615 | 0.545 | 1.000 |
| full_baseline | 25.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| full_stack_structure_overlay | 25.000 | 0.013 | -0.026 | 1.052 | 1.053 | 0.059 | 0.446 | -0.399 | -0.088 | 0.104 | 0.223 | 0.825 | 1.000 |
| full_stack_core_structure_overlay | 25.000 | 0.037 | 0.017 | 1.037 | 1.034 | 0.088 | 0.284 | -0.243 | -0.023 | 0.091 | 1.032 | 0.313 | 1.000 |
| structure_family_only_baseline | 25.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| structure_family_only_overlay | 25.000 | 0.074 | -0.193 | 1.098 | 1.239 | -0.428 | 1.805 | 1.645 | -0.435 | 0.530 | 0.246 | 0.808 | 1.000 |
| reversal_family_only_baseline | 25.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| reversal_family_only_overlay_negative_control | 25.000 | -0.174 | -0.224 | 1.094 | 1.199 | 0.553 | 1.659 | 2.486 | -0.716 | 0.367 | -0.508 | 0.617 | 1.000 |
| full_baseline | 50.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| full_stack_structure_overlay | 50.000 | 0.019 | 0.023 | 1.048 | 1.050 | 0.171 | 0.362 | -0.367 | -0.078 | 0.107 | 0.330 | 0.745 | 1.000 |
| full_stack_core_structure_overlay | 50.000 | 0.036 | 0.021 | 1.036 | 1.034 | 0.107 | 0.270 | -0.254 | -0.022 | 0.089 | 1.027 | 0.315 | 1.000 |
| structure_family_only_baseline | 50.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| structure_family_only_overlay | 50.000 | 0.100 | 0.074 | 1.086 | 1.227 | 0.000 | 1.675 | 2.694 | -0.389 | 0.540 | 0.347 | 0.732 | 1.000 |
| reversal_family_only_baseline | 50.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| reversal_family_only_overlay_negative_control | 50.000 | -0.031 | 0.439 | 1.080 | 1.188 | 1.862 | 1.298 | 3.465 | -0.604 | 0.538 | -0.086 | 0.932 | 1.000 |
