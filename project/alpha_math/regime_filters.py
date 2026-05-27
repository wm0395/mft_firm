from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from project.alpha_math.ohlcv import SeriesOrFrame, ema
from project.alpha_math.transforms import rolling_zscore
from project.alpha_math.volatility_estimators import (
    close_to_close_volatility,
    parkinson_volatility,
)


@dataclass(frozen=True)
class RegimeFilters:
    range_volatility: SeriesOrFrame
    close_volatility: SeriesOrFrame
    volatility_ratio: SeriesOrFrame
    volatility_zscore: SeriesOrFrame
    variance_ratio: SeriesOrFrame
    hurst_exponent: SeriesOrFrame
    high_volatility: SeriesOrFrame
    low_volatility: SeriesOrFrame
    expanding_volatility: SeriesOrFrame
    compressing_volatility: SeriesOrFrame
    trending: SeriesOrFrame
    mean_reverting: SeriesOrFrame


@dataclass(frozen=True)
class HigherTimeframeRegimeFilters:
    lower_trend: SeriesOrFrame
    higher_trend: SeriesOrFrame
    lower_trend_zscore: SeriesOrFrame
    higher_trend_zscore: SeriesOrFrame
    alignment_score: SeriesOrFrame
    bullish_regime: SeriesOrFrame
    bearish_regime: SeriesOrFrame
    regime_score: SeriesOrFrame


def volatility_regime_filters(
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    close: SeriesOrFrame,
    vol_window: int = 20,
    baseline_window: int = 120,
    persistence_window: int = 60,
    variance_lag: int = 2,
    high_zscore: float = 1.0,
    low_zscore: float = -1.0,
    trend_threshold: float = 1.05,
    mean_revert_threshold: float = 0.95,
    hurst_trend: float = 0.55,
    hurst_mean: float = 0.45,
) -> RegimeFilters:
    range_vol = parkinson_volatility(high, low, vol_window)
    close_vol = close_to_close_volatility(close, vol_window)
    ratio = range_vol.div(close_vol.replace(0.0, np.nan))
    zscore = rolling_zscore(range_vol, baseline_window)
    ratio_vr = variance_ratio(close, persistence_window, variance_lag)
    hurst = hurst_exponent(close, persistence_window)
    return _build_regime_filters(
        range_vol,
        close_vol,
        ratio,
        zscore,
        ratio_vr,
        hurst,
        high_zscore,
        low_zscore,
        trend_threshold,
        mean_revert_threshold,
        hurst_trend,
        hurst_mean,
    )


def higher_timeframe_regime_filters(
    close: SeriesOrFrame,
    higher_close: SeriesOrFrame,
    lower_fast: int = 20,
    lower_slow: int = 50,
    higher_fast: int = 20,
    higher_slow: int = 50,
    trend_window: int = 60,
    baseline_window: int = 120,
) -> HigherTimeframeRegimeFilters:
    lower_trend = _trend_strength(close, lower_fast, lower_slow, trend_window)
    higher_trend = _trend_strength(
        higher_close,
        higher_fast,
        higher_slow,
        trend_window,
    )
    lower_zscore = rolling_zscore(lower_trend, baseline_window)
    higher_zscore = rolling_zscore(higher_trend, baseline_window)
    alignment_score = np.sign(lower_trend.fillna(0.0)) + np.sign(
        higher_trend.fillna(0.0)
    )
    bullish_regime = lower_trend.gt(0.0) & higher_trend.gt(0.0)
    bearish_regime = lower_trend.lt(0.0) & higher_trend.lt(0.0)
    regime_score = alignment_score + 0.5 * (
        lower_zscore.fillna(0.0) + higher_zscore.fillna(0.0)
    )
    return HigherTimeframeRegimeFilters(
        lower_trend=lower_trend,
        higher_trend=higher_trend,
        lower_trend_zscore=lower_zscore,
        higher_trend_zscore=higher_zscore,
        alignment_score=alignment_score,
        bullish_regime=bullish_regime,
        bearish_regime=bearish_regime,
        regime_score=regime_score,
    )


def variance_ratio(
    values: SeriesOrFrame,
    window: int = 60,
    lag: int = 2,
) -> SeriesOrFrame:
    if lag < 2:
        raise ValueError("lag must be at least 2")
    logged = np.log(values.where(values > 0.0))
    if isinstance(logged, pd.Series):
        return _variance_ratio_series(logged, window, lag)
    return logged.apply(lambda column: _variance_ratio_series(column, window, lag))


def hurst_exponent(values: SeriesOrFrame, window: int = 60) -> SeriesOrFrame:
    logged = np.log(values.where(values > 0.0))
    if isinstance(logged, pd.Series):
        return _hurst_series(logged, window)
    return logged.apply(lambda column: _hurst_series(column, window))


def _variance_ratio_series(
    values: pd.Series,
    window: int,
    lag: int,
) -> pd.Series:
    return values.rolling(window, min_periods=window).apply(
        lambda chunk: _variance_ratio_window(chunk, lag),
        raw=True,
    )


def _variance_ratio_window(window: np.ndarray, lag: int) -> float:
    valid = window[~np.isnan(window)]
    if valid.size <= lag:
        return float("nan")
    returns = np.diff(valid)
    if returns.size < 2:
        return float("nan")
    base_variance = float(np.var(returns, ddof=0))
    if base_variance == 0.0:
        return float("nan")
    lagged_returns = valid[lag:] - valid[:-lag]
    lag_variance = float(np.var(lagged_returns, ddof=0))
    if lag_variance == 0.0:
        return float("nan")
    return lag_variance / (lag * base_variance)


def _trend_strength(
    close: SeriesOrFrame,
    fast: int,
    slow: int,
    window: int,
) -> SeriesOrFrame:
    spread = ema(close, fast) - ema(close, slow)
    scale_window = max(window, slow)
    scale = close.rolling(scale_window, min_periods=scale_window).std()
    return spread.div(scale.replace(0.0, np.nan))


def _hurst_series(values: pd.Series, window: int) -> pd.Series:
    return values.rolling(window, min_periods=window).apply(
        _hurst_window,
        raw=True,
    )


def _hurst_window(window: np.ndarray) -> float:
    valid = window[~np.isnan(window)]
    if valid.size < 2:
        return float("nan")
    centered = valid - valid.mean()
    cumulative = np.cumsum(centered)
    range_ = float(cumulative.max() - cumulative.min())
    scale = float(valid.std(ddof=0))
    if scale == 0.0 or range_ <= 0.0:
        return float("nan")
    return float(np.log(range_ / scale) / np.log(valid.size))


def _build_regime_filters(
    range_vol: SeriesOrFrame,
    close_vol: SeriesOrFrame,
    ratio: SeriesOrFrame,
    zscore: SeriesOrFrame,
    variance_ratio_values: SeriesOrFrame,
    hurst: SeriesOrFrame,
    high_zscore: float,
    low_zscore: float,
    trend_threshold: float,
    mean_revert_threshold: float,
    hurst_trend: float,
    hurst_mean: float,
) -> RegimeFilters:
    flags = _regime_flags(
        range_vol,
        zscore,
        variance_ratio_values,
        hurst,
        high_zscore,
        low_zscore,
        trend_threshold,
        mean_revert_threshold,
        hurst_trend,
        hurst_mean,
    )
    return RegimeFilters(
        range_volatility=range_vol,
        close_volatility=close_vol,
        volatility_ratio=ratio,
        volatility_zscore=zscore,
        variance_ratio=variance_ratio_values,
        hurst_exponent=hurst,
        high_volatility=flags[0],
        low_volatility=flags[1],
        expanding_volatility=flags[2],
        compressing_volatility=flags[3],
        trending=flags[4],
        mean_reverting=flags[5],
    )


def _regime_flags(
    range_vol: SeriesOrFrame,
    zscore: SeriesOrFrame,
    variance_ratio_values: SeriesOrFrame,
    hurst: SeriesOrFrame,
    high_zscore: float,
    low_zscore: float,
    trend_threshold: float,
    mean_revert_threshold: float,
    hurst_trend: float,
    hurst_mean: float,
) -> tuple[
    SeriesOrFrame,
    SeriesOrFrame,
    SeriesOrFrame,
    SeriesOrFrame,
    SeriesOrFrame,
    SeriesOrFrame,
]:
    high_volatility = zscore.ge(high_zscore)
    low_volatility = zscore.le(low_zscore)
    expanding = range_vol.gt(range_vol.shift(1))
    compressing = range_vol.lt(range_vol.shift(1))
    trending = variance_ratio_values.ge(trend_threshold) & hurst.ge(hurst_trend)
    mean_reverting = (
        variance_ratio_values.le(mean_revert_threshold) & hurst.le(hurst_mean)
    )
    return (
        high_volatility,
        low_volatility,
        expanding,
        compressing,
        trending,
        mean_reverting,
    )
