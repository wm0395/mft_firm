from __future__ import annotations

import html

from project.ui._streamlit import get_streamlit


def render_workflow_stepper(steps) -> None:
    st = get_streamlit()
    columns_fn = getattr(st, "columns", None)
    markdown_fn = getattr(st, "markdown", None)
    if not steps:
        return
    if callable(markdown_fn):
        markdown_fn(_stepper_html(steps), unsafe_allow_html=True)
        return
    if not callable(columns_fn):
        for step in steps:
            _render_step(step)
        return
    columns = columns_fn(len(steps))
    for column, step in zip(columns, steps):
        with column:
            _render_step(step)


def _render_step(step) -> None:
    st = get_streamlit()
    with st.container(border=True):
        st.caption(step.label)
        st.write(f"{step.state.upper()} • {step.detail}")


def _stepper_html(steps) -> str:
    rows = [
        "<section class='ui-stepper'>",
        "<div class='ui-stepper__eyebrow'>Workflow path</div>",
        "<div class='ui-stepper__grid'>",
    ]
    for index, step in enumerate(steps, start=1):
        rows.append(_step_html(step, index))
    rows.append("</div></section>")
    return "".join(rows)


def _step_html(step, index: int) -> str:
    state_slug = _state_slug(step.state)
    return "".join(
        [
            f"<article class='ui-stepper__card ui-stepper__card--{state_slug}'>",
            "<div class='ui-stepper__header'>",
            f"<span class='ui-stepper__index'>{index:02d}</span>",
            f"<span class='ui-stepper__state'>{html.escape(_state_label(step.state))}</span>",
            "</div>",
            f"<div class='ui-stepper__label'>{html.escape(step.label)}</div>",
            f"<div class='ui-stepper__detail'>{html.escape(step.detail)}</div>",
            "</article>",
        ]
    )


def _state_label(state: str) -> str:
    return state.replace("_", " ").title()


def _state_slug(state: str) -> str:
    return state.strip().lower().replace(" ", "-").replace("_", "-")
