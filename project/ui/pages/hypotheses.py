from __future__ import annotations

from collections.abc import Callable

from project.ui._streamlit import get_streamlit
from project.ui.components.hypothesis_card import render_hypothesis_card
from project.ui.components.json_debug import render_json_debug
from project.ui.components.status_card import render_status_cards
from project.ui.views.hypotheses import get_hypotheses_page_view
from project.ui.state import set_selected_hypothesis
from project.ui.views.common import StatusCardView


def render(repository) -> None:
    st = get_streamlit()
    current = st.session_state.get("selected_hypothesis_id") or None
    view = get_hypotheses_page_view(repository, current)
    st.title("Hypotheses")
    st.caption("Lifecycle board and readiness review.")
    render_status_cards(_cards(view))
    _render_board(st, view)
    _render_detail(st, view)
    render_json_debug("Raw JSON / Debug", view.debug_payload)


def _cards(view) -> tuple[StatusCardView, ...]:
    return tuple(
        StatusCardView(column.status.title(), str(len(column.cards)), "ok", "Lifecycle column")
        for column in view.columns
    )


def _render_board(st, view) -> None:
    st.subheader("Hypothesis board")
    columns = st.columns(len(view.columns))
    for column_ui, column in zip(columns, view.columns):
        with column_ui:
            st.write(column.status.title())
            for card in column.cards:
                render_hypothesis_card(
                    card,
                    on_select=_make_select_callback(st, card.hypothesis_id),
                )


def _render_detail(st, view) -> None:
    detail = view.selected_detail
    if detail is None:
        st.info("No hypothesis available.")
        return
    st.subheader(f"Hypothesis: {detail.name}")
    st.write(f"Status: {detail.status}")
    st.write(f"Version: {detail.version}")
    st.write(f"Readiness: {detail.readiness}")
    st.write(f"Required signals: {', '.join(detail.required_signals) or 'none'}")
    if detail.blockers:
        st.warning("Blockers: " + ", ".join(detail.blockers))
    st.write(f"Latest backtest: {detail.latest_backtest or 'none'}")
    st.write(f"Validation failures: {detail.validation_failures}")
    if detail.strategy_spec is not None:
        st.caption("Strategy specification present")


def _select_hypothesis(st, hypothesis_id: str) -> None:
    set_selected_hypothesis(st.session_state, hypothesis_id)
    st.rerun()


def _make_select_callback(st, hypothesis_id: str) -> Callable[[], None]:
    def _callback() -> None:
        _select_hypothesis(st, hypothesis_id)

    return _callback
