from __future__ import annotations

from project.ui._streamlit import get_streamlit
from project.ui.components.dossier_summary import render_dossier_summary
from project.ui.components.evidence_table import render_evidence_table
from project.ui.components.launch_preview import launch_hero_context
from project.ui.components.launch_preview import render_launch_preview
from project.ui.components.json_debug import render_json_debug
from project.ui.components.page_hero import render_page_hero
from project.ui.components.status_card import render_status_cards
from project.ui.views.common import StatusCardView
from project.ui_services.research_views import (
    get_research_page_view,
    launch_research_run,
)


def render(repository) -> None:
    st = get_streamlit()
    view = get_research_page_view(repository)
    st.title("Research")
    render_page_hero(
        (
            f"{len(view.projects)} projects, {len(view.runs)} runs, "
            f"{len(view.candidates)} candidates."
        ),
        view.launch.workflow_note,
        context=launch_hero_context(view.launch),
    )
    render_status_cards(_cards(view))
    _render_launch_panel(st, repository, view)
    _render_dossier(st, view.strategy_dossier)
    _render_table_section(
        st,
        "Research Projects",
        "Project records tied to strategy work.",
        view.projects,
    )
    _render_table_section(
        st,
        "Research Runs",
        "Historical run executions and outcomes.",
        view.runs,
    )
    _render_table_section(
        st,
        "Strategy Candidates",
        "Draft and promoted candidates in review.",
        view.candidates,
    )
    _render_table_section(
        st,
        "Dataset Snapshots",
        "Snapshot choices available for launch.",
        view.launch.snapshots,
    )
    _render_table_section(
        st,
        "Launch Hypotheses",
        "Actionable hypotheses in scope for launch.",
        view.launch.hypotheses,
    )
    render_json_debug("Raw JSON / Debug", view.debug_payload)


def _cards(view) -> tuple[StatusCardView, ...]:
    return (
        StatusCardView(
            "Projects",
            str(len(view.projects)),
            "ok" if view.projects else "warning",
            "Research projects",
        ),
        StatusCardView(
            "Runs",
            str(len(view.runs)),
            "ok" if view.runs else "warning",
            "Research run history",
        ),
        StatusCardView(
            "Candidates",
            str(len(view.candidates)),
            "ok" if view.candidates else "warning",
            "Strategy candidates",
        ),
        StatusCardView(
            "Snapshots",
            str(len(view.launch.snapshots)),
            "ok" if view.launch.snapshots else "warning",
            "Dataset snapshot options",
        ),
        StatusCardView(
            "Hypotheses",
            str(len(view.launch.hypotheses)),
            "ok" if view.launch.hypotheses else "warning",
            "Launch hypothesis options",
        ),
    )


def _render_launch_panel(st, repository, view) -> None:
    launch = view.launch
    with st.container(border=True):
        st.subheader("Guided research run")
        render_status_cards(_launch_cards(launch))
        if not (launch.assets and launch.snapshots and launch.hypotheses):
            st.info(
                "Add an asset, dataset snapshot, and actionable hypothesis to "
                "launch research."
            )
            return
        (
            asset_symbol,
            snapshot_id,
            hypothesis_id,
            start_date,
            end_date,
            include_testing,
            include_draft,
            submitted,
        ) = _launch_form_values(st, launch)
        if submitted:
            _launch_research(
                st,
                repository,
                hypothesis_id,
                asset_symbol,
                snapshot_id,
                start_date,
                end_date,
                include_testing,
                include_draft,
            )


def _launch_form_values(
    st,
    launch,
) -> tuple[str, str, str, str, str, bool, bool, bool]:
    with st.form("research-launch-form"):
        asset_symbol, snapshot_id, hypothesis_id = _launch_selection_values(st, launch)
        start_date, end_date, include_testing, include_draft = _launch_date_values(
            st, launch, hypothesis_id
        )
        _render_launch_preview(
            st,
            launch,
            asset_symbol,
            snapshot_id,
            hypothesis_id,
            start_date,
            end_date,
            include_testing,
            include_draft,
            render_status_cards,
        )
        _launch_preview_block(
            st,
            hypothesis_id,
            asset_symbol,
            snapshot_id,
            start_date,
            end_date,
            include_testing,
            include_draft,
        )
        submitted = st.form_submit_button("Launch research")
    return (
        asset_symbol,
        snapshot_id,
        hypothesis_id,
        start_date,
        end_date,
        include_testing,
        include_draft,
        submitted,
    )


def _launch_selection_values(st, launch) -> tuple[str, str, str]:
    asset_symbol = _select_value(
        st,
        "Asset",
        tuple(asset.symbol for asset in launch.assets),
        launch.default_asset_symbol,
    )
    snapshot_id = _select_value(
        st,
        "Dataset snapshot",
        tuple(snapshot.dataset_snapshot_id for snapshot in launch.snapshots),
        launch.default_dataset_snapshot_id,
    )
    hypothesis_id = _select_value(
        st,
        "Hypothesis",
        tuple(hypothesis.hypothesis_id for hypothesis in launch.hypotheses),
        launch.default_hypothesis_id,
    )
    return asset_symbol, snapshot_id, hypothesis_id


def _launch_date_values(
    st,
    launch,
    hypothesis_id: str,
) -> tuple[str, str, bool, bool]:
    start_date = st.text_input("Start date", value=launch.default_start_date)
    end_date = st.text_input("End date", value=launch.default_end_date)
    hypothesis = _selected_hypothesis(launch, hypothesis_id)
    include_testing, include_draft = _launch_flags(hypothesis)
    return start_date, end_date, include_testing, include_draft


def _launch_preview_block(
    st,
    hypothesis_id: str,
    asset_symbol: str,
    snapshot_id: str,
    start_date: str,
    end_date: str,
    include_testing: bool,
    include_draft: bool,
) -> None:
    st.code(
        _launch_preview(
            hypothesis_id,
            asset_symbol,
            snapshot_id,
            start_date,
            end_date,
        ),
        language="bash",
    )
    st.caption(
        f"Launch flags: include_testing={include_testing}, "
        f"include_draft={include_draft}"
    )


def _render_launch_preview(
    st,
    launch,
    asset_symbol: str,
    snapshot_id: str,
    hypothesis_id: str,
    start_date: str,
    end_date: str,
    include_testing: bool,
    include_draft: bool,
    render_status_cards_fn,
) -> None:
    render_launch_preview(
        st,
        launch,
        asset_symbol,
        snapshot_id,
        hypothesis_id,
        start_date,
        end_date,
        include_testing,
        include_draft,
        render_status_cards_fn,
    )


def _select_value(st, label: str, options: tuple[str, ...], default: str | None) -> str:
    index = options.index(default) if default in options else 0
    return st.selectbox(label, options, index=index)


def _selected_hypothesis(view, hypothesis_id: str) -> object | None:
    for hypothesis in view.hypotheses:
        if hypothesis.hypothesis_id == hypothesis_id:
            return hypothesis
    return None


def _launch_flags(hypothesis: object | None) -> tuple[bool, bool]:
    if hypothesis is None:
        return False, False
    status = str(getattr(hypothesis, "status", ""))
    return status == "testing", status == "draft"


def _launch_preview(
    hypothesis_id: str,
    asset_symbol: str,
    snapshot_id: str,
    start_date: str,
    end_date: str,
) -> str:
    return "\n".join(
        [
            f"mft research run {hypothesis_id} {asset_symbol} --snapshot {snapshot_id}",
            f"start-date={start_date} end-date={end_date}",
            "safe-call=project.backtesting.research_runner.run_strategy_research",
        ]
    )


def _launch_research(
    st,
    repository,
    hypothesis_id: str,
    asset_symbol: str,
    snapshot_id: str,
    start_date: str,
    end_date: str,
    include_testing: bool,
    include_draft: bool,
) -> None:
    try:
        result = launch_research_run(
            repository,
            snapshot_id,
            hypothesis_id,
            asset_symbol,
            start_date,
            end_date,
            include_testing=include_testing,
            include_draft=include_draft,
        )
    except Exception as error:
        st.error(str(error))
        return
    st.success(f"Launched research run {result.research_run_id}")
    st.write(result.__dict__)


def _render_dossier(st, dossier) -> None:
    with st.container(border=True):
        st.subheader("Canonical Strategy Dossier")
        if dossier is None:
            _surface_notice(st, "No strategy dossier is available yet.")
            return
        render_dossier_summary(st, dossier)
        render_json_debug("Canonical Strategy Dossier", dossier)


def _render_table_section(st, title: str, note: str, rows) -> None:
    with st.container(border=True):
        _surface_notice(st, note)
        render_evidence_table(title, rows)


def _surface_notice(st, text: str) -> None:
    info_fn = getattr(st, "info", None)
    if callable(info_fn):
        info_fn(text)
        return
    write_fn = getattr(st, "write", None)
    if callable(write_fn):
        write_fn(text)
        return
    caption_fn = getattr(st, "caption", None)
    if callable(caption_fn):
        caption_fn(text)


def _launch_cards(launch) -> tuple[StatusCardView, ...]:
    asset_symbol = getattr(launch, "default_asset_symbol", None)
    snapshot_id = getattr(launch, "default_dataset_snapshot_id", None)
    hypothesis_id = getattr(launch, "default_hypothesis_id", None)
    start_date = getattr(launch, "default_start_date", "")
    end_date = getattr(launch, "default_end_date", "")
    workflow_text = getattr(launch, "workflow_command", "") or getattr(
        launch, "workflow_note", ""
    )
    return (
        StatusCardView(
            "Asset",
            str(asset_symbol or "Missing"),
            "ok" if asset_symbol else "warning",
            f"{len(launch.assets)} assets available",
        ),
        StatusCardView(
            "Snapshot",
            str(snapshot_id or "Missing"),
            "ok" if snapshot_id else "warning",
            f"{len(launch.snapshots)} snapshots available",
        ),
        StatusCardView(
            "Hypothesis",
            str(hypothesis_id or "Missing"),
            "ok" if hypothesis_id else "warning",
            f"{len(launch.hypotheses)} hypotheses available",
        ),
        StatusCardView(
            "Window",
            f"{start_date} -> {end_date}",
            "ok",
            workflow_text,
        ),
    )
