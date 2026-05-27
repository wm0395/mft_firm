# Alpha Math Toolkit

Deterministic helper functions for cross-sectional transforms, neutralization,
validation splits, capacity stress, ensemble scoring, and diagnostics.

The toolkit is intentionally explicit:

- pure functions
- no hidden state
- predictable pandas/numpy semantics
- small functions that can be unit tested directly

Use these helpers from research code, not from notebooks as a source of truth.

## OHLCV Math

The `ohlcv` module collects reusable price-action primitives:

- trend and momentum: `ema`, `relative_strength_index`, `macd`,
  `average_directional_index`
- volatility and channels: `true_range`, `average_true_range`,
  `bollinger_bands`, `donchian_channels`
- volume confirmation: `on_balance_volume`, `money_flow_index`,
  `relative_volume`
- bar anatomy and patterns: `typical_price`, `candle_body`,
  `upper_shadow`, `lower_shadow`, `is_doji`
- price-action structure: `is_inside_bar`, `is_outside_bar`,
  `is_bullish_engulfing`, `is_bearish_engulfing`
- breakout geometry: `breakout_above`, `breakout_below`, `channel_position`

## Price Action Strategy Layer

The `price_action` module adds higher-level strategy primitives:

- volatility compression and squeeze: `bollinger_bandwidth`,
  `bollinger_percent_b`, `bollinger_squeeze`
- regime stops and trend followers: `parabolic_sar`, `chandelier_exit`
- pivot-based support and resistance: `pivot_points`
- ATR risk sizing: `atr_position_size`
- session breakout logic: `opening_range_breakout`

## Market Structure Layer

The `market_structure` module adds support/resistance and
regime-confirmation helpers:

- support and resistance projection: `support_resistance_levels`
- rolling support/resistance trendlines: `support_resistance_trendlines`
- failed-breakout detection: `failed_breakout_signal`
- multi-timeframe confirmation: `multi_timeframe_confirmation`
- gap pressure and fill: `gap_pressure`

## Trend Indicator Layer

The `trend_indicators` module adds oscillators and multi-line trend math:

- momentum oscillators: `commodity_channel_index`, `chande_momentum_oscillator`
- range-position oscillator: `aroon`
- Ichimoku structure: `ichimoku_cloud`
- Elder trend power: `elder_ray`
- blended momentum: `know_sure_thing`
- directional oscillators: `vortex_indicator`, `ultimate_oscillator`,
  `williams_r`

## Trend Regime Overlay Layer

The `trend_regimes` module adds channel, trend, chop, and triple-smoothing
regime helpers:

- Keltner Channels: `keltner_channels`
- SuperTrend overlay: `supertrend`
- Choppiness Index: `choppiness_index`
- TRIX oscillator: `trix`

## Cycle Indicator Layer

The `cycle_indicators` module adds cycle filtering and distribution shaping:

- Fisher Transform: `fisher_transform`
- inverse Fisher compression: `inverse_fisher_transform`
- detrended price oscillator: `detrended_price_oscillator`
- Mass Index: `mass_index`

## Volume Flow Layer

The `volume_flow` module adds classic volume-flow math:

- accumulation/distribution: `accumulation_distribution_line`
- Chaikin flow: `chaikin_money_flow`, `chaikin_oscillator`
- force pressure: `force_index`
- ease of movement: `ease_of_movement`
- price-volume trend: `price_volume_trend`

## Volume Profile Layer

The `volume_profile` module adds rolling auction and liquidity overlays:

- point-of-control and value-area projection: `volume_profile_levels`
- profile regime flags: `volume_profile_regime`

## Gap Regime Layer

The `gap_regimes` module adds opening-gap continuation and fill math:

- opening-gap metrics: `opening_gap_metrics`
- opening-gap regime classification: `opening_gap_regime`

## Volatility Estimator Layer

The `volatility_estimators` module adds range-based volatility math:

- close-to-close baseline: `close_to_close_volatility`
- Parkinson range estimator: `parkinson_volatility`
- Garman-Klass estimator: `garman_klass_volatility`
- Rogers-Satchell estimator: `rogers_satchell_volatility`
- Yang-Zhang estimator: `yang_zhang_volatility`
- bundled outputs: `volatility_estimates`

## Volatility Regime Filter Layer

The `regime_filters` module adds volatility and persistence gating:

- variance ratio: `variance_ratio`
- Hurst exponent: `hurst_exponent`
- regime snapshot: `volatility_regime_filters`

## Multi-Timeframe Regime Layer

The `regime_filters` module also adds higher-timeframe confirmation:

- higher-timeframe regime filters: `higher_timeframe_regime_filters`

## Trade Profile Layer

The `trade_profiles` module adds pattern scoring and trade ladders:

- failed-breakout scoring: `failed_breakout_score`
- failed-reversal scoring: `failed_reversal_score`
- hybrid trend/volume composite: `trend_volume_composite`
- hybrid trend/volume score stacks: `hybrid_trend_volume_scores`
- ATR pyramiding and scale-out ladders: `pyramiding_ladder`

## Relative Strength Layer

The `relative_strength` module adds benchmark-relative overlays and divergence:

- relative strength ratio: `relative_strength_ratio`
- relative strength spread: `relative_strength_spread`
- benchmark-relative overlay: `relative_strength_overlay`
- price/momentum/volume divergence: `divergence_scores`
- multi-horizon relative-strength ranking: `multi_horizon_relative_strength_rank`
- higher-order oscillator divergence stack: `higher_order_divergence_scores`

## Breadth and Rotation Layer

The `market_breadth` module adds breadth and rotation overlays:

- market breadth metrics: `market_breadth_metrics`
- relative rotation metrics: `relative_rotation_metrics`

## Breadth Thrust Layer

The `market_breadth` module also adds breadth-thrust composites:

- breadth thrust metrics: `breadth_thrust_metrics`
- breadth thrust composite: `breadth_thrust_composite`
- breadth dispersion metrics: `breadth_dispersion_metrics`
- breadth thrust plus volatility regime: `breadth_thrust_volatility_regime`
- nested-universe breadth normalization: `nested_universe_breadth_metrics`

## Oscillator Regime Layer

The `oscillator_regimes` module adds clustering and orthogonalization:

- oscillator regime clusters: `oscillator_regime_clusters`
- oscillator regime analysis: `oscillator_regime_analysis`
- oscillator orthogonalization: `orthogonalize_oscillators`
- cross-timeframe oscillator cluster persistence:
  `oscillator_cluster_persistence`

## Strategy Families Now Expressible

The point of the math layer is to make these families explicit instead of
re-implementing their formulas in each strategy:

1. Trend following and time-series momentum
2. Donchian and closing-price breakouts
3. Bollinger-style mean reversion and squeeze expansion
4. RSI and MFI exhaustion reversals
5. Candlestick reversal and continuation setups
6. Gap fade and gap continuation setups
7. Support/resistance interaction via channels, pivots, and breakout filters
8. Volume-confirmed continuation and reversal
9. Bollinger squeeze and volatility-compression expansion
10. Parabolic SAR and ATR stop management
11. Opening-range breakout for intraday session structure
12. Support/resistance projection and failed-breakout detection
13. Multi-timeframe confirmation and gap-pressure scoring
14. Aroon, CCI, Ichimoku, Elder Ray, and KST trend-oscillator stacks
15. Chaikin, Force Index, EOM, and price-volume trend flow math
16. Range-based volatility estimation and regime filters
17. Rolling support/resistance trendline projection
18. Rolling volume-profile and liquidity overlays
19. Volatility regime filters and persistence gates
20. Opening-gap continuation and gap-fill regimes
21. Failed-breakout and failed-reversal scoring, trend-volume composites, and
    pyramiding ladders
22. Higher-timeframe regime confirmation and trend gating
23. Hybrid trend/volume score stacks for breakout, pullback, and exhaustion
24. Cross-asset relative-strength overlays and benchmark-relative trend gating
25. Price, momentum, and volume divergence scoring
26. Multi-horizon relative-strength ranking across asset universes
27. Higher-order oscillator and composite-factor divergence stacks
28. Cross-sectional breadth and rotation overlays
29. Relative rotation graph style regime labels
30. Zweig-style breadth thrust composites over sector and asset universes
31. Oscillator regime clustering and factor orthogonalization
32. Breadth dispersion and participation-decay overlays across nested universes
33. Breadth thrust plus volatility-compression regime transitions
34. Cross-timeframe oscillator cluster persistence
35. Nested-universe breadth normalization and expansion factors
36. Directional oscillators and bounded momentum extremes
37. Channel overlays and trend-regime filters
38. Cycle filters and transformed oscillator extremes

## Remaining Research Surface

The current bundle does not exhaust the universe of OHLCV strategy ideas, but
there are no further explicit options called out in this note.
