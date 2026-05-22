from __future__ import annotations

from collections.abc import Mapping
import numpy as np
import pandas as pd


def equal_weight_ensemble(signals: pd.DataFrame | Mapping[str, pd.Series]) -> pd.Series:
    frame = _frame(signals)
    return frame.mean(axis=1)


def rank_average_ensemble(signals: pd.DataFrame | Mapping[str, pd.Series]) -> pd.Series:
    frame = _frame(signals)
    return frame.rank(axis=1, pct=True).mean(axis=1)


def inverse_correlation_weighting(signals: pd.DataFrame | Mapping[str, pd.Series]) -> pd.Series:
    frame = _frame(signals).fillna(0.0)
    if frame.shape[1] == 1:
        return frame.iloc[:, 0]
    corr = frame.corr().fillna(0.0).abs()
    weights = 1.0 / corr.sum(axis=1).replace(0.0, np.nan)
    weights = weights.fillna(0.0)
    if float(weights.sum()) == 0.0:
        return frame.mean(axis=1)
    weights = weights / weights.sum()
    return frame.mul(weights, axis=1).sum(axis=1)


def orthogonalized_ensemble(signals: pd.DataFrame | Mapping[str, pd.Series]) -> pd.Series:
    frame = _frame(signals).fillna(0.0)
    centered = frame - frame.mean(axis=0)
    if centered.shape[1] == 1:
        return centered.iloc[:, 0]
    q, _ = np.linalg.qr(centered.to_numpy(dtype=float))
    return pd.Series(q.mean(axis=1), index=centered.index)


def _frame(signals: pd.DataFrame | Mapping[str, pd.Series]) -> pd.DataFrame:
    if isinstance(signals, pd.DataFrame):
        return signals
    return pd.DataFrame(signals)
