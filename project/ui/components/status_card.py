from __future__ import annotations

from project.ui._streamlit import get_streamlit


def render_status_cards(cards) -> None:
    st = get_streamlit()
    columns = st.columns(len(cards)) if cards else ()
    for column, card in zip(columns, cards):
        with column:
            render_status_card(card)


def render_status_card(card) -> None:
    st = get_streamlit()
    with st.container(border=True):
        st.caption(card.label)
        st.metric(label=card.label, value=card.value)
        st.caption(card.state.upper())
        st.caption(card.detail)
