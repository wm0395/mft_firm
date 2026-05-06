from __future__ import annotations

import json

from project.common.models import Asset, RawDataPoint, Signal, TradeIdea, utc_now_iso
from project.data.db import DuckDBAccess


class DataRepository:
    def __init__(self, db: DuckDBAccess) -> None:
        self._db = db

    def initialize(self) -> None:
        self._db.initialize_schema()

    def add_asset(self, symbol: str, name: str, sector: str, market: str) -> Asset:
        if not symbol or not name or not market:
            raise ValueError("symbol, name, and market are required")
        asset = Asset(
            asset_id=f"asset:{symbol.upper()}",
            symbol=symbol.upper(),
            name=name,
            sector=sector,
            market=market,
            is_active=True,
            created_at=utc_now_iso(),
        )
        self._db.execute(
            """
            insert into assets values (?, ?, ?, ?, ?, ?, ?)
            on conflict(asset_id) do nothing
            """,
            (asset.asset_id, asset.symbol, asset.name, asset.sector, asset.market, asset.is_active, asset.created_at),
        )
        return asset

    def list_assets(self) -> tuple[Asset, ...]:
        rows = self._db.fetch_all(
            "select asset_id, symbol, name, sector, market, is_active, created_at from assets order by symbol"
        )
        return tuple(Asset(*row) for row in rows)

    def ingest_raw(self, point: RawDataPoint) -> None:
        self._db.execute(
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
        rows = self._db.fetch_all(
            """
            select data_id, asset_id, timestamp, data_type, value_json, source
            from raw_data
            where asset_id = ? and data_type = ?
            order by timestamp
            """,
            (asset_id, data_type),
        )
        return tuple(RawDataPoint(row[0], row[1], row[2], row[3], json.loads(row[4]), row[5]) for row in rows)

    def persist_signal(self, signal: Signal) -> None:
        signal_id = f"signal:{signal.asset_id}:{signal.timestamp}:{signal.signal_type}"
        self._db.execute(
            """
            insert into signals values (?, ?, ?, ?, ?, ?, ?)
            on conflict(asset_id, timestamp, signal_type) do nothing
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

    def persist_trade_idea(self, trade: TradeIdea) -> None:
        self._db.execute(
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
