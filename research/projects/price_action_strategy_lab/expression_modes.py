from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class ExpressionResult:
    mode: str
    positions: pd.DataFrame
    gross_return: pd.Series
    net_return: pd.Series
    turnover: pd.Series
    active: pd.Series
    reason_code: pd.Series


def cross_sectional_quintile(
    signal: pd.DataFrame,
    forward_returns: pd.DataFrame,
    *,
    active_mask: pd.DataFrame | None = None,
    long_quantile: float = 0.8,
    short_quantile: float = 0.2,
    min_names: int = 5,
    cost_bps: float = 10.0,
    rank_pct: pd.DataFrame | None = None,
) -> ExpressionResult:
    valid = _valid_mask(signal, forward_returns, active_mask)
    ranked = _rank_pct(signal, valid, rank_pct)
    long_mask = ranked.ge(long_quantile) & valid
    short_mask = ranked.le(short_quantile) & valid
    positions = _long_short_positions(long_mask, short_mask)
    active = _active_days(valid, positions, min_names)
    return _expression_result(
        "cross_sectional_quintile",
        positions.where(active, 0.0),
        forward_returns,
        active,
        cost_bps,
    )


def time_series_threshold(
    signal: pd.DataFrame,
    forward_returns: pd.DataFrame,
    *,
    active_mask: pd.DataFrame | None = None,
    long_threshold: float = 0.0,
    short_threshold: float = 0.0,
    min_names: int = 1,
    cost_bps: float = 10.0,
) -> ExpressionResult:
    valid = _valid_mask(signal, forward_returns, active_mask)
    long_mask = signal.gt(long_threshold) & valid
    short_mask = signal.lt(-short_threshold) & valid
    positions = _long_short_positions(long_mask, short_mask)
    active = _active_days(valid, positions, min_names)
    return _expression_result(
        "time_series_threshold",
        positions.where(active, 0.0),
        forward_returns,
        active,
        cost_bps,
    )


def ranked_long_only(
    signal: pd.DataFrame,
    forward_returns: pd.DataFrame,
    *,
    active_mask: pd.DataFrame | None = None,
    long_quantile: float = 0.8,
    min_names: int = 5,
    cost_bps: float = 10.0,
    rank_pct: pd.DataFrame | None = None,
) -> ExpressionResult:
    valid = _valid_mask(signal, forward_returns, active_mask)
    ranked = _rank_pct(signal, valid, rank_pct)
    positions = _long_only_positions(ranked.ge(long_quantile) & valid)
    active = _active_days(valid, positions, min_names)
    return _expression_result(
        "ranked_long_only",
        positions.where(active, 0.0),
        forward_returns,
        active,
        cost_bps,
    )


def _valid_mask(
    signal: pd.DataFrame,
    forward_returns: pd.DataFrame,
    active_mask: pd.DataFrame | None,
) -> pd.DataFrame:
    aligned_returns = forward_returns.reindex_like(signal)
    valid = signal.notna() & aligned_returns.notna()
    if active_mask is None:
        return valid
    return valid & active_mask.reindex_like(signal).fillna(False)


def _rank_pct(
    signal: pd.DataFrame,
    valid: pd.DataFrame,
    rank_pct: pd.DataFrame | None,
) -> pd.DataFrame:
    if rank_pct is None:
        return signal.where(valid).rank(axis=1, pct=True, method="average")
    return rank_pct.reindex_like(signal).where(valid)


def _long_short_positions(
    long_mask: pd.DataFrame,
    short_mask: pd.DataFrame,
) -> pd.DataFrame:
    long_count = long_mask.sum(axis=1).replace(0, float("nan"))
    short_count = short_mask.sum(axis=1).replace(0, float("nan"))
    longs = long_mask.astype(float).div(long_count, axis=0).fillna(0.0)
    shorts = short_mask.astype(float).div(short_count, axis=0).fillna(0.0)
    return longs - shorts


def _long_only_positions(long_mask: pd.DataFrame) -> pd.DataFrame:
    long_count = long_mask.sum(axis=1).replace(0, float("nan"))
    return long_mask.astype(float).div(long_count, axis=0).fillna(0.0)


def _active_days(
    valid: pd.DataFrame,
    positions: pd.DataFrame,
    min_names: int,
) -> pd.Series:
    has_names = valid.sum(axis=1).ge(min_names)
    has_positions = positions.abs().sum(axis=1).gt(0.0)
    return has_names & has_positions


def _expression_result(
    mode: str,
    positions: pd.DataFrame,
    forward_returns: pd.DataFrame,
    active: pd.Series,
    cost_bps: float,
) -> ExpressionResult:
    returns = forward_returns.reindex_like(positions).fillna(0.0)
    gross = (positions * returns).sum(axis=1).where(active)
    turnover = _turnover(positions).where(active)
    net = gross - turnover.mul(2.0 * float(cost_bps) / 10000.0)
    reason = _reason_code(active)
    return ExpressionResult(mode, positions, gross, net, turnover, active, reason)


def _turnover(positions: pd.DataFrame) -> pd.Series:
    return positions.diff().abs().sum(axis=1).mul(0.5).fillna(0.0)


def _reason_code(active: pd.Series) -> pd.Series:
    reason = pd.Series("active", index=active.index, dtype="object")
    return reason.where(active, "inactive")
