from __future__ import annotations

import numpy as np
import pandas as pd


def rank_cross_sectional(values: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    if isinstance(values, pd.Series):
        return values.rank(method="average", pct=True)
    return values.rank(axis=1, method="average", pct=True)


def zscore_cross_sectional(values: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    if isinstance(values, pd.Series):
        std = values.std(ddof=0)
        if pd.isna(std) or std == 0:
            return values * 0.0
        return (values - values.mean()) / std
    mean = values.mean(axis=1)
    std = values.std(axis=1, ddof=0).replace(0, np.nan)
    return values.sub(mean, axis=0).div(std, axis=0).fillna(0.0)


def robust_zscore(values: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    if isinstance(values, pd.Series):
        return _robust_zscore_series(values)
    return values.apply(_robust_zscore_series, axis=1)


def winsorize(
    values: pd.Series | pd.DataFrame,
    lower: float = 0.05,
    upper: float = 0.95,
) -> pd.Series | pd.DataFrame:
    if isinstance(values, pd.Series):
        return values.clip(values.quantile(lower), values.quantile(upper))
    return values.apply(
        lambda row: row.clip(row.quantile(lower), row.quantile(upper)),
        axis=1,
    )


def signed_power(values: pd.Series | pd.DataFrame, exponent: float) -> pd.Series | pd.DataFrame:
    return np.sign(values) * np.abs(values) ** exponent


def decay_linear(values: pd.Series | pd.DataFrame, window: int) -> pd.Series | pd.DataFrame:
    weights = np.arange(1, window + 1, dtype=float)
    if isinstance(values, pd.Series):
        return values.rolling(window, min_periods=window).apply(
            lambda arr: _weighted_average(arr, weights),
            raw=True,
        )
    return values.apply(
        lambda column: column.rolling(window, min_periods=window).apply(
            lambda arr: _weighted_average(arr, weights),
            raw=True,
        )
    )


def rolling_rank(values: pd.Series | pd.DataFrame, window: int) -> pd.Series | pd.DataFrame:
    if isinstance(values, pd.Series):
        return values.rolling(window, min_periods=window).apply(_last_rank, raw=True)
    return values.apply(lambda column: column.rolling(window, min_periods=window).apply(_last_rank, raw=True))


def rolling_zscore(values: pd.Series | pd.DataFrame, window: int) -> pd.Series | pd.DataFrame:
    if isinstance(values, pd.Series):
        return values.rolling(window, min_periods=window).apply(_last_zscore, raw=True)
    return values.apply(lambda column: column.rolling(window, min_periods=window).apply(_last_zscore, raw=True))


def _robust_zscore_series(values: pd.Series) -> pd.Series:
    median = values.median()
    mad = (values - median).abs().median()
    if pd.isna(mad) or mad == 0:
        return values * 0.0
    return 0.6745 * (values - median) / mad


def _weighted_average(values: np.ndarray, weights: np.ndarray) -> float:
    mask = ~np.isnan(values)
    if not mask.any():
        return float("nan")
    active_weights = weights[mask]
    return float(np.average(values[mask], weights=active_weights))


def _last_rank(values: np.ndarray) -> float:
    valid = values[~np.isnan(values)]
    if valid.size == 0:
        return float("nan")
    last = valid[-1]
    return float(np.mean(valid <= last))


def _last_zscore(values: np.ndarray) -> float:
    valid = values[~np.isnan(values)]
    if valid.size == 0:
        return float("nan")
    std = valid.std(ddof=0)
    if std == 0:
        return 0.0
    return float((valid[-1] - valid.mean()) / std)
