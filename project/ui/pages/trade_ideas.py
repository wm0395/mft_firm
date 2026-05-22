from __future__ import annotations

from project.ui._streamlit import get_streamlit
from project.ui.components.evidence_table import render_evidence_table
from project.ui.components.json_debug import render_json_debug
from project.ui.components.status_card import render_status_cards
from project.ui.views.common import StatusCardView
from project.ui.views.trade_ideas import (
    get_trade_ideas_page_view,
    submit_trade_decision,
)
from project.ui.state import set_selected_trade


DECISION_REASONS = (
    ("Low confidence", "low_confidence"),
    ("Conflicting signals", "conflicting_signals"),
    ("Risk constraints", "risk_constraints"),
    ("Intuition override", "intuition_override"),
    ("Market conditions", "market_conditions"),
    ("Duplicate exposure", "duplicate_exposure"),
)


def render(repository) -> None:
    st = get_streamlit()
    current = st.session_state.get("selected_trade_id") or None
    view = get_trade_ideas_page_view(repository, current)
    st.title("Trade Ideas")
    st.caption("Human decision queue for trade approval, rejection, or watchlisting.")
    render_status_cards(_cards(view))
    if not view.queue:
        st.info("No open trade ideas.")
        render_json_debug("Raw JSON / Debug", view.debug_payload)
        return
    trade_id = _trade_selector(st, view)
    if trade_id:
        set_selected_trade(st.session_state, trade_id)
    detail_view = get_trade_ideas_page_view(
        repository, trade_id or current
    ).selected_detail
    if detail_view is not None:
        _render_detail(st, detail_view, repository)
    render_json_debug("Raw JSON / Debug", view.debug_payload)


def _cards(view) -> tuple[StatusCardView, ...]:
    return (
        StatusCardView(
            "Review Queue", str(len(view.queue)), "action", "Open trade ideas"
        ),
        StatusCardView(
            "Reviewed",
            str(
                len([item for item in view.queue if item.decision_status == "reviewed"])
            ),
            "ok",
            "Already reviewed ideas",
        ),
    )


def _trade_selector(st, view) -> str | None:
    options = [item.trade_id for item in view.queue]
    index = 0
    current = st.session_state.get("selected_trade_id")
    if current in options:
        index = options.index(current)
    return st.selectbox("Trade idea", options, index=index)


def _render_detail(st, detail, repository) -> None:
    _render_detail_summary(st, detail)
    _render_detail_evidence(st, detail)
    _render_detail_decision(st, detail, repository)


def _render_detail_summary(st, detail) -> None:
    st.subheader(f"Trade idea: {detail.asset_symbol} {detail.direction}")
    st.write(f"Hypothesis: {detail.hypothesis_name}")
    st.write(f"Confidence: {detail.confidence:.2f}")
    st.write(f"Hypothesis status: {detail.hypothesis_status}")


def _render_detail_evidence(st, detail) -> None:
    render_evidence_table("Signal snapshot", detail.signals)
    if detail.evaluation_validation is not None:
        st.caption("Validation status")
        st.json(detail.evaluation_validation)
    if detail.evaluation_explanation is not None:
        st.caption("Explanation")
        st.json(detail.evaluation_explanation)


def _render_detail_decision(st, detail, repository) -> None:
    with st.container(border=True):
        st.subheader("Decision")
        with st.form("trade-decision-form"):
            auto_review = st.checkbox("Automatic decision", value=True)
            action, reason = None, None
            if not auto_review:
                action = st.radio(
                    "Action",
                    ["approve", "reject", "watch"],
                    horizontal=True,
                )
                reason_label = st.selectbox(
                    "Reason",
                    [item[0] for item in DECISION_REASONS],
                )
                reason = dict(DECISION_REASONS)[reason_label]
            notes = st.text_area("Notes")
            submitted = st.form_submit_button("Submit decision")
        if submitted:
            _submit_trade_decision(st, repository, detail.trade_id, action, reason, notes)


def _submit_trade_decision(
    st,
    repository,
    trade_id: str,
    action: str | None,
    reason: str | None,
    notes: str,
) -> None:
    try:
        decision = submit_trade_decision(repository, trade_id, action, reason, notes)
    except Exception as error:
        st.error(str(error))
        return
    st.success(f"Recorded {decision.action} decision")
    st.write(decision.__dict__)
    st.rerun()
