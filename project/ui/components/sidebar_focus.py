from __future__ import annotations

import html
from collections.abc import Mapping

from project.ui._streamlit import get_streamlit
from project.ui.navigation import page_definition


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
        return
    caption = getattr(sidebar, "caption", None)
    if callable(caption):
        for label, value in items:
            caption(f"{label}: {value}")


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
    rows = [
        "<section class='ui-sidebar-focus'>",
        "<div class='ui-sidebar-focus__eyebrow'>Current focus</div>",
    ]
    for label, value in items:
        rows.append(
            "<div class='ui-sidebar-focus__row'>"
            f"<span class='ui-sidebar-focus__label'>{html.escape(label)}</span>"
            f"<span class='ui-sidebar-focus__value'>{html.escape(value)}</span>"
            "</div>"
        )
    rows.append("</section>")
    return "".join(rows)
