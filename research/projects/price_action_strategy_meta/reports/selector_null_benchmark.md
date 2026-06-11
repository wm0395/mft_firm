# Selector Null Benchmark

## Protocol

- Random-strategy null: 100 seeded draws over the cached active-day strategy pool.
- The observed policy is read from cached gate outputs.

## Observed

| policy | test_portfolio_mean_net_bps | test_active_mean_net_bps | test_precision | lift_vs_baseline_bps |
| --- | --- | --- | --- | --- |
| loose | 6.109 | 34.758 | 0.549 | -3.694 |

## Summary

| benchmark | trials | median_portfolio_net_bps | p05_portfolio_net_bps | p95_portfolio_net_bps | median_lift_vs_baseline_bps | p_ge_observed |
| --- | --- | --- | --- | --- | --- | --- |
| observed | 1 | 6.109 | 6.109 | 6.109 | -3.694 | 1.000 |
| random_strategy | 100 | -0.105 | -4.307 | 3.072 | -9.908 | 0.000 |

## Interpretation

- The random-strategy null asks whether the chosen activation pool is better than picking among the same active strategies at random.
- If the null overlaps the observed selector materially, the selector remains fragile.

## Decision

- `SUSPECT_OVERFIT`
- The selector still trails the always-on baseline; this cached null check is a sanity test, not promotion evidence.