from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd

from project.common.models import Asset
from project.data.db import DuckDBAccess
from project.data.repository import DataRepository


@dataclass(frozen=True)
class MarketCollectorPanel:
    name: str
    open: pd.DataFrame
    high: pd.DataFrame
    low: pd.DataFrame
    close: pd.DataFrame
    volume: pd.DataFrame
    active_mask: pd.DataFrame
    constituents: pd.DataFrame
    industry: pd.Series
    pit_risk: str


@dataclass(frozen=True)
class MarketCollectorPanelRequest:
    name: str = "market_collector_nse"
    exchange: str = "NSE"
    symbol_suffix: str = ""
    symbols: tuple[str, ...] = ()
    start_timestamp: datetime | None = None
    end_timestamp: datetime | None = None
    min_history_days: int = 60
    max_missing_ratio: float = 0.25


def load_market_collector_panel(
    repository: DataRepository,
    request: MarketCollectorPanelRequest = MarketCollectorPanelRequest(),
) -> MarketCollectorPanel:
    assets = _eligible_assets(repository.list_assets(), request)
    if not assets:
        raise ValueError("no assets matched the market_collector panel request")
    rows = _market_rows(repository, tuple(asset.symbol for asset in assets))
    frames = _ohlcv_frames(rows)
    active = _active_mask(frames["close"], frames["volume"], request)
    columns = tuple(active.columns[active.any(axis=0)])
    if not columns:
        raise ValueError("no assets passed the market_collector panel filters")
    constituents = _constituents(tuple(asset for asset in assets if asset.symbol in columns))
    return _panel_from_frames(request.name, frames, active, constituents, columns)


def load_market_collector_panel_from_database(
    database_path: str | Path,
    request: MarketCollectorPanelRequest = MarketCollectorPanelRequest(),
) -> MarketCollectorPanel:
    repository = DataRepository(DuckDBAccess(database_path, read_only=True))
    try:
        return load_market_collector_panel(repository, request)
    finally:
        repository.close()


def load_market_collector_native_panel_from_database(
    database_path: str | Path,
    request: MarketCollectorPanelRequest = MarketCollectorPanelRequest(),
) -> MarketCollectorPanel:
    db = DuckDBAccess(database_path, read_only=True)
    try:
        db.execute("set temp_directory='/tmp'")
        rows = _native_market_rows(db, request)
    finally:
        db.close()
    frames = _ohlcv_frames(rows)
    active = _active_mask(frames["close"], frames["volume"], request)
    columns = tuple(active.columns[active.any(axis=0)])
    if not columns:
        raise ValueError("no native market-collector assets passed the panel filters")
    constituents = _native_constituents(columns, request)
    return _panel_from_frames(request.name, frames, active, constituents, columns)


def _eligible_assets(
    assets: tuple[Asset, ...],
    request: MarketCollectorPanelRequest,
) -> tuple[Asset, ...]:
    wanted = {symbol.upper() for symbol in request.symbols}
    rows = [
        asset
        for asset in assets
        if asset.is_active and asset.market.upper() == request.exchange.upper()
    ]
    if wanted:
        rows = [asset for asset in rows if asset.symbol.upper() in wanted]
    return tuple(rows)


def _market_rows(
    repository: DataRepository,
    symbols: tuple[str, ...],
) -> dict[str, tuple[tuple, ...]]:
    placeholders = ",".join("?" for _ in symbols)
    rows = repository._db.fetch_all(
        f"""
        select asset_symbol, timestamp, open, high, low, close, volume
        from raw_market_data
        where asset_symbol in ({placeholders})
        order by asset_symbol, timestamp
        """,
        list(symbols),
    )
    grouped: dict[str, list[tuple]] = {symbol: [] for symbol in symbols}
    for symbol, timestamp, open_, high, low, close, volume in rows:
        grouped[str(symbol)].append((timestamp, open_, high, low, close, volume))
    return {symbol: tuple(symbol_rows) for symbol, symbol_rows in grouped.items()}


def _native_market_rows(
    db: DuckDBAccess,
    request: MarketCollectorPanelRequest,
) -> dict[str, tuple[tuple, ...]]:
    conditions, params = _native_conditions(request)
    table = _native_price_table(db)
    rows = db.fetch_all(
        f"""
        select symbol, ts, max(open), max(high), max(low), max(close), max(volume)
        from {table}
        where {" and ".join(conditions)}
        group by symbol, ts
        order by symbol, ts
        """,
        params,
    )
    grouped: dict[str, list[tuple]] = {}
    for symbol, timestamp, open_, high, low, close, volume in rows:
        grouped.setdefault(str(symbol), []).append((timestamp, open_, high, low, close, volume))
    return {symbol: tuple(symbol_rows) for symbol, symbol_rows in grouped.items()}


def _native_conditions(request: MarketCollectorPanelRequest) -> tuple[list[str], list[object]]:
    conditions = ["resolution = '1d'"]
    params: list[object] = []
    if request.exchange:
        conditions.append("upper(exchange) = ?")
        params.append(request.exchange.upper())
    if request.symbol_suffix:
        conditions.append("symbol like ?")
        params.append(f"%{request.symbol_suffix}")
    if request.symbols:
        conditions.append(f"symbol in ({','.join('?' for _ in request.symbols)})")
        params.extend(request.symbols)
    if request.start_timestamp is not None:
        conditions.append("ts >= ?")
        params.append(request.start_timestamp)
    if request.end_timestamp is not None:
        conditions.append("ts <= ?")
        params.append(request.end_timestamp)
    return conditions, params


def _native_price_table(db: DuckDBAccess) -> str:
    tables = {str(row[0]) for row in db.fetch_all("show tables")}
    if "ohlcv_deduplicated" in tables:
        return "ohlcv_deduplicated"
    return "ohlcv"


def _native_constituents(
    symbols: tuple[str, ...],
    request: MarketCollectorPanelRequest,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"Symbol": symbol, "Name": symbol, "Industry": "unknown", "Market": request.exchange or "unknown"}
            for symbol in symbols
        ]
    )


def _ohlcv_frames(rows: dict[str, tuple[tuple, ...]]) -> dict[str, pd.DataFrame]:
    records = []
    for symbol, symbol_rows in rows.items():
        records.extend(_records_for_symbol(symbol, symbol_rows))
    if not records:
        raise ValueError("market_collector panel has no OHLCV rows")
    frame = pd.DataFrame(records).set_index(["timestamp", "symbol"]).sort_index()
    return {
        field: frame[field].unstack("symbol").sort_index()
        for field in ("open", "high", "low", "close", "volume")
    }


def _records_for_symbol(symbol: str, rows: tuple[tuple, ...]) -> list[dict[str, object]]:
    out = []
    for timestamp, open_, high, low, close, volume in rows:
        out.append(
            {
                "timestamp": pd.Timestamp(timestamp).tz_localize(None),
                "symbol": symbol,
                "open": float(open_),
                "high": float(high),
                "low": float(low),
                "close": float(close),
                "volume": float(volume),
            }
        )
    return out


def _active_mask(
    close: pd.DataFrame,
    volume: pd.DataFrame,
    request: MarketCollectorPanelRequest,
) -> pd.DataFrame:
    active = close.notna() & volume.notna() & volume.gt(0.0)
    enough_history = active.sum(axis=0).ge(request.min_history_days)
    missing_ratio = _listed_missing_ratio(close)
    low_missing = missing_ratio.le(request.max_missing_ratio)
    keep = enough_history & low_missing
    return active.loc[:, keep.index[keep]].astype(bool)


def _listed_missing_ratio(close: pd.DataFrame) -> pd.Series:
    ratios = {}
    for symbol in close.columns:
        observed = close[symbol].notna()
        if not observed.any():
            ratios[symbol] = 1.0
            continue
        listed = close.loc[observed.idxmax() : observed[::-1].idxmax(), symbol]
        ratios[symbol] = float(listed.isna().mean())
    return pd.Series(ratios)


def _constituents(assets: tuple[Asset, ...]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Symbol": asset.symbol,
                "Name": asset.name,
                "Industry": asset.sector or "unknown",
                "Market": asset.market,
            }
            for asset in assets
        ]
    )


def _panel_from_frames(
    name: str,
    frames: dict[str, pd.DataFrame],
    active: pd.DataFrame,
    constituents: pd.DataFrame,
    columns: tuple[str, ...],
) -> MarketCollectorPanel:
    industry = constituents.drop_duplicates("Symbol").set_index("Symbol")["Industry"]
    return MarketCollectorPanel(
        name=name,
        open=frames["open"][list(columns)],
        high=frames["high"][list(columns)],
        low=frames["low"][list(columns)],
        close=frames["close"][list(columns)],
        volume=frames["volume"][list(columns)],
        active_mask=active[list(columns)],
        constituents=constituents,
        industry=industry.reindex(columns).fillna("unknown"),
        pit_risk="market_collector_current_assets_no_point_in_time_membership",
    )
