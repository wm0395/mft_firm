from __future__ import annotations

import html
from datetime import date

from project.ui._streamlit import get_streamlit
from project.ui.components.empty_state import render_empty_state
from project.ui.components.evidence_table import render_evidence_table
from project.ui.components.json_debug import render_json_debug
from project.ui.components.page_hero import render_page_hero
from project.ui.components.snapshot_result import render_snapshot_result
from project.ui.components.status_card import render_status_cards
from project.ui.components.workflow_stepper import render_workflow_stepper
from project.ui.views.common import StatusCardView, WorkflowStepView
from project.ui.views.mission_control_actions import recommended_action_text
from project.ui.views.data import create_snapshot, get_data_page_view


def render(repository) -> None:
    st = get_streamlit()
    view = get_data_page_view(repository)
    st.title("Data")
    title, explanation, _ = recommended_action_text(view.workflow_next_command)
    render_page_hero(
        f"{len(view.assets)} assets, {len(view.snapshots)} snapshots, quality "
        f"{view.quality_status.upper()}.",
        f"Mission Control next step: {title}. {explanation}",
        context=(
            ("Assets", len(view.assets)),
            ("Snapshots", len(view.snapshots)),
            ("Quality", view.quality_status.upper()),
            ("Next", title),
        ),
    )
    _render_overview(st, view)
    render_status_cards(_summary_cards(view))
    render_workflow_stepper(_workflow_steps(view))
    _render_table_section(
        st,
        "Asset Universe",
        "Registered assets available for data and research workflows.",
        view.assets,
    )
    _render_table_section(
        st,
        "Data Quality",
        "Freshness and completeness signals by asset.",
        view.quality_rows,
    )
    _render_table_section(
        st,
        "Dataset Snapshots",
        "Reproducible dataset cuts available for research.",
        view.snapshots,
    )
    _render_snapshot_form(st, repository, view)
    render_json_debug("Raw JSON / Debug", view.debug_payload)


def _render_overview(st, view) -> None:
    title, explanation, _ = recommended_action_text(view.workflow_next_command)
    with st.container(border=True):
        st.subheader("At a glance")
        _surface_caption(
            st,
            f"{len(view.assets)} assets • {len(view.snapshots)} snapshots • "
            f"quality {view.quality_status.upper()}",
        )
        _surface_caption(st, f"Mission Control next step: {title}")
        _surface_caption(st, explanation)


def _summary_cards(view) -> tuple[StatusCardView, ...]:
    return (
        StatusCardView("Assets", str(len(view.assets)), "ok", "Loaded assets"),
        StatusCardView(
            "Quality",
            view.quality_status.upper(),
            view.quality_status,
            "Data quality status",
        ),
        StatusCardView(
            "Snapshots",
            str(len(view.snapshots)),
            "ok",
            "Dataset snapshots",
        ),
        StatusCardView(
            "Freshness",
            str(len([row for row in view.quality_rows if row.latest_timestamp])),
            "ok",
            "Symbols with data coverage",
        ),
    )


def _workflow_steps(view) -> tuple[WorkflowStepView, ...]:
    return (
        WorkflowStepView("Data Overview", "ok", f"{len(view.assets)} assets"),
        WorkflowStepView(
            "Market Data Sync",
            "ok" if view.quality_rows else "action required",
            "Freshness and sync",
        ),
        WorkflowStepView(
            "Data Quality",
            "ok" if view.quality_status == "ok" else "action required",
            "Quality report",
        ),
        WorkflowStepView(
            "Dataset Snapshots",
            "ok" if view.snapshots else "action required",
            "Reproducible snapshots",
        ),
        WorkflowStepView("Asset Universe", "ok", "Asset list"),
    )


def _render_snapshot_form(st, repository, view) -> None:
    defaults = view.default_snapshot
    with st.container(border=True):
        st.subheader("Create dataset snapshot")
        _surface_caption(
            st,
            "Define the exact asset set and date range for the next run.",
        )
        _surface_caption(st, "Review the draft values before creating the snapshot.")
        if view.workflow_next_command == "create-dataset-snapshot":
            render_empty_state(
                st,
                "Mission Control recommends creating a dataset snapshot.",
                "Prepare a reproducible cut of the current universe before launching research.",
                "Review the draft values below, then create the snapshot when the inputs look right.",
                (
                    ("Next step", "Confirm inputs", "action"),
                    ("Assets", f"{len(view.assets)} available", "ok"),
                    ("Snapshots", f"{len(view.snapshots)} existing", "warning"),
                ),
            )
        symbol_labels = {asset.symbol: asset.name for asset in view.assets}
        symbols = st.multiselect(
            "Assets",
            options=[asset.symbol for asset in view.assets],
            default=list(defaults.symbols),
            format_func=lambda symbol: _asset_label(symbol, symbol_labels),
        )
        name = st.text_input("Snapshot name", value=defaults.name)
        market = st.text_input("Market", value=defaults.market)
        data_start = st.date_input(
            "Data start",
            value=date.fromisoformat(defaults.data_start),
        )
        data_end = st.date_input(
            "Data end",
            value=date.fromisoformat(defaults.data_end),
        )
        resolution = st.text_input("Resolution", value=defaults.resolution)
        description = st.text_area("Description", value=defaults.description)
        errors = _snapshot_errors(tuple(symbols), data_start, data_end)
        _render_snapshot_preview(
            st,
            name,
            market,
            tuple(symbols),
            data_start,
            data_end,
            resolution,
            description,
            errors,
        )
        render_status_cards(
            _snapshot_cards(tuple(symbols), data_start, data_end, resolution, errors)
        )
        for error in errors:
            st.error(error)
        submitted = st.button("Create Snapshot", type="primary", disabled=bool(errors))
        if submitted:
            try:
                result = create_snapshot(
                    repository,
                    name,
                    market,
                    tuple(symbols),
                    data_start.isoformat(),
                    data_end.isoformat(),
                    resolution,
                    description or None,
                )
            except Exception as error:
                st.error(str(error))
            else:
                st.success(f"Created snapshot {result.dataset_snapshot_id}")
                render_snapshot_result(st, result)


def _snapshot_errors(
    symbols: tuple[str, ...],
    data_start: date,
    data_end: date,
) -> tuple[str, ...]:
    errors = []
    if not symbols:
        errors.append("Select at least one asset before creating a snapshot.")
    if data_start > data_end:
        errors.append("Data start must be on or before data end.")
    return tuple(errors)


def _asset_label(symbol: str, labels: dict[str, str]) -> str:
    name = labels.get(symbol, "")
    return f"{symbol} - {name}" if name else symbol


def _snapshot_cards(
    symbols: tuple[str, ...],
    data_start: date,
    data_end: date,
    resolution: str,
    errors: tuple[str, ...],
) -> tuple[StatusCardView, ...]:
    return (
        StatusCardView(
            "Assets",
            str(len(symbols)),
            "ok" if symbols else "warning",
            "Selected symbols",
        ),
        StatusCardView(
            "Window",
            f"{data_start.isoformat()} -> {data_end.isoformat()}",
            "ok" if data_start <= data_end else "warning",
            "Snapshot date range",
        ),
        StatusCardView(
            "Resolution",
            resolution,
            "ok",
            "Requested bar resolution",
        ),
        StatusCardView(
            "Readiness",
            "Ready" if not errors else "Check inputs",
            "ok" if not errors else "warning",
            "Validation status",
        ),
    )


def _render_snapshot_preview(
    st,
    name: str,
    market: str,
    symbols: tuple[str, ...],
    data_start: date,
    data_end: date,
    resolution: str,
    description: str,
    errors: tuple[str, ...],
) -> None:
    st.subheader("Snapshot preview")
    markdown_fn = getattr(st, "markdown", None)
    if callable(markdown_fn):
        markdown_fn(
            _snapshot_preview_html(
                name,
                market,
                symbols,
                data_start,
                data_end,
                resolution,
                description,
                errors,
            ),
            unsafe_allow_html=True,
        )
    else:
        _surface_caption(st, "Review the draft snapshot before you create it.")
    render_status_cards(
        _snapshot_preview_cards(
            name,
            market,
            symbols,
            data_start,
            data_end,
            resolution,
            errors,
        )
    )
    if description:
        _surface_caption(st, f"Description: {description}")
    else:
        _surface_caption(st, "Description: none provided.")


def _snapshot_preview_html(
    name: str,
    market: str,
    symbols: tuple[str, ...],
    data_start: date,
    data_end: date,
    resolution: str,
    description: str,
    errors: tuple[str, ...],
) -> str:
    rows = [
        "<section style='margin:0.9rem 0 1rem;padding:1rem 1.1rem;border:1px solid "
        "#e2e8f0;border-radius:14px;background:linear-gradient(180deg,#ffffff 0%,"
        "#f8fafc 100%);box-shadow:0 6px 18px rgba(15,23,42,0.05);'>",
        "<div style='color:#64748b;font-size:0.68rem;font-weight:700;"
        "letter-spacing:0.14em;text-transform:uppercase;margin-bottom:0.25rem;'>"
        "Snapshot draft</div>",
        f"<div style='color:#0f172a;font-size:1rem;font-weight:700;line-height:1.3;'>"
        f"{html.escape(name or 'n/a')}</div>",
        f"<div style='color:#475569;font-size:0.85rem;line-height:1.55;margin-top:0.35rem;'>"
        f"{html.escape(description or 'Review the draft snapshot before you create it.')}"
        "</div>",
        "<div style='display:flex;flex-wrap:wrap;gap:0.5rem;margin-top:0.85rem;'>",
        _summary_chip_html("Assets", _selected_assets_value(symbols), _snapshot_tone(symbols)),
        _summary_chip_html("Scope", f"{market or 'n/a'} • {resolution or 'n/a'}", "primary"),
        _summary_chip_html(
            "Window",
            f"{data_start.isoformat()} -> {data_end.isoformat()}",
            _window_tone(data_start, data_end),
        ),
        _summary_chip_html(
            "Readiness",
            "Ready" if not errors else "Check inputs",
            "ok" if not errors else "warning",
        ),
        "</div></section>",
    ]
    return "".join(rows)


def _snapshot_preview_cards(
    name: str,
    market: str,
    symbols: tuple[str, ...],
    data_start: date,
    data_end: date,
    resolution: str,
    errors: tuple[str, ...],
) -> tuple[StatusCardView, ...]:
    return (
        StatusCardView("Snapshot", name or "n/a", "ok", "Draft snapshot name"),
        StatusCardView(
            "Assets",
            _selected_assets_value(symbols),
            "ok" if symbols else "warning",
            f"{len(symbols)} selected assets",
        ),
        StatusCardView(
            "Scope",
            f"{market or 'n/a'} • {resolution or 'n/a'}",
            "ok",
            "Market and bar resolution",
        ),
        StatusCardView(
            "Window",
            f"{data_start.isoformat()} -> {data_end.isoformat()}",
            "ok" if data_start <= data_end else "warning",
            _window_detail(data_start, data_end),
        ),
        StatusCardView(
            "Readiness",
            "Ready" if not errors else "Check inputs",
            "ok" if not errors else "warning",
            "Validation status",
        ),
    )


def _selected_assets_value(symbols: tuple[str, ...]) -> str:
    if not symbols:
        return "none selected"
    if len(symbols) <= 3:
        return ", ".join(symbols)
    remaining = len(symbols) - 2
    return f"{symbols[0]}, {symbols[1]} (+{remaining} more)"


def _window_detail(data_start: date, data_end: date) -> str:
    span_days = (data_end - data_start).days + 1
    if span_days <= 0:
        return "Invalid date range"
    day_label = "day" if span_days == 1 else "days"
    return f"{span_days} {day_label} inclusive"


def _snapshot_tone(symbols: tuple[str, ...]) -> str:
    return "ok" if symbols else "warning"


def _window_tone(data_start: date, data_end: date) -> str:
    return "ok" if data_start <= data_end else "warning"


def _summary_chip_html(label: str, value: str, tone: str) -> str:
    return "".join(
        [
            "<div style='display:flex;flex-direction:column;gap:0.1rem;padding:0.55rem "
            "0.7rem;border-radius:12px;background:#ffffff;border:1px solid #e2e8f0;"
            "min-width:120px;'>",
            f"<div style='color:#64748b;font-size:0.62rem;font-weight:700;"
            f"letter-spacing:0.12em;text-transform:uppercase;'>{html.escape(label)}</div>",
            f"<div style='color:{_tone_color(tone)};font-size:0.84rem;font-weight:700;"
            f"line-height:1.35;word-break:break-word;'>{html.escape(value)}</div>",
            "</div>",
        ]
    )


def _tone_color(tone: str) -> str:
    if tone == "ok":
        return "#15803d"
    if tone == "warning":
        return "#b45309"
    return "#4f46e5"


def _render_table_section(st, title: str, note: str, rows) -> None:
    with st.container(border=True):
        _surface_caption(st, note)
        render_evidence_table(title, rows)


def _surface_caption(st, text: str) -> None:
    caption_fn = getattr(st, "caption", None)
    if callable(caption_fn):
        caption_fn(text)
        return
    write_fn = getattr(st, "write", None)
    if callable(write_fn):
        write_fn(text)
