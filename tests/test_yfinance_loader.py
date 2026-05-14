from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from project.data.db import DuckDBAccess
from project.data.repository import DataRepository
from project.data.yfinance_loader import (
    DEFAULT_NIFTY_ASSET_SPECS,
    YFinanceAssetSpec,
    YFinancePriceBatch,
    load_default_yfinance_universe,
)


def test_load_default_yfinance_universe_persists_prices(
    tmp_path: Path,
    monkeypatch,
) -> None:
    db = DuckDBAccess(tmp_path / "mft.duckdb")
    repository = DataRepository(db)
    repository.initialize()
    base = datetime(2026, 5, 1, tzinfo=UTC)

    def fake_download(
        spec: YFinanceAssetSpec,
        period: str,
        interval: str,
    ) -> YFinancePriceBatch:
        rows = []
        for index in range(25):
            timestamp = base + timedelta(days=index)
            price = 100.0 + float(index)
            rows.append((timestamp, price, price + 1.0, price - 1.0, price, 1000.0))
        return YFinancePriceBatch(spec.yahoo_symbols[0], tuple(rows))

    monkeypatch.setattr("project.data.yfinance_loader._download_price_batch", fake_download)

    payload = load_default_yfinance_universe(repository, period="6mo", interval="1d")

    assert payload["assets"] == [spec.asset_symbol for spec in DEFAULT_NIFTY_ASSET_SPECS]
    assert payload["rows_loaded"]["NIFTY"] == 25
    assert len(repository.list_assets()) == len(DEFAULT_NIFTY_ASSET_SPECS)
    for spec in DEFAULT_NIFTY_ASSET_SPECS:
        asset_id = f"asset:{spec.asset_symbol}"
        assert len(repository.read_raw_values(asset_id, "price")) == 25
        assert len(repository.get_market_data(spec.asset_symbol, None, None)) == 25
    db.close()
