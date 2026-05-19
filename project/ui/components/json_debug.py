from __future__ import annotations

import json

from project.ui._streamlit import get_streamlit


def render_json_debug(title: str, payload) -> None:
    st = get_streamlit()
    with st.expander(title, expanded=False):
        if payload is None:
            st.caption("No debug payload.")
            return
        st.code(json.dumps(payload, indent=2, sort_keys=True, default=str), language="json")
