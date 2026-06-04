# Price Action Strategy Meta

This project catalogs the repo-native price-action families in
`project.alpha_math`, measures where each family works, and evaluates a
regime-gated selector that only deploys the right family when conditions are
favorable.

## Objective

Identify which price-action strategies have durable out-of-sample edge, which
fail after costs, and which market regimes support a high-precision meta
selector.

## Scope

- Breakout continuation
- Trend-following exits
- Gap continuation and gap fade
- Reversal and failed-breakout setups
- Support/resistance and market-structure reactions
- Volume-confirmation overlays
- Regime filters used to gate deployment

## Strategy Inventory

See [reports/strategy_catalog.md](./reports/strategy_catalog.md) for the
family map and [reports/strategy_inventory.md](./reports/strategy_inventory.md)
for the exhaustive primitive map.

## Metrics

See [reports/metrics_framework.md](./reports/metrics_framework.md) for the
evaluation panel.

## Screening Readout

See [reports/screening_results.md](./reports/screening_results.md) for the
first-pass daily-bar screen across the repo-native price-action families.
The current readout is simple:

- 1-day trend, breakout, gap, structure, and volume families are cost-negative
  on the high-vol lane.
- 5-day reversal families are the only clear positive pocket after turnover
  stress.
- No strategy is yet stable across both universes and both horizons.

## Supplemental Extra Screen

See [reports/extra_strategy_screening.md](./reports/extra_strategy_screening.md)
for the supplemental pass over the extra first-principles strategies. The
useful addition is narrow:

- `fisher_transform_reversal_10` is the only stable extra winner.
- Its best pockets are in `bear`, `high_vol`, `up_gap_shock`, and
  `low_liquidity` states.
- `relative_volume_breakout_20`, `elder_ray_trend`, and
  `ultimate_oscillator_reversal` are clear losers after cost stress.
- The extra pool now also includes `supertrend_direction_10`,
  `parabolic_sar_trend`, `aroon_oscillator_25`,
  `ichimoku_kijun_spread_26`, `kst_momentum_9`,
  `inverse_fisher_rsi_reversal_10`, `mass_index_reversal_25`,
  `support_trendline_position_20`, `volume_profile_position_20`, and
  `choppiness_inverse_14` so the selector can probe more first-principles
  trend, reversal, and structure combinations.

## Regime Analysis

See [reports/regime_analysis.md](./reports/regime_analysis.md) for the
regime-conditioned scan over the top 100 high-vol names from each universe.
The current signal is more specific:

- Reversal exhaustion is the only broad positive pocket after costs, especially
  `bollinger_percent_b_mean_reversion_20`, `stochastic_mean_reversion_14`,
  `williams_r_mean_reversion_14`, and `mfi_mean_reversion_14` in `high_vol`,
  `bear`, and `risk_off` states.
- Breakout continuation, structure levels, and gap reaction are generally
  cost-negative; `keltner_breakout_20` is the weakest breakout variant in
  low-liquidity and gap-shock states.
- The supplemental extra screen adds one real candidate:
  `fisher_transform_reversal_10` is the strongest additional reversal signal
  and is especially strong in bear / high-vol / up-gap-shock states.
- `Metals & Mining` and `Capital Goods` are the strongest 5-day sector pockets
  in bullish or risk-on environments.
- Low-liquidity `risk_off` slices are consistently weak.
- Gap shocks are the best local proxy for news-like open shocks, but they
  mostly help reversal rather than continuation.

## Stock Regime Map

See [reports/stock_regime.md](./reports/stock_regime.md) for the stock-level
regime tilts. The useful pattern is not "buy everything in the strong state";
it is "know which names actually change behavior by regime."

- `ADANIENT`, `VOLTAS`, `CHENNPETRO`, `SUZLON`, and `WOCKPHARMA` are among the
  strongest 5-day positive tilts in risk-on / high-vol / bull regimes.
- `HINDZINC`, `TATASTEEL`, `BALRAMCHIN`, `GLENMARK`, and `IOC` are among the
  clearest negative tilts in the opposite states.
- Gap shocks are asymmetric at the stock level too: names like `ADANIENT`,
  `GLENMARK`, `RPOWER`, `JUBLPHARMA`, and `NCC` benefit from up-gap shocks,
  while `TATASTEEL`, `IOC`, `YESBANK`, and `TRIVENI` often show the opposite
  tilt.
- This stock map is a context layer for the selector, not a stand-alone
  trading rule.

## Meta Selector

See [reports/meta_selector_design.md](./reports/meta_selector_design.md) for
the initial selector framing and abstention rules.

Primary metrics:

- `trade_count`
- `win_rate`
- `mean_return_pct`
- `median_return_pct`
- `max_drawdown_pct`
- `sharpe_like_score`
- `cagr`
- `turnover`
- `capacity_estimate`

Selector metrics:

- `precision`
- `recall`
- `coverage`
- `calibration_error`
- `abstention_rate`

## Selector Gate

See [reports/selector_gate.md](./reports/selector_gate.md) for the first
abstaining gate prototype. The current strict policy is intentionally sparse:

- `strict` selects only when at least three regime dimensions agree and the
  train-set cells clear high mean-return, win-rate, t-stat, and sample-size
  thresholds.
- On the 5-day chronological holdout, the gate reached 54.3% precision with
  13.5% coverage and 6.735 bps mean portfolio return.
- The combined always-on baseline on the same holdout was 5.647 bps, so the
  gate still clears the simple baseline while staying selective.

## Walk-Forward Validation

See [reports/selector_walk_forward.md](./reports/selector_walk_forward.md) for
the leakage-controlled walk-forward, purged, and embargoed validation of the
selector gate.

- The walk-forward layer now refits the same candidate scan on each fold and
  records `abstain` when no policy survives the scan.
- The walk-forward, purged, and embargoed splits still show negative lift
  versus the combined always-on baseline.
- Average lift stays negative even after the adaptive scan:
  walk-forward `-21.136` bps, purged `-15.988` bps, and embargo
  `-21.070` bps.
- The gate therefore remains research-only.

## Done Conditions

- Every family is evaluated out of sample with walk-forward and regime holds.
- Transaction-cost stress is explicit.
- The selector must beat naive always-on and always-flat baselines out of sample.
- A review pack exists before any deployment discussion.

## Status

Draft. The project is scoped, the metrics panel is explicit, and the first-pass
screening readout, regime-conditioned scan, stock-level regime map, sparse
selector gate prototype, and leakage-controlled walk-forward validation all
exist. No deployment claim is made yet. The gate still needs positive
out-of-sample lift before anything is promoted.
