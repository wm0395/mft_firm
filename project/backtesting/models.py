from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True)
class BacktestConfig:
    slippage_bps: float = 1.0  # Basic slippage in basis points
    position_size: float = 10000.0  # Fixed position size in USD
    exit_horizon: int | None = None  # Exit after N bars if None


@dataclass(frozen=True)
class BacktestTrade:
    trade_id: str
    hypothesis_id: str
    asset_id: str
    direction: Literal["long", "short"]
    entry_timestamp: str
    entry_price: float
    exit_timestamp: str | None = None
    exit_price: float | None = None
    pnl: float | None = None
    duration: int | None = None


@dataclass(frozen=True)
class BacktestResult:
    hypothesis_id: str
    asset_id: str
    total_trades: int
    winning_trades: int
    win_rate: float
    total_pnl: float
    mean_pnl: float
    max_drawdown: float
    sharpe_ratio: float
    total_return_pct: float
    hypothesis_version: int = 1
    strategy_spec_id: str | None = None
    research_run_id: str | None = None
    dataset_snapshot_id: str | None = None
    start_timestamp: str | None = None
    end_timestamp: str | None = None
    parameters: tuple[tuple[str, Any], ...] = ()

    def performance_metrics(self) -> dict[str, float | int]:
        return {
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "win_rate": self.win_rate,
            "total_pnl": self.total_pnl,
            "mean_pnl": self.mean_pnl,
            "max_drawdown": self.max_drawdown,
            "sharpe_ratio": self.sharpe_ratio,
            "total_return_pct": self.total_return_pct,
        }
