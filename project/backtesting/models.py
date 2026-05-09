from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

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
