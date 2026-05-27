from __future__ import annotations

from project.ui.views.common import StatusCardView


def launch_hero_context(launch) -> tuple[tuple[str, object], ...]:
    return (
        ("Asset", getattr(launch, "default_asset_symbol", "missing")),
        ("Snapshot", getattr(launch, "default_dataset_snapshot_id", "missing")),
        ("Hypothesis", getattr(launch, "default_hypothesis_id", "missing")),
        (
            "Command",
            getattr(launch, "workflow_command", "")
            or getattr(launch, "workflow_note", "")
            or "n/a",
        ),
    )


def render_launch_preview(
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
    st.subheader("Launch preview")
    st.info(
        _preview_text(
            launch,
            asset_symbol,
            snapshot_id,
            hypothesis_id,
            start_date,
            end_date,
            include_testing,
            include_draft,
        )
    )
    render_status_cards_fn(
        _preview_cards(
            launch,
            asset_symbol,
            snapshot_id,
            hypothesis_id,
            start_date,
            end_date,
            include_testing,
            include_draft,
        )
    )


def _preview_text(
    launch,
    asset_symbol: str,
    snapshot_id: str,
    hypothesis_id: str,
    start_date: str,
    end_date: str,
    include_testing: bool,
    include_draft: bool,
) -> str:
    hypothesis = _selected_hypothesis(launch, hypothesis_id)
    hypothesis_name = str(getattr(hypothesis, "name", None) or hypothesis_id or "n/a")
    return (
        f"Ready to launch {hypothesis_name} on {asset_symbol} "
        f"with {snapshot_id} from {start_date} to {end_date}. "
        f"{_flag_text(include_testing, include_draft)}"
    )


def _preview_cards(
    launch,
    asset_symbol: str,
    snapshot_id: str,
    hypothesis_id: str,
    start_date: str,
    end_date: str,
    include_testing: bool,
    include_draft: bool,
) -> tuple[StatusCardView, ...]:
    hypothesis = _selected_hypothesis(launch, hypothesis_id)
    hypothesis_name = str(getattr(hypothesis, "name", None) or hypothesis_id or "n/a")
    return (
        StatusCardView("Asset", asset_symbol, "ok", "Launch asset"),
        StatusCardView("Snapshot", snapshot_id, "ok", "Dataset snapshot"),
        StatusCardView("Hypothesis", hypothesis_name, "ok", hypothesis_id),
        StatusCardView(
            "Window",
            f"{start_date} -> {end_date}",
            "ok",
            "Requested research window",
        ),
        StatusCardView(
            "Policy",
            _flag_text(include_testing, include_draft),
            "action" if include_testing or include_draft else "ok",
            "Hypothesis status flags",
        ),
    )


def _selected_hypothesis(view, hypothesis_id: str) -> object | None:
    for hypothesis in view.hypotheses:
        if hypothesis.hypothesis_id == hypothesis_id:
            return hypothesis
    return None


def _flag_text(include_testing: bool, include_draft: bool) -> str:
    if include_testing and include_draft:
        return "Includes testing and draft hypotheses"
    if include_testing:
        return "Includes testing hypotheses"
    if include_draft:
        return "Includes draft hypotheses"
    return "Production hypotheses only"
