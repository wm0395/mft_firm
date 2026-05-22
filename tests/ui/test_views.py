from __future__ import annotations

from pathlib import Path

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
