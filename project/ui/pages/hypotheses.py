from __future__ import annotations

from collections.abc import Callable

from project.ui._streamlit import get_streamlit
from project.ui.components.hypothesis_card import render_hypothesis_card
from project.ui.components.json_debug import render_json_debug
from project.ui.components.page_hero import render_page_hero
from project.ui.components.status_card import render_status_cards
from project.ui.views.hypotheses import get_hypotheses_page_view
from project.ui.state import set_selected_hypothesis
from project.ui.views.common import StatusCardView


def render(repository) -> None:
    st = get_streamlit()
    current = st.session_state.get("selected_hypothesis_id") or None
    view = get_hypotheses_page_view(repository, current)
    detail = view.selected_detail
    st.title("Hypotheses")
    render_page_hero(
        f"{len(view.columns)} lifecycle columns across the catalog.",
        (
            f"Selected hypothesis: {detail.name}"
            if detail is not None
            else "Open a card to inspect thesis and blockers."
        ),
        context=(
            ("Columns", len(view.columns)),
            ("Selected", detail.name if detail is not None else "none"),
            ("Readiness", detail.readiness if detail is not None else "n/a"),
            (
                "Validation",
                detail.validation_failures if detail is not None else 0,
            ),
        ),
    )
    st.caption(
        "Use the board to compare lifecycle state, then open a card for the "
        "thesis and blockers."
    )
    render_status_cards(_cards(view))
    if detail is not None:
        _render_detail_summary(st, detail)
    _render_board(st, view)
    _render_detail(st, view)
    render_json_debug("Raw JSON / Debug", view.debug_payload)


def _cards(view) -> tuple[StatusCardView, ...]:
    return tuple(
        StatusCardView(
            column.status.title(),
            str(len(column.cards)),
            "ok",
            "Lifecycle column",
        )
        for column in view.columns
    )


def _render_board(st, view) -> None:
    st.subheader("Hypothesis board")
    columns = st.columns(len(view.columns))
    for column_ui, column in zip(columns, view.columns):
        with column_ui:
            st.caption(f"{column.status.title()} • {len(column.cards)}")
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
    with st.container(border=True):
        st.subheader(f"Hypothesis: {detail.name}")
        st.caption(
            f"{detail.status.upper()} • v{detail.version} • "
            f"{detail.explainability_level}"
        )
        _render_detail_fields(st, detail)
        if detail.blockers:
            warning_fn = getattr(st, "warning", None)
            message = "Blockers: " + ", ".join(detail.blockers)
            if callable(warning_fn):
                warning_fn(message)
            else:
                st.write(message)
        else:
            st.caption("No readiness blockers.")
        st.write(f"Latest backtest: {detail.latest_backtest or 'none'}")
        st.write(f"Validation failures: {detail.validation_failures}")
        if detail.strategy_spec is not None:
            st.caption("Strategy specification present")


def _render_detail_summary(st, detail) -> None:
    render_status_cards(_detail_cards(detail))


def _detail_cards(detail) -> tuple[StatusCardView, ...]:
    return (
        StatusCardView(
            "Status",
            detail.status.title(),
            "ok",
            "Lifecycle state",
        ),
        StatusCardView(
            "Readiness",
            detail.readiness.title(),
            "ok" if detail.readiness == "ready" else "warning",
            "Readiness gate",
        ),
        StatusCardView(
            "Backtest",
            detail.latest_backtest or "none",
            "ok" if detail.latest_backtest else "warning",
            "Latest performance",
        ),
        StatusCardView(
            "Validation",
            str(detail.validation_failures),
            "ok" if detail.validation_failures == 0 else "warning",
            "Failed validations",
        ),
    )


def _render_detail_fields(st, detail) -> None:
    columns_fn = getattr(st, "columns", None)
    fields = _detail_fields(detail)
    if not callable(columns_fn):
        for label, value in fields:
            st.write(f"{label}: {value}")
        return
    left, right = columns_fn(2)
    left_fields, right_fields = _detail_field_groups(fields)
    for column, pairs in zip((left, right), (left_fields, right_fields)):
        with column:
            for label, value in pairs:
                st.write(f"{label}: {value}")


def _detail_fields(detail) -> tuple[tuple[str, str], ...]:
    return (
        ("Thesis", detail.thesis or "n/a"),
        ("Horizon", detail.horizon or "n/a"),
        ("Direction policy", detail.direction_policy or "n/a"),
        ("Readiness", detail.readiness),
        ("Required signals", ", ".join(detail.required_signals) or "none"),
        ("Latest backtest", detail.latest_backtest or "none"),
        ("Validation failures", str(detail.validation_failures)),
    )


def _detail_field_groups(
    fields: tuple[tuple[str, str], ...],
) -> tuple[tuple[tuple[str, str], ...], tuple[tuple[str, str], ...]]:
    midpoint = (len(fields) + 1) // 2
    return fields[:midpoint], fields[midpoint:]


def _select_hypothesis(st, hypothesis_id: str) -> None:
    set_selected_hypothesis(st.session_state, hypothesis_id)
    st.rerun()


def _make_select_callback(st, hypothesis_id: str) -> Callable[[], None]:
    def _callback() -> None:
        _select_hypothesis(st, hypothesis_id)

    return _callback
