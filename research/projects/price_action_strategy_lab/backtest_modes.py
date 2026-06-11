from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from research.projects.price_action_strategy_lab.costs import CostModel, apply_costs, mean_bps
from research.projects.price_action_strategy_lab.expression_modes import (
    ExpressionResult,
    cross_sectional_quintile,
    ranked_long_only,
    time_series_threshold,
)


@dataclass(frozen=True)
class BacktestConfig:
    name: str
    mode: str
    horizon: int
    cost_model: CostModel
    top_quantile: float = 0.8
    bottom_quantile: float = 0.2
    threshold: float = 0.0
    min_names: int = 1


@dataclass(frozen=True)
class BacktestResult:
    name: str
    mode: str
    horizon: int
    gross_return: pd.Series
    net_return: pd.Series
    turnover: pd.Series
    positions: pd.DataFrame
    active: pd.Series
    reason_code: pd.Series


def run_backtest(
    signal: pd.DataFrame,
    forward_return: pd.DataFrame,
    config: BacktestConfig,
    active_mask: pd.DataFrame | None = None,
    rank_pct: pd.DataFrame | None = None,
) -> BacktestResult:
    expression = _expression(signal, forward_return, config, active_mask, rank_pct)
    costs = apply_costs(expression.gross_return, expression.turnover, config.cost_model)
    return BacktestResult(
        name=config.name,
        mode=config.mode,
        horizon=config.horizon,
        gross_return=costs.gross_return,
        net_return=costs.net_return,
        turnover=costs.turnover,
        positions=expression.positions,
        active=expression.active,
        reason_code=expression.reason_code,
    )


def summarize_backtest(result: BacktestResult) -> dict[str, float | int | str]:
    gross_returns = result.gross_return.dropna()
    net_returns = result.net_return.dropna()
    return {
        "name": result.name,
        "mode": result.mode,
        "horizon": result.horizon,
        "obs": int(net_returns.shape[0]),
        "active_days": int(result.active.sum()),
        "coverage": float(result.active.mean()),
        "gross_mean_bps": mean_bps(result.gross_return),
        "gross_std_bps": _series_std_bps(gross_returns),
        "gross_sharpe_like": _sharpe_like(gross_returns),
        "net_mean_bps": mean_bps(result.net_return),
        "net_std_bps": _series_std_bps(net_returns),
        "net_sharpe_like": _sharpe_like(net_returns),
        "turnover": float(result.turnover.mean()),
        "win_rate": float(net_returns.gt(0.0).mean()) if not net_returns.empty else float("nan"),
        "hit_rate": float(net_returns.gt(0.0).mean()) if not net_returns.empty else float("nan"),
        "max_drawdown_bps": _max_drawdown_bps(net_returns),
    }


def _series_std_bps(series: pd.Series) -> float:
    if series.shape[0] < 2:
        return float("nan")
    return float(series.std(ddof=1) * 10_000.0)


def _sharpe_like(series: pd.Series) -> float:
    if series.shape[0] < 2:
        return float("nan")
    std = float(series.std(ddof=1))
    if std <= 0.0:
        return float("nan")
    return float(series.mean() / std * np.sqrt(252.0))


def _max_drawdown_bps(series: pd.Series) -> float:
    if series.empty:
        return float("nan")
    equity = series.fillna(0.0).cumsum()
    drawdown = equity - equity.cummax()
    return float(drawdown.min() * 10_000.0)


def _expression(
    signal: pd.DataFrame,
    forward_return: pd.DataFrame,
    config: BacktestConfig,
    active_mask: pd.DataFrame | None,
    rank_pct: pd.DataFrame | None,
) -> ExpressionResult:
    if config.mode == "cross_sectional_quintile":
        return cross_sectional_quintile(
            signal,
            forward_return,
            active_mask=active_mask,
            long_quantile=config.top_quantile,
            short_quantile=config.bottom_quantile,
            min_names=config.min_names,
            cost_bps=0.0,
            rank_pct=rank_pct,
        )
    if config.mode == "ranked_long_only":
        return ranked_long_only(
            signal,
            forward_return,
            active_mask=active_mask,
            long_quantile=config.top_quantile,
            min_names=config.min_names,
            cost_bps=0.0,
            rank_pct=rank_pct,
        )
    if config.mode == "time_series_threshold":
        return time_series_threshold(
            signal,
            forward_return,
            active_mask=active_mask,
            long_threshold=config.threshold,
            short_threshold=config.threshold,
            min_names=config.min_names,
            cost_bps=0.0,
        )
    raise ValueError(f"unsupported backtest mode: {config.mode}")
