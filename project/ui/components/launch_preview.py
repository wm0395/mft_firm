from __future__ import annotations

import html

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
    markdown_fn = getattr(st, "markdown", None)
    if callable(markdown_fn):
        markdown_fn(
            _preview_html(
                launch,
                asset_symbol,
                snapshot_id,
                hypothesis_id,
                start_date,
                end_date,
                include_testing,
                include_draft,
            ),
            unsafe_allow_html=True,
        )
    else:
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


def _preview_html(
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
    rows = [
        "<section style='margin:0.9rem 0 1rem;padding:1rem 1.1rem;border:1px solid "
        "#e2e8f0;border-radius:14px;background:linear-gradient(180deg,#ffffff 0%,"
        "#f8fafc 100%);box-shadow:0 6px 18px rgba(15,23,42,0.05);'>",
        "<div style='color:#64748b;font-size:0.68rem;font-weight:700;"
        "letter-spacing:0.14em;text-transform:uppercase;margin-bottom:0.25rem;'>"
        "Launch plan</div>",
        f"<div style='color:#0f172a;font-size:1rem;font-weight:700;line-height:1.3;'>"
        f"Ready to launch {html.escape(hypothesis_name)}</div>",
        f"<div style='color:#475569;font-size:0.85rem;line-height:1.55;margin-top:0.35rem;'>"
        f"{html.escape(asset_symbol)} • {html.escape(snapshot_id)} • "
        f"{html.escape(start_date)} → {html.escape(end_date)} • "
        f"{html.escape(_flag_text(include_testing, include_draft))}</div>",
        "<div style='display:flex;flex-wrap:wrap;gap:0.5rem;margin-top:0.85rem;'>",
        _chip_html("Asset", asset_symbol, "ok"),
        _chip_html("Snapshot", snapshot_id, "ok"),
        _chip_html("Hypothesis", hypothesis_name, "primary"),
        _chip_html("Window", f"{start_date} -> {end_date}", "primary"),
        _chip_html("Policy", _flag_text(include_testing, include_draft), _policy_tone(include_testing, include_draft)),
        "</div></section>",
    ]
    return "".join(rows)


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


def _chip_html(label: str, value: str, tone: str) -> str:
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


def _policy_tone(include_testing: bool, include_draft: bool) -> str:
    return "action" if include_testing or include_draft else "ok"


def _tone_color(tone: str) -> str:
    if tone == "ok":
        return "#15803d"
    if tone == "warning":
        return "#b45309"
    return "#4f46e5"
