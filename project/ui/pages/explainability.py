from __future__ import annotations

from project.ui._streamlit import get_streamlit
from project.ui.components.evidence_table import render_evidence_table
from project.ui.components.json_debug import render_json_debug
from project.ui.components.workflow_stepper import render_workflow_stepper
from project.ui.state import set_selected_evaluation
from project.ui.views.explainability import get_explainability_page_view


def render(repository) -> None:
    st = get_streamlit()
    current = st.session_state.get("selected_evaluation_id") or None
    view = get_explainability_page_view(repository, current)
    st.title("Explainability")
    st.caption("Trace signal lineage, validation, and downstream human decisions.")
    if not view.evaluations:
        st.info("No hypothesis evaluations available.")
        render_json_debug("Raw JSON / Debug", view.debug_payload)
        return
    evaluation_id = _evaluation_selector(st, view)
    if evaluation_id:
        set_selected_evaluation(st.session_state, evaluation_id)
    detail = view.selected_detail
    if detail is not None:
        st.subheader(detail.evaluation_id)
        render_workflow_stepper(detail.trace_steps)
        render_evidence_table("Signals", _signal_rows(detail.signals))
        st.caption("Validation")
        st.json(detail.validation or {})
        st.caption("Explanation")
        st.json(detail.explanation)
        st.write("Trade ideas: " + ", ".join(detail.trade_ideas) if detail.trade_ideas else "Trade ideas: none")
        st.write("Decisions: " + ", ".join(detail.decisions) if detail.decisions else "Decisions: none")
    render_json_debug("Raw JSON / Debug", view.debug_payload)


def _evaluation_selector(st, view) -> str | None:
    options = list(view.evaluations)
    index = 0
    current = st.session_state.get("selected_evaluation_id")
    if current in options:
        index = options.index(current)
    return st.selectbox("Evaluation", options, index=index)


def _signal_rows(signals: dict[str, object]):
    return [
        {"signal_type": key, "value": value}
        for key, value in sorted(signals.items())
    ]
