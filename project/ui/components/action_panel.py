from __future__ import annotations

from collections.abc import Callable

from project.ui._streamlit import get_streamlit


def render_action_panel(
    title: str,
    explanation: str,
    button_label: str,
    *,
    key: str,
    on_click: Callable[[], None] | None = None,
) -> None:
    st = get_streamlit()
    with st.container(border=True):
        st.subheader(title)
        st.caption("Recommended next step")
        st.write(explanation)
        st.button(button_label, key=key, on_click=on_click, type="primary")
