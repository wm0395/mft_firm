from __future__ import annotations

from project.ui._streamlit import get_streamlit
from project.ui.components.evidence_table import render_evidence_table
from project.ui.components.json_debug import render_json_debug
from project.ui.components.page_hero import render_page_hero
from project.ui.components.status_card import render_status_cards
from project.ui.components.trade_summary import render_trade_summary
from project.ui.views.common import StatusCardView
from project.ui.views.trade_ideas import (
    approval_position_warning,
    get_trade_idea_detail_view,
    get_trade_ideas_page_view,
    submit_trade_decision,
    TradeIdeaDetailView,
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
    trade_id, open_trade_ids = _selected_trade_context(
        st, repository, view, current
    )
    detail_view = (
        get_trade_idea_detail_view(repository, trade_id)
        if trade_id is not None
        else None
    )
    render_page_hero(
        f"{len(view.queue)} open trade ideas awaiting review.",
        _selected_trade_note(trade_id, detail_view),
        context=(
            ("Open", len(view.queue)),
            ("Reviewed", view.reviewed_trade_ideas),
            ("Total", view.total_trade_ideas),
            (
                "Selected",
                (
                    f"{detail_view.asset_symbol} {detail_view.direction}"
                    if detail_view is not None
                    else "none"
                ),
            ),
        ),
    )
    render_status_cards(_cards(view))
    if not view.queue:
        _show_no_open_trade_ideas(st)
    if detail_view is not None:
        _render_detail(
            st,
            detail_view,
            repository,
            allow_submit=detail_view.trade_id in open_trade_ids,
    )
    render_json_debug("Raw JSON / Debug", view.debug_payload)


def _selected_trade_context(
    st,
    repository,
    view,
    current,
) -> tuple[str | None, set[str]]:
    open_trade_ids = {item.trade_id for item in view.queue}
    trade_id = current
    if view.queue:
        selected_trade_id = _trade_selector(st, view)
        current_detail = (
            get_trade_idea_detail_view(repository, current)
            if current is not None
            else None
        )
        if current_detail is None or current in open_trade_ids:
            trade_id = selected_trade_id
            if trade_id:
                set_selected_trade(st.session_state, trade_id)
        elif selected_trade_id != view.queue[0].trade_id:
            trade_id = selected_trade_id
            if trade_id:
                set_selected_trade(st.session_state, trade_id)
    return trade_id, open_trade_ids


def _show_no_open_trade_ideas(st) -> None:
    info_fn = getattr(st, "info", None)
    if callable(info_fn):
        info_fn("No open trade ideas.")
    else:
        st.write("No open trade ideas.")
    st.caption("Closed reviews stay accessible when selected from session state.")


def _selected_trade_note(
    trade_id: str | None,
    detail_view: TradeIdeaDetailView | None,
) -> str:
    if detail_view is None:
        return f"Selected trade: {trade_id or 'none'}"
    decision_count = len(detail_view.decision_history)
    if decision_count == 0:
        return (
            f"Selected trade: {detail_view.asset_symbol} {detail_view.direction} "
            "• pending review"
        )
    decision_label = "decision" if decision_count == 1 else "decisions"
    return (
        f"Selected trade: {detail_view.asset_symbol} {detail_view.direction} "
        f"• {decision_count} prior {decision_label}"
    )


def _cards(view) -> tuple[StatusCardView, ...]:
    return (
        StatusCardView(
            "Open Queue",
            str(len(view.queue)),
            "action",
            "Open trade ideas",
        ),
        StatusCardView(
            "Reviewed",
            str(view.reviewed_trade_ideas),
            "ok" if view.reviewed_trade_ideas > 0 else "warning",
            "Closed review records",
        ),
        StatusCardView(
            "Total Ideas",
            str(view.total_trade_ideas),
            "ok",
            "All trade ideas",
        ),
    )


def _detail_cards(detail) -> tuple[StatusCardView, ...]:
    return (
        StatusCardView(
            "Trade",
            f"{detail.asset_symbol} {detail.direction}",
            "ok",
            f"Confidence {detail.confidence:.2f}",
        ),
        StatusCardView(
            "Hypothesis",
            detail.hypothesis_name,
            "ok" if detail.hypothesis_status == "active" else "warning",
            detail.hypothesis_status,
        ),
        StatusCardView(
            "Recommendation",
            detail.recommended_action,
            "action",
            detail.recommended_reason,
        ),
        StatusCardView(
            "Outcome",
            detail.approval_outcome.state.title(),
            _outcome_state(detail.approval_outcome.state),
            detail.approval_outcome.message,
        ),
    )


def _trade_selector(st, view) -> str | None:
    options = [item.trade_id for item in view.queue]
    index = 0
    current = st.session_state.get("selected_trade_id")
    if current in options:
        index = options.index(current)
    return st.selectbox("Trade idea", options, index=index)


def _render_detail(st, detail, repository, allow_submit: bool = True) -> None:
    render_status_cards(_detail_cards(detail))
    _render_detail_summary(st, detail)
    _render_detail_evidence(st, detail)
    _render_detail_history(st, detail)
    _render_approval_outcome(st, detail)
    if allow_submit:
        _render_detail_decision(st, detail, repository)
    else:
        st.caption("Read-only review record")


def _render_detail_summary(st, detail) -> None:
    with st.container(border=True):
        render_trade_summary(st, detail)


def _render_detail_evidence(st, detail) -> None:
    render_evidence_table("Signal snapshot", detail.signals)
    if detail.evaluation_validation is not None:
        st.caption("Validation status")
        st.json(detail.evaluation_validation)
    if detail.evaluation_explanation is not None:
        st.caption("Explanation")
        st.json(detail.evaluation_explanation)


def _render_detail_history(st, detail) -> None:
    render_evidence_table("Decision history", detail.decision_history)


def _render_approval_outcome(st, detail) -> None:
    outcome = detail.approval_outcome
    st.caption("Approval outcome")
    if outcome.state == "warning":
        warning_fn = getattr(st, "warning", None)
        if callable(warning_fn):
            warning_fn(outcome.message)
        else:
            st.write(outcome.message)
    elif outcome.state == "ok":
        success_fn = getattr(st, "success", None)
        if callable(success_fn):
            success_fn(outcome.message)
        else:
            st.write(outcome.message)
    elif outcome.state == "info":
        info_fn = getattr(st, "info", None)
        if callable(info_fn):
            info_fn(outcome.message)
        else:
            st.write(outcome.message)
    else:
        st.write(outcome.message)
    if outcome.open_position_status is not None:
        st.write(f"Open position status: {outcome.open_position_status}")
    if outcome.open_position_entry_price is not None:
        st.write(f"Entry price: {outcome.open_position_entry_price:.2f}")


def _render_detail_decision(st, detail, repository) -> None:
    with st.container(border=True):
        st.subheader("Decision")
        st.caption("Disable automatic review to override the recommendation.")
        with st.form("trade-decision-form"):
            auto_review = st.checkbox(
                "Use system recommendation",
                value=True,
                help=(
                    "Submit the system recommendation unless you switch to manual "
                    "override."
                ),
            )
            _render_decision_guidance(st, detail, auto_review)
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
            notes = st.text_area(
                "Notes",
                placeholder="Optional context, rationale, or risk notes.",
            )
            st.caption("Notes are saved with the decision and shown in history.")
            submitted = st.form_submit_button("Submit decision")
        if submitted:
            _submit_trade_decision(
                st,
                repository,
                detail.trade_id,
                action,
                reason,
                notes,
            )


def _render_decision_guidance(st, detail, auto_review: bool) -> None:
    if auto_review:
        st.write(
            f"Automatic review will submit {detail.recommended_action} "
            f"with reason {detail.recommended_reason}."
        )
        st.caption("Switch off automatic review to choose a different action.")
        return
    st.write("Manual override is active.")
    st.caption("Choose an explicit action and reason below.")


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
    warning = approval_position_warning(repository, trade_id, decision.action)
    if warning is not None:
        warning_fn = getattr(st, "warning", None)
        if callable(warning_fn):
            warning_fn(warning)
    st.write(decision.__dict__)
    st.rerun()


def _outcome_state(state: str) -> str:
    if state == "ok":
        return "ok"
    if state == "warning":
        return "warning"
    return "action"
