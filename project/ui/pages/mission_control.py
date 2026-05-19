from __future__ import annotations

from project.ui._streamlit import get_streamlit
from project.ui.components.action_panel import render_action_panel
from project.ui.components.json_debug import render_json_debug
from project.ui.components.status_card import render_status_cards
from project.ui.components.workflow_stepper import render_workflow_stepper
from project.ui.state import set_selected_page
from project.ui.views.mission_control import get_mission_control_view


def render(repository) -> None:
    st = get_streamlit()
    view = get_mission_control_view(repository)
    st.title("MFT Mission Control")
    st.caption("Human operating layer for the MFT workflow.")
    render_status_cards(view.cards)
    st.subheader("Workflow progress")
    render_workflow_stepper(view.workflow_steps)
    render_action_panel(
        "Recommended next action",
        view.recommended_action.explanation,
        view.recommended_action.button_label,
        key="mission-control-action",
        on_click=lambda: _navigate_to_action(st, view.recommended_action.command),
    )
    st.subheader("Recent warnings")
    for warning in view.warnings:
        st.write(f"{warning.title}: {warning.why_it_matters}")
        st.caption(warning.recommended_action)
    st.subheader("Recent activity")
    for item in view.recent_activity:
        st.write(f"{item.title}: {item.detail}")
        st.caption(item.timestamp)
    render_json_debug("Raw JSON / Debug", view.debug_payload)


def _navigate_to_action(st, command: str) -> None:
    if command in {"sync-market-data", "create-dataset-snapshot", "init-db"}:
        set_selected_page(st.session_state, "Data")
    elif command == "hypothesis-readiness":
        set_selected_page(st.session_state, "Hypotheses")
    elif command == "run-strategy-research":
        set_selected_page(st.session_state, "Research")
    else:
        set_selected_page(st.session_state, "Trade Ideas")
    st.rerun()
