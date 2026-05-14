from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
from pathlib import Path

import pytest

from project.cli import main
from project.common.models import TradeIdea
from project.data.db import DuckDBAccess
from project.data.repository import DataRepository
from project.data.yfinance_loader import (
    DEFAULT_NIFTY_ASSET_SPECS,
    YFinanceAssetSpec,
    YFinancePriceBatch,
    load_default_yfinance_universe,
)


def test_read_only_command_skips_schema_bootstrap(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
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


def test_mutating_command_emits_structured_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    db_path = tmp_path / "mft.duckdb"
    main(["init-db", "--database", str(db_path)])
    capsys.readouterr()

    exit_code = main(["review-trade-idea", "trade:missing", "approve", "--database", str(db_path)])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["status"] == "error"
    assert payload["command"] == "review-trade-idea"


def test_yfinance_loader_rolls_back_on_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db = DuckDBAccess(tmp_path / "mft.duckdb")
    repository = DataRepository(db)
    repository.initialize()
    base = datetime(2026, 5, 1, tzinfo=UTC)

    def fake_download(spec: YFinanceAssetSpec, period: str, interval: str) -> YFinancePriceBatch:
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

    monkeypatch.setattr("project.data.yfinance_loader._download_price_batch", fake_download)
    monkeypatch.setattr(repository, "add_asset", fail_on_second_asset)

    with pytest.raises(RuntimeError, match="boom"):
        load_default_yfinance_universe(repository, period="6mo", interval="1d")

    assert repository.list_assets() == ()
    assert repository.read_raw_values("asset:NIFTY", "price") == ()
    repository.close()


def test_yfinance_loader_is_idempotent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db = DuckDBAccess(tmp_path / "mft.duckdb")
    repository = DataRepository(db)
    repository.initialize()
    base = datetime(2026, 5, 1, tzinfo=UTC)

    def fake_download(spec: YFinanceAssetSpec, period: str, interval: str) -> YFinancePriceBatch:
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

    monkeypatch.setattr("project.data.yfinance_loader._download_price_batch", fake_download)
    load_default_yfinance_universe(repository, period="6mo", interval="1d")
    load_default_yfinance_universe(repository, period="6mo", interval="1d")

    assert len(repository.list_assets()) == len(DEFAULT_NIFTY_ASSET_SPECS)
    assert len(repository.read_raw_values("asset:NIFTY", "price")) == 2
    repository.close()
