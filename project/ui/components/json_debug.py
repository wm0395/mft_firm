from __future__ import annotations

import json

from project.ui._streamlit import get_streamlit


def render_json_debug(title: str, payload) -> None:
    st = get_streamlit()
    with st.expander(title, expanded=False):
        if payload is None:
            st.caption("No debug payload.")
            return
        st.write(_payload_summary(payload))
        st.caption("Raw payload for inspection.")
        st.code(
            json.dumps(payload, indent=2, sort_keys=True, default=str),
            language="json",
        )


def _payload_summary(payload) -> str:
    if isinstance(payload, dict):
        keys = tuple(str(key) for key in payload)
        if not keys:
            return "Empty object payload."
        preview = ", ".join(keys[:4])
        if len(keys) > 4:
            preview = f"{preview}, ..."
        return f"Object payload with {len(keys)} top-level fields: {preview}"
    if isinstance(payload, (list, tuple)):
        return f"Sequence payload with {len(payload)} items."
    return f"Payload type: {type(payload).__name__}"
