from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Callable

import pytest

from project.data.db import DuckDBAccess
from project.data.repository import DataRepository
from project.data.yfinance_loader import (
    DEFAULT_NIFTY_ASSET_SPECS,
    YFinanceAssetSpec,
    YFinancePriceBatch,
    load_default_yfinance_universe,
)


def _make_yfinance_download(
    base: datetime,
) -> Callable[[YFinanceAssetSpec, str, str], YFinancePriceBatch]:
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

    return fake_download


def _make_failing_add_asset(
    repository: DataRepository,
) -> Callable[[str, str, str, str], Any]:
    call_count = {"value": 0}
    original_add_asset = repository.add_asset

    def fail_on_second_asset(symbol: str, name: str, sector: str, market: str):
        call_count["value"] += 1
        if call_count["value"] == 2:
            raise RuntimeError("boom")
        return original_add_asset(symbol, name, sector, market)

    return fail_on_second_asset


def test_yfinance_loader_rolls_back_on_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db = DuckDBAccess(tmp_path / "mft.duckdb")
    repository = DataRepository(db)
    repository.initialize()
    base = datetime(2026, 5, 1, tzinfo=UTC)

    monkeypatch.setattr(
        "project.data.yfinance_loader._download_price_batch",
        _make_yfinance_download(base),
    )
    monkeypatch.setattr(repository, "add_asset", _make_failing_add_asset(repository))

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
