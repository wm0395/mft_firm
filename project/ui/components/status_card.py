from __future__ import annotations

from project.ui._streamlit import get_streamlit


def render_status_cards(cards) -> None:
    st = get_streamlit()
    columns_fn = getattr(st, "columns", None)
    if not cards or not callable(columns_fn):
        for card in cards:
            render_status_card(card)
        return
    columns = columns_fn(len(cards))
    for column, card in zip(columns, cards):
        with column:
            render_status_card(card)


def render_status_card(card) -> None:
    st = get_streamlit()
    with st.container(border=True):
        metric_fn = getattr(st, "metric", None)
        if callable(metric_fn):
            metric_fn(label=card.label, value=card.value)
        else:
            _surface_text(st, f"{card.label}: {card.value}")
        _surface_text(st, f"{card.state.upper()} • {card.detail}")


def _surface_text(st, text: str) -> None:
    write_fn = getattr(st, "write", None)
    if callable(write_fn):
        write_fn(text)
        return
    caption_fn = getattr(st, "caption", None)
    if callable(caption_fn):
        caption_fn(text)
