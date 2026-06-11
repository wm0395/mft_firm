from __future__ import annotations

import html
from collections.abc import Mapping

from project.ui._streamlit import get_streamlit
from project.ui.navigation import page_definition
from project.ui.state import set_selected_page


def render_sidebar_focus(
    repository: object,
    state: Mapping[str, object],
    page: str,
) -> None:
    st = get_streamlit()
    sidebar = getattr(st, "sidebar", None)
    if sidebar is None:
        return
    items = _focus_items(repository, state, page)
    markdown = getattr(sidebar, "markdown", None)
    if callable(markdown):
        markdown(_focus_html(items), unsafe_allow_html=True)
    else:
        caption = getattr(sidebar, "caption", None)
        if callable(caption):
            for label, value in items:
                caption(f"{label}: {value}")
    _render_research_jump(st, page)


def _focus_items(
    repository: object,
    state: Mapping[str, object],
    page: str,
) -> tuple[tuple[str, str], ...]:
    items = [
        ("Current page", page),
        ("Description", page_definition(page).description),
        ("Workflow", _workflow_value(state)),
    ]
    selected = _selected_items(repository, state)
    return tuple((*items, *selected))


def _selected_items(
    repository: object,
    state: Mapping[str, object],
) -> tuple[tuple[str, str], ...]:
    items: list[tuple[str, str]] = []
    hypothesis_id = str(state.get("selected_hypothesis_id", "") or "")
    trade_id = str(state.get("selected_trade_id", "") or "")
    evaluation_id = str(state.get("selected_evaluation_id", "") or "")
    project_id = str(state.get("selected_research_project_id", "") or "")
    if hypothesis_id:
        items.append(("Hypothesis", _hypothesis_value(repository, hypothesis_id)))
    if trade_id:
        items.append(("Trade", _trade_value(repository, trade_id)))
    if evaluation_id:
        items.append(("Evaluation", _evaluation_value(repository, evaluation_id)))
    if project_id:
        items.append(("Research project", _project_value(repository, project_id)))
    if not items:
        items.append(("Selection", "No focused item selected."))
    return tuple(items)


def _workflow_value(state: Mapping[str, object]) -> str:
    context = state.get("workflow_context")
    if context is None:
        return "No active handoff."
    source = _context_text(context, "source_page")
    target = _context_text(context, "target_page")
    title = (
        _context_text(context, "title")
        or _context_text(context, "command")
        or _context_text(context, "next_recommended_command")
    )
    if source and target:
        headline = title or "Workflow handoff"
        return f"{headline} ({source} -> {target})"
    return title or "Workflow handoff active."


def _context_text(context: object, attribute: str) -> str:
    if isinstance(context, Mapping):
        value = context.get(attribute, "")
    else:
        value = getattr(context, attribute, "")
    return str(value or "")


def _hypothesis_value(repository: object, hypothesis_id: str) -> str:
    getter = getattr(repository, "get_hypothesis", None)
    if callable(getter):
        hypothesis = getter(hypothesis_id)
        if hypothesis is not None:
            return f"{hypothesis.name} • {hypothesis.status}"
    return hypothesis_id


def _trade_value(repository: object, trade_id: str) -> str:
    getter = getattr(repository, "get_trade_ideas", None)
    if not callable(getter):
        return trade_id
    for trade in getter():
        if trade.trade_id == trade_id:
            asset_symbol = _asset_symbol(repository, trade.asset_id)
            state = _trade_state(repository, trade.trade_id)
            return f"{asset_symbol} {trade.direction} • {state}"
    return trade_id


def _evaluation_value(repository: object, evaluation_id: str) -> str:
    getter = getattr(repository, "get_hypothesis_evaluations", None)
    if not callable(getter):
        return evaluation_id
    for evaluation in getter():
        if evaluation.evaluation_id == evaluation_id:
            asset_symbol = _asset_symbol(repository, evaluation.asset_id)
            return (
                f"{asset_symbol} {evaluation.direction} • "
                f"{evaluation.hypothesis_id}"
            )
    return evaluation_id


def _project_value(repository: object, project_id: str) -> str:
    getter = getattr(repository, "get_research_projects", None)
    if not callable(getter):
        return project_id
    for project in getter():
        if project.project_id == project_id:
            return f"{project.name} • {project.status}"
    return project_id


def _asset_symbol(repository: object, asset_id: str) -> str:
    getter = getattr(repository, "list_assets", None)
    if not callable(getter):
        return asset_id
    for asset in getter():
        if asset.asset_id == asset_id:
            return asset.symbol
    return asset_id


def _trade_state(repository: object, trade_id: str) -> str:
    getter = getattr(repository, "get_decisions", None)
    if not callable(getter):
        return "pending review"
    return "reviewed" if getter(trade_id) else "pending review"


def _focus_html(items: tuple[tuple[str, str], ...]) -> str:
    page = _focus_value(items, "Current page")
    description = _focus_value(items, "Description")
    chips = [_chip_html("Workflow", _focus_value(items, "Workflow"), "workflow")]
    selection_items = items[3:]
    if len(selection_items) == 1 and selection_items[0][0] == "Selection":
        chips.append(_chip_html("Selection", selection_items[0][1], "idle"))
    else:
        for label, value in selection_items:
            chips.append(_chip_html(label, value, "selection"))
    rows = [
        "<style>",
        ".ui-sidebar-focus{margin:0 1rem 0.75rem;padding:0.9rem 0.95rem;",
        "border:1px solid rgba(226,232,240,0.95);border-radius:14px;",
        "background:linear-gradient(180deg,#ffffff 0%,#f8fafc 100%);",
        "box-shadow:0 8px 18px rgba(15,23,42,0.06);}",
        ".ui-sidebar-focus__eyebrow{color:#64748b;font-size:0.67rem;font-weight:700;",
        "letter-spacing:0.16em;text-transform:uppercase;margin-bottom:0.25rem;}",
        ".ui-sidebar-focus__title{color:#0f172a;font-size:1rem;font-weight:700;",
        "letter-spacing:-0.02em;line-height:1.25;}",
        ".ui-sidebar-focus__description{color:#475569;font-size:0.82rem;",
        "line-height:1.5;margin-top:0.35rem;}",
        ".ui-sidebar-focus__chips{display:flex;flex-direction:column;gap:0.45rem;",
        "margin-top:0.75rem;}",
        ".ui-sidebar-focus__chip{display:flex;flex-direction:column;gap:0.15rem;",
        "padding:0.55rem 0.65rem;border-radius:12px;border:1px solid #e2e8f0;",
        "background:#ffffff;}",
        ".ui-sidebar-focus__chip--workflow{background:#eef2ff;border-color:rgba(99,102,241,0.18);}",
        ".ui-sidebar-focus__chip--selection{background:#f0fdf4;border-color:rgba(34,197,94,0.18);}",
        ".ui-sidebar-focus__chip--idle{background:#f8fafc;border-color:#e2e8f0;}",
        ".ui-sidebar-focus__chip-label{color:#64748b;font-size:0.62rem;font-weight:700;",
        "letter-spacing:0.12em;text-transform:uppercase;}",
        ".ui-sidebar-focus__chip-value{color:#0f172a;font-size:0.8rem;font-weight:600;",
        "line-height:1.4;word-break:break-word;}",
        "</style>",
        "<section class='ui-sidebar-focus'>",
        "<div class='ui-sidebar-focus__eyebrow'>Current focus</div>",
        f"<div class='ui-sidebar-focus__title'>{html.escape(page)}</div>",
        (
            f"<div class='ui-sidebar-focus__description'>"
            f"{html.escape(description)}</div>"
        ),
        "<div class='ui-sidebar-focus__chips'>",
        *chips,
        "</div></section>",
    ]
    return "".join(rows)


def _focus_value(items: tuple[tuple[str, str], ...], label: str) -> str:
    for item_label, value in items:
        if item_label == label:
            return value
    return ""


def _render_research_jump(st, page: str) -> None:
    if page == "Research":
        return
    sidebar = getattr(st, "sidebar", None)
    button = getattr(sidebar, "button", None)
    if not callable(button):
        return
    if button("Go to Research", key="sidebar-go-research", type="primary", use_container_width=True):
        set_selected_page(st.session_state, "Research")
        rerun = getattr(st, "rerun", None)
        if callable(rerun):
            rerun()


def _chip_html(label: str, value: str, variant: str) -> str:
    return "".join(
        [
            f"<div class='ui-sidebar-focus__chip ui-sidebar-focus__chip--{variant}'>",
            f"<span class='ui-sidebar-focus__chip-label'>{html.escape(label)}</span>",
            f"<span class='ui-sidebar-focus__chip-value'>{html.escape(value)}</span>",
            "</div>",
        ]
    )
