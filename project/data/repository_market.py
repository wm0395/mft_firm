from __future__ import annotations

import json
from datetime import datetime
from typing import Any, cast

from project.common.models import RawDataPoint
from project.data.db import DuckDBAccess
from project.data.row_parsers import raw_point_from_row


class RepositoryMarketDataMixin:
    _db: DuckDBAccess

    def ingest_market_data(
        self,
        asset_symbol: str,
        timestamp: datetime,
        open: float,
        high: float,
        low: float,
        close: float,
        volume: float,
    ) -> None:
        db = _db(self)
        market_id = f"market:{asset_symbol}:{timestamp.isoformat()}"
        db.execute(
            """
            insert into raw_market_data values (?, ?, ?, ?, ?, ?, ?, ?)
            on conflict(id) do nothing
            """,
            (market_id, asset_symbol, timestamp, open, high, low, close, volume),
        )

    def get_market_data(
        self,
        asset_symbol: str,
        start_timestamp: datetime | None,
        end_timestamp: datetime | None,
    ) -> tuple[tuple, ...]:
        db = _db(self)
        conditions = ["asset_symbol = ?"]
        params: list[object] = [asset_symbol]
        if start_timestamp is not None:
            conditions.append("timestamp >= ?")
            params.append(start_timestamp)
        if end_timestamp is not None:
            conditions.append("timestamp <= ?")
            params.append(end_timestamp)
        rows = db.fetch_all(
            f"""
            select timestamp, open, high, low, close, volume
            from raw_market_data
            where {" and ".join(conditions)}
            order by timestamp
            """,
            params,
        )
        return tuple(rows)

    def ingest_raw(self, point: RawDataPoint) -> None:
        _db(self).execute(
            """
            insert into raw_data values (?, ?, ?, ?, ?, ?)
            on conflict(asset_id, timestamp, data_type, source) do nothing
            """,
            (
                point.data_id,
                point.asset_id,
                point.timestamp,
                point.data_type,
                json.dumps(point.value, sort_keys=True),
                point.source,
            ),
        )

    def read_raw_values(self, asset_id: str, data_type: str) -> tuple[RawDataPoint, ...]:
        rows = _db(self).fetch_all(
            """
            select data_id, asset_id, timestamp, data_type, value_json, source
            from raw_data
            where asset_id = ? and data_type = ?
            order by timestamp
            """,
            (asset_id, data_type),
        )
        return tuple(raw_point_from_row(row) for row in rows)


def _db(repository: Any) -> DuckDBAccess:
    return cast(DuckDBAccess, repository._db)
