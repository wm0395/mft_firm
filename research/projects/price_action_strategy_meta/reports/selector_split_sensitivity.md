# Selector Split Sensitivity

## Protocol

- Shifted boundary tests rerun the current selector after dropping the earliest portion of the date index.
- Embargo-length tests rerun the embargo split with alternate embargo windows.
- Train-window tests rerun the leakage-controlled selector with shorter and longer training spans.

## Summary

| sweep | setting | split_type | folds | active_folds | test_precision | test_coverage | test_mean_net_bps | baseline_mean_net_bps | lift_vs_baseline_bps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| shifted_boundaries | shift_0 | embargo | 5 | 1 | 0.714 | 0.008 | 0.412 | 2.367 | -1.955 |
| shifted_boundaries | shift_0 | purged | 5 | 1 | 0.714 | 0.008 | 0.412 | 2.538 | -2.126 |
| shifted_boundaries | shift_0 | walk_forward | 5 | 1 | 0.714 | 0.008 | 0.412 | 2.538 | -2.126 |
| shifted_boundaries | shift_63 | embargo | 5 | 1 | 0.636 | 0.013 | -0.320 | 3.620 | -3.940 |
| shifted_boundaries | shift_63 | purged | 5 | 1 | 0.700 | 0.012 | 0.807 | 3.620 | -2.813 |
| shifted_boundaries | shift_63 | walk_forward | 5 | 1 | 0.700 | 0.012 | 0.807 | 3.620 | -2.813 |
| shifted_boundaries | shift_126 | embargo | 5 | 1 | 0.609 | 0.009 | -0.613 | 4.845 | -5.459 |
| shifted_boundaries | shift_126 | purged | 5 | 1 | 0.667 | 0.011 | -0.324 | 5.751 | -6.075 |
| shifted_boundaries | shift_126 | walk_forward | 5 | 1 | 0.667 | 0.011 | -0.324 | 5.751 | -6.075 |
| embargo_length | embargo_0 | embargo | 5 | 1 | 0.714 | 0.008 | 0.412 | 2.538 | -2.126 |
| embargo_length | embargo_5 | embargo | 5 | 1 | 0.714 | 0.008 | 0.412 | 2.367 | -1.955 |
| embargo_length | embargo_10 | embargo | 5 | 1 | 0.714 | 0.008 | 0.412 | 2.374 | -1.962 |
| embargo_length | embargo_20 | embargo | 5 | 1 | 0.714 | 0.008 | 0.412 | 2.374 | -1.962 |
| train_window | train_1000 | embargo | 7 | 1 | 0.474 | 0.022 | 0.386 | 6.888 | -6.503 |
| train_window | train_1000 | walk_forward | 7 | 1 | 0.481 | 0.022 | 0.387 | 7.092 | -6.705 |
| train_window | train_1260 | embargo | 5 | 1 | 0.714 | 0.008 | 0.412 | 2.367 | -1.955 |
| train_window | train_1260 | walk_forward | 5 | 1 | 0.714 | 0.008 | 0.412 | 2.538 | -2.126 |
| train_window | train_1500 | embargo | 4 | 1 | 0.474 | 0.039 | 0.669 | 2.253 | -1.584 |
| train_window | train_1500 | walk_forward | 4 | 1 | 0.481 | 0.039 | 0.671 | 2.253 | -1.582 |

## Interpretation

- If the selector were durable, the lift would not collapse under modest boundary and window perturbations.
- If the selector is fragile, these sweeps should remain below the always-on baseline or swing sharply across settings.

## Decision

- `SUSPECT_OVERFIT`
- The current split-sensitive sweeps are still intended as falsification checks, not as deployment evidence.