from __future__ import annotations

from datetime import datetime
from pathlib import Path

from project.data.db import DuckDBAccess
from project.data.market_collector_panel import (
    MarketCollectorPanelRequest,
    load_market_collector_panel,
    load_market_collector_native_panel_from_database,
    load_market_collector_panel_from_database,
)
from project.data.repository import DataRepository
from research.projects.price_action_strategy_lab.universe_adapter import to_alpha101_panel


def test_load_market_collector_panel_exports_nse_alpha_panel(tmp_path: Path) -> None:
    repository = DataRepository(DuckDBAccess(tmp_path / "mft.duckdb"))
    repository.initialize()
    repository.add_asset("AAA", "AAA Ltd", "Industrials", "NSE")
    repository.add_asset("BBB", "BBB Ltd", "Financials", "NSE")
    repository.add_asset("CCC", "CCC Ltd", "Technology", "NASDAQ")
    for day in range(3):
        timestamp = datetime(2026, 1, day + 1)
        repository.ingest_market_data("AAA", timestamp, 10 + day, 11 + day, 9 + day, 10.5 + day, 1000)
        repository.ingest_market_data("BBB", timestamp, 20 + day, 21 + day, 19 + day, 20.5 + day, 2000)
        repository.ingest_market_data("CCC", timestamp, 30 + day, 31 + day, 29 + day, 30.5 + day, 3000)

    request = MarketCollectorPanelRequest(min_history_days=3)
    panel = load_market_collector_panel(repository, request)
    alpha_panel = to_alpha101_panel(panel)
    repository.close()

    db_panel = load_market_collector_panel_from_database(tmp_path / "mft.duckdb", request)

    assert tuple(panel.close.columns) == ("AAA", "BBB")
    assert tuple(db_panel.close.columns) == ("AAA", "BBB")
    assert panel.industry.to_dict() == {"AAA": "Industrials", "BBB": "Financials"}
    assert alpha_panel.name == "market_collector_nse"
    assert alpha_panel.active_mask.shape == (3, 2)


def test_load_market_collector_native_panel_reads_ohlcv_view(tmp_path: Path) -> None:
    db_path = tmp_path / "native.duckdb"
    db = DuckDBAccess(db_path)
    db.execute(
        "create table ohlcv(symbol varchar, exchange varchar, ts timestamp, "
        "open double, high double, low double, close double, volume double, resolution varchar)"
    )
    for day in range(3):
        timestamp = datetime(2026, 1, day + 1)
        _insert_native_row(db, "AAA.NS", "NSE", timestamp, 10.0 + day)
        _insert_native_row(db, "BBB.BO", "BSE", timestamp, 20.0 + day)
    db.close()

    request = MarketCollectorPanelRequest(
        exchange="",
        symbol_suffix=".NS",
        min_history_days=3,
    )
    panel = load_market_collector_native_panel_from_database(db_path, request)

    assert tuple(panel.close.columns) == ("AAA.NS",)
    assert panel.pit_risk == "market_collector_current_assets_no_point_in_time_membership"


def _insert_native_row(
    db: DuckDBAccess,
    symbol: str,
    exchange: str,
    timestamp: datetime,
    close: float,
) -> None:
    db.execute(
        "insert into ohlcv values (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (symbol, exchange, timestamp, close, close + 1.0, close - 1.0, close, 1000.0, "1d"),
    )
