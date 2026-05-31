from __future__ import annotations

import contextlib
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from project.backtesting.models import BacktestResult
from project.common.models import DatasetSnapshot, ResearchUniverse
from project.data.db import DuckDBAccess
from project.data.ingestion import build_raw_price_point
from project.data.repository import DataRepository
from project.hypotheses.ma_crossover import MACrossoverHypothesis
from project.hypotheses.rsi_mean_reversion import RSIMeanReversionHypothesis
from project.ui.pages import reports as reports_page
from project.ui.pages import research as research_page
from project.ui_services.reports_views import get_reports_page_view
from project.ui_services.research_views import get_research_page_view


class _FakeStreamlit:
    def title(self, *_args, **_kwargs) -> None:
        return None

    def caption(self, *_args, **_kwargs) -> None:
        return None

    def write(self, *_args, **_kwargs) -> None:
        return None

    def info(self, *_args, **_kwargs) -> None:
        return None

    def subheader(self, *_args, **_kwargs) -> None:
        return None

    def warning(self, *_args, **_kwargs) -> None:
        return None

    def container(self, *_args, **_kwargs):
        return contextlib.nullcontext()

    def columns(self, count: int):
        return tuple(contextlib.nullcontext() for _ in range(count))


def _render_canonical_dossier(
    page_module: Any, view: Any, monkeypatch
) -> list[tuple[str, object]]:
    calls: list[tuple[str, object]] = []

    def capture(title: str, payload) -> None:
        calls.append((title, payload))

    monkeypatch.setattr(page_module, "get_streamlit", lambda: _FakeStreamlit())
    monkeypatch.setattr(page_module, "render_status_cards", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(page_module, "render_evidence_table", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(page_module, "render_json_debug", capture)
    page_module.render(object())
    return calls


def test_page_services_select_latest_backtest_hypothesis(tmp_path: Path) -> None:
    repository = _repository_with_backtests(tmp_path)
    try:
        reports = get_reports_page_view(repository)
        research = get_research_page_view(repository)
        assert reports.strategy_dossier is not None
        assert reports.strategy_dossier["hypothesis_id"] == "hypothesis:rsi_mean_reversion"
        assert research.strategy_dossier is not None
        assert research.strategy_dossier["hypothesis_id"] == "hypothesis:rsi_mean_reversion"
    finally:
        repository.close()


def test_live_pages_render_canonical_dossier(monkeypatch) -> None:
    view = SimpleNamespace(
        backtests=(),
        performance=(),
        rejected=(),
        projects=(),
        runs=(),
        candidates=(),
        launch=SimpleNamespace(
            assets=(),
            snapshots=(),
            hypotheses=(),
            workflow_note="",
        ),
        strategy_dossier={"hypothesis_id": "hypothesis:rsi_mean_reversion"},
        debug_payload=None,
    )
    monkeypatch.setattr(reports_page, "get_reports_page_view", lambda _repository: view)
    assert _render_canonical_dossier(reports_page, view, monkeypatch) == [
        ("Canonical Strategy Dossier", view.strategy_dossier),
        ("Raw JSON / Debug", None),
    ]

    monkeypatch.setattr(research_page, "get_streamlit", lambda: _FakeStreamlit())
    monkeypatch.setattr(research_page, "get_research_page_view", lambda _repository: view)
    assert _render_canonical_dossier(research_page, view, monkeypatch) == [
        ("Canonical Strategy Dossier", view.strategy_dossier),
        ("Raw JSON / Debug", None),
    ]


def _repository_with_backtests(tmp_path: Path) -> DataRepository:
    db, repository, asset, snapshot, spec_rsi, spec_ma = _dossier_pages_repository(tmp_path)
    _seed_raw_prices(repository, asset.asset_id)
    _persist_old_backtest(repository, asset.asset_id, snapshot.dataset_snapshot_id, spec_ma)
    _persist_new_backtest(repository, asset.asset_id, snapshot.dataset_snapshot_id, spec_rsi)
    return repository


def _dossier_pages_repository(
    tmp_path: Path,
) -> tuple[DuckDBAccess, DataRepository, Any, DatasetSnapshot, Any, Any]:
    db = DuckDBAccess(tmp_path / "mft.duckdb")
    repository = DataRepository(db)
    repository.initialize()
    asset = repository.add_asset("nifty", "NIFTY 50", "index", "NSE")
    universe = ResearchUniverse(
        universe_id="research_universe:dossier_pages:nse",
        name="Dossier Pages",
        market="NSE",
        description="Fixture universe",
        asset_ids=(asset.asset_id,),
    )
    snapshot = DatasetSnapshot(
        dataset_snapshot_id="dataset_snapshot:dossier_pages:2026-05-02",
        universe_id=universe.universe_id,
        captured_at="2026-05-02T00:00:00+00:00",
        data_start="2026-05-01T00:00:00+00:00",
        data_end="2026-05-02T00:00:00+00:00",
        asset_ids=(asset.asset_id,),
    )
    spec_rsi = RSIMeanReversionHypothesis.strategy_spec(universe.universe_id)
    spec_ma = MACrossoverHypothesis.strategy_spec(universe.universe_id)
    for artifact in (universe, snapshot, spec_rsi, spec_ma):
        repository.persist_research_artifact(artifact)
    return db, repository, asset, snapshot, spec_rsi, spec_ma


def _persist_old_backtest(
    repository: DataRepository,
    asset_id: str,
    dataset_snapshot_id: str,
    spec_ma: Any,
) -> None:
    repository.persist_backtest_result(
        BacktestResult(
            hypothesis_id=spec_ma.hypothesis_id,
            asset_id=asset_id,
            total_trades=1,
            winning_trades=0,
            win_rate=0.0,
            total_pnl=-1.0,
            mean_pnl=-1.0,
            max_drawdown=1.0,
            sharpe_ratio=-1.0,
            total_return_pct=-0.5,
            hypothesis_version=spec_ma.hypothesis_version,
            strategy_spec_id=spec_ma.strategy_spec_id,
            research_run_id="research_run:old",
            dataset_snapshot_id=dataset_snapshot_id,
            start_timestamp="2026-05-01T00:00:00+00:00",
            end_timestamp="2026-05-02T00:00:00+00:00",
            parameters=spec_ma.parameters,
        )
    )


def _persist_new_backtest(
    repository: DataRepository,
    asset_id: str,
    dataset_snapshot_id: str,
    spec_rsi: Any,
) -> None:
    repository.persist_backtest_result(
        BacktestResult(
            hypothesis_id=spec_rsi.hypothesis_id,
            asset_id=asset_id,
            total_trades=1,
            winning_trades=1,
            win_rate=1.0,
            total_pnl=0.0,
            mean_pnl=0.0,
            max_drawdown=0.0,
            sharpe_ratio=0.0,
            total_return_pct=0.0,
            hypothesis_version=spec_rsi.hypothesis_version,
            strategy_spec_id=spec_rsi.strategy_spec_id,
            research_run_id="research_run:new",
            dataset_snapshot_id=dataset_snapshot_id,
            start_timestamp="2026-05-10T00:00:00+00:00",
            end_timestamp="2026-05-11T00:00:00+00:00",
            parameters=spec_rsi.parameters,
        )
    )


def _seed_raw_prices(repository: DataRepository, asset_id: str) -> None:
    base = datetime(2026, 5, 1, tzinfo=UTC)
    for index in range(2):
        timestamp = base + timedelta(days=index)
        repository.ingest_raw(
            build_raw_price_point(
                asset_id,
                timestamp.isoformat(),
                100.0 + float(index),
                "fixture_csv",
            )
        )
