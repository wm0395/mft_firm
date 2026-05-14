from __future__ import annotations

import json
from typing import Any, cast

from project.common.models import Signal, TradeIdea
from project.data.db import DuckDBAccess
from project.data.models import SignalEvaluation
from project.data.row_parsers import build_filters, trade_idea_from_row


class RepositorySignalsMixin:
    _db: DuckDBAccess

    def persist_signal(self, signal: Signal) -> None:
        db = _db(self)
        signal_id = f"signal:{signal.asset_id}:{signal.timestamp}:{signal.signal_type}"
        db.execute(
            """
            insert into signals values (?, ?, ?, ?, ?, ?, ?)
            on conflict(signal_id) do nothing
            """,
            (
                signal_id,
                signal.asset_id,
                signal.timestamp,
                signal.signal_type,
                signal.value,
                json.dumps(signal.metadata, sort_keys=True),
                signal.is_persistent,
            ),
        )

    def get_signal_evaluations(self) -> tuple[SignalEvaluation, ...]:
        rows = _db(self).fetch_all(
            """
            select signal_id, hypothesis_id, forward_return_1, forward_return_5,
                   forward_return_20, evaluation_timestamp
            from signal_evaluations
            order by evaluation_timestamp, signal_id
            """,
        )
        return tuple(SignalEvaluation(*row) for row in rows)

    def persist_trade_idea(self, trade: TradeIdea) -> None:
        _db(self).execute(
            """
            insert into trade_ideas values (?, ?, ?, ?, ?, ?, ?)
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
            select trade_id, asset_id, hypothesis_id, version, direction, confidence, signals_snapshot_json
            from trade_ideas
            where {where_clause}
            order by trade_id
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
                   ti.direction, ti.confidence, ti.signals_snapshot_json
            from trade_ideas ti
            left join decisions d on ti.trade_id = d.trade_id
            where d.decision_id is null and {where_clause}
            order by ti.trade_id
            """,
            params,
        )
        return tuple(trade_idea_from_row(row) for row in rows)


def _db(repository: Any) -> DuckDBAccess:
    return cast(DuckDBAccess, repository._db)
