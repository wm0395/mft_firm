from __future__ import annotations

from project.common.models import Position


def open_position(trade_id: str, entry_price: float) -> Position:
    if entry_price <= 0:
        raise ValueError("entry_price must be positive")
    return Position(
        position_id=f"position:{trade_id}",
        trade_id=trade_id,
        entry_price=entry_price,
        exit_price=None,
        pnl=None,
        status="open",
    )


def close_position(position: Position, exit_price: float) -> Position:
    if position.status != "open":
        raise ValueError("only open positions can be closed")
    return Position(
        position_id=position.position_id,
        trade_id=position.trade_id,
        entry_price=position.entry_price,
        exit_price=exit_price,
        pnl=round(exit_price - position.entry_price, 6),
        status="closed",
    )
