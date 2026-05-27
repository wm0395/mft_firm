from __future__ import annotations

import json
from typing import Any, cast

from project.backtesting.models import BacktestResult
from project.cli_support import parse_datetime
from project.cli_utils import ensure_default_hypothesis_catalog
from project.common.models import (
    Position,
    ResearchRun,
    StrategyEvidenceSummary,
    TradeIdea,
    utc_now_iso,
)
from project.data.db import DuckDBAccess
from project.data.ingestion import build_raw_price_point
from project.data.models import (
    HypothesisEvaluation,
    ResearchArtifactRecord,
    ResearchProjectRecord,
    StrategyCandidateRecord,
)
from project.data.repository import DataRepository
from project.hypotheses.rsi_mean_reversion import RSIMeanReversionHypothesis
from project.ui_services.data_views import create_snapshot, get_data_page_view
from project.ui_services.explainability_views import get_explainability_page_view
from project.ui_services.hypothesis_views import get_hypotheses_page_view
from project.ui_services.mission_control import get_mission_control_view
from project.ui_services.reports_views import get_reports_page_view
from project.ui_services.research_views import get_research_page_view
from project.ui_services.trade_idea_views import get_trade_ideas_page_view
from project.ui.views import mission_control as mission_control_views


def _empty_repository(tmp_path) -> DataRepository:
    db = DuckDBAccess(tmp_path / "empty.duckdb")
    repository = DataRepository(db)
    repository.initialize()
    return repository


def _first_hypothesis_id(columns) -> str:
    for column in columns:
        if column.cards:
            return column.cards[0].hypothesis_id
    raise AssertionError("Expected at least one fallback hypothesis")


def _seed_repository(tmp_path):
    db = DuckDBAccess(tmp_path / "mft.duckdb")
    repository = DataRepository(db)
    repository.initialize()
    ensure_default_hypothesis_catalog(repository)
    repository.update_hypothesis_status("hypothesis:ma_crossover", "testing")
    asset = repository.add_asset("NIFTY", "NIFTY 50", "index", "NSE")
    _seed_market_history(repository, asset)
    snapshot_result = create_snapshot(
        repository,
        "Operator Snapshot",
        "NSE",
        (asset.symbol,),
        "2026-05-01",
        "2026-05-25",
        "1d",
        "Cockpit fixture",
    )
    strategy_spec = RSIMeanReversionHypothesis.strategy_spec(
        snapshot_result.universe_id
    )
    repository.persist_research_artifact(strategy_spec)
    now = utc_now_iso()
    run = _seed_research_records(
        repository, asset, strategy_spec, snapshot_result, now
    )
    trade = _seed_trade_records(
        repository, asset, strategy_spec, run, snapshot_result, now
    )
    return repository, asset.symbol, trade.trade_id, "evaluation:operator:1"


def _assert_seeded_repository_views(
    repository: DataRepository,
    asset_symbol: str,
    trade_id: str,
    evaluation_id: str,
) -> None:
    repeat_hypothesis = get_hypotheses_page_view(
        repository, "hypothesis:rsi_mean_reversion"
    )
    stale_hypothesis = get_hypotheses_page_view(repository, "missing-hypothesis")
    repeat_evaluation = get_explainability_page_view(repository, evaluation_id)
    stale_evaluation = get_explainability_page_view(repository, "missing-evaluation")
    repeat_trade = get_trade_ideas_page_view(repository, trade_id)
    stale_trade = get_trade_ideas_page_view(repository, "missing-trade")
    mission = get_mission_control_view(repository)
    data = get_data_page_view(repository)
    reports = get_reports_page_view(repository)
    research = get_research_page_view(repository)
    _assert_seeded_summary_views(mission, data, reports, research)
    _assert_seeded_detail_views(
        repeat_hypothesis,
        stale_hypothesis,
        repeat_evaluation,
        stale_evaluation,
        repeat_trade,
        stale_trade,
        asset_symbol,
        trade_id,
        evaluation_id,
    )


def _assert_seeded_summary_views(mission, data, reports, research) -> None:
    assert mission.health == "Warning"
    assert mission.recommended_action.command == "hypothesis-readiness"
    assert mission.recommended_action.target_page == "Hypotheses"
    assert mission.recommended_action.workflow_context_key == "workflow_action_command"
    assert mission.recommended_action.workflow_context_value == "hypothesis-readiness"
    assert mission.recommended_action.is_executable is True
    assert mission.recommended_action.disabled_reason is None
    assert any(
        card.label == "Trade Ideas" and card.value == "1" for card in mission.cards
    )
    assert data.quality_status == "ok"
    assert len(data.snapshots) == 1
    assert len(reports.backtests) == 1
    assert len(reports.performance) == 1
    assert len(reports.rejected) == 1
    assert len(research.projects) == 1
    assert len(research.runs) == 1


def test_mission_control_recommended_action_contract_maps_pages() -> None:
    cases: tuple[tuple[dict[str, object], str, str], ...] = (
        ({"next_recommended_command": "init-db"}, "Data", "Initialize the database"),
        (
            {"next_recommended_command": "sync-market-data"},
            "Data",
            "Sync market data",
        ),
        (
            {"next_recommended_command": "create-dataset-snapshot"},
            "Data",
            "Create a dataset snapshot",
        ),
        (
            {"next_recommended_command": "data-quality-report"},
            "Data",
            "Review data quality",
        ),
        (
            {"next_recommended_command": "hypothesis-readiness"},
            "Hypotheses",
            "Review hypothesis readiness",
        ),
        (
            {"next_recommended_command": "run-strategy-research"},
            "Research",
            "Run research",
        ),
        ({"next_recommended_command": "promote-hypothesis"}, "Trade Ideas", "Review trade ideas"),
        ({}, "Trade Ideas", "Review trade ideas"),
    )

    for workflow, expected_page, expected_title in cases:
        action = mission_control_views._recommended_action(workflow)
        assert action.target_page == expected_page
        assert action.title == expected_title
        if workflow.get("next_recommended_command"):
            assert action.is_executable is True
            assert action.workflow_context_key == "workflow_action_command"
            assert action.workflow_context_value == workflow["next_recommended_command"]
            assert action.disabled_reason is None
        else:
            assert action.is_executable is False
            assert action.workflow_context_key is None
            assert action.workflow_context_value is None
            assert action.disabled_reason == "No recommended action is available."


def _assert_seeded_detail_views(
    repeat_hypothesis,
    stale_hypothesis,
    repeat_evaluation,
    stale_evaluation,
    repeat_trade,
    stale_trade,
    asset_symbol: str,
    trade_id: str,
    evaluation_id: str,
) -> None:
    assert repeat_hypothesis.selected_detail is not None
    assert repeat_hypothesis.selected_detail.hypothesis_id == "hypothesis:rsi_mean_reversion"
    assert repeat_hypothesis.selected_detail.readiness == "ready"
    assert repeat_hypothesis.selected_detail.validation_failures == 1
    assert stale_hypothesis.selected_detail is not None
    assert (
        stale_hypothesis.selected_detail.hypothesis_id
        == repeat_hypothesis.selected_detail.hypothesis_id
    )
    assert len(repeat_trade.queue) == 1
    assert repeat_trade.selected_detail is not None
    assert repeat_trade.selected_detail.asset_symbol == asset_symbol
    assert stale_trade.selected_detail is not None
    assert stale_trade.selected_detail.trade_id == trade_id
    assert repeat_evaluation.selected_detail is not None
    assert repeat_evaluation.selected_detail.evaluation_id == evaluation_id
    assert len(repeat_evaluation.selected_detail.trace_steps) == 6
    assert stale_evaluation.selected_detail is not None
    assert stale_evaluation.selected_detail.evaluation_id == evaluation_id


def _seed_market_history(repository: DataRepository, asset) -> None:
    for index, close in enumerate(range(100, 125), start=1):
        timestamp = parse_datetime(f"2026-05-{index:02d}T00:00:00+00:00")
        repository.ingest_market_data(
            asset.symbol,
            timestamp,
            float(close - 1),
            float(close + 1),
            float(close - 2),
            float(close),
            1000.0 + index,
        )
        repository.ingest_raw(
            build_raw_price_point(
                asset.asset_id,
                timestamp.isoformat(),
                float(close),
                "fixture",
            )
        )


def _seed_research_records(
    repository,
    asset,
    strategy_spec,
    snapshot_result,
    now: str,
):
    project = _build_research_project(now)
    repository.persist_research_project(project)
    _persist_research_note(repository, project, now)
    run = _build_research_run(strategy_spec, snapshot_result, now)
    repository.persist_research_artifact(run)
    _persist_strategy_evidence(repository, strategy_spec, run, snapshot_result, now)
    _persist_strategy_candidate(repository, project, now)
    _persist_backtest_fixture(repository, asset, strategy_spec, run, snapshot_result)
    return run


def _seed_trade_records(
    repository,
    asset,
    strategy_spec,
    run,
    snapshot_result,
    now: str,
) -> TradeIdea:
    trade = _build_operator_trade(asset, strategy_spec, now)
    repository.persist_trade_idea(trade)
    _persist_operator_position(repository, trade)
    _persist_operator_evaluation(
        repository, asset, strategy_spec, run, snapshot_result, now
    )
    return trade


def _build_research_project(now: str) -> ResearchProjectRecord:
    return ResearchProjectRecord(
        project_id="research_project:operator",
        name="Operator Research",
        description="Fixture research project",
        status="active",
        created_at=now,
        updated_at=now,
    )


def _persist_research_note(repository, project: ResearchProjectRecord, now: str) -> None:
    cast(Any, repository).persist_research_artifact(
        ResearchArtifactRecord(
            artifact_id="artifact:research_notes",
            project_id=project.project_id,
            research_run_id=None,
            artifact_type="note",
            payload_json=json.dumps({"scope": "cockpit"}, sort_keys=True),
            content_hash="research-notes",
            created_at=now,
        )
    )


def _build_research_run(strategy_spec, snapshot_result, now: str) -> ResearchRun:
    return ResearchRun(
        research_run_id="research_run:operator:1",
        strategy_spec_id=strategy_spec.strategy_spec_id,
        dataset_snapshot_id=snapshot_result.dataset_snapshot_id,
        started_at=now,
        completed_at=now,
        status="completed",
        notes="Fixture run",
    )


def _persist_strategy_evidence(
    repository,
    strategy_spec,
    run: ResearchRun,
    snapshot_result,
    now: str,
) -> None:
    repository.persist_research_artifact(
        StrategyEvidenceSummary(
            evidence_summary_id="strategy_evidence_summary:operator:1",
            strategy_spec_id=strategy_spec.strategy_spec_id,
            research_run_id=run.research_run_id,
            dataset_snapshot_id=snapshot_result.dataset_snapshot_id,
            summary="Fixture summary",
            metrics=(("confidence", 0.72), ("trade_ideas", 1)),
            created_at=now,
        )
    )


def _persist_strategy_candidate(repository, project: ResearchProjectRecord, now: str) -> None:
    repository.persist_strategy_candidate(
        StrategyCandidateRecord(
            candidate_id="strategy_candidate:operator:1",
            project_id=project.project_id,
            strategy_version_id="strategy_version:operator:1",
            label="RSI operator candidate",
            status="queued",
            created_at=now,
            promoted_at=None,
        )
    )


def _persist_backtest_fixture(
    repository,
    asset,
    strategy_spec,
    run: ResearchRun,
    snapshot_result,
) -> None:
    repository.persist_backtest_result(
        BacktestResult(
            hypothesis_id=strategy_spec.hypothesis_id,
            asset_id=asset.asset_id,
            total_trades=1,
            winning_trades=1,
            win_rate=1.0,
            total_pnl=10.0,
            mean_pnl=10.0,
            max_drawdown=0.0,
            sharpe_ratio=1.2,
            total_return_pct=5.0,
            hypothesis_version=strategy_spec.hypothesis_version,
            strategy_spec_id=strategy_spec.strategy_spec_id,
            research_run_id=run.research_run_id,
            dataset_snapshot_id=snapshot_result.dataset_snapshot_id,
            start_timestamp=snapshot_result.dataset_snapshot.data_start,
            end_timestamp=snapshot_result.dataset_snapshot.data_end,
            parameters=strategy_spec.parameters,
        )
    )


def _build_operator_trade(asset, strategy_spec, now: str) -> TradeIdea:
    return TradeIdea(
        trade_id="trade:operator:1",
        asset_id=asset.asset_id,
        hypothesis_id=strategy_spec.hypothesis_id,
        version=strategy_spec.hypothesis_version,
        direction="long",
        confidence=0.72,
        signals_snapshot={"rsi_14": 22.5},
        timestamp=now,
    )


def _persist_operator_position(repository, trade: TradeIdea) -> None:
    repository.persist_position(
        Position(
            position_id="position:operator:1",
            trade_id=trade.trade_id,
            entry_price=100.0,
            exit_price=110.0,
            pnl=10.0,
            status="closed",
        )
    )


def _persist_operator_evaluation(
    repository,
    asset,
    strategy_spec,
    run: ResearchRun,
    snapshot_result,
    now: str,
) -> None:
    repository.persist_hypothesis_evaluation(
        HypothesisEvaluation(
            evaluation_id="evaluation:operator:1",
            asset_id=asset.asset_id,
            hypothesis_id=strategy_spec.hypothesis_id,
            hypothesis_version=strategy_spec.hypothesis_version,
            timestamp=now,
            direction="long",
            confidence=0.72,
            signals_snapshot_json=json.dumps({"rsi_14": 22.5}, sort_keys=True),
            explanation_json=json.dumps(
                {
                    "hypothesis_id": strategy_spec.hypothesis_id,
                    "message": "Operator fixture",
                },
                sort_keys=True,
            ),
            generated_trade_idea=True,
            validation_result_json=json.dumps(
                {"is_valid": False, "reasons": ["missing_dataset_snapshot"]},
                sort_keys=True,
            ),
            created_at=now,
            research_run_id=run.research_run_id,
            dataset_snapshot_id=snapshot_result.dataset_snapshot_id,
        )
    )
