from __future__ import annotations

from collections.abc import Callable

from project.ui._streamlit import get_streamlit
from project.ui.components.empty_state import render_empty_state
from project.ui.components.hypothesis_card import render_hypothesis_card
from project.ui.components.hypothesis_summary import render_hypothesis_summary
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
            _render_column_header(st, column.status, len(column.cards))
            for card in column.cards:
                render_hypothesis_card(
                    card,
                    on_select=_make_select_callback(st, card.hypothesis_id),
                )


def _render_detail(st, view) -> None:
    detail = view.selected_detail
    if detail is None:
        render_empty_state(
            st,
            "No hypothesis selected.",
            "Pick a hypothesis from the board to inspect the thesis and blockers.",
            "The selected detail panel stays empty until you choose a card.",
            (
                ("Board", f"{len(view.columns)} columns", "ok"),
                ("Selected", "none", "warning"),
                ("Next step", "Open a card", "action"),
            ),
        )
        return
    with st.container(border=True):
        st.subheader(f"Hypothesis: {detail.name}")
        render_hypothesis_summary(st, detail)
        _render_detail_fields(st, detail)
        if detail.blockers:
            warning_fn = getattr(st, "warning", None)
            message = "Blockers: " + ", ".join(detail.blockers)
            if callable(warning_fn):
                warning_fn(message)
            else:
                st.write(message)
        st.write(f"Latest backtest: {detail.latest_backtest or 'none'}")
        st.write(f"Validation failures: {detail.validation_failures}")


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


def _render_column_header(st, status: str, count: int) -> None:
    markdown_fn = getattr(st, "markdown", None)
    if callable(markdown_fn):
        markdown_fn(
            _column_header_html(status, count),
            unsafe_allow_html=True,
        )
        return
    st.write("Lifecycle column")
    st.write(status.title())
    st.write(_hypothesis_count_text(count))


def _column_header_html(status: str, count: int) -> str:
    return "".join(
        [
            "<section style='margin:0 0 0.65rem;padding:0.7rem 0.8rem;"
            "border:1px solid #e2e8f0;border-radius:12px;"
            "background:linear-gradient(180deg,#ffffff 0%,#f8fafc 100%);'>",
            "<div style='color:#64748b;font-size:0.62rem;font-weight:700;"
            "letter-spacing:0.12em;text-transform:uppercase;'>Lifecycle column</div>",
            f"<div style='color:#0f172a;font-size:0.9rem;font-weight:700;"
            f"line-height:1.35;margin-top:0.2rem;'>{status.title()}</div>",
            f"<div style='color:#475569;font-size:0.78rem;line-height:1.45;margin-top:0.1rem;'>"
            f"{_hypothesis_count_text(count)}</div>",
            "</section>",
        ]
    )


def _hypothesis_count_text(count: int) -> str:
    return f"{count} hypothesis" if count == 1 else f"{count} hypotheses"


def _select_hypothesis(st, hypothesis_id: str) -> None:
    set_selected_hypothesis(st.session_state, hypothesis_id)
    st.rerun()


def _make_select_callback(st, hypothesis_id: str) -> Callable[[], None]:
    def _callback() -> None:
        _select_hypothesis(st, hypothesis_id)

    return _callback
