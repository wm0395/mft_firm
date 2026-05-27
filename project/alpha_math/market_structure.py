from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from project.alpha_math.ohlcv import (
    SeriesOrFrame,
    average_true_range,
    ema,
    true_range,
)


@dataclass(frozen=True)
class MarketStructureLevels:
    support: SeriesOrFrame
    resistance: SeriesOrFrame
    midpoint: SeriesOrFrame
    position: SeriesOrFrame


@dataclass(frozen=True)
class BreakoutFailureSignal:
    failed_up: SeriesOrFrame
    failed_down: SeriesOrFrame
    range_expansion: SeriesOrFrame


@dataclass(frozen=True)
class MultiTimeframeConfirmation:
    score: SeriesOrFrame
    bullish: SeriesOrFrame
    bearish: SeriesOrFrame


@dataclass(frozen=True)
class GapPressure:
    gap: SeriesOrFrame
    fill_ratio: SeriesOrFrame
    filled: SeriesOrFrame


@dataclass(frozen=True)
class TrendlineProjection:
    support: SeriesOrFrame
    resistance: SeriesOrFrame


def support_resistance_levels(
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    close: SeriesOrFrame,
    lookback: int = 20,
) -> MarketStructureLevels:
    support = low.rolling(lookback, min_periods=lookback).min().shift(1)
    resistance = high.rolling(lookback, min_periods=lookback).max().shift(1)
    spread = (resistance - support).replace(0.0, np.nan)
    position = (close - support).div(spread)
    position = position.where(~spread.eq(0.0), 0.5)
    return MarketStructureLevels(
        support=support,
        resistance=resistance,
        midpoint=(support + resistance) / 2.0,
        position=position,
    )


def failed_breakout_signal(
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    close: SeriesOrFrame,
    lookback: int = 20,
    atr_period: int = 14,
) -> BreakoutFailureSignal:
    levels = support_resistance_levels(high, low, close, lookback)
    atr = average_true_range(high, low, close, atr_period).replace(0.0, np.nan)
    failed_up = high.gt(levels.resistance) & close.lt(levels.resistance)
    failed_down = low.lt(levels.support) & close.gt(levels.support)
    range_expansion = true_range(high, low, close).div(atr)
    return BreakoutFailureSignal(failed_up, failed_down, range_expansion)


def multi_timeframe_confirmation(
    close: SeriesOrFrame,
    windows: tuple[int, ...] = (5, 20, 50, 200),
) -> MultiTimeframeConfirmation:
    score = close * 0.0
    for window in windows:
        trend = ema(close, window)
        score = score + _timeframe_score(close, trend)
    bullish = score.ge(len(windows))
    bearish = score.le(-len(windows))
    return MultiTimeframeConfirmation(score=score, bullish=bullish, bearish=bearish)


def gap_pressure(
    open_: SeriesOrFrame,
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    close: SeriesOrFrame,
) -> GapPressure:
    previous_close = close.shift(1)
    gap = open_ - previous_close
    gap_size = gap.abs().replace(0.0, np.nan)
    up_fill = (open_ - low).where(gap.gt(0.0), 0.0)
    down_fill = (high - open_).where(gap.lt(0.0), 0.0)
    fill_ratio = (up_fill + down_fill).div(gap_size).clip(0.0, 1.0)
    filled = (gap.gt(0.0) & low.le(previous_close)) | (
        gap.lt(0.0) & high.ge(previous_close)
    )
    return GapPressure(gap=gap, fill_ratio=fill_ratio, filled=filled)


def support_resistance_trendlines(
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    lookback: int = 20,
) -> TrendlineProjection:
    support = low.rolling(lookback, min_periods=lookback).apply(
        _project_trendline,
        raw=True,
    )
    resistance = high.rolling(lookback, min_periods=lookback).apply(
        _project_trendline,
        raw=True,
    )
    return TrendlineProjection(support=support, resistance=resistance)


def _timeframe_score(close: SeriesOrFrame, trend: SeriesOrFrame) -> SeriesOrFrame:
    above = close.gt(trend).astype(float)
    below = close.lt(trend).astype(float)
    rising = trend.gt(trend.shift(1)).astype(float)
    falling = trend.lt(trend.shift(1)).astype(float)
    return above + rising - below - falling


def _project_trendline(window: np.ndarray) -> float:
    y = window.astype(float)
    valid = ~np.isnan(y)
    if valid.sum() < 2:
        return float("nan")
    x = np.arange(len(y), dtype=float)[valid]
    slope, intercept = np.polyfit(x, y[valid], 1)
    return float(slope * x[-1] + intercept)
