from __future__ import annotations

import html

from project.ui._streamlit import get_streamlit
from project.ui.components.action_panel import render_action_panel
from project.ui.components.json_debug import render_json_debug
from project.ui.components.page_hero import render_page_hero
from project.ui.components.status_card import render_status_cards
from project.ui.components.workflow_stepper import render_workflow_stepper
from project.ui.state import (
    WorkflowContext,
    set_selected_page,
    set_workflow_context,
)
from project.ui.views.common import StatusCardView
from project.ui.views.mission_control import get_mission_control_view


WORKFLOW_PAGE_BY_COMMAND = {
    "init-db": "Data",
    "sync-market-data": "Data",
    "create-dataset-snapshot": "Data",
    "run-strategy-research": "Research",
    "hypothesis-readiness": "Hypotheses",
}


def render(repository) -> None:
    st = get_streamlit()
    view = get_mission_control_view(repository)
    st.title("MFT Mission Control")
    render_page_hero(
        "System health and the next recommended action.",
        f"Next handoff: {_action_title(view.recommended_action)}",
        context=(
            ("Health", getattr(view, "health", "unknown")),
            ("Handoff", _action_title(view.recommended_action)),
            ("Warnings", len(view.warnings)),
            ("Activity", len(view.recent_activity)),
        ),
    )
    _render_overview(st, view)
    render_status_cards(view.cards)
    st.subheader("Workflow progress")
    render_workflow_stepper(view.workflow_steps)
    render_action_panel(
        "Recommended next action",
        view.recommended_action.explanation,
        view.recommended_action.button_label,
        key="mission-control-action",
        on_click=lambda: _navigate_to_action(st, view.recommended_action),
    )
    st.subheader("Recent warnings")
    _render_warnings(st, view.warnings)
    st.subheader("Recent activity")
    _render_activity(st, view.recent_activity)
    render_json_debug("Raw JSON / Debug", view.debug_payload)


def _render_overview(st, view) -> None:
    health = getattr(view, "health", "unknown")
    action = getattr(view, "recommended_action", None)
    action_title = _action_title(action)
    action_explanation = getattr(action, "explanation", "")
    with st.container(border=True):
        st.subheader("At a glance")
        render_status_cards(_overview_cards(view))
        _surface_caption(st, f"Health: {health}")
        _surface_caption(st, f"Next step: {action_title}")
        _surface_caption(st, action_explanation)


def _overview_cards(view) -> tuple[StatusCardView, ...]:
    health = str(getattr(view, "health", "unknown"))
    action = getattr(view, "recommended_action", None)
    warnings = tuple(getattr(view, "warnings", ()))
    activity = tuple(getattr(view, "recent_activity", ()))
    return (
        StatusCardView(
            "Health",
            health,
            _health_state(health),
            "Current system posture",
        ),
        StatusCardView(
            "Handoff",
            _action_title(action),
            "action",
            getattr(action, "explanation", "Recommended next step"),
        ),
        StatusCardView(
            "Warnings",
            str(len(warnings)),
            "warning" if warnings else "ok",
            "Items needing attention",
        ),
        StatusCardView(
            "Activity",
            str(len(activity)),
            "ok" if activity else "warning",
            "Recent operational events",
        ),
    )


def _render_warnings(st, warnings) -> None:
    with st.container(border=True):
        _surface_caption(st, "Review these items before handing off the workflow.")
        if not warnings:
            _surface_caption(st, "No current warnings.")
            return
        markdown_fn = getattr(st, "markdown", None)
        if callable(markdown_fn):
            _render_html(markdown_fn, _warning_cards_html(warnings))
            return
        for warning in warnings:
            _surface_caption(st, warning.title)
            st.write(f"{warning.title}: {warning.why_it_matters}")
            _surface_caption(st, warning.recommended_action)


def _render_activity(st, activity) -> None:
    with st.container(border=True):
        _surface_caption(st, "Recent operational activity.")
        if not activity:
            _surface_caption(st, "No recent activity recorded.")
            return
        markdown_fn = getattr(st, "markdown", None)
        if callable(markdown_fn):
            _render_html(markdown_fn, _activity_cards_html(activity))
            return
        for item in activity:
            _surface_caption(st, item.title)
            st.write(f"{item.title}: {item.detail}")
            _surface_caption(st, item.timestamp)


def _navigate_to_action(st, action: object) -> None:
    command = _action_command(action)
    target_page = _target_page(action, command)
    set_selected_page(st.session_state, target_page)
    set_workflow_context(
        st.session_state,
        _workflow_context(action, command, target_page),
    )
    st.rerun()


def _action_command(action: object) -> str:
    if isinstance(action, str):
        return action
    return str(getattr(action, "command", ""))


def _target_page(action: object, command: str) -> str:
    structured_page = _action_page(action)
    if structured_page:
        return structured_page
    return WORKFLOW_PAGE_BY_COMMAND.get(command, "Trade Ideas")


def _action_page(action: object) -> str:
    if isinstance(action, str):
        return ""
    page = getattr(action, "target_page", "") or getattr(action, "page", "")
    return str(page)


def _workflow_context(
    action: object,
    command: str,
    target_page: str,
) -> WorkflowContext:
    return WorkflowContext(
        source_page="Mission Control",
        target_page=target_page,
        command=command,
        title=_action_text(action, "title"),
        explanation=_action_text(action, "explanation"),
        button_label=_action_text(action, "button_label"),
    )


def _action_text(action: object, field: str) -> str:
    if isinstance(action, str):
        return ""
    return str(getattr(action, field, ""))


def _action_title(action: object | None) -> str:
    if action is None:
        return "unknown"
    title = getattr(action, "title", "") or getattr(action, "button_label", "")
    if title:
        return str(title)
    command = getattr(action, "command", "")
    return str(command) if command else "unknown"


def _health_state(health: str) -> str:
    normalized = health.strip().lower()
    if normalized == "ok":
        return "ok"
    if normalized == "warning":
        return "warning"
    if normalized == "critical":
        return "warning"
    return "action"


def _surface_caption(st, text: str) -> None:
    caption_fn = getattr(st, "caption", None)
    if callable(caption_fn):
        caption_fn(text)
        return
    write_fn = getattr(st, "write", None)
    if callable(write_fn):
        write_fn(text)


def _warning_cards_html(warnings) -> str:
    items = [
        (warning.title, warning.why_it_matters, warning.recommended_action)
        for warning in warnings
    ]
    return _record_cards_html("Warnings", items, "warning")


def _activity_cards_html(activity) -> str:
    items = [
        (item.title, item.detail, item.timestamp)
        for item in activity
    ]
    return _record_cards_html("Activity", items, "activity")


def _record_cards_html(
    eyebrow: str,
    items: tuple[tuple[str, str, str], ...] | list[tuple[str, str, str]],
    variant: str,
) -> str:
    cards = [
        "<section class='ui-record-list'>",
        f"<div class='ui-record-list__eyebrow'>{html.escape(eyebrow)}</div>",
        "<div class='ui-record-list__grid'>",
    ]
    for title, body, meta in items:
        cards.append(
            "<article class='ui-record-card "
            f"ui-record-card--{html.escape(variant)}'>"
            f"<div class='ui-record-card__title'>{html.escape(title)}</div>"
            f"<div class='ui-record-card__body'>{html.escape(body)}</div>"
            f"<div class='ui-record-card__meta'>{html.escape(meta)}</div>"
            "</article>"
        )
    cards.append("</div></section>")
    return "".join(cards)


def _render_html(markdown_fn, html_text: str) -> None:
    try:
        markdown_fn(html_text, unsafe_allow_html=True)
    except TypeError:
        markdown_fn(html_text)
