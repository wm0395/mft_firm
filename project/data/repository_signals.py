from __future__ import annotations

import json
from typing import Any, cast

from project.common.models import Signal
from project.data.db import DuckDBAccess
from project.data.models import SignalEvaluation
from project.data.row_parsers import build_filters, signal_from_row


class RepositorySignalsMixin:
    _db: DuckDBAccess

    def persist_signal(self, signal: Signal) -> None:
        self.persist_signals((signal,))

    def persist_signals(self, signals: tuple[Signal, ...]) -> None:
        db = _db(self)
        for signal in signals:
            signal_id = f"signal:{signal.asset_id}:{signal.timestamp}:{signal.signal_type}"
            db.execute(
                """
                insert into signals (
                    signal_id, asset_id, timestamp, signal_type, raw_reference,
                    value, metadata_json, is_persistent
                ) values (?, ?, ?, ?, ?, ?, ?, ?)
                on conflict(signal_id) do nothing
                """,
                (
                    signal_id,
                    signal.asset_id,
                    signal.timestamp,
                    signal.signal_type,
                    signal.raw_reference,
                    signal.value,
                    json.dumps(signal.metadata, sort_keys=True),
                    signal.is_persistent,
                ),
            )

    def get_signals(
        self,
        asset_id: str | None = None,
        signal_type: str | None = None,
    ) -> tuple[Signal, ...]:
        where_clause, params = build_filters(
            [("asset_id = ?", asset_id), ("signal_type = ?", signal_type)]
        )
        rows = _db(self).fetch_all(
            f"""
            select signal_id, asset_id, timestamp, signal_type, raw_reference,
                   value, metadata_json, is_persistent
            from signals
            where {where_clause}
            order by timestamp, signal_type, signal_id
            """,
            params,
        )
        return tuple(signal_from_row(row) for row in rows)

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


def _db(repository: Any) -> DuckDBAccess:
    return cast(DuckDBAccess, repository._db)
