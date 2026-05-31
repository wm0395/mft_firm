from __future__ import annotations

from project.ui._streamlit import get_streamlit
from project.ui.components.table_rows import build_table_rows


def render_evidence_table(title: str, rows) -> None:
    st = get_streamlit()
    rows = tuple(rows)
    with st.container(border=True):
        st.subheader(title)
        if not rows:
            st.caption("No records captured yet.")
            return
        frame = build_table_rows(rows)
        st.caption(f"{len(rows)} records")
        st.dataframe(frame, use_container_width=True)
