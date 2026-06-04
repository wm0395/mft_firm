from __future__ import annotations

from project.ui._streamlit import get_streamlit
from project.ui.components.empty_state import render_empty_state
from project.ui.components.evidence_table import render_evidence_table
from project.ui.components.evaluation_summary import render_evaluation_summary
from project.ui.components.json_debug import render_json_debug
from project.ui.components.page_hero import render_page_hero
from project.ui.components.status_card import render_status_cards
from project.ui.components.workflow_stepper import render_workflow_stepper
from project.ui.state import set_selected_evaluation
from project.ui.views.common import StatusCardView
from project.ui.views.explainability import get_explainability_page_view


def render(repository) -> None:
    st = get_streamlit()
    current = st.session_state.get("selected_evaluation_id") or None
    view = get_explainability_page_view(repository, current)
    detail = view.selected_detail
    st.title("Explainability")
    render_page_hero(
        f"{len(view.evaluations)} evaluations with traceable signal lineage.",
        (
            "Open an evaluation to inspect the path from signals to decisions."
            if view.evaluations
            else "No evaluations recorded yet."
        ),
        context=(
            ("Evaluations", len(view.evaluations)),
            (
                "Selected",
                detail.evaluation_id if detail is not None else "none",
            ),
            ("Trace", len(detail.trace_steps) if detail is not None else 0),
            (
                "Validation",
                _validation_value(detail) if detail is not None else "n/a",
            ),
        ),
    )
    if not view.evaluations:
        render_empty_state(
            st,
            "No hypothesis evaluations available.",
            "Generate an evaluation to inspect signal lineage and decision traceability.",
            "Run research or load a seeded repository to populate this page.",
            (
                ("Evaluations", "0 recorded", "warning"),
                ("Trace", "No trace yet", "action"),
                ("Next step", "Run research", "ok"),
            ),
        )
        render_json_debug("Raw JSON / Debug", view.debug_payload)
        return
    evaluation_id = _evaluation_selector(st, view)
    if evaluation_id:
        set_selected_evaluation(st.session_state, evaluation_id)
        detail = get_explainability_page_view(repository, evaluation_id).selected_detail
    if detail is not None:
        render_status_cards(_cards(view, detail))
        render_status_cards(_detail_cards(detail))
        _render_summary(st, detail)
        st.caption(
            "Use the trace to confirm how evidence becomes a trade idea and decision."
        )
        st.subheader("Trace")
        render_workflow_stepper(detail.trace_steps)
        _render_signal_section(st, detail)
        _render_payload_section(
            st,
            "Validation",
            detail.validation,
            "No validation payload available.",
        )
        _render_payload_section(st, "Explanation", detail.explanation, None)
        _render_related_section(st, detail)
    render_json_debug("Raw JSON / Debug", view.debug_payload)


def _cards(view, detail) -> tuple[StatusCardView, ...]:
    return (
        StatusCardView(
            "Evaluations",
            str(len(view.evaluations)),
            "ok",
            "Available evaluations",
        ),
        StatusCardView(
            "Trace Steps",
            str(len(detail.trace_steps)),
            "ok",
            "Evidence path",
        ),
        StatusCardView(
            "Validation",
            _validation_value(detail),
            _validation_state(detail),
            "Validation payload",
        ),
        StatusCardView(
            "Linked Objects",
            str(len(detail.trade_ideas) + len(detail.decisions)),
            "ok" if (detail.trade_ideas or detail.decisions) else "warning",
            "Trade ideas and decisions",
        ),
    )


def _detail_cards(detail) -> tuple[StatusCardView, ...]:
    return (
        StatusCardView(
            "Asset",
            detail.asset_symbol,
            "ok",
            f"{detail.direction} evaluation",
        ),
        StatusCardView(
            "Hypothesis",
            detail.hypothesis_id,
            "ok",
            "Selected evaluation",
        ),
        StatusCardView(
            "Confidence",
            f"{detail.confidence:.2f}",
            "ok" if detail.confidence >= 0.5 else "warning",
            f"{len(detail.trade_ideas)} linked trade ideas",
        ),
        StatusCardView(
            "Validation",
            _validation_value(detail),
            _validation_state(detail),
            "Selected evaluation",
        ),
    )


def _render_summary(st, detail) -> None:
    with st.container(border=True):
        st.subheader("Selected evaluation")
        render_evaluation_summary(st, detail)


def _render_signal_section(st, detail) -> None:
    with st.container(border=True):
        render_evidence_table("Signals", _signal_rows(detail.signals))


def _render_payload_section(
    st,
    title: str,
    payload: dict[str, object] | None,
    empty_message: str | None,
) -> None:
    with st.container(border=True):
        st.subheader(title)
        if payload is None:
            if empty_message is not None:
                render_empty_state(
                    st,
                    empty_message,
                    "This evaluation does not include a validation payload yet.",
                    "Run research with validation enabled to populate this section.",
                    (
                        ("Validation", "Missing", "warning"),
                        ("Trace", "Still available", "ok"),
                        ("Next step", "Run research", "action"),
                    ),
                )
            return
        st.json(payload)


def _render_related_section(st, detail) -> None:
    with st.container(border=True):
        st.subheader("Related objects")
        st.write(f"Trade ideas: {', '.join(detail.trade_ideas) or 'none'}")
        st.write(f"Decisions: {', '.join(detail.decisions) or 'none'}")


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


def _validation_value(detail) -> str:
    if detail.validation is None:
        return "Missing"
    return "Passed" if detail.validation.get("is_valid", False) else "Failed"


def _validation_state(detail) -> str:
    if detail.validation is None:
        return "warning"
    return "ok" if detail.validation.get("is_valid", False) else "warning"
