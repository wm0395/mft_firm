from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
from pathlib import Path

import pytest

from project.backtesting.models import BacktestConfig
from project.backtesting.research_runner import run_strategy_research
from project.cli import main
from project.cli_utils import ensure_default_hypothesis_catalog
from project.common.models import DatasetSnapshot, ResearchUniverse
from project.data.db import DuckDBAccess
from project.data.repository import DataRepository


def test_run_strategy_research_rejects_missing_snapshot(tmp_path: Path) -> None:
    repository = _repository(tmp_path)

    with pytest.raises(ValueError, match="dataset snapshot not found"):
        run_strategy_research(
            repository,
            "dataset_snapshot:missing",
            "hypothesis:rsi_mean_reversion",
            "AAPL",
            "2024-01-01",
            "2024-01-10",
        )

    repository.close()


def test_run_strategy_research_rejects_asset_outside_snapshot(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    aapl = repository.add_asset("AAPL", "Apple", "equity", "NASDAQ")
    msft = repository.add_asset("MSFT", "Microsoft", "equity", "NASDAQ")
    _persist_snapshot(
        repository,
        asset_ids=(aapl.asset_id,),
        dataset_snapshot_id="dataset_snapshot:us-largecap-daily-v1:2024-01-01:2024-01-10",
    )

    with pytest.raises(ValueError, match="is not included in dataset snapshot"):
        run_strategy_research(
            repository,
            "dataset_snapshot:us-largecap-daily-v1:2024-01-01:2024-01-10",
            "hypothesis:rsi_mean_reversion",
            msft.symbol,
            "2024-01-01",
            "2024-01-10",
        )

    repository.close()


def test_run_strategy_research_rejects_out_of_range_dates(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    asset = repository.add_asset("AAPL", "Apple", "equity", "NASDAQ")
    _persist_snapshot(
        repository,
        asset_ids=(asset.asset_id,),
        dataset_snapshot_id="dataset_snapshot:us-largecap-daily-v1:2024-01-01:2024-01-10",
    )

    with pytest.raises(ValueError, match="requested date range is outside dataset snapshot range"):
        run_strategy_research(
            repository,
            "dataset_snapshot:us-largecap-daily-v1:2024-01-01:2024-01-10",
            "hypothesis:rsi_mean_reversion",
            asset.symbol,
            "2023-12-31",
            "2024-01-10",
        )

    repository.close()


def test_run_strategy_research_persists_audit_context(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    asset = repository.add_asset("AAPL", "Apple", "equity", "NASDAQ")
    snapshot = _persist_snapshot(
        repository,
        asset_ids=(asset.asset_id,),
        dataset_snapshot_id="dataset_snapshot:us-largecap-daily-v1:2024-01-01:2024-01-10",
    )
    _seed_market_data(repository, asset.symbol)

    result = run_strategy_research(
        repository,
        snapshot.dataset_snapshot_id,
        "hypothesis:rsi_mean_reversion",
        asset.symbol,
        "2024-01-01",
        "2024-01-10",
        BacktestConfig(),
    )

    runs = repository.get_research_runs()
    backtests = repository.get_backtest_results()
    evidence_summaries = repository.get_strategy_evidence_summaries()
    strategy_specs = repository.get_strategy_specs()

    assert result.status == "completed"
    assert result.dataset_snapshot_id == snapshot.dataset_snapshot_id
    assert result.hypothesis_id == "hypothesis:rsi_mean_reversion"
    assert result.asset_id == asset.asset_id
    assert result.metrics["total_trades"] == 0
    assert len(strategy_specs) == 1
    assert len(runs) == 1
    assert len(backtests) == 1
    assert len(evidence_summaries) == 1

    run = runs[0]
    backtest = backtests[0]
    summary = evidence_summaries[0]
    spec = strategy_specs[0]

    assert run.research_run_id == result.research_run_id
    assert run.strategy_spec_id == spec.strategy_spec_id
    assert run.dataset_snapshot_id == snapshot.dataset_snapshot_id
    assert run.status == "completed"
    assert backtest.research_run_id == result.research_run_id
    assert backtest.strategy_spec_id == spec.strategy_spec_id
    assert backtest.dataset_snapshot_id == snapshot.dataset_snapshot_id
    assert backtest.start_timestamp == "2024-01-01T00:00:00+00:00"
    assert backtest.end_timestamp == "2024-01-10T23:59:59+00:00"
    assert backtest.parameters == (
        ("exit_horizon", None),
        ("position_size", 10000.0),
        ("slippage_bps", 1.0),
    )
    assert summary.research_run_id == result.research_run_id
    assert summary.strategy_spec_id == spec.strategy_spec_id
    assert summary.dataset_snapshot_id == snapshot.dataset_snapshot_id

    repository.close()


def test_run_strategy_research_creates_new_run_ids(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    asset = repository.add_asset("AAPL", "Apple", "equity", "NASDAQ")
    snapshot = _persist_snapshot(
        repository,
        asset_ids=(asset.asset_id,),
        dataset_snapshot_id="dataset_snapshot:us-largecap-daily-v1:2024-01-01:2024-01-10",
    )
    _seed_market_data(repository, asset.symbol)

    first = run_strategy_research(
        repository,
        snapshot.dataset_snapshot_id,
        "hypothesis:rsi_mean_reversion",
        asset.symbol,
        "2024-01-01",
        "2024-01-10",
    )
    second = run_strategy_research(
        repository,
        snapshot.dataset_snapshot_id,
        "hypothesis:rsi_mean_reversion",
        asset.symbol,
        "2024-01-01",
        "2024-01-10",
    )

    assert first.research_run_id != second.research_run_id
    assert len(repository.get_research_runs()) == 2
    assert len(repository.get_strategy_evidence_summaries()) == 2
    assert len(repository.get_backtest_results()) == 2

    repository.close()


def test_run_strategy_research_command_emits_structured_result(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db_path = tmp_path / "mft.duckdb"
    repository = _repository(tmp_path)
    asset = repository.add_asset("AAPL", "Apple", "equity", "NASDAQ")
    start, end = "2024-01-01", "2024-01-10"
    snapshot = _persist_snapshot(
        repository,
        asset_ids=(asset.asset_id,),
        dataset_snapshot_id="dataset_snapshot:us-largecap-daily-v1:2024-01-01:2024-01-10",
    )
    _seed_market_data(repository, asset.symbol)
    repository.close()

    exit_code = main(
        [
            "run-strategy-research",
            "--dataset-snapshot-id",
            snapshot.dataset_snapshot_id,
            "--hypothesis-id",
            "hypothesis:rsi_mean_reversion",
            "--asset-symbol",
            "AAPL",
            "--start-date",
            start,
            "--end-date",
            end,
            "--database",
            str(db_path),
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "ok"
    assert payload["command"] == "run-strategy-research"
    assert payload["result"]["status"] == "completed"
    assert payload["result"]["dataset_snapshot_id"] == snapshot.dataset_snapshot_id
    assert payload["result"]["hypothesis_id"] == "hypothesis:rsi_mean_reversion"
    assert payload["result"]["asset_id"] == "asset:AAPL"
    assert payload["result"]["metrics"]["total_trades"] == 0


def test_run_strategy_research_respects_draft_flag(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    asset = repository.add_asset("AAPL", "Apple", "equity", "NASDAQ")
    snapshot = _persist_snapshot(
        repository,
        asset_ids=(asset.asset_id,),
        dataset_snapshot_id="dataset_snapshot:us-largecap-daily-v1:2024-01-01:2024-01-10",
    )
    _seed_market_data(repository, asset.symbol)
    ensure_default_hypothesis_catalog(repository)
    repository.update_hypothesis_status("hypothesis:rsi_mean_reversion", "draft")

    with pytest.raises(ValueError, match="cannot be evaluated"):
        run_strategy_research(
            repository,
            snapshot.dataset_snapshot_id,
            "hypothesis:rsi_mean_reversion",
            asset.symbol,
            "2024-01-01",
            "2024-01-10",
        )

    result = run_strategy_research(
        repository,
        snapshot.dataset_snapshot_id,
        "hypothesis:rsi_mean_reversion",
        asset.symbol,
        "2024-01-01",
        "2024-01-10",
        include_draft=True,
    )

    assert result.status == "completed"


def _repository(tmp_path: Path) -> DataRepository:
    db = DuckDBAccess(tmp_path / "mft.duckdb")
    repository = DataRepository(db)
    repository.initialize()
    return repository


def _persist_snapshot(
    repository: DataRepository,
    asset_ids: tuple[str, ...],
    dataset_snapshot_id: str,
) -> DatasetSnapshot:
    universe = ResearchUniverse(
        universe_id="research_universe:us_largecap_daily_v1:us",
        name="US Large Cap Daily V1",
        market="US",
        description="US large cap research universe",
        asset_ids=asset_ids,
    )
    snapshot = DatasetSnapshot(
        dataset_snapshot_id=dataset_snapshot_id,
        universe_id=universe.universe_id,
        captured_at="2024-01-10T23:59:59+00:00",
        data_start="2024-01-01T00:00:00+00:00",
        data_end="2024-01-10T23:59:59+00:00",
        asset_ids=asset_ids,
    )
    repository.persist_research_artifact(universe)
    repository.persist_research_artifact(snapshot)
    return snapshot


def _seed_market_data(repository: DataRepository, asset_symbol: str) -> None:
    base = datetime(2024, 1, 1, tzinfo=UTC)
    for index in range(10):
        timestamp = base + timedelta(days=index)
        price = 100.0 + float(index)
        repository.ingest_market_data(
            asset_symbol,
            timestamp,
            price,
            price + 1.0,
            price - 1.0,
            price,
            1000.0,
        )
