from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from project.alpha_math.ohlcv import SeriesOrFrame


@dataclass(frozen=True)
class VolatilityEstimates:
    close_to_close: SeriesOrFrame
    parkinson: SeriesOrFrame
    garman_klass: SeriesOrFrame
    rogers_satchell: SeriesOrFrame
    yang_zhang: SeriesOrFrame


def close_to_close_volatility(
    close: SeriesOrFrame,
    period: int = 20,
    annualization: float = 252.0,
) -> SeriesOrFrame:
    log_returns = np.log(close).diff()
    variance = log_returns.rolling(period, min_periods=period).var()
    return _annualized_volatility(variance, annualization)


def parkinson_volatility(
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    period: int = 20,
    annualization: float = 252.0,
) -> SeriesOrFrame:
    log_range = np.log(high / low)
    variance = log_range.pow(2).rolling(period, min_periods=period).mean()
    variance = variance / (4.0 * np.log(2.0))
    return _annualized_volatility(variance, annualization)


def garman_klass_volatility(
    open_: SeriesOrFrame,
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    close: SeriesOrFrame,
    period: int = 20,
    annualization: float = 252.0,
) -> SeriesOrFrame:
    log_range = np.log(high / low)
    log_open_close = np.log(close / open_)
    coefficient = (2.0 * np.log(2.0)) - 1.0
    variance = (0.5 * log_range.pow(2)) - (
        coefficient * log_open_close.pow(2)
    )
    variance = variance.rolling(period, min_periods=period).mean()
    return _annualized_volatility(variance, annualization)


def rogers_satchell_volatility(
    open_: SeriesOrFrame,
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    close: SeriesOrFrame,
    period: int = 20,
    annualization: float = 252.0,
) -> SeriesOrFrame:
    variance = np.log(high / open_) * np.log(high / close)
    variance = variance + np.log(low / open_) * np.log(low / close)
    variance = variance.rolling(period, min_periods=period).mean()
    return _annualized_volatility(variance, annualization)


def yang_zhang_volatility(
    open_: SeriesOrFrame,
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    close: SeriesOrFrame,
    period: int = 20,
    annualization: float = 252.0,
) -> SeriesOrFrame:
    if period <= 1:
        raise ValueError("period must be greater than 1 for Yang-Zhang volatility")

    open_jump = np.log(open_ / close.shift(1))
    open_close = np.log(close / open_)
    rs_variance = np.log(high / open_) * np.log(high / close)
    rs_variance = rs_variance + np.log(low / open_) * np.log(low / close)
    open_var = open_jump.rolling(period, min_periods=period).var()
    close_var = open_close.rolling(period, min_periods=period).var()
    rs_mean = rs_variance.rolling(period, min_periods=period).mean()
    weight = 0.34 / (1.34 + ((period + 1.0) / (period - 1.0)))
    variance = open_var + (weight * close_var) + ((1.0 - weight) * rs_mean)
    return _annualized_volatility(variance, annualization)


def volatility_estimates(
    open_: SeriesOrFrame,
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    close: SeriesOrFrame,
    period: int = 20,
    annualization: float = 252.0,
) -> VolatilityEstimates:
    return VolatilityEstimates(
        close_to_close=close_to_close_volatility(close, period, annualization),
        parkinson=parkinson_volatility(high, low, period, annualization),
        garman_klass=garman_klass_volatility(
            open_,
            high,
            low,
            close,
            period,
            annualization,
        ),
        rogers_satchell=rogers_satchell_volatility(
            open_,
            high,
            low,
            close,
            period,
            annualization,
        ),
        yang_zhang=yang_zhang_volatility(
            open_,
            high,
            low,
            close,
            period,
            annualization,
        ),
    )


def _annualized_volatility(
    variance: SeriesOrFrame,
    annualization: float,
) -> SeriesOrFrame:
    return np.sqrt(variance.clip(lower=0.0)) * np.sqrt(annualization)
