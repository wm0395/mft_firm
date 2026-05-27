from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from project.common.models import Asset, HypothesisDefinition, Position, TradeIdea
from project.data.repository import DataRepository


@dataclass(frozen=True)
class PositionTableRowView:
    position_id: str
    trade_id: str
    asset_symbol: str
    hypothesis_name: str
    direction: str
    status: str
    entry_price: str
    exit_price: str
    pnl: str
    trade_timestamp: str


@dataclass(frozen=True)
class PositionDetailView:
    position_id: str
    trade_id: str
    asset_id: str
    asset_symbol: str
    asset_name: str
    hypothesis_id: str
    hypothesis_name: str
    direction: str
    status: str
    entry_price: float
    exit_price: float | None
    pnl: float | None
    trade_timestamp: str
    signals_snapshot: dict[str, object]


@dataclass(frozen=True)
class PositionsPageView:
    positions: tuple[PositionDetailView, ...]
    open_count: int
    closed_count: int
    realized_pnl: float | None
    debug_payload: dict[str, Any]


def get_positions_page_view(repository: DataRepository) -> PositionsPageView:
    positions = tuple(repository.get_positions())
    assets = tuple(repository.list_assets())
    hypotheses = tuple(repository.get_hypotheses())
    trades = tuple(repository.get_trade_ideas())
    asset_lookup = _asset_lookup(assets)
    hypothesis_lookup = _hypothesis_lookup(hypotheses)
    trade_lookup = _trade_lookup(trades)
    detail_rows = tuple(
        _position_detail(
            position,
            trade_lookup.get(position.trade_id),
            asset_lookup,
            hypothesis_lookup,
        )
        for position in positions
    )
    open_count, closed_count, realized_pnl = _summary(positions)
    return PositionsPageView(
        positions=detail_rows,
        open_count=open_count,
        closed_count=closed_count,
        realized_pnl=realized_pnl,
        debug_payload=_debug_payload(positions, assets, hypotheses, trades),
    )


def _position_detail(
    position: Position,
    trade: TradeIdea | None,
    assets: dict[str, Asset],
    hypotheses: dict[str, HypothesisDefinition],
) -> PositionDetailView:
    asset = assets.get(trade.asset_id) if trade is not None else None
    hypothesis = hypotheses.get(trade.hypothesis_id) if trade is not None else None
    asset_symbol = asset.symbol if asset is not None else ""
    asset_name = asset.name if asset is not None else ""
    hypothesis_id = trade.hypothesis_id if trade is not None else ""
    hypothesis_name = hypothesis.name if hypothesis is not None else ""
    direction = trade.direction if trade is not None else ""
    trade_timestamp = trade.timestamp if trade is not None else ""
    return PositionDetailView(
        position.position_id,
        position.trade_id,
        trade.asset_id if trade is not None else "",
        asset_symbol,
        asset_name,
        hypothesis_id,
        hypothesis_name or hypothesis_id,
        direction,
        position.status,
        position.entry_price,
        position.exit_price,
        position.pnl,
        trade_timestamp,
        dict(trade.signals_snapshot) if trade is not None else {},
    )


def _summary(positions: tuple[Position, ...]) -> tuple[int, int, float | None]:
    open_count = sum(1 for position in positions if position.status == "open")
    closed_count = sum(1 for position in positions if position.status == "closed")
    pnl_values = [
        position.pnl
        for position in positions
        if position.status == "closed" and position.pnl is not None
    ]
    realized_pnl = sum(pnl_values) if pnl_values else None
    return open_count, closed_count, realized_pnl


def _asset_lookup(assets: tuple[Asset, ...]) -> dict[str, Asset]:
    return {asset.asset_id: asset for asset in assets}


def _hypothesis_lookup(
    hypotheses: tuple[HypothesisDefinition, ...],
) -> dict[str, HypothesisDefinition]:
    return {hypothesis.hypothesis_id: hypothesis for hypothesis in hypotheses}


def _trade_lookup(trades: tuple[TradeIdea, ...]) -> dict[str, TradeIdea]:
    return {trade.trade_id: trade for trade in trades}


def _money(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.2f}"


def _debug_payload(
    positions: tuple[Position, ...],
    assets: tuple[Asset, ...],
    hypotheses: tuple[HypothesisDefinition, ...],
    trades: tuple[TradeIdea, ...],
) -> dict[str, Any]:
    return {
        "positions": [position.__dict__ for position in positions],
        "assets": [asset.__dict__ for asset in assets],
        "hypotheses": [hypothesis.__dict__ for hypothesis in hypotheses],
        "trade_ideas": [trade.__dict__ for trade in trades],
    }
