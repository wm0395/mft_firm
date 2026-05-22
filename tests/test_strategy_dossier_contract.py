from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from project.cli_support import build_strategy_dossier
from project.common.models import DatasetSnapshot, ResearchUniverse, StrategySpec
from project.data.db import DuckDBAccess
from project.data.ingestion import build_raw_price_point
from project.data.repository import DataRepository
from tests.ui.test_views_support import _seed_repository


def _strategy_dossier(repository: DataRepository, hypothesis_id: str) -> dict[str, Any]:
    return cast(dict[str, Any], build_strategy_dossier(repository, hypothesis_id))


def _expected_strategy_dossier_keys() -> set[str]:
    return {
        "hypothesis_id",
        "strategy_spec_id",
        "strategy_name",
        "activation_status",
        "tradeability_status",
        "tradeability_blockers",
        "thesis",
        "bar_timeframe",
        "holding_horizon",
        "required_signals",
        "expected_failure_modes",
        "dataset_snapshot_id",
        "dataset_snapshot",
        "provenance",
        "research_run_id",
        "latest_research_run",
        "best_backtest",
        "evidence_summary",
        "signal_registration_status",
        "validation_errors",
        "available_research_runs",
        "available_backtests",
        "next_action",
        "next_command",
        "strategy_spec",
    }


def _build_blocker_case_repository(tmp_path: Path) -> tuple[DuckDBAccess, DataRepository]:
    db = DuckDBAccess(tmp_path / "mft.duckdb")
    repository = DataRepository(db)
    repository.initialize()
    asset = repository.add_asset("nifty", "NIFTY 50", "index", "NSE")
    _seed_blocker_case_prices(repository, asset.asset_id)
    _persist_blocker_case_artifacts(repository, asset.asset_id)
    return db, repository


def _seed_blocker_case_prices(repository: DataRepository, asset_id: str) -> None:
    for index, close in enumerate([100.0, 99.0, 98.0, 97.0, 96.0], start=1):
        repository.ingest_raw(
            build_raw_price_point(
                asset_id,
                f"2026-05-{index:02d}T00:00:00+00:00",
                close,
                "fixture_csv",
            )
        )


def _persist_blocker_case_artifacts(
    repository: DataRepository, asset_id: str
) -> None:
    universe = ResearchUniverse(
        universe_id="research_universe:blocker_case",
        name="Blocker Case",
        market="NSE",
        description="Partial research fixture",
        asset_ids=(asset_id,),
    )
    snapshot = DatasetSnapshot(
        dataset_snapshot_id="dataset_snapshot:blocker_case:2026-05-05",
        universe_id=universe.universe_id,
        captured_at="2026-05-05T00:00:00+00:00",
        data_start="2026-05-01T00:00:00+00:00",
        data_end="2026-05-05T00:00:00+00:00",
        asset_ids=(asset_id,),
    )
    strategy_spec = StrategySpec(
        strategy_spec_id="strategy_spec:blocker_case:v1",
        universe_id=universe.universe_id,
        hypothesis_id="hypothesis:rsi_mean_reversion",
        hypothesis_version=1,
        name="Blocker Case",
        parameters=(
            ("thesis", "Partial seed"),
            ("bar_timeframe", "1d"),
            ("holding_horizon", 5),
            ("required_signals", ("rsi_14",)),
            ("expected_failure_modes", ("rangebound",)),
            ("evidence_standard", "research"),
        ),
    )
    for artifact in (universe, snapshot, strategy_spec):
        repository.persist_research_artifact(artifact)


def test_strategy_dossier_exposes_full_contract(tmp_path: Path) -> None:
    repository, _, _, _ = _seed_repository(tmp_path)
    try:
        dossier = _strategy_dossier(repository, "hypothesis:rsi_mean_reversion")
        assert set(dossier) == _expected_strategy_dossier_keys()
        assert dossier["tradeability_status"] == "eligible"
        assert dossier["tradeability_blockers"] == ()
        assert dossier["validation_errors"] == ()
        assert dossier["signal_registration_status"] == (
            {"signal_type": "rsi_14", "registered": True},
        )
        assert len(dossier["available_research_runs"]) == 1
        assert len(dossier["available_backtests"]) == 1
        assert dossier["next_action"]
        assert dossier["next_command"]
        assert dossier["best_backtest"]["research_run_id"] == dossier["research_run_id"]
        assert dossier["latest_research_run"]["research_run_id"] == dossier["research_run_id"]
        assert dossier["evidence_summary"]["research_run_id"] == dossier["research_run_id"]
    finally:
        repository.close()


def test_strategy_dossier_reports_missing_evidence_blockers(tmp_path: Path) -> None:
    db, repository = _build_blocker_case_repository(tmp_path)
    try:
        dossier = _strategy_dossier(repository, "hypothesis:rsi_mean_reversion")
        assert dossier["tradeability_status"] == "blocked"
        assert dossier["validation_errors"] == ()
        assert "missing_research_run" in dossier["tradeability_blockers"]
        assert "missing_backtest_result" in dossier["tradeability_blockers"]
        assert "missing_evidence_summary" in dossier["tradeability_blockers"]
        assert dossier["best_backtest"] is None
    finally:
        db.close()
