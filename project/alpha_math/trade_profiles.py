from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from project.alpha_math.market_structure import (
    failed_breakout_signal,
    support_resistance_levels,
)
from project.alpha_math.ohlcv import (
    SeriesOrFrame,
    average_true_range,
    candle_body,
    channel_position,
    close_location_value,
    ema,
    lower_shadow,
    money_flow_index,
    relative_volume,
    upper_shadow,
)
from project.alpha_math.price_action import atr_position_size
from project.alpha_math.volume_flow import chaikin_money_flow, force_index


@dataclass(frozen=True)
class PatternScore:
    score: SeriesOrFrame
    bullish_score: SeriesOrFrame
    bearish_score: SeriesOrFrame


@dataclass(frozen=True)
class TrendVolumeComposite:
    trend_component: SeriesOrFrame
    volume_component: SeriesOrFrame
    flow_component: SeriesOrFrame
    score: SeriesOrFrame
    bullish: SeriesOrFrame
    bearish: SeriesOrFrame


@dataclass(frozen=True)
class HybridTrendVolumeScores:
    breakout_score: SeriesOrFrame
    pullback_score: SeriesOrFrame
    exhaustion_score: SeriesOrFrame
    confirmation_score: SeriesOrFrame
    bullish: SeriesOrFrame
    bearish: SeriesOrFrame


@dataclass(frozen=True)
class PyramidingLadder:
    entry: SeriesOrFrame
    stop_loss: SeriesOrFrame
    add_1: SeriesOrFrame
    add_2: SeriesOrFrame
    scale_out_1: SeriesOrFrame
    scale_out_2: SeriesOrFrame
    initial_size: SeriesOrFrame


def failed_breakout_score(
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    close: SeriesOrFrame,
    volume: SeriesOrFrame,
    lookback: int = 20,
    atr_period: int = 14,
    volume_period: int = 20,
) -> PatternScore:
    levels = support_resistance_levels(high, low, close, lookback)
    signal = failed_breakout_signal(high, low, close, lookback, atr_period)
    position = channel_position(close, levels.support, levels.resistance)
    position = position.fillna(0.5).clip(0.0, 1.0)
    participation = relative_volume(volume, volume_period).fillna(1.0)
    strength = signal.range_expansion.fillna(1.0).clip(lower=1.0) * participation
    bullish = signal.failed_down.astype(float) * strength * position
    bearish = signal.failed_up.astype(float) * strength * (1.0 - position)
    return _pattern_score(bullish, bearish)


def failed_reversal_score(
    open_: SeriesOrFrame,
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    close: SeriesOrFrame,
    volume: SeriesOrFrame,
    trend_period: int = 20,
    volume_period: int = 20,
) -> PatternScore:
    trend_context = close.ge(ema(close, trend_period))
    pattern = _reversal_pattern(open_, high, low, close)
    participation = relative_volume(volume, volume_period).fillna(1.0)
    bullish = trend_context.astype(float) * pattern.clip(lower=0.0) * participation
    bearish = (~trend_context).astype(float) * (-pattern).clip(lower=0.0) * participation
    return _pattern_score(bullish, bearish)


def trend_volume_composite(
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    close: SeriesOrFrame,
    volume: SeriesOrFrame,
    trend_fast: int = 12,
    trend_slow: int = 26,
    flow_period: int = 20,
) -> TrendVolumeComposite:
    atr = average_true_range(high, low, close, flow_period).replace(0.0, np.nan)
    trend_component = (ema(close, trend_fast) - ema(close, trend_slow)).div(atr)
    volume_component = chaikin_money_flow(
        high,
        low,
        close,
        volume,
        flow_period,
    ).cmf.fillna(0.0)
    flow_component = _normalized_component(
        force_index(close, volume, flow_period).smoothed_force_index,
        flow_period,
    )
    score = trend_component.fillna(0.0) + volume_component + (0.5 * flow_component)
    bullish = score.ge(0.5)
    bearish = score.le(-0.5)
    return TrendVolumeComposite(
        trend_component=trend_component,
        volume_component=volume_component,
        flow_component=flow_component,
        score=score,
        bullish=bullish,
        bearish=bearish,
    )


def hybrid_trend_volume_scores(
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    close: SeriesOrFrame,
    volume: SeriesOrFrame,
    trend_fast: int = 12,
    trend_slow: int = 26,
    volume_period: int = 20,
    oscillator_period: int = 14,
) -> HybridTrendVolumeScores:
    atr = average_true_range(high, low, close, volume_period).replace(0.0, np.nan)
    trend = (ema(close, trend_fast) - ema(close, trend_slow)).div(atr)
    volume_pressure = relative_volume(volume, volume_period).fillna(1.0) - 1.0
    flow = chaikin_money_flow(high, low, close, volume, volume_period).cmf.fillna(0.0)
    momentum = (
        money_flow_index(high, low, close, volume, oscillator_period) - 50.0
    ).div(50.0)
    location = close_location_value(high, low, close) - 0.5
    breakout_score = trend.fillna(0.0) + volume_pressure + flow + _normalized_component(
        force_index(close, volume, oscillator_period).smoothed_force_index,
        oscillator_period,
    )
    pullback_score = trend.fillna(0.0) - volume_pressure.abs() + location + 0.5 * flow
    exhaustion_score = momentum - flow - volume_pressure + (0.5 - location)
    confirmation_score = breakout_score + pullback_score - exhaustion_score
    bullish = confirmation_score.ge(0.5)
    bearish = confirmation_score.le(-0.5)
    return HybridTrendVolumeScores(
        breakout_score=breakout_score,
        pullback_score=pullback_score,
        exhaustion_score=exhaustion_score,
        confirmation_score=confirmation_score,
        bullish=bullish,
        bearish=bearish,
    )


def pyramiding_ladder(
    entry: SeriesOrFrame,
    atr: SeriesOrFrame,
    capital_at_risk: float,
    direction: float = 1.0,
    risk_fraction: float = 0.01,
    stop_multiple: float = 2.0,
    add_multiples: tuple[float, float] = (1.0, 2.0),
    scale_out_multiples: tuple[float, float] = (1.5, 3.0),
) -> PyramidingLadder:
    _validate_ladder_inputs(capital_at_risk, direction, risk_fraction, stop_multiple)
    distance = atr * stop_multiple
    return PyramidingLadder(
        entry=entry,
        stop_loss=entry - (direction * distance),
        add_1=entry + (direction * distance * add_multiples[0]),
        add_2=entry + (direction * distance * add_multiples[1]),
        scale_out_1=entry + (direction * distance * scale_out_multiples[0]),
        scale_out_2=entry + (direction * distance * scale_out_multiples[1]),
        initial_size=atr_position_size(
            capital_at_risk,
            atr,
            risk_fraction,
            stop_multiple,
        ),
    )


def _pattern_score(
    bullish_score: SeriesOrFrame,
    bearish_score: SeriesOrFrame,
) -> PatternScore:
    return PatternScore(
        score=bullish_score - bearish_score,
        bullish_score=bullish_score,
        bearish_score=bearish_score,
    )


def _reversal_pattern(
    open_: SeriesOrFrame,
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    close: SeriesOrFrame,
) -> SeriesOrFrame:
    spread = (high - low).replace(0.0, np.nan)
    body = candle_body(open_, close).div(spread).clip(-1.0, 1.0)
    close_bias = (close_location_value(high, low, close) - 0.5) * 2.0
    shadow_bias = (lower_shadow(open_, low, close) - upper_shadow(open_, high, close))
    return 0.5 * body + 0.3 * close_bias + 0.2 * shadow_bias.div(spread)


def _normalized_component(
    component: SeriesOrFrame,
    period: int,
) -> SeriesOrFrame:
    scale = component.abs().rolling(period, min_periods=period).mean()
    return component.div(scale.replace(0.0, np.nan)).fillna(0.0)


def _validate_ladder_inputs(
    capital_at_risk: float,
    direction: float,
    risk_fraction: float,
    stop_multiple: float,
) -> None:
    if capital_at_risk <= 0.0:
        raise ValueError("capital_at_risk must be positive")
    if direction == 0.0:
        raise ValueError("direction must be non-zero")
    if risk_fraction <= 0.0:
        raise ValueError("risk_fraction must be positive")
    if stop_multiple <= 0.0:
        raise ValueError("stop_multiple must be positive")
