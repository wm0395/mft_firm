from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
import subprocess
import sys
from pathlib import Path

import pytest

from project.cli import main
from project.common.models import Asset, TradeIdea
from project.data.ingestion import build_raw_price_point
from project.data.db import DuckDBAccess
from project.data.repository import DataRepository
from project.data.yfinance_loader import (
    DEFAULT_NIFTY_ASSET_SPECS,
    YFinanceAssetSpec,
    YFinancePriceBatch,
    load_default_yfinance_universe,
)


CSV_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "market_data" / "NIFTY.csv"


def _run_help(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *command],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )


def test_project_main_script_help() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    result = _run_help(["project/main.py", "--help"], repo_root)

    assert result.returncode == 0
    assert "usage:" in result.stdout.lower()


def test_project_main_module_help() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    result = _run_help(["-m", "project.main", "--help"], repo_root)

    assert result.returncode == 0
    assert "usage:" in result.stdout.lower()


def test_read_only_command_skips_schema_bootstrap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "mft.duckdb"
    repository = DataRepository(DuckDBAccess(db_path))
    repository.initialize()
    asset = repository.add_asset("AAPL", "Apple", "equity", "NASDAQ")
    repository.persist_trade_idea(
        TradeIdea(
            trade_id="trade:1",
            asset_id=asset.asset_id,
            hypothesis_id="hypothesis:test",
            version=1,
            direction="long",
            confidence=1.0,
            signals_snapshot={},
        )
    )
    repository.close()

    def fail_initialize_schema(self) -> None:
        raise AssertionError("read-only command must not bootstrap schema")

    monkeypatch.setattr(DuckDBAccess, "initialize_schema", fail_initialize_schema)
    exit_code = main(["show-trade-idea", "trade:1", "--database", str(db_path)])
    capsys.readouterr()

    assert exit_code == 0


def test_init_db_bootstraps_schema(tmp_path: Path) -> None:
    db_path = tmp_path / "mft.duckdb"

    exit_code = main(["init-db", "--database", str(db_path)])

    assert exit_code == 0
    db = DuckDBAccess(db_path)
    try:
        assert {row[0] for row in db.fetch_all("show tables")} >= {
            "assets",
            "raw_data",
            "raw_market_data",
        }
    finally:
        db.close()


def test_mutating_command_emits_structured_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "mft.duckdb"
    main(["init-db", "--database", str(db_path)])
    capsys.readouterr()

    exit_code = main(
        ["review-trade-idea", "trade:missing", "approve", "--database", str(db_path)]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["status"] == "error"
    assert payload["command"] == "review-trade-idea"


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
    db_path = tmp_path / "mft.duckdb"
    repository = DataRepository(DuckDBAccess(db_path))
    repository.initialize()
    assets = (
        repository.add_asset("AAPL", "Apple", "equity", "NASDAQ"),
        repository.add_asset("MSFT", "Microsoft", "equity", "NASDAQ"),
    )
    start, end = _seed_cli_snapshot_data(repository, assets)
    repository.close()

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


def test_hypothesis_registry_cli_commands(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db_path = tmp_path / "mft.duckdb"

    exit_code = main(["init-db", "--database", str(db_path)])
    capsys.readouterr()
    assert exit_code == 0

    exit_code = main(["list-hypotheses", "--database", str(db_path)])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "list-hypotheses"
    assert any(
        item["hypothesis_id"] == "hypothesis:rsi_mean_reversion"
        for item in payload["result"]
    )

    exit_code = main(
        ["show-hypothesis", "hypothesis:rsi_mean_reversion", "--database", str(db_path)]
    )
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "show-hypothesis"
    assert payload["result"]["hypothesis_id"] == "hypothesis:rsi_mean_reversion"
    assert payload["result"]["status"] == "active"

    exit_code = main(
        [
            "validate-hypothesis",
            "hypothesis:rsi_mean_reversion",
            "--database",
            str(db_path),
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "validate-hypothesis"
    assert payload["result"]["valid"] is True

    exit_code = main(
        [
            "hypothesis-readiness",
            "hypothesis:rsi_mean_reversion",
            "--database",
            str(db_path),
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "hypothesis-readiness"
    assert payload["status"] in {"warn", "ok"}
    assert payload["result"]["hypothesis_id"] == "hypothesis:rsi_mean_reversion"
    assert payload["result"]["readiness"] in {"ready", "not_ready"}
    assert payload["result"]["signal_registration_status"]

    exit_code = main(
        [
            "promote-hypothesis",
            "hypothesis:rsi_mean_reversion",
            "--to",
            "deprecated",
            "--database",
            str(db_path),
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["result"]["previous_status"] == "active"
    assert payload["result"]["new_status"] == "deprecated"

    exit_code = main(
        ["show-hypothesis", "hypothesis:rsi_mean_reversion", "--database", str(db_path)]
    )
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["result"]["status"] == "deprecated"


def test_operator_commands_emit_envelopes(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db_path = tmp_path / "mft.duckdb"
    repository = DataRepository(DuckDBAccess(db_path))
    repository.initialize()
    repository.close()

    exit_code = main(["doctor", "--database", str(db_path)])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "doctor"
    assert payload["status"] in {"fail", "warn"}
    assert any(
        check["check"] == "schema_initialized" for check in payload["result"]["checks"]
    )

    exit_code = main(["workflow-status", "--database", str(db_path)])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "workflow-status"
    assert payload["result"]["next_recommended_command"] == "sync-market-data"

    exit_code = main(["next-steps", "--database", str(db_path)])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "next-steps"
    assert payload["result"]["steps"][0]["command"] == "init-db"


def test_yfinance_loader_rolls_back_on_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db = DuckDBAccess(tmp_path / "mft.duckdb")
    repository = DataRepository(db)
    repository.initialize()
    base = datetime(2026, 5, 1, tzinfo=UTC)

    def fake_download(
        spec: YFinanceAssetSpec, period: str, interval: str
    ) -> YFinancePriceBatch:
        rows = tuple(
            (
                base + timedelta(days=index),
                100.0 + float(index),
                101.0 + float(index),
                99.0 + float(index),
                100.0 + float(index),
                1000.0,
            )
            for index in range(2)
        )
        return YFinancePriceBatch(spec.yahoo_symbols[0], rows)

    call_count = {"value": 0}
    original_add_asset = repository.add_asset

    def fail_on_second_asset(symbol: str, name: str, sector: str, market: str):
        call_count["value"] += 1
        if call_count["value"] == 2:
            raise RuntimeError("boom")
        return original_add_asset(symbol, name, sector, market)

    monkeypatch.setattr(
        "project.data.yfinance_loader._download_price_batch", fake_download
    )
    monkeypatch.setattr(repository, "add_asset", fail_on_second_asset)

    with pytest.raises(RuntimeError, match="boom"):
        load_default_yfinance_universe(repository, period="6mo", interval="1d")

    assert repository.list_assets() == ()
    assert repository.read_raw_values("asset:NIFTY", "price") == ()
    repository.close()


def test_yfinance_loader_is_idempotent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db = DuckDBAccess(tmp_path / "mft.duckdb")
    repository = DataRepository(db)
    repository.initialize()
    base = datetime(2026, 5, 1, tzinfo=UTC)

    def fake_download(
        spec: YFinanceAssetSpec, period: str, interval: str
    ) -> YFinancePriceBatch:
        rows = tuple(
            (
                base + timedelta(days=index),
                100.0 + float(index),
                101.0 + float(index),
                99.0 + float(index),
                100.0 + float(index),
                1000.0,
            )
            for index in range(2)
        )
        return YFinancePriceBatch(spec.yahoo_symbols[0], rows)

    monkeypatch.setattr(
        "project.data.yfinance_loader._download_price_batch", fake_download
    )
    load_default_yfinance_universe(repository, period="6mo", interval="1d")
    load_default_yfinance_universe(repository, period="6mo", interval="1d")

    assert len(repository.list_assets()) == len(DEFAULT_NIFTY_ASSET_SPECS)
    assert len(repository.read_raw_values("asset:NIFTY", "price")) == 2
    repository.close()


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
