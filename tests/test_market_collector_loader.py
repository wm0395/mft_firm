from __future__ import annotations

from datetime import datetime
from pathlib import Path

import duckdb

from project.data.db import DuckDBAccess
from project.data.market_collector_loader import load_market_collector_ohlcv
from project.data.repository import DataRepository


def test_load_market_collector_ohlcv_imports_latest_rows(tmp_path: Path) -> None:
    source_database = tmp_path / "market.duckdb"
    _seed_market_collector_database(source_database)

    repository = DataRepository(DuckDBAccess(tmp_path / "mft.duckdb"))
    repository.initialize()

    payload = load_market_collector_ohlcv(
        repository,
        source_database,
        symbols=("AAPL",),
        resolution="1d",
    )

    market_rows = repository.get_market_data("AAPL", None, None)
    raw_rows = repository.read_raw_values("asset:AAPL", "price")
    assets = repository.list_assets()
    repository._db.close()

    assert payload["assets"] == ["AAPL"]
    assert payload["rows_loaded"] == {"AAPL": 2}
    assert payload["latest_timestamps"] == {"AAPL": "2026-05-02T00:00:00+00:00"}
    assert payload["source_database"] == str(source_database)
    assert len(assets) == 1
    assert market_rows == (
        (datetime(2026, 5, 1), 100.0, 106.0, 99.0, 105.0, 1000.0),
        (datetime(2026, 5, 2), 106.0, 109.0, 104.0, 108.0, 1100.0),
    )
    assert [point.source for point in raw_rows] == [
        "market_collector:yahoo:1d",
        "market_collector:yahoo:1d",
    ]
    assert raw_rows[-1].value == {"close": 108.0}


def _seed_market_collector_database(source_database: Path) -> None:
    connection = duckdb.connect(str(source_database))
    connection.execute(
        """
        create table ohlcv (
            symbol varchar not null,
            exchange varchar not null,
            ts timestamp not null,
            open double,
            high double,
            low double,
            close double,
            volume double,
            currency varchar,
            source varchar not null,
            resolution varchar not null,
            ingest_ts timestamp not null,
            schema_version integer not null,
            object_id varchar not null
        )
        """
    )
    connection.executemany(
        "insert into ohlcv values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (
                "AAPL",
                "NASDAQ",
                datetime(2026, 5, 1),
                100.0,
                105.0,
                99.0,
                104.0,
                1000.0,
                "USD",
                "yahoo",
                "1d",
                datetime(2026, 5, 1, 0, 0, 0),
                1,
                "object:1",
            ),
            (
                "AAPL",
                "NASDAQ",
                datetime(2026, 5, 1),
                100.0,
                106.0,
                99.0,
                105.0,
                1000.0,
                "USD",
                "yahoo",
                "1d",
                datetime(2026, 5, 1, 0, 1, 0),
                1,
                "object:2",
            ),
            (
                "AAPL",
                "NASDAQ",
                datetime(2026, 5, 2),
                106.0,
                109.0,
                104.0,
                108.0,
                1100.0,
                "USD",
                "yahoo",
                "1d",
                datetime(2026, 5, 2, 0, 1, 0),
                1,
                "object:3",
            ),
        ],
    )
    connection.close()
