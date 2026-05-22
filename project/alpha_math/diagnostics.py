from __future__ import annotations

from collections.abc import Mapping
import pandas as pd

from project.alpha_math.validation import rank_ic


def alpha_correlation_matrix(alphas: pd.DataFrame) -> pd.DataFrame:
    return alphas.corr().fillna(0.0)


def cluster_alphas(alphas: pd.DataFrame, threshold: float = 0.8) -> tuple[tuple[str, ...], ...]:
    corr = alpha_correlation_matrix(alphas).abs()
    remaining = set(corr.columns)
    clusters = []
    while remaining:
        seed = min(remaining)
        cluster = _component(seed, corr, threshold, remaining)
        clusters.append(tuple(sorted(cluster)))
    return tuple(sorted(clusters, key=lambda item: item[0]))


def duplicate_alpha_detection(alphas: pd.DataFrame, threshold: float = 0.999) -> tuple[tuple[str, ...], ...]:
    return tuple(cluster for cluster in cluster_alphas(alphas, threshold) if len(cluster) > 1)


def alpha_decay_report(
    signal: pd.DataFrame,
    forward_returns_by_horizon: Mapping[str | int, pd.DataFrame],
) -> pd.DataFrame:
    rows = []
    for horizon, returns in forward_returns_by_horizon.items():
        ic_value = float(rank_ic(signal, returns).mean())
        rows.append({"horizon": str(horizon), "ic": ic_value, "abs_ic": abs(ic_value)})
    return pd.DataFrame(rows).sort_values("horizon").reset_index(drop=True)


def failure_window_report(returns: pd.Series, window: int = 20, threshold: float = 0.0) -> pd.DataFrame:
    rolling = returns.rolling(window, min_periods=window).sum()
    rows = []
    for timestamp, value in rolling.items():
        if pd.notna(value) and value <= threshold:
            rows.append({"timestamp": timestamp, "window_return": float(value), "window": window})
    return pd.DataFrame(rows)


def _component(
    seed: str,
    corr: pd.DataFrame,
    threshold: float,
    remaining: set[str],
) -> set[str]:
    stack = [seed]
    cluster = set()
    while stack:
        item = stack.pop()
        if item not in remaining or item in cluster:
            continue
        cluster.add(item)
        neighbors = [
            other
            for other in corr.columns
            if other in remaining and other not in cluster and corr.loc[item, other] >= threshold
        ]
        stack.extend(neighbors)
    remaining.difference_update(cluster)
    return cluster
