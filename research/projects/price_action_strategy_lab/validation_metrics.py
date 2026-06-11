from __future__ import annotations

from math import sqrt

import numpy as np
import pandas as pd


def annualized_sharpe(returns: pd.Series) -> float:
    series = returns.dropna()
    if series.shape[0] < 2:
        return float("nan")
    std = float(series.std(ddof=1))
    if std <= 0.0:
        return float("nan")
    return float(series.mean() / std * sqrt(252.0))


def max_drawdown_bps(returns: pd.Series) -> float:
    series = returns.dropna()
    if series.empty:
        return float("nan")
    equity = series.cumsum()
    drawdown = equity - equity.cummax()
    return float(drawdown.min() * 10_000.0)


def hac_t_stat(returns: pd.Series, lag: int) -> float:
    series = returns.dropna()
    if series.shape[0] < 2:
        return float("nan")
    centered = series.to_numpy(dtype=float) - float(series.mean())
    var = _newey_west_variance(centered, lag)
    if var <= 0.0:
        return float("nan")
    return float(series.mean() / sqrt(var / centered.shape[0]))


def stationary_bootstrap_bounds(
    returns: pd.Series,
    reps: int,
    block_length: int,
    seed: int = 0,
) -> tuple[float, float]:
    series = returns.dropna()
    if series.empty or reps <= 0:
        return float("nan"), float("nan")
    samples = _bootstrap_means(series.to_numpy(dtype=float), reps, block_length, seed)
    low, high = np.quantile(samples, [0.025, 0.975])
    return float(low * 10_000.0), float(high * 10_000.0)


def break_even_cost_bps(gross_mean_bps: float, turnover: float) -> float:
    if turnover <= 0.0:
        return float("inf")
    return float(gross_mean_bps / (2.0 * turnover))


def _bootstrap_means(values: np.ndarray, reps: int, block_length: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    length = max(int(block_length), 1)
    p = 1.0 / length
    samples = np.empty(reps, dtype=float)
    for rep in range(reps):
        samples[rep] = _stationary_sample_mean(values, rng, p)
    return samples


def _stationary_sample_mean(values: np.ndarray, rng: np.random.Generator, p: float) -> float:
    n = values.shape[0]
    sample = np.empty(n, dtype=float)
    index = int(rng.integers(0, n))
    for pos in range(n):
        if pos == 0 or float(rng.random()) < p:
            index = int(rng.integers(0, n))
        else:
            index = (index + 1) % n
        sample[pos] = values[index]
    return float(sample.mean())


def _newey_west_variance(centered: np.ndarray, lag: int) -> float:
    n = centered.shape[0]
    max_lag = min(max(int(lag), 0), n - 1)
    var = float(np.mean(centered * centered))
    for offset in range(1, max_lag + 1):
        weight = 1.0 - offset / (max_lag + 1)
        cov = float(np.mean(centered[offset:] * centered[:-offset]))
        var += 2.0 * weight * cov
    return max(var, 0.0)
