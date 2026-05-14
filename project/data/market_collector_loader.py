from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from project.data.ingestion import build_raw_price_point
from project.data.repository import DataRepository
from project.data.validation import validate_historical_data


@dataclass(frozen=True)
class MarketCollectorRow:
    symbol: str
    exchange: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    source: str
    resolution: str


def load_market_collector_ohlcv(
    repository: DataRepository,
    source_database: Path,
    symbols: tuple[str, ...] = (),
    resolution: str = "1d",
) -> dict[str, object]:
    source_database = source_database.expanduser()
    rows = _read_market_collector_rows(
        source_database,
        tuple(symbol.upper() for symbol in symbols),
        resolution,
    )
    if not rows:
        raise ValueError("market_collector returned no rows for the requested filters")
    _validate_rows(rows)
    with repository.transaction():
        payload = _persist_rows(repository, rows)
    payload["source_database"] = str(source_database)
    return payload


def _read_market_collector_rows(
    source_database: Path,
    symbols: tuple[str, ...],
    resolution: str,
) -> tuple[MarketCollectorRow, ...]:
    connection = _connect_market_collector(source_database)
    try:
        statement, parameters = _build_query(symbols, resolution)
        return tuple(MarketCollectorRow(*row) for row in connection.execute(statement, parameters).fetchall())
    except Exception as error:
        msg = f"failed to read market_collector data from {source_database}: {error}"
        raise RuntimeError(msg) from error
    finally:
        connection.close()


def _connect_market_collector(source_database: Path) -> Any:
    try:
        import duckdb
    except ImportError as error:
        raise RuntimeError("DuckDB is required for the market_collector loader") from error
    if not source_database.exists():
        raise ValueError(f"market_collector database not found: {source_database}")
    return duckdb.connect(str(source_database), read_only=True)


def _build_query(
    symbols: tuple[str, ...],
    resolution: str,
) -> tuple[str, list[object]]:
    filters = ["resolution = ?"]
    parameters: list[object] = [resolution]
    if symbols:
        placeholders = ", ".join("?" for _ in symbols)
        filters.append(f"upper(symbol) in ({placeholders})")
        parameters.extend(symbols)
    statement = f"""
        select symbol, exchange, ts, open, high, low, close, volume, source, resolution
        from ohlcv
        where {" and ".join(filters)}
        qualify row_number() over (
            partition by upper(symbol), upper(exchange), ts, resolution
            order by ingest_ts desc, object_id desc
        ) = 1
        order by upper(symbol), ts
    """
    return statement, parameters


def _validate_rows(rows: tuple[MarketCollectorRow, ...]) -> None:
    symbols = sorted({row.symbol.upper() for row in rows})
    for symbol in symbols:
        history = [
            (row.timestamp, row.open, row.high, row.low, row.close, row.volume)
            for row in rows
            if row.symbol.upper() == symbol
        ]
        validation = validate_historical_data(history)
        if validation.is_valid:
            continue
        raise ValueError(f"market_collector validation failed for {symbol}: {validation.errors}")


def _persist_rows(
    repository: DataRepository,
    rows: tuple[MarketCollectorRow, ...],
) -> dict[str, object]:
    assets_seen: dict[str, str] = {}
    rows_loaded: dict[str, int] = {}
    latest_timestamps: dict[str, str] = {}
    for row in rows:
        symbol = row.symbol.upper()
        asset = repository.add_asset(symbol, symbol, "equity", row.exchange.upper())
        timestamp = _normalize_timestamp(row.timestamp)
        source = f"market_collector:{row.source}:{row.resolution}"
        repository.ingest_market_data(symbol, timestamp, row.open, row.high, row.low, row.close, row.volume)
        repository.ingest_raw(
            build_raw_price_point(asset.asset_id, timestamp.isoformat(), row.close, source)
        )
        assets_seen[symbol] = asset.asset_id
        rows_loaded[symbol] = rows_loaded.get(symbol, 0) + 1
        latest_timestamps[symbol] = timestamp.isoformat()
    return {
        "assets": sorted(assets_seen),
        "rows_loaded": rows_loaded,
        "latest_timestamps": latest_timestamps,
        "resolution": rows[0].resolution,
    }


def _normalize_timestamp(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).replace(microsecond=0)
