from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import duckdb


@dataclass(frozen=True)
class OffloadObject:
    object_id: str
    blob_path: Path
    source_node_id: str
    symbol: str
    exchange: str
    source: str
    resolution: str
    source_state_dir: str | None = None
    content_hash: str | None = None
    node_name: str | None = None
    platform: str = "collector"


@dataclass(frozen=True)
class OhlcvRow:
    symbol: str
    exchange: str
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    source: str
    resolution: str
    ingest_ts: datetime


DUCKDB_SCHEMA_SQL = (
    """
    create schema if not exists market_raw
    """,
    """
    create table if not exists market_raw.collector_nodes (
        node_id text primary key,
        node_name text not null,
        platform text not null,
        created_at timestamp not null,
        last_seen_at timestamp,
        is_active boolean not null default true
    )
    """,
    """
    create table if not exists market_raw.ingest_objects (
        object_id text primary key,
        node_id text not null references market_raw.collector_nodes(node_id),
        source text not null,
        resolution text not null,
        source_uri text,
        content_hash text,
        row_count integer not null default 0,
        status text not null,
        ingested_at timestamp not null
    )
    """,
    """
    create table if not exists market_raw.catalog_objects (
        object_id text primary key references market_raw.ingest_objects(object_id),
        symbol text not null,
        exchange text not null,
        resolution text not null,
        cataloged_at timestamp not null
    )
    """,
    """
    create table if not exists market_raw.ohlcv (
        object_id text not null references market_raw.ingest_objects(object_id),
        source_node_id text not null references market_raw.collector_nodes(node_id),
        symbol text not null,
        exchange text not null,
        ts timestamp not null,
        open double precision not null,
        high double precision not null,
        low double precision not null,
        close double precision not null,
        volume double precision not null,
        source text not null,
        resolution text not null,
        ingest_ts timestamp not null,
        primary key (object_id, symbol, exchange, ts, resolution)
    )
    """,
)


def read_ohlcv_rows(blob_path: Path) -> tuple[OhlcvRow, ...]:
    if not blob_path.exists():
        raise ValueError(f"parquet blob not found: {blob_path}")
    connection = duckdb.connect()
    try:
        rows = connection.execute(
            """
            select symbol, exchange, ts, open, high, low, close, volume, source, resolution, ingest_ts
            from read_parquet(?)
            order by upper(symbol), upper(exchange), ts, ingest_ts
            """,
            [str(blob_path)],
        ).fetchall()
    except Exception as error:
        msg = f"failed to read parquet blob {blob_path}: {error}"
        raise RuntimeError(msg) from error
    finally:
        connection.close()
    return tuple(_row_from_tuple(row) for row in rows)


def ensure_duckdb_schema(connection: Any) -> None:
    for statement in DUCKDB_SCHEMA_SQL:
        connection.execute(statement)


def collector_node_insert_sql(placeholder: str) -> str:
    return _insert_sql(
        "market_raw.collector_nodes",
        ("node_id", "node_name", "platform", "created_at", "last_seen_at", "is_active"),
        placeholder,
        "node_id",
        ("node_name", "platform", "last_seen_at", "is_active"),
    )


def ingest_object_insert_sql(placeholder: str) -> str:
    return _insert_sql(
        "market_raw.ingest_objects",
        (
            "object_id",
            "node_id",
            "source",
            "resolution",
            "source_uri",
            "content_hash",
            "row_count",
            "status",
            "ingested_at",
        ),
        placeholder,
        "object_id",
        (),
    )


def catalog_object_insert_sql(placeholder: str) -> str:
    return _insert_sql(
        "market_raw.catalog_objects",
        ("object_id", "symbol", "exchange", "resolution", "cataloged_at"),
        placeholder,
        "object_id",
        (),
    )


def ohlcv_insert_sql(placeholder: str) -> str:
    return _insert_sql(
        "market_raw.ohlcv",
        (
            "object_id",
            "source_node_id",
            "symbol",
            "exchange",
            "ts",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "source",
            "resolution",
            "ingest_ts",
        ),
        placeholder,
        ("object_id", "symbol", "exchange", "ts", "resolution"),
        (),
    )


def collector_node_values(blob: OffloadObject) -> tuple[Any, ...]:
    now = _utc_now()
    return (
        blob.source_node_id,
        blob.node_name or blob.source_node_id,
        blob.platform,
        now,
        now,
        True,
    )


def ingest_object_values(blob: OffloadObject, row_count: int) -> tuple[Any, ...]:
    now = _utc_now()
    return (
        blob.object_id,
        blob.source_node_id,
        blob.source,
        blob.resolution,
        blob.source_state_dir or str(blob.blob_path.parent),
        blob.content_hash,
        row_count,
        "completed",
        now,
    )


def catalog_object_values(blob: OffloadObject) -> tuple[Any, ...]:
    return (
        blob.object_id,
        blob.symbol,
        blob.exchange,
        blob.resolution,
        _utc_now(),
    )


def ohlcv_values(blob: OffloadObject, row: OhlcvRow) -> tuple[Any, ...]:
    return (
        blob.object_id,
        blob.source_node_id,
        row.symbol,
        row.exchange,
        row.ts,
        row.open,
        row.high,
        row.low,
        row.close,
        row.volume,
        row.source,
        row.resolution,
        row.ingest_ts,
    )


def commit_if_supported(connection: Any) -> None:
    commit = getattr(connection, "commit", None)
    if callable(commit):
        commit()


def close_if_supported(connection: Any) -> None:
    close = getattr(connection, "close", None)
    if callable(close):
        close()


def _insert_sql(
    table: str,
    columns: tuple[str, ...],
    placeholder: str,
    conflict_key: str | tuple[str, ...],
    update_columns: tuple[str, ...],
) -> str:
    values = ", ".join(placeholder for _ in columns)
    if isinstance(conflict_key, str):
        conflict = conflict_key
    else:
        conflict = ", ".join(conflict_key)
    if not update_columns:
        return f"insert into {table} ({', '.join(columns)}) values ({values}) on conflict({conflict}) do nothing"
    updates = ", ".join(f"{column} = excluded.{column}" for column in update_columns)
    return (
        f"insert into {table} ({', '.join(columns)}) values ({values}) "
        f"on conflict({conflict}) do update set {updates}"
    )


def _row_from_tuple(row: tuple[Any, ...]) -> OhlcvRow:
    symbol, exchange, ts, open_p, high, low, close, volume, source, resolution, ingest_ts = row
    return OhlcvRow(
        symbol=str(symbol),
        exchange=str(exchange),
        ts=_normalize_datetime(ts),
        open=float(open_p),
        high=float(high),
        low=float(low),
        close=float(close),
        volume=float(volume),
        source=str(source),
        resolution=str(resolution),
        ingest_ts=_normalize_datetime(ingest_ts),
    )


def _normalize_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value.astimezone(UTC).replace(microsecond=0) if value.tzinfo else value.replace(
            tzinfo=UTC, microsecond=0
        )
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return _normalize_datetime(parsed)


def _utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)
