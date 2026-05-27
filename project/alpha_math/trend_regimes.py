from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from project.alpha_math.ohlcv import (
    SeriesOrFrame,
    average_true_range,
    ema,
    true_range,
)


@dataclass(frozen=True)
class KeltnerChannelResult:
    middle: SeriesOrFrame
    upper: SeriesOrFrame
    lower: SeriesOrFrame
    breakout_above: SeriesOrFrame
    breakout_below: SeriesOrFrame


@dataclass(frozen=True)
class SuperTrendResult:
    supertrend: SeriesOrFrame
    upper_band: SeriesOrFrame
    lower_band: SeriesOrFrame
    trend_up: SeriesOrFrame
    bullish: SeriesOrFrame
    bearish: SeriesOrFrame


@dataclass(frozen=True)
class ChoppinessIndexResult:
    index: SeriesOrFrame
    trending: SeriesOrFrame
    choppy: SeriesOrFrame


@dataclass(frozen=True)
class TRIXResult:
    trix: SeriesOrFrame
    signal: SeriesOrFrame
    histogram: SeriesOrFrame
    positive: SeriesOrFrame
    negative: SeriesOrFrame


def keltner_channels(
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    close: SeriesOrFrame,
    ema_period: int = 20,
    atr_period: int = 10,
    multiplier: float = 2.0,
) -> KeltnerChannelResult:
    middle = ema(close, ema_period)
    atr = average_true_range(high, low, close, atr_period)
    upper = middle + (multiplier * atr)
    lower = middle - (multiplier * atr)
    return KeltnerChannelResult(
        middle=middle,
        upper=upper,
        lower=lower,
        breakout_above=close.gt(upper),
        breakout_below=close.lt(lower),
    )


def supertrend(
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    close: SeriesOrFrame,
    atr_period: int = 10,
    multiplier: float = 3.0,
) -> SuperTrendResult:
    if isinstance(high, pd.DataFrame):
        return _supertrend_frame(high, low, close, atr_period, multiplier)
    return _supertrend_series(high, low, close, atr_period, multiplier)


def choppiness_index(
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    close: SeriesOrFrame,
    period: int = 14,
    trending_threshold: float = 38.2,
    choppy_threshold: float = 61.8,
) -> ChoppinessIndexResult:
    if period <= 1:
        raise ValueError("period must be greater than 1")
    price_range = high.rolling(period, min_periods=period).max()
    price_range = price_range - low.rolling(period, min_periods=period).min()
    price_range = price_range.replace(0.0, np.nan)
    tr_sum = true_range(high, low, close).rolling(period, min_periods=period).sum()
    ratio = tr_sum.div(price_range)
    ratio = ratio.where(ratio.gt(0.0))
    index = 100.0 * np.log10(ratio) / np.log10(period)
    return ChoppinessIndexResult(
        index=index,
        trending=index.le(trending_threshold),
        choppy=index.ge(choppy_threshold),
    )


def trix(
    close: SeriesOrFrame,
    period: int = 15,
    signal_period: int = 9,
) -> TRIXResult:
    first = ema(close, period)
    second = ema(first, period)
    third = ema(second, period)
    trix_line = third.pct_change(periods=1, fill_method=None) * 100.0
    signal = ema(trix_line, signal_period)
    histogram = trix_line - signal
    return TRIXResult(
        trix=trix_line,
        signal=signal,
        histogram=histogram,
        positive=trix_line.gt(0.0),
        negative=trix_line.lt(0.0),
    )


def _supertrend_frame(
    high: pd.DataFrame,
    low: pd.DataFrame,
    close: pd.DataFrame,
    atr_period: int,
    multiplier: float,
) -> SuperTrendResult:
    supertrend_values = pd.DataFrame(
        index=close.index,
        columns=close.columns,
        dtype=float,
    )
    upper_band = pd.DataFrame(
        index=close.index,
        columns=close.columns,
        dtype=float,
    )
    lower_band = pd.DataFrame(
        index=close.index,
        columns=close.columns,
        dtype=float,
    )
    trend_up = pd.DataFrame(index=close.index, columns=close.columns, dtype=bool)
    for column in close.columns:
        result = _supertrend_series(
            high[column],
            low[column],
            close[column],
            atr_period,
            multiplier,
        )
        supertrend_values[column] = result.supertrend
        upper_band[column] = result.upper_band
        lower_band[column] = result.lower_band
        trend_up[column] = result.trend_up
    return SuperTrendResult(
        supertrend=supertrend_values,
        upper_band=upper_band,
        lower_band=lower_band,
        trend_up=trend_up,
        bullish=trend_up,
        bearish=~trend_up,
    )


def _supertrend_series(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    atr_period: int,
    multiplier: float,
) -> SuperTrendResult:
    atr = average_true_range(high, low, close, atr_period).replace(0.0, np.nan)
    hl2 = (high + low) / 2.0
    basic_upper = hl2 + (multiplier * atr)
    basic_lower = hl2 - (multiplier * atr)
    upper_band = pd.Series(np.nan, index=close.index, dtype=float)
    lower_band = pd.Series(np.nan, index=close.index, dtype=float)
    supertrend_values = pd.Series(np.nan, index=close.index, dtype=float)
    trend_up = pd.Series(False, index=close.index, dtype=bool)
    valid = np.flatnonzero(atr.notna().to_numpy())
    if valid.size == 0:
        return SuperTrendResult(
            supertrend=supertrend_values,
            upper_band=upper_band,
            lower_band=lower_band,
            trend_up=trend_up,
            bullish=trend_up,
            bearish=~trend_up,
        )
    start = int(valid[0])
    upper_band.iloc[start] = float(basic_upper.iloc[start])
    lower_band.iloc[start] = float(basic_lower.iloc[start])
    supertrend_values.iloc[start] = upper_band.iloc[start]
    for idx in range(start + 1, len(close)):
        basic_upper_value = basic_upper.iloc[idx]
        basic_lower_value = basic_lower.iloc[idx]
        prev_upper = upper_band.iloc[idx - 1]
        prev_lower = lower_band.iloc[idx - 1]
        prev_close = close.iloc[idx - 1]
        if pd.isna(basic_upper_value) or pd.isna(basic_lower_value):
            continue
        upper_band.iloc[idx] = (
            basic_upper_value
            if (
                pd.isna(prev_upper)
                or basic_upper_value < prev_upper
                or prev_close > prev_upper
            )
            else prev_upper
        )
        lower_band.iloc[idx] = (
            basic_lower_value
            if (
                pd.isna(prev_lower)
                or basic_lower_value > prev_lower
                or prev_close < prev_lower
            )
            else prev_lower
        )
        prev_supertrend = supertrend_values.iloc[idx - 1]
        if pd.isna(prev_supertrend) or prev_supertrend == prev_upper:
            trend_is_up = close.iloc[idx] > upper_band.iloc[idx]
        else:
            trend_is_up = close.iloc[idx] >= lower_band.iloc[idx]
        trend_up.iloc[idx] = bool(trend_is_up)
        supertrend_values.iloc[idx] = (
            lower_band.iloc[idx] if trend_is_up else upper_band.iloc[idx]
        )
    return SuperTrendResult(
        supertrend=supertrend_values,
        upper_band=upper_band,
        lower_band=lower_band,
        trend_up=trend_up,
        bullish=trend_up,
        bearish=~trend_up,
    )
