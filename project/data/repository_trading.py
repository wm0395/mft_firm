from __future__ import annotations

import json
from typing import Any, cast

from project.backtesting.models import BacktestResult
from project.common.models import Position, TradeIdea, TradeOutcome
from project.data.db import DuckDBAccess
from project.data.reporting_store import load_backtest_results, load_trade_outcomes, persist_backtest_result
from project.data.row_parsers import build_filters, trade_idea_from_row


class RepositoryTradingMixin:
    _db: DuckDBAccess

    def persist_backtest_result(self, result: BacktestResult) -> None:
        persist_backtest_result(_db(self), result)

    def get_backtest_results(self) -> tuple[BacktestResult, ...]:
        return load_backtest_results(_db(self))

    def persist_trade_idea(self, trade: TradeIdea) -> None:
        _db(self).execute(
            """
            insert into trade_ideas (
                trade_id, asset_id, hypothesis_id, version, direction,
                confidence, signals_snapshot_json, timestamp
            ) values (?, ?, ?, ?, ?, ?, ?, ?)
            on conflict(trade_id) do nothing
            """,
            (
                trade.trade_id,
                trade.asset_id,
                trade.hypothesis_id,
                trade.version,
                trade.direction,
                trade.confidence,
                json.dumps(trade.signals_snapshot, sort_keys=True),
                trade.timestamp,
            ),
        )

    def get_trade_ideas(
        self,
        asset_id: str | None = None,
        hypothesis_id: str | None = None,
        direction: str | None = None,
    ) -> tuple[TradeIdea, ...]:
        where_clause, params = build_filters(
            [
                ("asset_id = ?", asset_id),
                ("hypothesis_id = ?", hypothesis_id),
                ("direction = ?", direction),
            ]
        )
        rows = _db(self).fetch_all(
            f"""
            select trade_id, asset_id, hypothesis_id, version, direction,
                   confidence, signals_snapshot_json, timestamp
            from trade_ideas
            where {where_clause}
            order by timestamp, trade_id
            """,
            params,
        )
        return tuple(trade_idea_from_row(row) for row in rows)

    def get_open_trade_ideas(
        self,
        asset_id: str | None = None,
        hypothesis_id: str | None = None,
        direction: str | None = None,
    ) -> tuple[TradeIdea, ...]:
        where_clause, params = build_filters(
            [
                ("ti.asset_id = ?", asset_id),
                ("ti.hypothesis_id = ?", hypothesis_id),
                ("ti.direction = ?", direction),
            ]
        )
        rows = _db(self).fetch_all(
            f"""
            select ti.trade_id, ti.asset_id, ti.hypothesis_id, ti.version,
                   ti.direction, ti.confidence, ti.signals_snapshot_json, ti.timestamp
            from trade_ideas ti
            left join decisions d on ti.trade_id = d.trade_id
            where d.decision_id is null and {where_clause}
            order by ti.timestamp, ti.trade_id
            """,
            params,
        )
        return tuple(trade_idea_from_row(row) for row in rows)

    def persist_position(self, position: Position) -> None:
        _db(self).execute(
            """
            insert into positions values (?, ?, ?, ?, ?, ?)
            on conflict(position_id) do update set
                exit_price = excluded.exit_price,
                pnl = excluded.pnl,
                status = excluded.status
            """,
            (
                position.position_id,
                position.trade_id,
                position.entry_price,
                position.exit_price,
                position.pnl,
                position.status,
            ),
        )

    def get_positions(
        self,
        asset_id: str | None = None,
        hypothesis_id: str | None = None,
        direction: str | None = None,
        status: str | None = None,
    ) -> tuple[Position, ...]:
        where_clause, params = build_filters(
            [
                ("ti.asset_id = ?", asset_id),
                ("ti.hypothesis_id = ?", hypothesis_id),
                ("ti.direction = ?", direction),
                ("p.status = ?", status),
            ]
        )
        rows = _db(self).fetch_all(
            f"""
            select p.position_id, p.trade_id, p.entry_price, p.exit_price, p.pnl, p.status
            from positions p
            join trade_ideas ti on p.trade_id = ti.trade_id
            where {where_clause}
            order by p.position_id
            """,
            params,
        )
        return tuple(Position(*row) for row in rows)

    def get_trade_outcomes(self) -> tuple[TradeOutcome, ...]:
        return load_trade_outcomes(_db(self))


def _db(repository: Any) -> DuckDBAccess:
    return cast(DuckDBAccess, repository._db)
