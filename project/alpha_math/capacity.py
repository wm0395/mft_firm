from __future__ import annotations

import numpy as np
import pandas as pd


def liquidity_score(
    volume: pd.Series | float,
    turnover: pd.Series | float | None = None,
    open_interest: pd.Series | float | None = None,
) -> pd.Series | float:
    score = _log1p(volume)
    if turnover is not None:
        score = score + 0.5 * _log1p(turnover)
    if open_interest is not None:
        score = score + 0.25 * _log1p(open_interest)
    return score


def capacity_estimate(
    price: pd.Series | float,
    volume: pd.Series | float,
    participation_rate: float,
    turnover: pd.Series | float | None = None,
) -> pd.Series | float:
    estimate = _as_object(price) * _as_object(volume) * participation_rate
    if turnover is not None:
        estimate = estimate * (1.0 + 0.1 * _as_object(turnover))
    return estimate


def turnover_penalty(turnover: pd.Series | float, target_turnover: float) -> pd.Series | float:
    if target_turnover <= 0:
        raise ValueError("target_turnover must be positive")
    return 1.0 / (1.0 + _as_object(turnover) / target_turnover)


def transaction_cost_stress(
    gross_return: pd.Series | float,
    turnover: pd.Series | float,
    cost_bps: float,
) -> pd.Series | float:
    return _as_object(gross_return) - _as_object(turnover) * (cost_bps / 10_000.0)


def participation_rate_limit(volume: pd.Series | float, max_participation_rate: float) -> pd.Series | float:
    if max_participation_rate <= 0:
        raise ValueError("max_participation_rate must be positive")
    return _as_object(volume) * max_participation_rate


def _log1p(value: pd.Series | float) -> pd.Series | float:
    return np.log1p(_as_object(value))


def _as_object(value: pd.Series | float) -> pd.Series | float:
    return value.astype(float) if isinstance(value, pd.Series) else float(value)
