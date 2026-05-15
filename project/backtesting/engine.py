from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from statistics import stdev
from typing import Literal

from project.backtesting.models import BacktestConfig, BacktestResult, BacktestTrade
from project.data.repository import DataRepository


@dataclass(frozen=True)
class _OpenTrade:
    direction: Literal["long", "short"]
    entry_timestamp: str
    entry_price: float
    entry_bar_index: int


class BacktestEngine:
    def __init__(self, repository: DataRepository) -> None:
        self.repository = repository

    def run(
        self,
        hypothesis_id: str,
        asset_symbol: str,
        start_timestamp: datetime,
        end_timestamp: datetime,
        config: BacktestConfig,
    ) -> BacktestResult:
        asset_id = _asset_id(asset_symbol)
        market_data = self.repository.get_market_data(asset_symbol, start_timestamp, end_timestamp)
        if not market_data:
            raise ValueError("No market data found for the specified range.")
        evaluations = self.repository.get_hypothesis_evaluations(
            asset_id=asset_id,
            hypothesis_id=hypothesis_id,
        )
        if not evaluations:
            return _empty_result(hypothesis_id, asset_id)
        trades = _simulate_trades(market_data, evaluations, hypothesis_id, asset_id, config)
        return _result_from_trades(hypothesis_id, asset_id, trades)


def _asset_id(asset_symbol: str) -> str:
    return f"asset:{asset_symbol.upper()}"


def _simulate_trades(
    market_data: list[tuple[object, ...]],
    evaluations: tuple[object, ...],
    hypothesis_id: str,
    asset_id: str,
    config: BacktestConfig,
) -> tuple[BacktestTrade, ...]:
    evaluation_map = _evaluation_map(evaluations)
    trades: list[BacktestTrade] = []
    active_trade: _OpenTrade | None = None
    for bar_index in range(len(market_data) - 1):
        timestamp, _, _, _, _, _ = market_data[bar_index]
        next_timestamp, next_open, _, _, _, _ = market_data[bar_index + 1]
        current_timestamp = _normalize_timestamp(timestamp)
        direction = evaluation_map.get(current_timestamp, "flat")
        if active_trade and _should_exit(active_trade, direction, bar_index, config.exit_horizon):
            exit_price = _apply_slippage(float(next_open), active_trade.direction, config.slippage_bps, True)
            trades.append(
                _close_trade(
                    hypothesis_id,
                    asset_id,
                    active_trade,
                    _timestamp_text(next_timestamp),
                    exit_price,
                    bar_index,
                )
            )
            active_trade = None
        if active_trade is None and direction != "flat":
            entry_price = _apply_slippage(float(next_open), direction, config.slippage_bps, False)
            active_trade = _OpenTrade(direction, _timestamp_text(next_timestamp), entry_price, bar_index + 1)
    return tuple(trades)


def _evaluation_map(evaluations: tuple[object, ...]) -> dict[datetime, str]:
    mapping: dict[datetime, str] = {}
    for evaluation in evaluations:
        mapping[_normalize_timestamp(getattr(evaluation, "timestamp"))] = str(
            getattr(evaluation, "direction")
        )
    return mapping


def _should_exit(
    active_trade: _OpenTrade,
    direction: str,
    bar_index: int,
    exit_horizon: int | None,
) -> bool:
    if direction != "flat" and direction != active_trade.direction:
        return True
    if exit_horizon is None:
        return False
    return bar_index - active_trade.entry_bar_index >= exit_horizon


def _apply_slippage(price: float, direction: Literal["long", "short"], slippage_bps: float, closing: bool) -> float:
    delta = price * (slippage_bps / 10000.0)
    if direction == "long":
        return price - delta if closing else price + delta
    return price + delta if closing else price - delta


def _close_trade(
    hypothesis_id: str,
    asset_id: str,
    active_trade: _OpenTrade,
    exit_timestamp: str,
    exit_price: float,
    bar_index: int,
) -> BacktestTrade:
    pnl_pct = _pnl_pct(active_trade.direction, active_trade.entry_price, exit_price)
    return BacktestTrade(
        trade_id=f"trade:{hypothesis_id}:{active_trade.entry_timestamp}",
        hypothesis_id=hypothesis_id,
        asset_id=asset_id,
        direction=active_trade.direction,
        entry_timestamp=active_trade.entry_timestamp,
        entry_price=active_trade.entry_price,
        exit_timestamp=exit_timestamp,
        exit_price=exit_price,
        pnl=pnl_pct * 10000.0,
        duration=bar_index - active_trade.entry_bar_index,
    )


def _pnl_pct(direction: Literal["long", "short"], entry_price: float, exit_price: float) -> float:
    if direction == "long":
        return (exit_price - entry_price) / entry_price
    return (entry_price - exit_price) / entry_price


def _result_from_trades(
    hypothesis_id: str,
    asset_id: str,
    trades: tuple[BacktestTrade, ...],
) -> BacktestResult:
    pnls = [trade.pnl for trade in trades if trade.pnl is not None]
    if not pnls:
        return _empty_result(hypothesis_id, asset_id)
    total_pnl = sum(pnls)
    mean_pnl = total_pnl / len(pnls)
    volatility = stdev(pnls) if len(pnls) > 1 else 0.0
    return BacktestResult(
        hypothesis_id=hypothesis_id,
        asset_id=asset_id,
        total_trades=len(trades),
        winning_trades=sum(1 for value in pnls if value > 0),
        win_rate=sum(1 for value in pnls if value > 0) / len(pnls),
        total_pnl=total_pnl,
        mean_pnl=mean_pnl,
        max_drawdown=_max_drawdown(pnls),
        sharpe_ratio=mean_pnl / volatility if volatility > 0 else 0.0,
        total_return_pct=(total_pnl / 10000.0) * 100,
    )


def _max_drawdown(pnls: list[float]) -> float:
    equity = 0.0
    peak = 0.0
    max_drawdown = 0.0
    for pnl in pnls:
        equity += pnl
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, peak - equity)
    return max_drawdown


def _empty_result(hypothesis_id: str, asset_id: str) -> BacktestResult:
    return BacktestResult(
        hypothesis_id=hypothesis_id,
        asset_id=asset_id,
        total_trades=0,
        winning_trades=0,
        win_rate=0.0,
        total_pnl=0.0,
        mean_pnl=0.0,
        max_drawdown=0.0,
        sharpe_ratio=0.0,
        total_return_pct=0.0,
    )


def _normalize_timestamp(value: object) -> datetime:
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if not isinstance(value, datetime):
        raise ValueError("timestamp must be datetime-like")
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def _timestamp_text(value: object) -> str:
    return _normalize_timestamp(value).astimezone(UTC).replace(microsecond=0).isoformat()
