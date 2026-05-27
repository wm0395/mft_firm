from __future__ import annotations

from pathlib import Path

import pytest

from project.common.models import TradeIdea, utc_now_iso
from project.data.repository import DataRepository
from project.tracking.positions import open_position
from project.ui_services.data_views import get_data_page_view
from project.ui_services.explainability_views import get_explainability_page_view
from project.ui_services.hypothesis_views import get_hypotheses_page_view
from project.ui_services.mission_control import get_mission_control_view
from project.ui_services.reports_views import get_reports_page_view
from project.ui_services.research_views import get_research_page_view
from project.ui_services.trade_idea_views import (
    get_trade_ideas_page_view,
    submit_trade_decision,
)
from tests.ui.test_views_support import (
    _assert_seeded_repository_views,
    _empty_repository,
    _first_hypothesis_id,
    _seed_repository,
)


def test_cockpit_views_handle_empty_repository(tmp_path: Path) -> None:
    repository = _empty_repository(tmp_path)
    try:
        mission = get_mission_control_view(repository)
        data = get_data_page_view(repository)
        hypotheses = get_hypotheses_page_view(repository, "missing-hypothesis")
        trade_ideas = get_trade_ideas_page_view(repository, "missing-trade")
        explainability = get_explainability_page_view(repository, "missing-evaluation")
        reports = get_reports_page_view(repository)
        research = get_research_page_view(repository)

        assert mission.cards
        assert mission.recommended_action.target_page == "Data"
        assert mission.recommended_action.workflow_context_key == "workflow_action_command"
        assert mission.recommended_action.workflow_context_value == "sync-market-data"
        assert mission.recommended_action.is_executable is True
        assert mission.recommended_action.disabled_reason is None
        assert data.assets == ()
        assert data.quality_rows == ()
        assert data.snapshots == ()
        assert data.quality_status == "unknown"
        assert hypotheses.columns
        assert hypotheses.selected_detail is not None
        assert hypotheses.selected_detail.hypothesis_id == _first_hypothesis_id(
            hypotheses.columns
        )
        assert trade_ideas.queue == ()
        assert trade_ideas.selected_detail is None
        assert explainability.evaluations == ()
        assert explainability.selected_detail is None
        assert reports.backtests == ()
        assert reports.performance == ()
        assert reports.rejected == ()
        assert reports.strategy_dossier is None
        assert research.projects == ()
        assert research.runs == ()
        assert research.candidates == ()
        assert research.strategy_dossier is None
    finally:
        repository.close()


def test_cockpit_views_reflect_seeded_repository(tmp_path: Path) -> None:
    repository, asset_symbol, trade_id, evaluation_id = _seed_repository(tmp_path)
    try:
        _assert_seeded_repository_views(
            repository, asset_symbol, trade_id, evaluation_id
        )
        reports = get_reports_page_view(repository)
        research = get_research_page_view(repository)
        assert reports.strategy_dossier is not None
        assert reports.strategy_dossier["tradeability_status"] == "eligible"
        assert research.strategy_dossier is not None
        assert research.strategy_dossier["tradeability_status"] == "eligible"
        data = get_data_page_view(repository)
        assert data.default_snapshot.symbols == (asset_symbol,)
        assert data.default_snapshot.data_start == "2026-05-01"
        assert data.default_snapshot.data_end == "2026-05-25"
    finally:
        repository.close()


def test_create_snapshot_and_trade_decision_mutations(tmp_path: Path) -> None:
    repository, _, trade_id, _ = _seed_repository(tmp_path)
    try:
        decision = submit_trade_decision(
            repository,
            trade_id,
            "watch",
            "market_conditions",
            "fixture",
        )
        updated_trade_ideas = get_trade_ideas_page_view(repository, trade_id)
        decisions = repository.get_decisions(trade_id)

        assert decision.action == "watch"
        assert len(decisions) == 1
        assert decisions[0][2] == "watch"
        assert updated_trade_ideas.queue == ()
        assert updated_trade_ideas.selected_detail is None
    finally:
        repository.close()


@pytest.mark.parametrize(
    ("trade_id_suffix", "signals_snapshot", "expected_entry_price"),
    [
        ("close", {"close": 112.0, "entry_price": 111.0, "price": 110.0}, 112.0),
        ("entry-price", {"entry_price": 111.0, "price": 110.0}, 111.0),
        ("price", {"price": 110.0}, 110.0),
    ],
)
def test_submit_trade_decision_approve_opens_position_with_price_priority(
    tmp_path: Path,
    trade_id_suffix: str,
    signals_snapshot: dict[str, float],
    expected_entry_price: float,
) -> None:
    repository, trade = _seed_trade_with_signals(
        tmp_path,
        trade_id_suffix=trade_id_suffix,
        signals_snapshot=signals_snapshot,
    )
    try:
        decision = submit_trade_decision(
            repository,
            trade.trade_id,
            "approve",
            "market_conditions",
            "fixture",
        )

        assert decision.action == "approve"
        assert repository.get_decisions(trade.trade_id)[0][2] == "approve"
        assert repository.get_positions(status="open") == (
            open_position(trade.trade_id, expected_entry_price),
        )
    finally:
        repository.close()


@pytest.mark.parametrize(
    ("review_action", "expected_action"),
    [("reject", "reject"), ("watch", "watch")],
)
def test_submit_trade_decision_reject_and_watch_do_not_open_positions(
    tmp_path: Path,
    review_action: str,
    expected_action: str,
) -> None:
    repository, trade = _seed_trade_with_signals(
        tmp_path,
        trade_id_suffix=review_action,
        signals_snapshot={"close": 112.0},
    )
    try:
        decision = submit_trade_decision(
            repository,
            trade.trade_id,
            review_action,
            "market_conditions",
            "fixture",
        )

        assert decision.action == expected_action
        assert repository.get_decisions(trade.trade_id)[0][2] == expected_action
        assert repository.get_positions(status="open") == ()
    finally:
        repository.close()


def _seed_trade_with_signals(
    tmp_path: Path,
    *,
    trade_id_suffix: str,
    signals_snapshot: dict[str, float],
) -> tuple[DataRepository, TradeIdea]:
    repository, _, base_trade_id, _ = _seed_repository(tmp_path)
    base_trade = next(
        idea for idea in repository.get_trade_ideas() if idea.trade_id == base_trade_id
    )
    trade = TradeIdea(
        trade_id=f"{base_trade_id}:approve:{trade_id_suffix}",
        asset_id=base_trade.asset_id,
        hypothesis_id=base_trade.hypothesis_id,
        version=base_trade.version,
        direction=base_trade.direction,
        confidence=base_trade.confidence,
        signals_snapshot=signals_snapshot,
        timestamp=utc_now_iso(),
    )
    repository.persist_trade_idea(trade)
    return repository, trade
