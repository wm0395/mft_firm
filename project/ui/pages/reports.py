from __future__ import annotations

from project.ui._streamlit import get_streamlit
from project.ui.components.evidence_table import render_evidence_table
from project.ui.components.json_debug import render_json_debug
from project.ui.components.status_card import render_status_cards
from project.ui.views.common import StatusCardView
from project.ui_services.reports_views import get_reports_page_view


def render(repository) -> None:
    st = get_streamlit()
    view = get_reports_page_view(repository)
    st.title("Reports")
    st.caption("Backtests, hypothesis performance, and rejected evaluations.")
    render_status_cards(_cards(view))
    render_json_debug("Canonical Strategy Dossier", view.strategy_dossier)
    render_evidence_table("Backtest Results", view.backtests)
    render_evidence_table("Hypothesis Performance", view.performance)
    render_evidence_table("Rejected Hypotheses", view.rejected)
    render_json_debug("Raw JSON / Debug", view.debug_payload)


def _cards(view) -> tuple[StatusCardView, ...]:
    return (
        StatusCardView("Backtests", str(len(view.backtests)), "ok", "Stored backtest results"),
        StatusCardView("Performance", str(len(view.performance)), "ok", "Hypothesis performance rows"),
        StatusCardView("Rejected", str(len(view.rejected)), "warning", "Invalid evaluations"),
    )
