from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


ResearchFamily = Literal["momentum_continuation", "mean_reversion"]


@dataclass(frozen=True)
class ParameterAxis:
    name: str
    values: tuple[Any, ...]


@dataclass(frozen=True)
class ParameterSet:
    strategy_family: ResearchFamily
    parameters: tuple[tuple[str, Any], ...]
    parameter_set_hash: str
    parameter_set_id: str


@dataclass(frozen=True)
class WorkbenchBar:
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class WorkbenchSeries:
    asset_symbol: str
    bars: tuple[WorkbenchBar, ...]


@dataclass(frozen=True)
class ResearchMetrics:
    trade_count: int
    winning_trades: int
    win_rate: float
    total_return_pct: float
    mean_return_pct: float
    median_return_pct: float
    volatility_pct: float
    max_drawdown_pct: float
    sharpe_like_score: float


@dataclass(frozen=True)
class ParameterEvaluation:
    parameter_set: ParameterSet
    trade_returns_pct: tuple[float, ...]
    equity_curve_pct: tuple[float, ...]
    metrics: ResearchMetrics
