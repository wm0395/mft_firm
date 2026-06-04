# Strategy Inventory

This inventory is exhaustive over the repo-native public helpers that support
price-action research. It separates raw primitives from strategy families so
the research loop can ask which components help, which hurt, and which only act
as gates.

## Candlestick And Range Primitives

| helper | role | research usage |
| --- | --- | --- |
| `typical_price` | price anchor | baseline for flow and oscillator inputs |
| `median_price` | price anchor | smoother anchor for structure and trend filters |
| `candle_body` | candle anatomy | reversal and exhaustion scoring |
| `candle_range` | candle anatomy | normalization and volatility scaling |
| `upper_shadow` | candle anatomy | rejection and exhaustion scoring |
| `lower_shadow` | candle anatomy | rejection and exhaustion scoring |
| `close_location_value` | candle anatomy | close-strength and reversal context |
| `gap_up` | gap primitive | opening-gap direction filter |
| `gap_down` | gap primitive | opening-gap direction filter |
| `is_doji` | reversal primitive | indecision and exhaustion context |
| `is_inside_bar` | compression primitive | breakout setup filter |
| `is_outside_bar` | expansion primitive | volatility and reversal context |
| `is_bullish_engulfing` | reversal primitive | bullish reversal setup |
| `is_bearish_engulfing` | reversal primitive | bearish reversal setup |
| `ema` | trend base | used by trend exits and regime filters |
| `true_range` | range base | ATR and volatility context |
| `average_true_range` | volatility base | stop sizing and trend exits |
| `relative_strength_index` | momentum oscillator | overbought/oversold gating |
| `stochastic_oscillator` | momentum oscillator | stretch and reversal context |
| `macd` | momentum/trend hybrid | trend confirmation and momentum divergence |
| `directional_movement_index` | trend strength | directional persistence context |
| `average_directional_index` | trend strength | trend-vs-chop gating |
| `channel_position` | location metric | mean-reversion and breakout context |

## Trend And Breakout Families

| helper | role | research usage |
| --- | --- | --- |
| `breakout_above` | breakout trigger | continuation entry test |
| `breakout_below` | breakout trigger | continuation entry test |
| `donchian_channels` | breakout structure | trend-following and breakout confirmation |
| `bollinger_bands` | compression/expansion | squeeze and mean-reversion tests |
| `bollinger_bandwidth` | compression measure | breakout readiness filter |
| `bollinger_percent_b` | band position | breakout and mean-reversion context |
| `bollinger_squeeze` | compression regime | pre-breakout gate |
| `opening_range_breakout` | session breakout | intraday continuation setup |
| `pivot_points` | structure levels | reaction and breakout reference |
| `chandelier_exit` | trailing exit | trend-following risk control |
| `parabolic_sar` | trailing exit | trend persistence test |
| `keltner_channels` | volatility channel | trend expansion and breakout test |
| `supertrend` | trend regime | trend direction and exit gate |
| `trix` | trend momentum | trend persistence and regime filter |

## Structure And Regime Families

| helper | role | research usage |
| --- | --- | --- |
| `support_resistance_levels` | structure map | reaction and failed-breakout tests |
| `support_resistance_trendlines` | projected structure | channel and trendline reactions |
| `failed_breakout_signal` | breakout failure | reversal and stop-run scoring |
| `multi_timeframe_confirmation` | trend stack | regime confirmation gate |
| `gap_pressure` | opening imbalance | gap-fade and gap-continuation split |
| `opening_gap_metrics` | opening gap panel | gap context and normalization |
| `opening_gap_regime` | opening gap regime | gap continuation vs fade classification |
| `choppiness_index` | regime filter | trend vs chop gating |
| `mass_index` | reversal regime | expansion and reversal precursor |
| `vortex_indicator` | trend direction | trend confirmation filter |
| `commodity_channel_index` | oscillator | stretch and trend context |
| `chande_momentum_oscillator` | oscillator | momentum reversal filter |
| `aroon` | trend age | persistence and late-trend context |
| `ichimoku_cloud` | trend structure | multi-horizon support and regime gate |
| `elder_ray` | trend pressure | trend strength and exhaustion context |
| `know_sure_thing` | trend momentum | directional persistence test |
| `ultimate_oscillator` | momentum composite | multi-horizon momentum confirmation |
| `williams_r` | stretch oscillator | overbought/oversold gate |
| `fisher_transform` | cycle transform | exhaustion and reversal timing |
| `inverse_fisher_transform` | cycle transform | strong reversal or continuation gate |
| `detrended_price_oscillator` | cycle oscillator | mean-reversion and cycle stretch |

## Volume And Flow Families

| helper | role | research usage |
| --- | --- | --- |
| `on_balance_volume` | accumulation proxy | participation confirmation |
| `money_flow_index` | price-volume oscillator | trend and exhaustion context |
| `relative_volume` | participation gauge | breakout quality gate |
| `accumulation_distribution_line` | flow base | volume confirmation core |
| `chaikin_money_flow` | flow confirmation | breakout and trend validation |
| `chaikin_oscillator` | flow momentum | participation acceleration |
| `force_index` | impulse measure | continuation and exhaustion context |
| `ease_of_movement` | volume-efficiency measure | trend quality gate |
| `price_volume_trend` | cumulative flow | participation and drift confirmation |
| `volume_profile_levels` | acceptance map | support, value area, and POC context |
| `volume_profile_regime` | volume regime | acceptance and breakout quality gate |

## Composite Trade Profiles

| helper | role | research usage |
| --- | --- | --- |
| `failed_breakout_score` | composite failure score | breakout-fade candidate |
| `failed_reversal_score` | composite reversal score | end-of-trend reversal candidate |
| `trend_volume_composite` | composite trend score | trend-plus-participation selector |
| `hybrid_trend_volume_scores` | composite signal panel | breakout, pullback, and exhaustion gating |
| `pyramiding_ladder` | risk scaffold | position scaling and exit planning |

## Family Coverage

The current project groups these helpers into the following family tests:

1. Breakout continuation
1. Trend following
1. Gap reaction
1. Reversal exhaustion
1. Structure levels
1. Volume confirmation

That grouping is intentional: the selector should only deploy a family when
its prerequisite primitives and regime filters agree.
