# Metrics Framework

This project uses a layered metric panel so strategy edge, risk, cost
sensitivity, and selector quality are all visible.

## Primary Panel

- `trade_count`: sample-size gate.
- `win_rate`: directional correctness.
- `mean_return_pct`: average edge per trade.
- `median_return_pct`: robustness against skew.
- `total_return_pct`: aggregate trade contribution.
- `max_drawdown_pct`: tail-risk constraint.
- `sharpe_like_score`: simple risk-adjusted score.
- `cagr`: compounding check for multi-trade runs.
- `turnover`: cost sensitivity and friction exposure.
- `capacity_estimate`: scale check before any deployment discussion.

## Conditional Panel

- `win_rate_by_regime`: where each family works.
- `sharpe_by_regime`: which regimes deserve deployment.
- `false_breakout_rate`: breakout-specific failure control.
- `gap_fill_rate`: gap family failure control.
- `failure_window_report`: when a family tends to break.
- `stability_by_universe`: whether edge survives basket changes.

## Selector Panel

- `precision`: how often the selector is right when it acts.
- `recall`: how much of the usable edge the selector captures.
- `coverage`: how often the selector is willing to act.
- `calibration_error`: whether selector scores align with realized edge.
- `abstention_rate`: whether the selector stays out when conditions are weak.

## Validation Protocol

- Use walk-forward splits first.
- Add purged and embargoed splits for leakage control.
- Hold out entire regimes, not just random rows.
- Stress costs at `0`, `5`, `10`, and `25` bps.
- Compare every family against always-on and always-flat baselines.
- Do not treat an in-sample win as a research result.

## Selector Rule

The meta selector only qualifies if it improves out-of-sample precision
without collapsing coverage and without relying on a single regime slice.
