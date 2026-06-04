# Price Action Meta Pack

## Purpose

Committed review pack for the price-action strategy meta project. It captures
the current scope, the exhaustive inventory, the metric gates, and the first
screening, regime, selector-gate, and walk-forward readouts.

## Canonical Inputs

- `../project.json`
- `../README.md`
- `../research_state.json`
- `../reports/strategy_catalog.md`
- `../reports/strategy_inventory.md`
- `../reports/metrics_framework.md`
- `../reports/screening_results.md`
- `../reports/extra_strategy_screening.md`
- `../reports/regime_analysis.md`
- `../reports/stock_regime.md`
- `../reports/selector_gate.md`
- `../reports/selector_walk_forward.md`
- `../reports/meta_selector_design.md`

## State Snapshot

- Project status: `draft`
- Phase: `cataloging price-action families, stock regime map, selector gate v0, and walk-forward validation`
- Scope: exhaustive price-action family inventory with a regime-gated selector,
  a first-pass daily screen, a regime scan on the top 100 high-vol names from
  each universe, a stock-level regime map, a sparse selector gate prototype,
  and leakage-controlled walk-forward validation
- Metrics: trade quality, cost stress, regime robustness, and selector
  precision
- Research stance: no deployment claim yet
- Screening readout: 1-day trend, breakout, gap, structure, and volume
  families are cost-negative on the high-vol lane; 5-day reversal families are
  the only clear positive pocket after turnover stress.
- Supplemental extra screen: `fisher_transform_reversal_10` is the only
  stable extra winner, with its best pockets in bear / high-vol / up-gap-shock
  states.
- Expanded extra pool: the supplemental screen now also includes
  `supertrend_direction_10`, `parabolic_sar_trend`, `aroon_oscillator_25`,
  `ichimoku_kijun_spread_26`, `kst_momentum_9`,
  `inverse_fisher_rsi_reversal_10`, `mass_index_reversal_25`,
  `support_trendline_position_20`, `volume_profile_position_20`, and
  `choppiness_inverse_14` to widen the first-principles gate search.
- Regime readout: reversal exhaustion is the strongest broad pocket, while
  `keltner_breakout_20` is a weak breakout variant in low-liquidity and
  gap-shock states; `Metals & Mining` and `Capital Goods` are the strongest
  5-day sector pockets in bullish or risk-on states.
- Stock readout: `ADANIENT`, `VOLTAS`, `CHENNPETRO`, `SUZLON`, and
  `WOCKPHARMA` tilt into risk-on / high-vol states, while `HINDZINC`,
  `TATASTEEL`, `BALRAMCHIN`, `GLENMARK`, and `IOC` tilt the other way.
- Gate readout: the strict selector clears the combined always-on baseline on
  the simple 5-day holdout with 54.3% precision, 13.5% coverage, and 6.735 bps
  mean portfolio return, but leakage-controlled walk-forward, purged, and
  embargoed validation still show negative lift.
- Walk-forward readout: the adaptive candidate scan now records `abstain`
  when no policy survives a fold, but the aggregate lift remains negative
  across walk-forward, purged, and embargoed splits.

## Decision

- Keep breakout, trend, gap, reversal, structure, and volume families
  separate.
- Evaluate each family with walk-forward, purged, and embargoed splits.
- Require explicit cost stress before any selector discussion.
- Allow abstention when the regime does not support a high-confidence call.
- Do not promote the selector until the leakage-controlled out-of-sample gate
  passes.
- Treat the first-pass daily screen as evidence, not as a deployment gate.
