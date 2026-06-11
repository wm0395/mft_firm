# Selector Neutral Variant

## Protocol

- This is a selected-portfolio sensitivity, not a full neutral refit.
- I keep the current gate schedule fixed and recompute only the strategies that were actually selected.
- Market neutrality subtracts the same-day universe mean from 5-day forward returns.
- Sector neutrality subtracts the same-day industry mean from 5-day forward returns.

## Summary

| source | mode | label | active_strategies | active_folds | raw_active_mean_net_bps | neutral_active_mean_net_bps | raw_portfolio_mean_net_bps | neutral_portfolio_mean_net_bps | raw_precision | neutral_precision | coverage | active_days | delta_active_net_bps | delta_portfolio_net_bps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gate_holdout | market_neutral | market-neutral | 4 | 1 | 34.758 | 34.758 | 6.109 | 6.109 | 0.549 | 0.549 | 0.176 | 805.000 | 0.000 | 0.000 |
| gate_holdout | sector_neutral | sector-neutral | 4 | 1 | 34.758 | 27.378 | 6.109 | 4.812 | 0.549 | 0.566 | 0.176 | 805.000 | -7.380 | -1.297 |
| walk_forward | market_neutral | market-neutral | 1 | 1 | 49.441 | 49.441 | 0.412 | 0.412 | 0.714 | 0.714 | 0.008 | 63.000 | 0.000 | 0.000 |
| walk_forward | sector_neutral | sector-neutral | 1 | 1 | 49.441 | 158.719 | 0.412 | 1.323 | 0.714 | 0.762 | 0.008 | 63.000 | 109.278 | 0.911 |

## Interpretation

- If neutrality were the missing explanation, the selected portfolio would improve materially relative to the raw schedule.
- The holdout gate is flat to slightly worse under neutrality, and the walk-forward active pocket is still too sparse to rescue the selector.

## Decision

- `NEEDS_MORE_DATA`
- This is a useful sensitivity check, but it is not a full neutral refit and it does not change the rejection state of the selector.