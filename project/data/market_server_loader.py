from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from project.data.ingestion import build_raw_price_point
from project.data.repository import DataRepository
from project.data.validation import validate_historical_data


MARKET_SERVER_SOURCE = "postgres"
MARKET_SERVER_RELATION = "market_raw.ohlcv_deduplicated"


@dataclass(frozen=True)
class MarketServerRow:
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


def sync_market_data(
    repository: DataRepository,
    symbols: tuple[str, ...],
    resolution: str = "1d",
    market_db_url_env: str = "MARKET_DB_URL",
) -> dict[str, object]:
    normalized_symbols = _normalize_symbols(symbols)
    rows = _read_market_server_rows(normalized_symbols, resolution, market_db_url_env)
    if not rows:
        joined_symbols = ", ".join(normalized_symbols)
        message = (
            f"{MARKET_SERVER_RELATION} returned no rows for symbols "
            f"{joined_symbols} at resolution {resolution}"
        )
        raise ValueError(message)
    _validate_rows(rows)
    with repository.transaction():
        payload = _persist_rows(repository, rows)
    payload["source"] = MARKET_SERVER_SOURCE
    payload["source_relation"] = MARKET_SERVER_RELATION
    payload["resolution"] = resolution
    return payload


def _normalize_symbols(symbols: tuple[str, ...]) -> tuple[str, ...]:
    normalized: dict[str, None] = {}
    for symbol in symbols:
        text = symbol.strip().upper()
        if text:
            normalized.setdefault(text, None)
    if not normalized:
        raise ValueError("at least one symbol is required")
    return tuple(normalized)


def _read_market_server_rows(
    symbols: tuple[str, ...],
    resolution: str,
    market_db_url_env: str,
) -> tuple[MarketServerRow, ...]:
    connection = _connect_market_server(market_db_url_env)
    try:
        _ensure_source_relation(connection)
        statement, parameters = _build_query(symbols, resolution)
        rows = connection.execute(statement, parameters).fetchall()
        return tuple(_normalize_row(row) for row in rows)
    except RuntimeError:
        raise
    except Exception as error:
        raise RuntimeError(
            f"failed to read {MARKET_SERVER_RELATION}: {error}"
        ) from error
    finally:
        connection.close()


def _connect_market_server(market_db_url_env: str) -> Any:
    conninfo = os.environ.get(market_db_url_env)
    if not conninfo:
        raise RuntimeError(f"environment variable {market_db_url_env} is not set")
    try:
        import psycopg  # type: ignore[import-not-found]
    except ImportError as error:
        raise RuntimeError("psycopg is required for sync-market-data") from error
    try:
        return psycopg.connect(conninfo)
    except Exception as error:
        raise RuntimeError(
            f"failed to connect to Postgres using {market_db_url_env}: {error}"
        ) from error


def _ensure_source_relation(connection: Any) -> None:
    row = connection.execute(
        """
        select 1
        from information_schema.tables
        where table_schema = %s and table_name = %s
        """,
        ("market_raw", "ohlcv_deduplicated"),
    ).fetchone()
    if row is None:
        raise RuntimeError(
            f"required source relation {MARKET_SERVER_RELATION} not found"
        )


def _build_query(
    symbols: tuple[str, ...], resolution: str
) -> tuple[str, tuple[object, ...]]:
    filters = ["resolution = %s"]
    parameters: list[object] = [resolution]
    if symbols:
        placeholders = ", ".join("%s" for _ in symbols)
        filters.append(f"upper(symbol) in ({placeholders})")
        parameters.extend(symbols)
    statement = (
        "select symbol, exchange, ts, open, high, low, close, volume, "
        "source, resolution "
        f"from {MARKET_SERVER_RELATION} "
        f"where {' and '.join(filters)} "
        "order by upper(symbol), ts"
    )
    return statement, tuple(parameters)


def _normalize_row(row: tuple[Any, ...]) -> MarketServerRow:
    (
        symbol,
        exchange,
        timestamp,
        open_p,
        high,
        low,
        close,
        volume,
        source,
        resolution,
    ) = row
    return MarketServerRow(
        symbol=_required_text(symbol, "symbol").upper(),
        exchange=_required_text(exchange, "exchange").upper(),
        timestamp=_normalize_timestamp(timestamp),
        open=float(open_p),
        high=float(high),
        low=float(low),
        close=float(close),
        volume=float(volume),
        source=_required_text(source, "source"),
        resolution=_required_text(resolution, "resolution"),
    )


def _required_text(value: Any, field_name: str) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError(f"{field_name} is required")
    return text


def _normalize_timestamp(value: Any) -> datetime:
    timestamp = value.to_pydatetime() if hasattr(value, "to_pydatetime") else value
    if not isinstance(timestamp, datetime):
        raise ValueError(f"expected datetime timestamp, got {type(value)!r}")
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=UTC)
    return timestamp.astimezone(UTC).replace(microsecond=0)


def _validate_rows(rows: tuple[MarketServerRow, ...]) -> None:
    for symbol, history in _rows_by_symbol(rows).items():
        validation = validate_historical_data(history)
        if validation.is_valid:
            continue
        message = (
            f"{MARKET_SERVER_RELATION} validation failed for {symbol}: "
            f"{validation.errors}"
        )
        raise ValueError(message)


def _rows_by_symbol(
    rows: tuple[MarketServerRow, ...],
) -> dict[str, list[tuple[datetime, float, float, float, float, float]]]:
    grouped: dict[str, list[tuple[datetime, float, float, float, float, float]]] = {}
    for row in rows:
        grouped.setdefault(row.symbol, []).append(
            (row.timestamp, row.open, row.high, row.low, row.close, row.volume)
        )
    return grouped


def _persist_rows(
    repository: DataRepository, rows: tuple[MarketServerRow, ...]
) -> dict[str, object]:
    grouped = _group_rows(rows)
    symbols = sorted(grouped)
    rows_loaded: dict[str, int] = {}
    latest_timestamps: dict[str, str] = {}
    for symbol in symbols:
        symbol_rows = grouped[symbol]
        asset = repository.add_asset(symbol, symbol, "equity", symbol_rows[0].exchange)
        for row in symbol_rows:
            repository.ingest_market_data(
                symbol,
                row.timestamp,
                row.open,
                row.high,
                row.low,
                row.close,
                row.volume,
            )
            repository.ingest_raw(
                build_raw_price_point(
                    asset.asset_id,
                    row.timestamp.isoformat(),
                    row.close,
                    f"{MARKET_SERVER_SOURCE}:{row.source}:{row.resolution}",
                )
            )
        rows_loaded[symbol] = len(symbol_rows)
        latest_timestamps[symbol] = symbol_rows[-1].timestamp.isoformat()
    return {
        "symbols": symbols,
        "rows_loaded": rows_loaded,
        "latest_timestamps": latest_timestamps,
    }


def _group_rows(rows: tuple[MarketServerRow, ...]) -> dict[str, list[MarketServerRow]]:
    grouped: dict[str, list[MarketServerRow]] = {}
    for row in rows:
        grouped.setdefault(row.symbol, []).append(row)
    return grouped
