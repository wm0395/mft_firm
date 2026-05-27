from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from project.alpha_math.ohlcv import SeriesOrFrame, ema, true_range


@dataclass(frozen=True)
class AroonResult:
    up: SeriesOrFrame
    down: SeriesOrFrame
    oscillator: SeriesOrFrame


@dataclass(frozen=True)
class IchimokuResult:
    tenkan_sen: SeriesOrFrame
    kijun_sen: SeriesOrFrame
    senkou_span_a: SeriesOrFrame
    senkou_span_b: SeriesOrFrame
    chikou_span: SeriesOrFrame


@dataclass(frozen=True)
class ElderRayResult:
    bull_power: SeriesOrFrame
    bear_power: SeriesOrFrame
    ema: SeriesOrFrame


@dataclass(frozen=True)
class KSTResult:
    kst: SeriesOrFrame
    signal: SeriesOrFrame


@dataclass(frozen=True)
class VortexResult:
    positive_vi: SeriesOrFrame
    negative_vi: SeriesOrFrame
    spread: SeriesOrFrame
    bullish: SeriesOrFrame
    bearish: SeriesOrFrame


@dataclass(frozen=True)
class UltimateOscillatorResult:
    oscillator: SeriesOrFrame
    short_ratio: SeriesOrFrame
    medium_ratio: SeriesOrFrame
    long_ratio: SeriesOrFrame
    buying_pressure: SeriesOrFrame
    range: SeriesOrFrame


@dataclass(frozen=True)
class WilliamsRResult:
    percent_r: SeriesOrFrame
    overbought: SeriesOrFrame
    oversold: SeriesOrFrame
    above_centerline: SeriesOrFrame


def commodity_channel_index(
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    close: SeriesOrFrame,
    period: int = 20,
    constant: float = 0.015,
) -> SeriesOrFrame:
    typical_price = (high + low + close) / 3.0
    mean = typical_price.rolling(period, min_periods=period).mean()
    deviation = _mean_deviation(typical_price, period)
    denom = (constant * deviation).replace(0.0, np.nan)
    return (typical_price - mean).div(denom)


def chande_momentum_oscillator(close: SeriesOrFrame, period: int = 14) -> SeriesOrFrame:
    delta = close.diff()
    gains = delta.clip(lower=0.0).rolling(period, min_periods=period).sum()
    losses = (-delta).clip(lower=0.0).rolling(period, min_periods=period).sum()
    denom = (gains + losses).replace(0.0, np.nan)
    return 100.0 * (gains - losses).div(denom)


def aroon(high: SeriesOrFrame, low: SeriesOrFrame, period: int = 25) -> AroonResult:
    up = 100.0 * _rolling_position(high, period, "max") / period
    down = 100.0 * _rolling_position(low, period, "min") / period
    return AroonResult(up=up, down=down, oscillator=up - down)


def ichimoku_cloud(
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    close: SeriesOrFrame,
    tenkan_period: int = 9,
    kijun_period: int = 26,
    senkou_b_period: int = 52,
    displacement: int = 26,
) -> IchimokuResult:
    tenkan = _midpoint(high, low, tenkan_period)
    kijun = _midpoint(high, low, kijun_period)
    span_a = ((tenkan + kijun) / 2.0).shift(displacement)
    span_b = _midpoint(high, low, senkou_b_period).shift(displacement)
    chikou = close.shift(-displacement)
    return IchimokuResult(
        tenkan_sen=tenkan,
        kijun_sen=kijun,
        senkou_span_a=span_a,
        senkou_span_b=span_b,
        chikou_span=chikou,
    )


def elder_ray(
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    close: SeriesOrFrame,
    period: int = 13,
) -> ElderRayResult:
    baseline = ema(close, period)
    return ElderRayResult(
        bull_power=high - baseline,
        bear_power=low - baseline,
        ema=baseline,
    )


def know_sure_thing(
    close: SeriesOrFrame,
    roc_periods: tuple[int, int, int, int] = (10, 15, 20, 30),
    sma_periods: tuple[int, int, int, int] = (10, 10, 10, 15),
    weights: tuple[int, int, int, int] = (1, 2, 3, 4),
    signal_period: int = 9,
) -> KSTResult:
    kst_line = close * 0.0
    for roc_period, sma_period, weight in zip(
        roc_periods,
        sma_periods,
        weights,
        strict=True,
    ):
        roc = rate_of_change(close, roc_period)
        kst_line = kst_line + weight * roc.rolling(
            sma_period,
            min_periods=sma_period,
        ).mean()
    signal = kst_line.rolling(signal_period, min_periods=signal_period).mean()
    return KSTResult(kst=kst_line, signal=signal)


def vortex_indicator(
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    close: SeriesOrFrame,
    period: int = 14,
) -> VortexResult:
    positive_vm = high.sub(low.shift(1)).abs()
    negative_vm = low.sub(high.shift(1)).abs()
    tr_sum = true_range(high, low, close)
    tr_sum = tr_sum.rolling(period, min_periods=period).sum().replace(0.0, np.nan)
    positive_vi = positive_vm.rolling(period, min_periods=period).sum().div(tr_sum)
    negative_vi = negative_vm.rolling(period, min_periods=period).sum().div(tr_sum)
    spread = positive_vi - negative_vi
    return VortexResult(
        positive_vi=positive_vi,
        negative_vi=negative_vi,
        spread=spread,
        bullish=spread.gt(0.0),
        bearish=spread.lt(0.0),
    )


def ultimate_oscillator(
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    close: SeriesOrFrame,
    short_period: int = 7,
    medium_period: int = 14,
    long_period: int = 28,
) -> UltimateOscillatorResult:
    previous_close = close.shift(1)
    high_or_previous_close = high.where(high >= previous_close, previous_close)
    low_or_previous_close = low.where(low <= previous_close, previous_close)
    range_ = high_or_previous_close - low_or_previous_close
    buying_pressure = close - low_or_previous_close
    short_ratio = _pressure_ratio(buying_pressure, range_, short_period)
    medium_ratio = _pressure_ratio(buying_pressure, range_, medium_period)
    long_ratio = _pressure_ratio(buying_pressure, range_, long_period)
    oscillator = 100.0 * (
        (4.0 * short_ratio) + (2.0 * medium_ratio) + long_ratio
    ) / 7.0
    return UltimateOscillatorResult(
        oscillator=oscillator,
        short_ratio=short_ratio,
        medium_ratio=medium_ratio,
        long_ratio=long_ratio,
        buying_pressure=buying_pressure,
        range=range_,
    )


def williams_r(
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    close: SeriesOrFrame,
    period: int = 14,
    overbought_level: float = -20.0,
    oversold_level: float = -80.0,
    centerline_level: float = -50.0,
) -> WilliamsRResult:
    highest_high = high.rolling(period, min_periods=period).max()
    lowest_low = low.rolling(period, min_periods=period).min()
    price_range = (highest_high - lowest_low).replace(0.0, np.nan)
    percent_r = -100.0 * (highest_high - close).div(price_range)
    return WilliamsRResult(
        percent_r=percent_r,
        overbought=percent_r.ge(overbought_level),
        oversold=percent_r.le(oversold_level),
        above_centerline=percent_r.ge(centerline_level),
    )


def _midpoint(high: SeriesOrFrame, low: SeriesOrFrame, period: int) -> SeriesOrFrame:
    upper = high.rolling(period, min_periods=period).max()
    lower = low.rolling(period, min_periods=period).min()
    return (upper + lower) / 2.0


def rate_of_change(values: SeriesOrFrame, period: int) -> SeriesOrFrame:
    return values.pct_change(periods=period, fill_method=None) * 100.0


def _mean_deviation(values: SeriesOrFrame, period: int) -> SeriesOrFrame:
    if isinstance(values, pd.Series):
        return values.rolling(period, min_periods=period).apply(
            _mean_deviation_series,
            raw=True,
        )
    return _mean_deviation_frame(values, period)


def _mean_deviation_series(window: np.ndarray) -> float:
    valid = window[~np.isnan(window)]
    if valid.size == 0:
        return float("nan")
    return float(np.mean(np.abs(valid - valid.mean())))


def _mean_deviation_frame(values: pd.DataFrame, period: int) -> pd.DataFrame:
    return values.apply(
        lambda column: column.rolling(period, min_periods=period).apply(
            _mean_deviation_series,
            raw=True,
        )
    )


def _pressure_ratio(
    numerator: SeriesOrFrame,
    denominator: SeriesOrFrame,
    period: int,
) -> SeriesOrFrame:
    rolling_denominator = denominator.rolling(period, min_periods=period).sum()
    rolling_denominator = rolling_denominator.replace(0.0, np.nan)
    return numerator.rolling(period, min_periods=period).sum().div(rolling_denominator)


def _rolling_position(values: SeriesOrFrame, period: int, mode: str) -> SeriesOrFrame:
    if isinstance(values, pd.Series):
        return values.rolling(period, min_periods=period).apply(
            lambda window: _last_position(window, mode),
            raw=True,
        )
    return values.apply(
        lambda column: column.rolling(period, min_periods=period).apply(
            lambda window: _last_position(window, mode),
            raw=True,
        )
    )


def _last_position(window: np.ndarray, mode: str) -> float:
    valid = window[~np.isnan(window)]
    if valid.size == 0:
        return float("nan")
    index = int(np.argmax(valid) if mode == "max" else np.argmin(valid))
    return float(index + 1)
