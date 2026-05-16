from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from project.data.db import DuckDBAccess
from project.data.ingestion import build_raw_price_point
from project.data.quality import build_data_quality_report
from project.data.repository import DataRepository


def test_data_quality_report_marks_clean_dataset_ok(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    asset = repository.add_asset("AAPL", "Apple", "equity", "NASDAQ")
    _seed_daily_data(repository, asset.asset_id, asset.symbol, "csv:fixture")

    report = build_data_quality_report(
        repository,
        ("AAPL",),
        as_of=datetime(2026, 5, 15, tzinfo=UTC),
    )
    repository.close()

    symbol = report.symbols[0]
    assert report.status == "ok"
    assert report.source_count == 1
    assert report.sources == ("csv:fixture",)
    assert symbol.row_count == 20
    assert symbol.duplicate_timestamp_count == 0
    assert symbol.missing_ohlcv_count == 0
    assert symbol.invalid_ohlc_count == 0
    assert symbol.non_positive_close_count == 0
    assert symbol.non_positive_volume_count == 0
    assert symbol.large_gap_count == 0
    assert symbol.status == "ok"


def test_data_quality_report_detects_duplicate_timestamps(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = _repository(tmp_path)
    asset = repository.add_asset("AAPL", "Apple", "equity", "NASDAQ")
    row = (datetime(2026, 5, 14, tzinfo=UTC), 100.0, 101.0, 99.0, 100.0, 1000.0)
    monkeypatch.setattr(repository, "get_market_data", lambda *args: [row, row])
    monkeypatch.setattr(
        repository,
        "read_raw_values",
        lambda *args: (
            build_raw_price_point(asset.asset_id, row[0].isoformat(), 1.0, "csv:fixture"),
        ),
    )

    report = build_data_quality_report(
        repository,
        ("AAPL",),
        as_of=datetime(2026, 5, 15, tzinfo=UTC),
    )
    repository.close()

    symbol = report.symbols[0]
    assert report.status == "fail"
    assert symbol.status == "fail"
    assert symbol.duplicate_timestamp_count == 1
    assert "duplicate timestamps: 1" in symbol.errors


def test_data_quality_report_detects_invalid_ohlc(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = _repository(tmp_path)
    asset = repository.add_asset("AAPL", "Apple", "equity", "NASDAQ")
    row = (datetime(2026, 5, 14, tzinfo=UTC), 100.0, 99.0, 98.0, 100.0, 1000.0)
    monkeypatch.setattr(repository, "get_market_data", lambda *args: [row])
    monkeypatch.setattr(
        repository,
        "read_raw_values",
        lambda *args: (
            build_raw_price_point(asset.asset_id, row[0].isoformat(), 1.0, "csv:fixture"),
        ),
    )

    report = build_data_quality_report(
        repository,
        ("AAPL",),
        as_of=datetime(2026, 5, 15, tzinfo=UTC),
    )
    repository.close()

    symbol = report.symbols[0]
    assert report.status == "fail"
    assert symbol.invalid_ohlc_count == 1
    assert "invalid OHLC relations: 1" in symbol.errors


def test_data_quality_report_detects_non_positive_close(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = _repository(tmp_path)
    asset = repository.add_asset("AAPL", "Apple", "equity", "NASDAQ")
    row = (datetime(2026, 5, 14, tzinfo=UTC), 0.0, 1.0, 0.0, 0.0, 1000.0)
    monkeypatch.setattr(repository, "get_market_data", lambda *args: [row])
    monkeypatch.setattr(
        repository,
        "read_raw_values",
        lambda *args: (
            build_raw_price_point(asset.asset_id, row[0].isoformat(), 1.0, "csv:fixture"),
        ),
    )

    report = build_data_quality_report(
        repository,
        ("AAPL",),
        as_of=datetime(2026, 5, 15, tzinfo=UTC),
    )
    repository.close()

    symbol = report.symbols[0]
    assert report.status == "fail"
    assert symbol.non_positive_close_count == 1
    assert "non-positive close values: 1" in symbol.errors


def test_data_quality_report_marks_missing_data_as_fail(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    repository.add_asset("AAPL", "Apple", "equity", "NASDAQ")

    report = build_data_quality_report(
        repository,
        ("AAPL",),
        as_of=datetime(2026, 5, 15, tzinfo=UTC),
    )
    repository.close()

    symbol = report.symbols[0]
    assert report.status == "fail"
    assert symbol.row_count == 0
    assert "no rows in requested data" in symbol.errors


def _repository(tmp_path: Path) -> DataRepository:
    db = DuckDBAccess(tmp_path / "mft.duckdb")
    repository = DataRepository(db)
    repository.initialize()
    return repository


def _seed_daily_data(
    repository: DataRepository,
    asset_id: str,
    symbol: str,
    source: str,
) -> None:
    base = datetime(2026, 4, 26, tzinfo=UTC)
    for index in range(20):
        timestamp = base + timedelta(days=index)
        close = 100.0 + float(index)
        repository.ingest_market_data(
            symbol,
            timestamp,
            close,
            close + 1.0,
            close - 1.0,
            close,
            1000.0 + float(index),
        )
        repository.ingest_raw(
            build_raw_price_point(asset_id, timestamp.isoformat(), close, source)
        )
