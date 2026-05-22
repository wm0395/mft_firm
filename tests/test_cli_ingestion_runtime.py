from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from project.cli import main
from project.common.models import Asset
from project.data.db import DuckDBAccess
from project.data.ingestion import build_raw_price_point
from project.data.repository import DataRepository


CSV_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "market_data" / "NIFTY.csv"


def _prepare_dataset_snapshot_command(
    tmp_path: Path,
) -> tuple[Path, str, str]:
    db_path = tmp_path / "mft.duckdb"
    repository = DataRepository(DuckDBAccess(db_path))
    repository.initialize()
    assets = (
        repository.add_asset("AAPL", "Apple", "equity", "NASDAQ"),
        repository.add_asset("MSFT", "Microsoft", "equity", "NASDAQ"),
    )
    start, end = _seed_cli_snapshot_data(repository, assets)
    repository.close()
    return db_path, start, end


def _run_dataset_snapshot_command(
    db_path: Path,
    start: str,
    end: str,
    capsys: pytest.CaptureFixture[str],
) -> tuple[int, dict[str, Any]]:
    exit_code = main(
        [
            "create-dataset-snapshot",
            "--name",
            "us-largecap-daily-v1",
            "--market",
            "US",
            "--symbol",
            "AAPL",
            "--symbol",
            "MSFT",
            "--data-start",
            start,
            "--data-end",
            end,
            "--resolution",
            "1d",
            "--database",
            str(db_path),
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    return exit_code, payload


def _assert_dataset_snapshot_artifacts(
    db_path: Path,
    exit_code: int,
    payload: dict[str, Any],
) -> None:
    repository = DataRepository(DuckDBAccess(db_path))

    try:
        assert exit_code == 0
        assert payload["status"] == "ok"
        assert payload["result"]["quality_status"] == "ok"
        assert (
            payload["result"]["universe_id"]
            == "research_universe:us_largecap_daily_v1:us"
        )
        assert len(repository.get_research_universes()) == 1
        assert len(repository.get_dataset_snapshots()) == 1
    finally:
        repository.close()


def test_load_ohlcv_csv_command_ingests_data(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "mft.duckdb"

    exit_code = main(["init-db", "--database", str(db_path)])
    capsys.readouterr()
    assert exit_code == 0

    exit_code = main(
        [
            "load-ohlcv-csv",
            "--file-path",
            str(CSV_FIXTURE),
            "--asset-symbol",
            "NIFTY",
            "--database",
            str(db_path),
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    db = DuckDBAccess(db_path)
    repository = DataRepository(db)
    try:
        assert exit_code == 0
        assert payload["status"] == "ok"
        assert payload["command"] == "load-ohlcv-csv"
        assert payload["result"]["asset_symbol"] == "NIFTY"
        assert payload["result"]["rows_loaded"] == 25
        assert len(repository.list_assets()) == 1
        assert len(repository.get_market_data("NIFTY", None, None)) == 25
    finally:
        db.close()


def test_load_ohlcv_csv_command_reports_missing_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "mft.duckdb"
    missing = tmp_path / "missing.csv"

    exit_code = main(["init-db", "--database", str(db_path)])
    capsys.readouterr()
    assert exit_code == 0

    exit_code = main(
        [
            "load-ohlcv-csv",
            "--file-path",
            str(missing),
            "--asset-symbol",
            "NIFTY",
            "--database",
            str(db_path),
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["status"] == "error"
    assert payload["command"] == "load-ohlcv-csv"
    assert "No such file" in payload["error"] or "not found" in payload["error"]


def test_data_quality_report_command_emits_report(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db_path = tmp_path / "mft.duckdb"
    repository = DataRepository(DuckDBAccess(db_path))
    repository.initialize()
    asset = repository.add_asset("AAPL", "Apple", "equity", "NASDAQ")
    _seed_cli_data(repository, asset.asset_id, asset.symbol)
    repository.close()

    exit_code = main(
        ["data-quality-report", "--symbol", "AAPL", "--database", str(db_path)]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "ok"
    assert payload["result"]["requested_symbols"] == ["AAPL"]
    assert payload["result"]["symbols"][0]["row_count"] == 20


def test_data_quality_report_default_is_non_fatal(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db_path = tmp_path / "mft.duckdb"
    repository = DataRepository(DuckDBAccess(db_path))
    repository.initialize()
    repository.close()

    exit_code = main(
        ["data-quality-report", "--symbol", "AAPL", "--database", str(db_path)]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "fail"
    assert payload["command"] == "data-quality-report"
    assert payload["result"]["status"] == "fail"

    exit_code = main(
        [
            "data-quality-report",
            "--symbol",
            "AAPL",
            "--strict",
            "--database",
            str(db_path),
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["status"] == "fail"


def test_create_dataset_snapshot_command_persists_artifacts(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db_path, start, end = _prepare_dataset_snapshot_command(tmp_path)
    exit_code, payload = _run_dataset_snapshot_command(db_path, start, end, capsys)
    _assert_dataset_snapshot_artifacts(db_path, exit_code, payload)


def _seed_cli_data(repository: DataRepository, asset_id: str, symbol: str) -> None:
    base = datetime.now(UTC).replace(microsecond=0) - timedelta(days=19)
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
            build_raw_price_point(asset_id, timestamp.isoformat(), close, "csv:fixture")
        )


def _seed_cli_snapshot_data(
    repository: DataRepository,
    assets: tuple[Asset, ...],
) -> tuple[str, str]:
    base = datetime.now(UTC).replace(microsecond=0) - timedelta(days=19)
    for index in range(20):
        timestamp = base + timedelta(days=index)
        close = 100.0 + float(index)
        for asset in assets:
            repository.ingest_market_data(
                asset.symbol,
                timestamp,
                close,
                close + 1.0,
                close - 1.0,
                close,
                1000.0 + float(index),
            )
            repository.ingest_raw(
                build_raw_price_point(
                    asset.asset_id,
                    timestamp.isoformat(),
                    close,
                    "csv:fixture",
                )
            )
    return base.date().isoformat(), (base + timedelta(days=19)).date().isoformat()
