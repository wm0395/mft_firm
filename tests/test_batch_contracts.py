from __future__ import annotations

import json
from pathlib import Path

import pytest

from project.cli import main
from project.data.db import DuckDBAccess
from project.data.ingestion import build_raw_price_point
from project.data.repository import DataRepository
from project.signals.pipeline import compute_latest_price_signals
from project.signals.registry import default_signal_registry


def test_signal_compute_is_pure_and_raw_reference_round_trips(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    try:
        asset = repository.add_asset("NIFTY", "NIFTY 50", "index", "NSE")
        _seed_prices(repository, asset.asset_id)

        signals = compute_latest_price_signals(repository, default_signal_registry(), asset.asset_id)
        assert repository.get_signals(asset.asset_id) == ()

        repository.persist_signals(signals)
        retrieved = repository.get_signals(asset.asset_id)

        assert len(retrieved) == len(signals)
        assert retrieved[-1].raw_reference == _latest_raw_reference(asset.asset_id)
        assert all(signal.raw_reference == _latest_raw_reference(asset.asset_id) for signal in retrieved)
    finally:
        repository.close()


def test_batch_commands_are_explicit_about_persistence(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db_path = tmp_path / "mft.duckdb"
    repository = _repository(tmp_path)
    asset = repository.add_asset("NIFTY", "NIFTY 50", "index", "NSE")
    _seed_prices(repository, asset.asset_id)
    repository.close()

    exit_code = main(["summarize-batch", asset.asset_id, "--database", str(db_path)])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["result"]["persisted"] is False

    repository = DataRepository(DuckDBAccess(db_path))
    try:
        assert repository.get_signals(asset.asset_id) == ()
        assert repository.get_trade_ideas() == ()
        assert repository.get_hypothesis_evaluations() == ()
    finally:
        repository.close()

    exit_code = main(["run-batch", asset.asset_id, "--database", str(db_path)])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["result"]["persisted"] is True

    repository = DataRepository(DuckDBAccess(db_path))
    try:
        signals = repository.get_signals(asset.asset_id)
        ideas = repository.get_trade_ideas()
        evaluations = repository.get_hypothesis_evaluations(asset_id=asset.asset_id)

        assert signals
        assert evaluations
        if ideas:
            assert len({idea.timestamp for idea in ideas}) == 1
            assert all(idea.trade_id.endswith(idea.timestamp) for idea in ideas)
    finally:
        repository.close()


def _repository(tmp_path: Path) -> DataRepository:
    db = DuckDBAccess(tmp_path / "mft.duckdb")
    repository = DataRepository(db)
    repository.initialize()
    return repository


def _seed_prices(repository: DataRepository, asset_id: str) -> None:
    prices = tuple(float(value) for value in range(100, 79, -1))
    for index, close in enumerate(prices, start=1):
        repository.ingest_raw(
            build_raw_price_point(
                asset_id,
                f"2026-05-{index:02d}T00:00:00+00:00",
                close,
                "fixture",
            )
        )


def _latest_raw_reference(asset_id: str) -> str:
    return f"raw:{asset_id}:2026-05-21T00:00:00+00:00:price:fixture"
