from __future__ import annotations

import html

from project.ui._streamlit import get_streamlit
from project.ui.components.evidence_table import render_evidence_table
from project.ui.components.json_debug import render_json_debug
from project.ui.components.page_hero import render_page_hero
from project.ui.components.status_card import render_status_cards
from project.ui.components.table_rows import build_table_rows
from project.ui.views.common import StatusCardView
from project.ui.views.positions import (
    PositionsPageView,
    PositionDetailView,
    PositionTableRowView,
    get_positions_page_view,
)


STATUS_FILTERS = ("all", "open", "closed")


def render(repository) -> None:
    st = get_streamlit()
    st.title("Positions")
    status_filter = _status_filter(st)
    view = get_positions_page_view(repository)
    render_page_hero(
        f"{len(view.positions)} positions, {view.open_count} open, realized PnL "
        f"{_money(view.realized_pnl)}.",
        f"Filter: {status_filter}",
        context=(
            ("Total", len(view.positions)),
            ("Open", view.open_count),
            ("Closed", view.closed_count),
            ("PnL", _money(view.realized_pnl)),
        ),
    )
    st.caption("Use the filter to narrow the list, then pick one position to inspect.")
    render_status_cards(_cards(view))
    filtered_positions = _filter_positions(view.positions, status_filter)
    if not filtered_positions:
        st.info("No positions match the current filter.")
        st.caption("Try a different filter state to surface open or closed positions.")
        render_evidence_table("Positions", ())
        render_json_debug("Raw JSON / Debug", view.debug_payload)
        return
    selected_position_id = _selected_position_id(st, filtered_positions)
    detail = _selected_detail(filtered_positions, selected_position_id)
    if detail is not None:
        _render_detail_summary(st, detail)
        _render_detail(st, detail)
    st.subheader("Positions")
    st.dataframe(
        _positions_dataframe(filtered_positions),
        use_container_width=True,
    )
    render_json_debug("Raw JSON / Debug", view.debug_payload)


def _cards(view: PositionsPageView) -> tuple[StatusCardView, ...]:
    total = len(view.positions)
    realized_pnl = _money(view.realized_pnl)
    return (
        StatusCardView("Positions", str(total), "ok", "Tracked positions"),
        StatusCardView(
            "Open",
            str(view.open_count),
            "action" if view.open_count > 0 else "ok",
            "Unclosed positions",
        ),
        StatusCardView("Closed", str(view.closed_count), "ok", "Closed positions"),
        StatusCardView(
            "Realized PnL",
            realized_pnl,
            _pnl_state(view.realized_pnl),
            "Closed positions with PnL",
        ),
    )


def _filter_positions(
    positions: tuple[PositionDetailView, ...],
    status_filter: str,
) -> tuple[PositionDetailView, ...]:
    return tuple(
        position
        for position in positions
        if status_filter == "all" or position.status == status_filter
    )


def _selected_detail(
    positions: tuple[PositionDetailView, ...],
    position_id: str | None,
) -> PositionDetailView | None:
    if position_id is None:
        return None
    for detail in positions:
        if detail.position_id == position_id:
            return detail
    return None


def _status_filter(st) -> str:
    selectbox = getattr(st, "selectbox", None)
    if not callable(selectbox):
        return "all"
    return selectbox(
        "Status filter",
        STATUS_FILTERS,
        index=0,
        key="positions_status_filter",
    )


def _selected_position_id(
    st,
    positions: tuple[PositionDetailView, ...],
) -> str | None:
    options = [row.position_id for row in positions]
    if not options:
        return None
    current = _current_position_id(st, options[0], options)
    selectbox = getattr(st, "selectbox", None)
    if not callable(selectbox):
        return None
    return selectbox(
        "Position",
        options,
        index=options.index(current),
        key="positions_selected_position_id",
    )


def _table_rows(
    positions: tuple[PositionDetailView, ...],
) -> tuple[PositionTableRowView, ...]:
    return tuple(_table_row(position) for position in positions)


def _table_row(position: PositionDetailView) -> PositionTableRowView:
    return PositionTableRowView(
        position.position_id,
        position.trade_id,
        position.asset_symbol,
        position.hypothesis_name,
        position.direction,
        position.status,
        _money(position.entry_price),
        _money(position.exit_price),
        _money(position.pnl),
        position.trade_timestamp,
    )


def _render_detail(st, detail: PositionDetailView) -> None:
    with st.container(border=True):
        st.subheader("Position detail")
        st.caption(
            f"{detail.asset_symbol} • {detail.direction} • {detail.status}"
        )
        _render_detail_fields(st, detail)
        if detail.status == "open":
            st.caption("Open positions do not have an exit price or realized PnL yet.")
        if detail.signals_snapshot:
            with st.expander("Linked trade snapshot", expanded=False):
                st.json(detail.signals_snapshot)


def _render_detail_summary(st, detail: PositionDetailView) -> None:
    markdown_fn = getattr(st, "markdown", None)
    if callable(markdown_fn):
        html_text = _detail_summary_html(detail)
        try:
            markdown_fn(html_text, unsafe_allow_html=True)
        except TypeError:
            markdown_fn(html_text)
        return
    caption_fn = getattr(st, "caption", None)
    if callable(caption_fn):
        caption_fn("Selected position")
    write_fn = getattr(st, "write", None)
    if not callable(write_fn):
        return
    write_fn(f"Position: {detail.position_id} • Trade {detail.trade_id}")
    write_fn(f"Asset: {detail.asset_symbol} • {detail.asset_name or 'n/a'}")
    write_fn(
        f"Hypothesis: {detail.hypothesis_name} • {detail.hypothesis_id or 'n/a'}"
    )
    write_fn(
        "Outcome: "
        f"{_position_outcome_value(detail)} • {detail.direction.title()} • "
        f"{detail.status.title()}"
    )


def _detail_summary_html(detail: PositionDetailView) -> str:
    cards = (
        ("Position", detail.position_id, f"Trade {detail.trade_id}", ""),
        ("Asset", detail.asset_symbol, detail.asset_name or "n/a", ""),
        ("Hypothesis", detail.hypothesis_name, detail.hypothesis_id or "n/a", ""),
        (
            "Outcome",
            _position_outcome_value(detail),
            f"{detail.direction.title()} • {detail.status.title()}",
            _outcome_variant(detail),
        ),
    )
    return _record_cards_html("Selected position", cards)


def _record_cards_html(
    eyebrow: str,
    cards: tuple[tuple[str, str, str, str], ...],
) -> str:
    parts = [
        "<section class='ui-record-list'>",
        f"<div class='ui-record-list__eyebrow'>{html.escape(eyebrow)}</div>",
        "<div class='ui-record-list__grid'>",
    ]
    for title, body, meta, variant in cards:
        card_class = "ui-record-card"
        if variant:
            card_class = f"{card_class} {variant}"
        parts.append(
            f"<article class='{card_class}'>"
            f"<div class='ui-record-card__title'>{html.escape(title)}</div>"
            f"<div class='ui-record-card__body'>{html.escape(body)}</div>"
            f"<div class='ui-record-card__meta'>{html.escape(meta)}</div>"
            "</article>"
        )
    parts.append("</div></section>")
    return "".join(parts)


def _outcome_variant(detail: PositionDetailView) -> str:
    if detail.pnl is None or detail.status == "open":
        return "ui-record-card--warning"
    if detail.pnl > 0:
        return "ui-record-card--success"
    if detail.pnl < 0:
        return "ui-record-card--warning"
    return ""


def _position_outcome_value(detail: PositionDetailView) -> str:
    if detail.pnl is None or detail.status == "open":
        return "Open position"
    return _money(detail.pnl)


def _render_detail_fields(st, detail: PositionDetailView) -> None:
    columns_fn = getattr(st, "columns", None)
    fields = _detail_fields(detail)
    if not callable(columns_fn):
        for label, value in fields:
            st.write(f"{label}: {value}")
        return
    left, right = columns_fn(2)
    for column, pair in zip((left, right), _detail_field_groups(fields), strict=False):
        with column:
            for label, value in pair:
                st.write(f"{label}: {value}")


def _detail_fields(detail: PositionDetailView) -> tuple[tuple[str, str], ...]:
    return (
        ("Position ID", detail.position_id),
        ("Trade ID", detail.trade_id),
        ("Asset", _asset_label(detail.asset_symbol, detail.asset_name)),
        ("Hypothesis", _asset_label(detail.hypothesis_name, detail.hypothesis_id)),
        ("Direction", detail.direction),
        ("Status", detail.status),
        ("Trade timestamp", detail.trade_timestamp or "n/a"),
        ("Entry price", _money(detail.entry_price)),
        ("Exit price", _money(detail.exit_price)),
        ("PnL", _money(detail.pnl)),
    )


def _detail_field_groups(
    fields: tuple[tuple[str, str], ...],
) -> tuple[tuple[tuple[str, str], ...], tuple[tuple[str, str], ...]]:
    midpoint = (len(fields) + 1) // 2
    return fields[:midpoint], fields[midpoint:]


def _money(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.2f}"


def _pnl_state(value: float | None) -> str:
    if value is None:
        return "warning"
    if value > 0:
        return "ok"
    if value < 0:
        return "warning"
    return "ok"


def _asset_label(primary: str, secondary: str) -> str:
    parts = [part for part in (primary, secondary) if part]
    return " ".join(parts) if parts else "n/a"


def _positions_dataframe(positions: tuple[PositionDetailView, ...]):
    return build_table_rows(_table_rows(positions))


def _current_position_id(
    st,
    default: str,
    options: list[str],
) -> str:
    session_state = getattr(st, "session_state", None)
    if session_state is None:
        return default
    current = session_state.get("positions_selected_position_id")
    if current in options:
        return str(current)
    session_state["positions_selected_position_id"] = default
    return default
