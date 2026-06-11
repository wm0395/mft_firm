from __future__ import annotations

import numpy as np
import pandas as pd

from project.alpha_math.gap_regimes import opening_gap_regime
from project.alpha_math.market_structure import multi_timeframe_confirmation as build_multi_timeframe_confirmation
from project.alpha_math.market_structure import support_resistance_levels
from project.alpha_math.market_structure import support_resistance_trendlines
from project.alpha_math.ohlcv import (
    SeriesOrFrame,
    average_true_range,
    breakout_above,
    breakout_below,
    candle_body,
    candle_range,
    close_location_value,
    ema,
    is_bearish_engulfing,
    is_bullish_engulfing,
    is_doji,
    is_inside_bar,
    is_outside_bar,
    lower_shadow,
    relative_volume,
    upper_shadow,
)
from project.alpha_math.price_action import bollinger_squeeze
from project.alpha_math.price_action import chandelier_exit
from project.alpha_math.price_action import parabolic_sar
from project.alpha_math.trend_regimes import keltner_channels
from project.alpha_math.trend_regimes import supertrend
from research.notebooks.alpha_001.research.alpha101_engine import Alpha101Panel
from research.projects.price_action_strategy_lab.alpha_registry import AlphaSpec
from research.projects.price_action_strategy_lab.alpha_registry import alpha_spec


PATTERN_MODES = (
    "cross_sectional_quintile",
    "time_series_threshold",
    "ranked_long_only",
)
BREAKOUT_TAGS = ("breakout", "price_action")
TREND_TAGS = ("trend", "price_action")
STRUCTURE_TAGS = ("structure", "price_action")
GAP_TAGS = ("gap", "price_action")
CANDLE_TAGS = ("candlestick", "price_action", "reversal")


@alpha_spec(
    name="breakout_20",
    family="breakout_continuation",
    description="Close breakout score.",
    inputs=("close",),
    horizons=(5,),
    expression_modes=PATTERN_MODES,
    tags=BREAKOUT_TAGS,
)
def breakout_20(panel: Alpha101Panel) -> pd.DataFrame:
    return breakout_above(panel.close, 20).astype(float) - breakout_below(
        panel.close,
        20,
    ).astype(float)


@alpha_spec(
    name="keltner_breakout_20",
    family="breakout_continuation",
    description="Keltner channel breakout score.",
    inputs=("high", "low", "close"),
    horizons=(5,),
    expression_modes=PATTERN_MODES,
    tags=BREAKOUT_TAGS,
)
def keltner_breakout_20(panel: Alpha101Panel) -> pd.DataFrame:
    channels = keltner_channels(panel.high, panel.low, panel.close)
    return channels.breakout_above.astype(float) - channels.breakout_below.astype(float)


@alpha_spec(
    name="squeeze_breakout_20",
    family="breakout_continuation",
    description="Breakout after Bollinger squeeze.",
    inputs=("close",),
    horizons=(5,),
    expression_modes=PATTERN_MODES,
    tags=BREAKOUT_TAGS,
)
def squeeze_breakout_20(panel: Alpha101Panel) -> pd.DataFrame:
    squeeze = bollinger_squeeze(panel.close)
    score = breakout_above(panel.close, 20).astype(float) - breakout_below(
        panel.close,
        20,
    ).astype(float)
    return score.where(squeeze, 0.0)


@alpha_spec(
    name="relative_volume_breakout_20",
    family="breakout_continuation",
    description="Breakout score scaled by relative volume.",
    inputs=("close", "volume"),
    horizons=(5,),
    expression_modes=PATTERN_MODES,
    tags=BREAKOUT_TAGS,
)
def relative_volume_breakout_20(panel: Alpha101Panel) -> pd.DataFrame:
    breakout = breakout_above(panel.close, 20).astype(float) - breakout_below(
        panel.close,
        20,
    ).astype(float)
    participation = relative_volume(panel.volume, 20).fillna(1.0)
    return breakout * participation


@alpha_spec(
    name="supertrend_direction_10",
    family="trend_following",
    description="SuperTrend direction score.",
    inputs=("high", "low", "close"),
    horizons=(5,),
    expression_modes=PATTERN_MODES,
    tags=TREND_TAGS,
)
def supertrend_direction_10(panel: Alpha101Panel) -> pd.DataFrame:
    return supertrend(panel.high, panel.low, panel.close).trend_up.astype(float).mul(
        2.0,
    ).sub(1.0)


@alpha_spec(
    name="parabolic_sar_trend",
    family="trend_following",
    description="Parabolic SAR trend score.",
    inputs=("high", "low", "close"),
    horizons=(5,),
    expression_modes=PATTERN_MODES,
    tags=TREND_TAGS,
)
def parabolic_sar_trend(panel: Alpha101Panel) -> pd.DataFrame:
    return parabolic_sar(panel.high, panel.low, panel.close).trend


@alpha_spec(
    name="chandelier_trend",
    family="trend_following",
    description="Chandelier exit trend score.",
    inputs=("high", "low", "close"),
    horizons=(5,),
    expression_modes=PATTERN_MODES,
    tags=TREND_TAGS,
)
def chandelier_trend(panel: Alpha101Panel) -> pd.DataFrame:
    stops = chandelier_exit(panel.high, panel.low, panel.close)
    bullish = panel.close.gt(stops.long_stop).astype(float)
    bearish = panel.close.lt(stops.short_stop).astype(float)
    return bullish - bearish


@alpha_spec(
    name="support_resistance_position_20",
    family="structure_levels",
    description="Support/resistance position score.",
    inputs=("high", "low", "close"),
    horizons=(5,),
    expression_modes=PATTERN_MODES,
    tags=STRUCTURE_TAGS,
)
def support_resistance_position_20(panel: Alpha101Panel) -> pd.DataFrame:
    levels = support_resistance_levels(panel.high, panel.low, panel.close)
    return levels.position.sub(0.5)


@alpha_spec(
    name="support_trendline_position_20",
    family="structure_levels",
    description="Projected support trendline position score.",
    inputs=("high", "low", "close"),
    horizons=(5,),
    expression_modes=PATTERN_MODES,
    tags=STRUCTURE_TAGS,
)
def support_trendline_position_20(panel: Alpha101Panel) -> pd.DataFrame:
    trendlines = support_resistance_trendlines(panel.high, panel.low, lookback=20)
    spread = (trendlines.resistance - trendlines.support).replace(0.0, np.nan)
    return panel.close.sub(trendlines.support).div(spread).sub(0.5)


@alpha_spec(
    name="multi_timeframe_confirmation",
    family="trend_following",
    description="Multi-timeframe confirmation score.",
    inputs=("close",),
    horizons=(5,),
    expression_modes=PATTERN_MODES,
    tags=TREND_TAGS,
)
def multi_timeframe_confirmation(panel: Alpha101Panel) -> pd.DataFrame:
    return build_multi_timeframe_confirmation(panel.close).score


@alpha_spec(
    name="opening_gap_regime_score",
    family="gap_reaction",
    description="Opening gap continuation minus fade score.",
    inputs=("open", "high", "low", "close"),
    horizons=(5,),
    expression_modes=PATTERN_MODES,
    tags=GAP_TAGS,
)
def opening_gap_regime_score(panel: Alpha101Panel) -> pd.DataFrame:
    regime = opening_gap_regime(panel.open, panel.high, panel.low, panel.close)
    return regime.gap_continuation.astype(float) - regime.gap_faded.astype(float)


@alpha_spec(
    name="doji_reversal_score",
    family="reversal_exhaustion",
    description="Doji reversal score.",
    inputs=("open", "high", "low", "close"),
    horizons=(5,),
    expression_modes=PATTERN_MODES,
    tags=CANDLE_TAGS,
)
def doji_reversal_score(panel: Alpha101Panel) -> pd.DataFrame:
    context = _trend_context(
        panel.close.shift(1),
        panel.high.shift(1),
        panel.low.shift(1),
        5,
    )
    strength = is_doji(panel.open, panel.high, panel.low, panel.close).astype(float)
    strength *= 1.0 - _body_ratio(panel.open, panel.high, panel.low, panel.close)
    return strength * (-context)


@alpha_spec(
    name="engulfing_reversal_score",
    family="reversal_exhaustion",
    description="Bullish and bearish engulfing reversal score.",
    inputs=("open", "high", "low", "close"),
    horizons=(5,),
    expression_modes=PATTERN_MODES,
    tags=CANDLE_TAGS,
)
def engulfing_reversal_score(panel: Alpha101Panel) -> pd.DataFrame:
    context = _trend_context(
        panel.close.shift(1),
        panel.high.shift(1),
        panel.low.shift(1),
        5,
    )
    strength = 1.0 - _body_ratio(panel.open, panel.high, panel.low, panel.close)
    bullish = is_bullish_engulfing(
        panel.open,
        panel.high,
        panel.low,
        panel.close,
    ).astype(float)
    bearish = is_bearish_engulfing(
        panel.open,
        panel.high,
        panel.low,
        panel.close,
    ).astype(float)
    long_side = bullish * strength * (-context).clip(lower=0.0)
    short_side = bearish * strength * context.clip(lower=0.0)
    return long_side - short_side


@alpha_spec(
    name="hammer_shooting_star_score",
    family="reversal_exhaustion",
    description="Hammer and shooting-star reversal score.",
    inputs=("open", "high", "low", "close"),
    horizons=(5,),
    expression_modes=PATTERN_MODES,
    tags=CANDLE_TAGS,
)
def hammer_shooting_star_score(panel: Alpha101Panel) -> pd.DataFrame:
    context = _trend_context(
        panel.close.shift(1),
        panel.high.shift(1),
        panel.low.shift(1),
        5,
    )
    body = _body_ratio(panel.open, panel.high, panel.low, panel.close)
    spread = candle_range(panel.high, panel.low).replace(0.0, np.nan)
    lower = lower_shadow(panel.open, panel.low, panel.close).div(spread).fillna(0.0)
    upper = upper_shadow(panel.open, panel.high, panel.close).div(spread).fillna(0.0)
    hammer = lower * (1.0 - body)
    shooting = upper * (1.0 - body)
    long_side = hammer * (-context).clip(lower=0.0)
    short_side = shooting * context.clip(lower=0.0)
    return long_side - short_side


@alpha_spec(
    name="inside_outside_bar_score",
    family="breakout_continuation",
    description="Inside-bar breakout and outside-bar reversal score.",
    inputs=("high", "low", "close"),
    horizons=(5,),
    expression_modes=PATTERN_MODES,
    tags=BREAKOUT_TAGS,
)
def inside_outside_bar_score(panel: Alpha101Panel) -> pd.DataFrame:
    prior_inside = is_inside_bar(panel.high.shift(1), panel.low.shift(1)).astype(float)
    breakout = panel.close.gt(panel.high.shift(1)).astype(float) - panel.close.lt(
        panel.low.shift(1),
    ).astype(float)
    outside = is_outside_bar(panel.high, panel.low).astype(float)
    reversal = (close_location_value(panel.high, panel.low, panel.close) - 0.5) * 2.0
    return (prior_inside * breakout) + (outside * reversal)


@alpha_spec(
    name="piercing_dark_cloud_score",
    family="reversal_exhaustion",
    description="Piercing line and dark cloud cover score.",
    inputs=("open", "high", "low", "close"),
    horizons=(5,),
    expression_modes=PATTERN_MODES,
    tags=CANDLE_TAGS,
)
def piercing_dark_cloud_score(panel: Alpha101Panel) -> pd.DataFrame:
    context = _trend_context(
        panel.close.shift(1),
        panel.high.shift(1),
        panel.low.shift(1),
        5,
    )
    prev_open = panel.open.shift(1)
    prev_close = panel.close.shift(1)
    midpoint = (prev_open + prev_close) / 2.0
    bullish = (
        prev_close.lt(prev_open)
        & panel.open.lt(prev_close)
        & panel.close.gt(midpoint)
        & panel.close.gt(panel.open)
    ).astype(float)
    bearish = (
        prev_close.gt(prev_open)
        & panel.open.gt(prev_close)
        & panel.close.lt(midpoint)
        & panel.close.lt(panel.open)
    ).astype(float)
    long_side = bullish * (-context).clip(lower=0.0)
    short_side = bearish * context.clip(lower=0.0)
    return long_side - short_side


def _trend_context(
    close: SeriesOrFrame,
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    period: int,
) -> SeriesOrFrame:
    atr = average_true_range(high, low, close, period).replace(0.0, np.nan)
    return (close - ema(close, period)).div(atr).fillna(0.0)


def _body_ratio(
    open_: SeriesOrFrame,
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    close: SeriesOrFrame,
) -> SeriesOrFrame:
    spread = candle_range(high, low).replace(0.0, np.nan)
    return candle_body(open_, close).abs().div(spread).fillna(0.0)


BROAD_PRICE_ACTION_ALPHA_SPECS: tuple[AlphaSpec, ...] = (
    breakout_20,
    keltner_breakout_20,
    squeeze_breakout_20,
    relative_volume_breakout_20,
    supertrend_direction_10,
    parabolic_sar_trend,
    chandelier_trend,
    support_resistance_position_20,
    support_trendline_position_20,
    multi_timeframe_confirmation,
    opening_gap_regime_score,
    doji_reversal_score,
    engulfing_reversal_score,
    hammer_shooting_star_score,
    inside_outside_bar_score,
    piercing_dark_cloud_score,
)
