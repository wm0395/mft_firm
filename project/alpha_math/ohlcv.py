from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
import pandas as pd


SeriesOrFrame: TypeAlias = pd.Series | pd.DataFrame


@dataclass(frozen=True)
class PriceBands:
    middle: SeriesOrFrame
    upper: SeriesOrFrame
    lower: SeriesOrFrame


@dataclass(frozen=True)
class MACDResult:
    macd: SeriesOrFrame
    signal: SeriesOrFrame
    histogram: SeriesOrFrame


@dataclass(frozen=True)
class StochasticResult:
    percent_k: SeriesOrFrame
    percent_d: SeriesOrFrame


@dataclass(frozen=True)
class DirectionalMovement:
    plus_di: SeriesOrFrame
    minus_di: SeriesOrFrame
    adx: SeriesOrFrame


def typical_price(
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    close: SeriesOrFrame,
) -> SeriesOrFrame:
    return (high + low + close) / 3.0


def median_price(high: SeriesOrFrame, low: SeriesOrFrame) -> SeriesOrFrame:
    return (high + low) / 2.0


def candle_body(open_: SeriesOrFrame, close: SeriesOrFrame) -> SeriesOrFrame:
    return close - open_


def candle_range(high: SeriesOrFrame, low: SeriesOrFrame) -> SeriesOrFrame:
    return high - low


def upper_shadow(
    open_: SeriesOrFrame,
    high: SeriesOrFrame,
    close: SeriesOrFrame,
) -> SeriesOrFrame:
    return high - np.maximum(open_, close)


def lower_shadow(
    open_: SeriesOrFrame,
    low: SeriesOrFrame,
    close: SeriesOrFrame,
) -> SeriesOrFrame:
    return np.minimum(open_, close) - low


def close_location_value(
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    close: SeriesOrFrame,
) -> SeriesOrFrame:
    spread = candle_range(high, low).replace(0.0, np.nan)
    return ((close - low) / spread).where(spread.ne(0.0), 0.5)


def gap_up(open_: SeriesOrFrame, close: SeriesOrFrame) -> SeriesOrFrame:
    previous_close = close.shift(1)
    return (open_ - previous_close).clip(lower=0.0)


def gap_down(open_: SeriesOrFrame, close: SeriesOrFrame) -> SeriesOrFrame:
    previous_close = close.shift(1)
    return (previous_close - open_).clip(lower=0.0)


def ema(values: SeriesOrFrame, period: int) -> SeriesOrFrame:
    return values.ewm(span=period, adjust=False, min_periods=period).mean()


def true_range(
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    close: SeriesOrFrame,
) -> SeriesOrFrame:
    current_range = candle_range(high, low)
    previous_close = close.shift(1)
    high_gap = (high - previous_close).abs()
    low_gap = (low - previous_close).abs()
    values = np.fmax.reduce(
        [
            current_range.to_numpy(dtype=float),
            high_gap.to_numpy(dtype=float),
            low_gap.to_numpy(dtype=float),
        ]
    )
    return _wrap_like(current_range, values)


def average_true_range(
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    close: SeriesOrFrame,
    period: int = 14,
) -> SeriesOrFrame:
    return _wilder_smooth(true_range(high, low, close), period)


def relative_strength_index(close: SeriesOrFrame, period: int = 14) -> SeriesOrFrame:
    delta = close.diff()
    gains = delta.clip(lower=0.0)
    losses = (-delta).clip(lower=0.0)
    avg_gain = _wilder_smooth(gains, period)
    avg_loss = _wilder_smooth(losses, period)
    relative_strength = avg_gain.div(avg_loss.replace(0.0, np.nan))
    rsi = 100.0 - (100.0 / (1.0 + relative_strength))
    return rsi.where(~avg_loss.eq(0.0), np.where(avg_gain.gt(0.0), 100.0, 50.0))


def stochastic_oscillator(
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    close: SeriesOrFrame,
    period: int = 14,
    smooth: int = 3,
) -> StochasticResult:
    lowest_low = low.rolling(period, min_periods=period).min()
    highest_high = high.rolling(period, min_periods=period).max()
    spread = (highest_high - lowest_low).replace(0.0, np.nan)
    percent_k = 100.0 * (close - lowest_low).div(spread)
    percent_k = percent_k.where(~spread.eq(0.0), 50.0)
    percent_d = percent_k.rolling(smooth, min_periods=smooth).mean()
    return StochasticResult(percent_k=percent_k, percent_d=percent_d)


def bollinger_bands(
    close: SeriesOrFrame,
    period: int = 20,
    stddevs: float = 2.0,
) -> PriceBands:
    middle = close.rolling(period, min_periods=period).mean()
    spread = close.rolling(period, min_periods=period).std()
    return PriceBands(
        middle=middle,
        upper=middle + (stddevs * spread),
        lower=middle - (stddevs * spread),
    )


def donchian_channels(
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    period: int = 20,
) -> PriceBands:
    upper = high.rolling(period, min_periods=period).max()
    lower = low.rolling(period, min_periods=period).min()
    return PriceBands(middle=(upper + lower) / 2.0, upper=upper, lower=lower)


def macd(
    close: SeriesOrFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> MACDResult:
    macd_line = ema(close, fast) - ema(close, slow)
    signal_line = ema(macd_line, signal)
    return MACDResult(
        macd=macd_line,
        signal=signal_line,
        histogram=macd_line - signal_line,
    )


def directional_movement_index(
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    close: SeriesOrFrame,
    period: int = 14,
) -> DirectionalMovement:
    up_move = high.diff()
    down_move = low.shift(1) - low
    plus_dm = up_move.where((up_move > down_move) & (up_move > 0.0), 0.0)
    minus_dm = down_move.where((down_move > up_move) & (down_move > 0.0), 0.0)
    atr = average_true_range(high, low, close, period).replace(0.0, np.nan)
    plus_di = 100.0 * _wilder_smooth(plus_dm, period).div(atr)
    minus_di = 100.0 * _wilder_smooth(minus_dm, period).div(atr)
    dx = 100.0 * (plus_di - minus_di).abs().div(
        (plus_di + minus_di).replace(0.0, np.nan)
    )
    return DirectionalMovement(
        plus_di=plus_di,
        minus_di=minus_di,
        adx=_wilder_smooth(dx, period),
    )


def average_directional_index(
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    close: SeriesOrFrame,
    period: int = 14,
) -> SeriesOrFrame:
    return directional_movement_index(high, low, close, period).adx


def on_balance_volume(close: SeriesOrFrame, volume: SeriesOrFrame) -> SeriesOrFrame:
    signed_volume = volume * np.sign(close.diff().fillna(0.0))
    return signed_volume.cumsum()


def money_flow_index(
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    close: SeriesOrFrame,
    volume: SeriesOrFrame,
    period: int = 14,
) -> SeriesOrFrame:
    tp = typical_price(high, low, close)
    flow = tp * volume
    positive = flow.where(tp.diff() > 0.0, 0.0)
    negative = flow.where(tp.diff() < 0.0, 0.0).abs()
    pos_sum = positive.rolling(period, min_periods=period).sum()
    neg_sum = negative.rolling(period, min_periods=period).sum()
    money_ratio = pos_sum.div(neg_sum.replace(0.0, np.nan))
    mfi = 100.0 - (100.0 / (1.0 + money_ratio))
    return mfi.where(~neg_sum.eq(0.0), np.where(pos_sum.gt(0.0), 100.0, 50.0))


def relative_volume(volume: SeriesOrFrame, period: int = 20) -> SeriesOrFrame:
    return volume / volume.rolling(period, min_periods=period).mean()


def breakout_above(close: SeriesOrFrame, lookback: int = 20) -> SeriesOrFrame:
    prior_high = close.rolling(lookback, min_periods=lookback).max().shift(1)
    return close > prior_high


def breakout_below(close: SeriesOrFrame, lookback: int = 20) -> SeriesOrFrame:
    prior_low = close.rolling(lookback, min_periods=lookback).min().shift(1)
    return close < prior_low


def channel_position(
    close: SeriesOrFrame,
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    lookback: int = 20,
) -> SeriesOrFrame:
    channels = donchian_channels(high, low, lookback)
    spread = (channels.upper - channels.lower).replace(0.0, np.nan)
    position = (close - channels.lower).div(spread)
    return position.where(~spread.eq(0.0), 0.5)


def is_doji(
    open_: SeriesOrFrame,
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    close: SeriesOrFrame,
    threshold: float = 0.1,
) -> SeriesOrFrame:
    body_ratio = candle_body(open_, close).abs().div(
        candle_range(high, low).replace(0.0, np.nan)
    )
    return body_ratio.fillna(0.0) <= threshold


def is_inside_bar(high: SeriesOrFrame, low: SeriesOrFrame) -> SeriesOrFrame:
    return (high < high.shift(1)) & (low > low.shift(1))


def is_outside_bar(high: SeriesOrFrame, low: SeriesOrFrame) -> SeriesOrFrame:
    return (high > high.shift(1)) & (low < low.shift(1))


def is_bullish_engulfing(
    open_: SeriesOrFrame,
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    close: SeriesOrFrame,
) -> SeriesOrFrame:
    previous_open = open_.shift(1)
    previous_close = close.shift(1)
    current_bullish = close > open_
    previous_bearish = previous_close < previous_open
    engulfing = (open_ <= previous_close) & (close >= previous_open)
    return current_bullish & previous_bearish & engulfing


def is_bearish_engulfing(
    open_: SeriesOrFrame,
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    close: SeriesOrFrame,
) -> SeriesOrFrame:
    previous_open = open_.shift(1)
    previous_close = close.shift(1)
    current_bearish = close < open_
    previous_bullish = previous_close > previous_open
    engulfing = (open_ >= previous_close) & (close <= previous_open)
    return current_bearish & previous_bullish & engulfing


def _wilder_smooth(values: SeriesOrFrame, period: int) -> SeriesOrFrame:
    if isinstance(values, pd.Series):
        return _wilder_smooth_series(values, period)
    return values.apply(lambda column: _wilder_smooth_series(column, period))


def _wilder_smooth_series(values: pd.Series, period: int) -> pd.Series:
    raw = values.to_numpy(dtype=float)
    out = np.full(len(raw), np.nan, dtype=float)
    running_total = 0.0
    valid_count = 0
    smoothed = np.nan
    for index, current in enumerate(raw):
        if np.isnan(current):
            continue
        valid_count += 1
        if valid_count < period:
            running_total += current
            continue
        if valid_count == period:
            running_total += current
            smoothed = running_total / period
            out[index] = smoothed
            continue
        smoothed = ((smoothed * (period - 1)) + current) / period
        out[index] = smoothed
    return pd.Series(out, index=values.index, name=values.name)


def _wrap_like(reference: SeriesOrFrame, values: np.ndarray) -> SeriesOrFrame:
    if isinstance(reference, pd.Series):
        return pd.Series(values, index=reference.index, name=reference.name)
    return pd.DataFrame(values, index=reference.index, columns=reference.columns)
