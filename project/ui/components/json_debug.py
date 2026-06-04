from __future__ import annotations

import html
import json

from project.ui._streamlit import get_streamlit


def render_json_debug(title: str, payload) -> None:
    st = get_streamlit()
    with st.expander(title, expanded=False):
        if payload is None:
            st.caption("No debug payload.")
            return
        summary = _payload_summary(payload)
        markdown_fn = getattr(st, "markdown", None)
        if callable(markdown_fn):
            markdown_fn(_summary_html(summary), unsafe_allow_html=True)
        else:
            st.write(summary)
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


def _summary_html(summary: str) -> str:
    return "".join(
        [
            "<section style='margin:0.25rem 0 0.75rem;padding:0.85rem 1rem;"
            "border:1px solid #e2e8f0;border-radius:12px;"
            "background:linear-gradient(180deg,#ffffff 0%,#f8fafc 100%);'>",
            "<div style='color:#64748b;font-size:0.68rem;font-weight:700;"
            "letter-spacing:0.14em;text-transform:uppercase;margin-bottom:0.25rem;'>"
            "Debug summary</div>",
            f"<div style='color:#0f172a;font-size:0.92rem;font-weight:700;"
            f"line-height:1.45;'>{html.escape(summary)}</div>",
            "</section>",
        ]
    )
