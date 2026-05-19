from __future__ import annotations

import pandas as pd  # type: ignore[import-untyped]

from project.ui._streamlit import get_streamlit


def render_evidence_table(title: str, rows) -> None:
    st = get_streamlit()
    st.subheader(title)
    if not rows:
        st.caption("No records.")
        return
    st.dataframe(pd.DataFrame([_row_data(row) for row in rows]), use_container_width=True)


def _row_data(row) -> dict[str, object]:
    if isinstance(row, dict):
        return row
    return row.__dict__
