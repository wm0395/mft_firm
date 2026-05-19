from __future__ import annotations

from project.ui._streamlit import get_streamlit
from project.ui.components.evidence_table import render_evidence_table
from project.ui.components.json_debug import render_json_debug
from project.ui.components.status_card import render_status_cards
from project.ui.components.workflow_stepper import render_workflow_stepper
from project.ui.views.common import StatusCardView, WorkflowStepView
from project.ui.views.data import create_snapshot, get_data_page_view


def render(repository) -> None:
    st = get_streamlit()
    view = get_data_page_view(repository)
    st.title("Data")
    st.caption("Data readiness, freshness, and dataset snapshots.")
    render_status_cards(_summary_cards(view))
    render_workflow_stepper(_workflow_steps(view))
    render_evidence_table("Asset Universe", view.assets)
    render_evidence_table("Data Quality", view.quality_rows)
    render_evidence_table("Dataset Snapshots", view.snapshots)
    _render_snapshot_form(st, repository, view)
    render_json_debug("Raw JSON / Debug", view.debug_payload)


def _summary_cards(view) -> tuple[StatusCardView, ...]:
    return (
        StatusCardView("Assets", str(len(view.assets)), "ok", "Loaded assets"),
        StatusCardView("Quality", view.quality_status.upper(), view.quality_status, "Data quality status"),
        StatusCardView("Snapshots", str(len(view.snapshots)), "ok", "Dataset snapshots"),
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
        WorkflowStepView("Market Data Sync", "ok" if view.quality_rows else "action required", "Freshness and sync"),
        WorkflowStepView("Data Quality", "ok" if view.quality_status == "ok" else "action required", "Quality report"),
        WorkflowStepView("Dataset Snapshots", "ok" if view.snapshots else "action required", "Reproducible snapshots"),
        WorkflowStepView("Asset Universe", "ok", "Asset list"),
    )


def _render_snapshot_form(st, repository, view) -> None:
    defaults = view.default_snapshot
    with st.container(border=True):
        st.subheader("Snapshot creation form")
        with st.form("snapshot-form"):
            name = st.text_input("Snapshot name", value=defaults.name)
            market = st.text_input("Market", value=defaults.market)
            symbols_text = st.text_area("Symbols", value=", ".join(defaults.symbols))
            data_start = st.text_input("Data start", value=defaults.data_start)
            data_end = st.text_input("Data end", value=defaults.data_end)
            resolution = st.text_input("Resolution", value=defaults.resolution)
            description = st.text_area("Description", value=defaults.description)
            submitted = st.form_submit_button("Create Snapshot")
        if submitted:
            symbols = _split_symbols(symbols_text)
            try:
                result = create_snapshot(
                    repository,
                    name,
                    market,
                    symbols,
                    data_start,
                    data_end,
                    resolution,
                    description or None,
                )
            except Exception as error:
                st.error(str(error))
            else:
                st.success(f"Created snapshot {result.dataset_snapshot_id}")
                st.write(result.dataset_snapshot.__dict__)


def _split_symbols(symbols_text: str) -> tuple[str, ...]:
    parts = [item.strip().upper() for item in symbols_text.replace("\n", ",").split(",")]
    return tuple(item for item in parts if item)
