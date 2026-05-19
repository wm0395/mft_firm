from __future__ import annotations

from project.ui._streamlit import get_streamlit


def render_workflow_stepper(steps) -> None:
    st = get_streamlit()
    columns = st.columns(len(steps)) if steps else ()
    for column, step in zip(columns, steps):
        with column:
            with st.container(border=True):
                st.caption(step.label)
                st.write(step.state.upper())
                st.caption(step.detail)
