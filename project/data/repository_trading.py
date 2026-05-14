from __future__ import annotations

from typing import Any, cast

from project.backtesting.models import BacktestResult
from project.common.models import Position, TradeOutcome
from project.data.db import DuckDBAccess
from project.data.reporting_store import load_backtest_results, load_trade_outcomes, persist_backtest_result
from project.data.row_parsers import build_filters


class RepositoryTradingMixin:
    _db: DuckDBAccess

    def persist_backtest_result(self, result: BacktestResult) -> None:
        persist_backtest_result(_db(self), result)

    def get_backtest_results(self) -> tuple[BacktestResult, ...]:
        return load_backtest_results(_db(self))

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

    def persist_decision(self, decision: Any) -> None:
        _db(self).execute(
            """
            insert into decisions values (?, ?, ?, ?, ?, ?)
            on conflict(decision_id) do nothing
            """,
            (
                decision.decision_id,
                decision.trade_id,
                decision.action,
                decision.structured_reason,
                decision.notes,
                decision.created_at,
            ),
        )

    def get_decisions(self, trade_id: str | None = None) -> tuple[tuple, ...]:
        where_clause, params = build_filters([("trade_id = ?", trade_id)])
        return tuple(
            _db(self).fetch_all(
                f"""
            select decision_id, trade_id, action, structured_reason, notes, created_at
            from decisions
            where {where_clause}
            order by created_at, decision_id
            """,
                params,
            )
        )

    def get_trade_outcomes(self) -> tuple[TradeOutcome, ...]:
        return load_trade_outcomes(_db(self))


def _db(repository: Any) -> DuckDBAccess:
    return cast(DuckDBAccess, repository._db)
