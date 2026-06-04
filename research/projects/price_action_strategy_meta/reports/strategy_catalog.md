# Price Action Strategy Catalog

This catalog maps the repo-native price-action primitives to research families.
It is descriptive, not executable.

## Families

| family | primitives | intended edge | common failure mode |
| --- | --- | --- | --- |
| breakout continuation | `breakout_above`, `breakout_below`, `donchian_channels`, `opening_range_breakout`, `bollinger_squeeze`, `bollinger_bandwidth`, `bollinger_percent_b` | expansion after compression or level break | whipsaw, failed breakout, late entry |
| trend following | `parabolic_sar`, `chandelier_exit`, `supertrend`, `keltner_channels`, `trix` | persistent directional move with managed exits | range chop, volatility shock |
| gap reaction | `gap_up`, `gap_down`, `opening_gap_metrics`, `opening_gap_regime`, `gap_pressure` | opening imbalance resolves in a directional way | gap fill, exhaustion, reversal |
| reversal exhaustion | `is_bullish_engulfing`, `is_bearish_engulfing`, `is_doji`, `failed_breakout_signal` | rejection at extremes or false breakout | trend continuation, thin liquidity |
| structure levels | `pivot_points`, `support_resistance_levels`, `support_resistance_trendlines`, `multi_timeframe_confirmation` | reaction around prior structure and horizon alignment | broken structure, regime shift |
| volume confirmation | `volume_profile_regime`, `relative_volume`, `on_balance_volume`, `money_flow_index`, `price_volume_trend`, `accumulation_distribution_line`, `chaikin_money_flow`, `chaikin_oscillator`, `ease_of_movement`, `force_index` | breakout quality improves when participation confirms | hollow move, drift without sponsorship |

## Regime Filters

The selector should only deploy a family when supporting filters agree.

- `choppiness_index`
- `mass_index`
- `vortex_indicator`
- `williams_r`
- `relative_strength_index`
- `commodity_channel_index`
- `elder_ray`
- `ichimoku_cloud`

## Interpretation

- Breakouts should be evaluated separately from reversals.
- Gap setups should be split into continuation and fade tests.
- Trend-following families need cost stress because they can be high turnover.
- Volume confirmation is a gate, not a standalone edge claim.
- Regime filters are selector inputs, not replacements for the family tests.
