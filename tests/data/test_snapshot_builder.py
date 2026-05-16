from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from project.common.models import Asset
from project.data.db import DuckDBAccess
from project.data.ingestion import build_raw_price_point
from project.data.repository import DataRepository
from project.data.snapshot_builder import create_dataset_snapshot


def test_create_dataset_snapshot_persists_research_artifacts(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    assets = (
        repository.add_asset("AAPL", "Apple", "equity", "NASDAQ"),
        repository.add_asset("MSFT", "Microsoft", "equity", "NASDAQ"),
    )
    start, end = _seed_snapshot_data(repository, assets)

    try:
        result = create_dataset_snapshot(
            repository,
            name="us-largecap-daily-v1",
            market="US",
            symbols=("MSFT", "AAPL"),
            data_start=start,
            data_end=end,
            resolution="1d",
        )

        assert result.universe_id == "research_universe:us_largecap_daily_v1:us"
        assert result.dataset_snapshot.universe_id == result.universe_id
        assert result.assets == ("AAPL", "MSFT")
        assert result.quality_status == "ok"
        assert result.quality_report.status == "ok"
        assert result.quality_report.sources == ("csv:fixture",)
        assert result.provenance.snapshot_identity == result.dataset_snapshot_id
        assert result.provenance.bar_timeframe == "1d"
        assert len(repository.get_research_universes()) == 1
        assert len(repository.get_dataset_snapshots()) == 1
        assert repository.get_dataset_snapshots()[0].dataset_snapshot_id == result.dataset_snapshot_id
    finally:
        repository.close()


def test_create_dataset_snapshot_is_idempotent(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    assets = (
        repository.add_asset("AAPL", "Apple", "equity", "NASDAQ"),
        repository.add_asset("MSFT", "Microsoft", "equity", "NASDAQ"),
    )
    start, end = _seed_snapshot_data(repository, assets)

    try:
        first = create_dataset_snapshot(
            repository,
            name="us-largecap-daily-v1",
            market="US",
            symbols=("AAPL", "MSFT"),
            data_start=start,
            data_end=end,
            resolution="1d",
        )
        second = create_dataset_snapshot(
            repository,
            name="us-largecap-daily-v1",
            market="US",
            symbols=("AAPL", "MSFT"),
            data_start=start,
            data_end=end,
            resolution="1d",
        )

        assert first.universe_id == second.universe_id
        assert first.dataset_snapshot_id == second.dataset_snapshot_id
        assert len(repository.get_research_universes()) == 1
        assert len(repository.get_dataset_snapshots()) == 1
    finally:
        repository.close()


def test_create_dataset_snapshot_blocks_hard_quality_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = _repository(tmp_path)
    asset = repository.add_asset("AAPL", "Apple", "equity", "NASDAQ")
    timestamp = datetime.now(UTC).replace(microsecond=0)
    row = (timestamp, 100.0, 99.0, 98.0, 100.0, 1000.0)
    monkeypatch.setattr(repository, "get_market_data", lambda *args: [row])
    monkeypatch.setattr(
        repository,
        "read_raw_values",
        lambda *args: (
            build_raw_price_point(asset.asset_id, timestamp.isoformat(), 100.0, "csv:fixture"),
        ),
    )

    try:
        with pytest.raises(ValueError, match="invalid OHLC relations"):
            create_dataset_snapshot(
                repository,
                name="bad-dataset",
                market="US",
                symbols=("AAPL",),
                data_start=timestamp.date().isoformat(),
                data_end=timestamp.date().isoformat(),
                resolution="1d",
            )
        assert repository.get_research_universes() == ()
        assert repository.get_dataset_snapshots() == ()
    finally:
        repository.close()


def _repository(tmp_path: Path) -> DataRepository:
    db = DuckDBAccess(tmp_path / "mft.duckdb")
    repository = DataRepository(db)
    repository.initialize()
    return repository


def _seed_snapshot_data(
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
