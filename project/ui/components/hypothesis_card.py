from __future__ import annotations

from collections.abc import Callable

from project.ui._streamlit import get_streamlit


def render_hypothesis_card(card, on_select: Callable[[], None] | None = None) -> None:
    st = get_streamlit()
    with st.container(border=True):
        st.caption(f"{card.status.upper()} • v{card.version}")
        st.subheader(card.name)
        st.caption(card.hypothesis_id)
        st.caption(f"Readiness: {card.readiness}")
        st.write(f"Required signals: {', '.join(card.required_signals) or 'none'}")
        if card.blockers:
            st.caption(f"Blockers: {', '.join(card.blockers)}")
        else:
            st.caption("No readiness blockers.")
        if on_select is not None and st.button(
            "Open",
            key=f"open-{card.hypothesis_id}",
        ):
            on_select()
