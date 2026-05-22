from __future__ import annotations

from project.ui._streamlit import get_streamlit
from project.ui.components.evidence_table import render_evidence_table
from project.ui.components.json_debug import render_json_debug
from project.ui.components.status_card import render_status_cards
from project.ui.views.common import StatusCardView
from project.ui_services.research_views import get_research_page_view


def render(repository) -> None:
    st = get_streamlit()
    view = get_research_page_view(repository)
    st.title("Research")
    st.caption("Research projects, runs, and strategy candidates.")
    render_status_cards(_cards(view))
    render_json_debug("Canonical Strategy Dossier", view.strategy_dossier)
    render_evidence_table("Research Projects", view.projects)
    render_evidence_table("Research Runs", view.runs)
    render_evidence_table("Strategy Candidates", view.candidates)
    st.info("Wizard-based research workflows can be layered onto this surface next.")
    render_json_debug("Raw JSON / Debug", view.debug_payload)


def _cards(view) -> tuple[StatusCardView, ...]:
    return (
        StatusCardView("Projects", str(len(view.projects)), "ok", "Research projects"),
        StatusCardView("Runs", str(len(view.runs)), "ok", "Research run history"),
        StatusCardView("Candidates", str(len(view.candidates)), "ok", "Strategy candidates"),
    )
