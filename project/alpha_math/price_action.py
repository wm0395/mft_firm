from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from project.alpha_math.ohlcv import (
    SeriesOrFrame,
    average_true_range,
    bollinger_bands,
)


@dataclass(frozen=True)
class PivotLevels:
    pivot: SeriesOrFrame
    resistance_1: SeriesOrFrame
    resistance_2: SeriesOrFrame
    resistance_3: SeriesOrFrame
    support_1: SeriesOrFrame
    support_2: SeriesOrFrame
    support_3: SeriesOrFrame


@dataclass(frozen=True)
class ParabolicSARResult:
    sar: SeriesOrFrame
    trend: SeriesOrFrame
    acceleration_factor: SeriesOrFrame


@dataclass(frozen=True)
class ChandelierExitResult:
    long_stop: SeriesOrFrame
    short_stop: SeriesOrFrame


@dataclass(frozen=True)
class OpeningRangeBreakoutResult:
    opening_high: SeriesOrFrame
    opening_low: SeriesOrFrame
    long_breakout: SeriesOrFrame
    short_breakout: SeriesOrFrame


@dataclass(frozen=True)
class _SarState:
    sar_value: float
    extreme_point: float
    acceleration: float
    uptrend: bool


def bollinger_bandwidth(
    close: SeriesOrFrame,
    period: int = 20,
    stddevs: float = 2.0,
) -> SeriesOrFrame:
    bands = bollinger_bands(close, period=period, stddevs=stddevs)
    spread = bands.upper - bands.lower
    middle = bands.middle.replace(0.0, np.nan)
    return spread.div(middle)


def bollinger_percent_b(
    close: SeriesOrFrame,
    period: int = 20,
    stddevs: float = 2.0,
) -> SeriesOrFrame:
    bands = bollinger_bands(close, period=period, stddevs=stddevs)
    spread = bands.upper - bands.lower
    percent_b = (close - bands.lower).div(spread.replace(0.0, np.nan))
    return percent_b.where(~spread.eq(0.0), 0.5)


def bollinger_squeeze(
    close: SeriesOrFrame,
    period: int = 20,
    stddevs: float = 2.0,
    lookback: int = 125,
) -> SeriesOrFrame:
    bandwidth = bollinger_bandwidth(close, period=period, stddevs=stddevs)
    squeeze_floor = bandwidth.rolling(lookback, min_periods=lookback).min()
    return bandwidth <= squeeze_floor


def atr_position_size(
    capital_at_risk: float,
    atr: SeriesOrFrame,
    risk_fraction: float = 0.01,
    stop_multiple: float = 2.0,
) -> SeriesOrFrame:
    risk_budget = capital_at_risk * risk_fraction
    stop_distance = (atr * stop_multiple).replace(0.0, np.nan)
    return risk_budget / stop_distance


def pivot_points(
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    close: SeriesOrFrame,
) -> PivotLevels:
    prior_high = high.shift(1)
    prior_low = low.shift(1)
    prior_close = close.shift(1)
    pivot = (prior_high + prior_low + prior_close) / 3.0
    range_ = prior_high - prior_low
    return PivotLevels(
        pivot=pivot,
        resistance_1=2.0 * pivot - prior_low,
        resistance_2=pivot + range_,
        resistance_3=prior_high + 2.0 * (pivot - prior_low),
        support_1=2.0 * pivot - prior_high,
        support_2=pivot - range_,
        support_3=prior_low - 2.0 * (prior_high - pivot),
    )


def chandelier_exit(
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    close: SeriesOrFrame,
    period: int = 22,
    multiple: float = 3.0,
) -> ChandelierExitResult:
    atr = average_true_range(high, low, close, period=period)
    highest = high.rolling(period, min_periods=period).max()
    lowest = low.rolling(period, min_periods=period).min()
    return ChandelierExitResult(
        long_stop=highest - (atr * multiple),
        short_stop=lowest + (atr * multiple),
    )


def parabolic_sar(
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    close: SeriesOrFrame,
    step: float = 0.02,
    max_step: float = 0.2,
) -> ParabolicSARResult:
    if isinstance(high, pd.Series):
        return _parabolic_sar_series(high, low, close, step, max_step)
    sar = pd.DataFrame(index=high.index, columns=high.columns, dtype=float)
    trend = pd.DataFrame(index=high.index, columns=high.columns, dtype=float)
    af = pd.DataFrame(index=high.index, columns=high.columns, dtype=float)
    for column in high.columns:
        result = _parabolic_sar_series(
            high[column],
            low[column],
            close[column],
            step,
            max_step,
        )
        sar[column] = result.sar
        trend[column] = result.trend
        af[column] = result.acceleration_factor
    return ParabolicSARResult(sar=sar, trend=trend, acceleration_factor=af)


def opening_range_breakout(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    session: pd.Series,
    bars: int = 3,
) -> OpeningRangeBreakoutResult:
    opening_high, opening_low, ready = _opening_range_levels(high, low, session, bars)
    long_breakout = ready & close.gt(opening_high)
    short_breakout = ready & close.lt(opening_low)
    return OpeningRangeBreakoutResult(
        opening_high=opening_high,
        opening_low=opening_low,
        long_breakout=long_breakout,
        short_breakout=short_breakout,
    )


def _opening_range_levels(
    high: pd.Series,
    low: pd.Series,
    session: pd.Series,
    bars: int,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    grouped = session.astype(str)
    opening_high = high.groupby(grouped).transform(
        lambda values: values.iloc[:bars].max()
    )
    opening_low = low.groupby(grouped).transform(
        lambda values: values.iloc[:bars].min()
    )
    ready = grouped.groupby(grouped).cumcount().ge(bars - 1)
    return opening_high, opening_low, ready


def _parabolic_sar_series(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    step: float,
    max_step: float,
) -> ParabolicSARResult:
    sar = np.full(len(close), np.nan, dtype=float)
    trend = np.full(len(close), np.nan, dtype=float)
    af = np.full(len(close), np.nan, dtype=float)
    if len(close) < 2:
        index = close.index
        return ParabolicSARResult(
            sar=pd.Series(sar, index=index),
            trend=pd.Series(trend, index=index),
            acceleration_factor=pd.Series(af, index=index),
        )
    state = _initial_sar_state(high, low, close, step)
    for index in range(len(close)):
        if index > 0:
            state, sar_value = _next_sar_state(
                state,
                float(high.iloc[index]),
                float(low.iloc[index]),
                float(high.iloc[index - 1]),
                float(low.iloc[index - 1]),
                step,
                max_step,
            )
        else:
            sar_value = state.sar_value
        sar[index] = sar_value
        trend[index] = 1.0 if state.uptrend else -1.0
        af[index] = state.acceleration
    index = close.index
    return ParabolicSARResult(
        sar=pd.Series(sar, index=index),
        trend=pd.Series(trend, index=index),
        acceleration_factor=pd.Series(af, index=index),
    )


def _initial_sar_state(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    step: float,
) -> _SarState:
    uptrend = bool(close.iloc[1] >= close.iloc[0])
    extreme_point = float(high.iloc[:2].max() if uptrend else low.iloc[:2].min())
    sar_value = float(low.iloc[0] if uptrend else high.iloc[0])
    return _SarState(sar_value, extreme_point, step, uptrend)


def _next_sar_state(
    state: _SarState,
    high_value: float,
    low_value: float,
    prev_high: float,
    prev_low: float,
    step: float,
    max_step: float,
) -> tuple[_SarState, float]:
    projected = state.sar_value + state.acceleration * (
        state.extreme_point - state.sar_value
    )
    if state.uptrend:
        return _advance_uptrend(
            state,
            projected,
            high_value,
            low_value,
            prev_low,
            step,
            max_step,
        )
    return _advance_downtrend(
        state,
        projected,
        high_value,
        low_value,
        prev_high,
        step,
        max_step,
    )


def _advance_uptrend(
    state: _SarState,
    sar_value: float,
    high_value: float,
    low_value: float,
    prev_low: float,
    step: float,
    max_step: float,
) -> tuple[_SarState, float]:
    if low_value < sar_value:
        return (
            _SarState(state.extreme_point, low_value, step, False),
            state.extreme_point,
        )
    sar_value = min(sar_value, prev_low, low_value)
    extreme_point = state.extreme_point
    acceleration = state.acceleration
    if high_value > extreme_point:
        extreme_point = high_value
        acceleration = min(max_step, acceleration + step)
    return _SarState(sar_value, extreme_point, acceleration, True), sar_value


def _advance_downtrend(
    state: _SarState,
    sar_value: float,
    high_value: float,
    low_value: float,
    prev_high: float,
    step: float,
    max_step: float,
) -> tuple[_SarState, float]:
    if high_value > sar_value:
        return (
            _SarState(state.extreme_point, high_value, step, True),
            state.extreme_point,
        )
    sar_value = max(sar_value, prev_high, high_value)
    extreme_point = state.extreme_point
    acceleration = state.acceleration
    if low_value < extreme_point:
        extreme_point = low_value
        acceleration = min(max_step, acceleration + step)
    return _SarState(sar_value, extreme_point, acceleration, False), sar_value
