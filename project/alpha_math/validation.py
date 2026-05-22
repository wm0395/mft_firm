from __future__ import annotations

from collections.abc import Mapping, Iterator
import pandas as pd

from project.alpha_math.transforms import rank_cross_sectional


def rolling_ic(signal: pd.DataFrame, forward_returns: pd.DataFrame) -> pd.Series:
    left, right = _align(signal, forward_returns)
    return left.corrwith(right, axis=1)


def rank_ic(signal: pd.DataFrame, forward_returns: pd.DataFrame) -> pd.Series:
    left, right = _align(rank_cross_sectional(signal), rank_cross_sectional(forward_returns))
    return left.corrwith(right, axis=1)


def ic_decay(
    signal: pd.DataFrame,
    forward_returns_by_horizon: Mapping[str | int, pd.DataFrame],
) -> pd.Series:
    results = {
        str(horizon): float(rank_ic(signal, returns).mean())
        for horizon, returns in forward_returns_by_horizon.items()
    }
    return pd.Series(dict(sorted(results.items(), key=lambda item: str(item[0]))))


def walk_forward_split(
    index: pd.Index,
    train_size: int,
    test_size: int,
    step_size: int | None = None,
) -> Iterator[tuple[pd.Index, pd.Index]]:
    step = test_size if step_size is None else step_size
    for start in range(0, len(index) - train_size - test_size + 1, step):
        train = index[start : start + train_size]
        test = index[start + train_size : start + train_size + test_size]
        yield train, test


def purged_time_split(
    index: pd.Index,
    train_size: int,
    test_size: int,
    lookahead: int,
    step_size: int | None = None,
) -> Iterator[tuple[pd.Index, pd.Index]]:
    step = test_size if step_size is None else step_size
    for start in range(0, len(index) - train_size - test_size + 1, step):
        train_end = max(start, start + train_size - lookahead)
        train = index[start:train_end]
        test = index[start + train_size : start + train_size + test_size]
        if len(train) and len(test):
            yield train, test


def embargo_time_split(
    index: pd.Index,
    train_size: int,
    test_size: int,
    embargo: int,
    step_size: int | None = None,
) -> Iterator[tuple[pd.Index, pd.Index]]:
    step = test_size if step_size is None else step_size
    for start in range(0, len(index) - train_size - test_size - embargo + 1, step):
        train = index[start : start + train_size]
        test = index[start + train_size + embargo : start + train_size + embargo + test_size]
        if len(train) and len(test):
            yield train, test


def stability_by_regime(metric: pd.Series, regimes: pd.Series) -> pd.DataFrame:
    aligned_metric, aligned_regimes = metric.align(regimes, join="inner")
    grouped = aligned_metric.groupby(aligned_regimes.fillna("__missing__"))
    return grouped.agg(["count", "mean", "std"])


def stability_by_universe(metric: pd.Series, universes: pd.Series) -> pd.DataFrame:
    return stability_by_regime(metric, universes)


def _align(left: pd.DataFrame, right: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    aligned_left, aligned_right = left.align(right, join="inner", axis=0)
    aligned_left, aligned_right = aligned_left.align(aligned_right, join="inner", axis=1)
    return aligned_left, aligned_right
