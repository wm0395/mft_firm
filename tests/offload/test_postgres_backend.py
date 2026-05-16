from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import duckdb
import pytest

from market_collector.offload.backend import OffloadError
from market_collector.offload.ingester import OffloadObject
from market_collector.offload.postgres_backend import PostgresOffloadBackend


@dataclass
class FakeResult:
    rows: list[tuple[Any, ...]]

    def fetchall(self) -> list[tuple[Any, ...]]:
        return list(self.rows)

    def fetchone(self) -> tuple[Any, ...] | None:
        return self.rows[0] if self.rows else None


class FakePostgresConnection:
    def __init__(self, schema_exists: bool = True, tables: set[str] | None = None) -> None:
        self.schema_exists = schema_exists
        self.tables = tables if tables is not None else {"collector_nodes", "ingest_objects", "catalog_objects", "ohlcv"}
        self.collector_nodes: dict[str, tuple[Any, ...]] = {}
        self.ingest_objects: dict[str, tuple[Any, ...]] = {}
        self.catalog_objects: dict[str, tuple[Any, ...]] = {}
        self.ohlcv: dict[tuple[Any, ...], tuple[Any, ...]] = {}
        self.commits = 0
        self.closed = False

    def execute(self, statement: str, params: tuple[Any, ...] | list[Any] | None = None) -> FakeResult:
        normalized = " ".join(statement.lower().split())
        values = tuple(params or ())
        if "information_schema.schemata" in normalized:
            return FakeResult([(1,)] if self.schema_exists else [])
        if "information_schema.tables" in normalized:
            table_name = values[-1]
            return FakeResult([(1,)] if self.schema_exists and table_name in self.tables else [])
        if normalized.startswith("insert into market_raw.collector_nodes"):
            self.collector_nodes[values[0]] = values
            return FakeResult([])
        if normalized.startswith("insert into market_raw.ingest_objects"):
            self.ingest_objects.setdefault(values[0], values)
            return FakeResult([])
        if normalized.startswith("insert into market_raw.catalog_objects"):
            self.catalog_objects.setdefault(values[0], values)
            return FakeResult([])
        if normalized.startswith("insert into market_raw.ohlcv"):
            key = (values[0], values[2], values[3], values[4], values[11])
            self.ohlcv.setdefault(key, values)
            return FakeResult([])
        raise AssertionError(f"unexpected sql: {statement}")

    def commit(self) -> None:
        self.commits += 1

    def close(self) -> None:
        self.closed = True


def test_postgres_backend_inserts_ingest_object_idempotently(tmp_path: Path) -> None:
    backend = PostgresOffloadBackend(FakePostgresConnection(), "postgresql://example")
    blob = _make_blob(tmp_path)

    backend.ingest_blob(blob)
    backend.ingest_blob(blob)

    assert len(backend.connection.collector_nodes) == 1
    assert len(backend.connection.ingest_objects) == 1
    assert len(backend.connection.ohlcv) == 2


def test_postgres_backend_inserts_catalog_object_idempotently(tmp_path: Path) -> None:
    backend = PostgresOffloadBackend(FakePostgresConnection(), "postgresql://example")
    blob = _make_blob(tmp_path)

    backend.ingest_blob(blob)
    backend.register_catalog_object(blob)
    backend.register_catalog_object(blob)

    assert len(backend.connection.catalog_objects) == 1


def test_postgres_backend_inserts_ohlcv_rows_with_source_node_id(tmp_path: Path) -> None:
    backend = PostgresOffloadBackend(FakePostgresConnection(), "postgresql://example")
    blob = _make_blob(tmp_path)

    backend.ingest_blob(blob)

    assert any(row[0] == blob.object_id and row[1] == blob.source_node_id for row in backend.connection.ohlcv.values())


def test_missing_schema_produces_clear_offload_error() -> None:
    backend = PostgresOffloadBackend(FakePostgresConnection(schema_exists=False, tables=set()), "postgresql://example")

    with pytest.raises(OffloadError, match="market_raw schema"):
        backend.ensure_schema()


def _make_blob(tmp_path: Path) -> OffloadObject:
    blob_path = tmp_path / "ohlcv.parquet"
    _write_parquet(blob_path)
    return OffloadObject(
        object_id="object:1",
        blob_path=blob_path,
        source_node_id="node:1",
        symbol="AAPL",
        exchange="NASDAQ",
        source="yahoo",
        resolution="1d",
        source_state_dir="/var/lib/market/state",
        content_hash="hash:1",
        node_name="collector-1",
        platform="android",
    )


def _write_parquet(blob_path: Path) -> None:
    connection = duckdb.connect()
    connection.execute(
        """
        create table rows as
        select * from (
            values
            (
                'AAPL',
                'NASDAQ',
                timestamp '2026-05-01 00:00:00',
                100.0,
                105.0,
                99.0,
                104.0,
                1000.0,
                'yahoo',
                '1d',
                timestamp '2026-05-01 00:01:00'
            ),
            (
                'AAPL',
                'NASDAQ',
                timestamp '2026-05-02 00:00:00',
                106.0,
                109.0,
                104.0,
                108.0,
                1100.0,
                'yahoo',
                '1d',
                timestamp '2026-05-02 00:01:00'
            )
        ) as t(
            symbol,
            exchange,
            ts,
            open,
            high,
            low,
            close,
            volume,
            source,
            resolution,
            ingest_ts
        )
        """
    )
    connection.execute(f"copy rows to '{blob_path.as_posix()}' (format parquet)")
    connection.close()
