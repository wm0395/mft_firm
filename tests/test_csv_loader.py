from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from project.data.db import DuckDBAccess
from project.data.loader import load_ohlcv_csv
from project.data.repository import DataRepository


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "market_data" / "NIFTY.csv"


def test_load_ohlcv_csv_ingests_market_and_raw_rows(tmp_path: Path) -> None:
    repository = _repository(tmp_path)

    rows_loaded = load_ohlcv_csv(FIXTURE, "NIFTY", repository)

    assert rows_loaded == 25
    assert len(repository.list_assets()) == 1
    market_rows = repository.get_market_data("NIFTY", None, None)
    raw_rows = repository.read_raw_values("asset:NIFTY", "price")
    assert len(market_rows) == 25
    assert market_rows[0] == (
        datetime(2026, 4, 20),
        99.5,
        101.0,
        99.0,
        100.0,
        1000.0,
    )
    assert market_rows[-1] == (
        datetime(2026, 5, 14),
        112.5,
        113.0,
        111.0,
        112.0,
        1240.0,
    )
    assert len(raw_rows) == 25
    assert raw_rows[0].source == "csv:NIFTY.csv"
    assert raw_rows[-1].source == "csv:NIFTY.csv"
    assert raw_rows[-1].timestamp == "2026-05-14T00:00:00+00:00"
    assert raw_rows[-1].value == {"close": 112.0}
    repository.close()


def test_load_ohlcv_csv_is_idempotent(tmp_path: Path) -> None:
    repository = _repository(tmp_path)

    load_ohlcv_csv(FIXTURE, "NIFTY", repository)
    load_ohlcv_csv(FIXTURE, "NIFTY", repository)

    assert len(repository.get_market_data("NIFTY", None, None)) == 25
    assert len(repository.read_raw_values("asset:NIFTY", "price")) == 25
    repository.close()


def test_load_ohlcv_csv_supports_headerless_rows(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    csv_path = tmp_path / "headerless.csv"
    csv_path.write_text(
        "2026-01-01T00:00:00+00:00,99.5,101.0,99.0,100.0,1000\n"
        "2026-01-02T00:00:00+00:00,100.5,102.0,100.0,101.0,1010\n",
        encoding="utf-8",
    )

    rows_loaded = load_ohlcv_csv(csv_path, "NIFTY", repository)

    assert rows_loaded == 2
    assert len(repository.get_market_data("NIFTY", None, None)) == 2
    assert repository.read_raw_values("asset:NIFTY", "price")[0].source == "csv:headerless.csv"
    repository.close()


def test_load_ohlcv_csv_rejects_malformed_first_row(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    csv_path = tmp_path / "malformed_first_row.csv"
    csv_path.write_text(
        "bad,row,that,should,fail,here\n"
        "2026-01-02T00:00:00+00:00,100.5,102.0,100.0,101.0,1010\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Invalid CSV row"):
        load_ohlcv_csv(csv_path, "NIFTY", repository)
    repository.close()


def test_load_ohlcv_csv_rejects_duplicate_timestamps(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    csv_path = tmp_path / "duplicate.csv"
    csv_path.write_text(
        "timestamp,open,high,low,close,volume\n"
        "2026-01-01T00:00:00+00:00,99.5,101.0,99.0,100.0,1000\n"
        "2026-01-01T00:00:00+00:00,99.5,101.0,99.0,100.0,1000\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Duplicate timestamp"):
        load_ohlcv_csv(csv_path, "NIFTY", repository)
    repository.close()


def test_load_ohlcv_csv_rejects_invalid_ohlc(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    csv_path = tmp_path / "invalid_ohlc.csv"
    csv_path.write_text(
        "timestamp,open,high,low,close,volume\n"
        "2026-01-01T00:00:00+00:00,100.0,99.0,98.0,100.0,1000\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="OHLC"):
        load_ohlcv_csv(csv_path, "NIFTY", repository)
    repository.close()


def test_load_ohlcv_csv_rejects_invalid_timestamp(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    csv_path = tmp_path / "invalid_timestamp.csv"
    csv_path.write_text(
        "timestamp,open,high,low,close,volume\n"
        "not-a-timestamp,100.0,101.0,99.0,100.0,1000\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Invalid CSV row"):
        load_ohlcv_csv(csv_path, "NIFTY", repository)
    repository.close()


def _repository(tmp_path: Path) -> DataRepository:
    repository = DataRepository(DuckDBAccess(tmp_path / "mft.duckdb"))
    repository.initialize()
    return repository
