from __future__ import annotations

import html


def render_hypothesis_summary(st, detail) -> None:
    markdown_fn = getattr(st, "markdown", None)
    if callable(markdown_fn):
        markdown_fn(_summary_html(detail), unsafe_allow_html=True)
        return
    st.caption("Selected hypothesis")
    st.write(f"Hypothesis: {detail.name} • {detail.hypothesis_id}")
    st.write(
        f"Status: {detail.status} • v{detail.version} • {detail.explainability_level}"
    )
    st.write(f"Readiness: {detail.readiness}")
    st.write(f"Latest backtest: {detail.latest_backtest or 'none'}")
    st.write(f"Validation failures: {detail.validation_failures}")
    if detail.blockers:
        st.write(f"Blockers: {', '.join(detail.blockers)}")
    else:
        st.caption("No readiness blockers.")


def _summary_html(detail) -> str:
    rows = [
        "<section style='margin:0.9rem 0 1rem;padding:1rem 1.1rem;border:1px solid "
        "#e2e8f0;border-radius:14px;background:linear-gradient(180deg,#ffffff 0%,"
        "#f8fafc 100%);box-shadow:0 6px 18px rgba(15,23,42,0.05);'>",
        "<div style='color:#64748b;font-size:0.68rem;font-weight:700;"
        "letter-spacing:0.14em;text-transform:uppercase;margin-bottom:0.25rem;'>"
        "Selected hypothesis</div>",
        f"<div style='color:#0f172a;font-size:1rem;font-weight:700;line-height:1.3;'>"
        f"{html.escape(detail.name)}</div>",
        f"<div style='color:#475569;font-size:0.85rem;line-height:1.55;margin-top:0.35rem;'>"
        f"{html.escape(detail.hypothesis_id)} • v{detail.version} • "
        f"{html.escape(detail.explainability_level)}</div>",
        "<div style='display:flex;flex-wrap:wrap;gap:0.5rem;margin-top:0.85rem;'>",
        _chip_html("Status", detail.status.title(), "primary"),
        _chip_html(
            "Readiness",
            detail.readiness.title(),
            "ok" if detail.readiness == "ready" else "warning",
        ),
        _chip_html(
            "Backtest",
            detail.latest_backtest or "none",
            "ok" if detail.latest_backtest else "warning",
        ),
        _chip_html(
            "Validation",
            f"{detail.validation_failures}",
            "ok" if detail.validation_failures == 0 else "warning",
        ),
        _chip_html(
            "Blockers",
            _blocker_value(detail),
            "warning" if detail.blockers else "ok",
        ),
        "</div></section>",
    ]
    return "".join(rows)


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


def _blocker_value(detail) -> str:
    if not detail.blockers:
        return "None"
    count = len(detail.blockers)
    return f"{count} blocker{'s' if count != 1 else ''}"


def _tone_color(tone: str) -> str:
    if tone == "ok":
        return "#15803d"
    if tone == "warning":
        return "#b45309"
    return "#4f46e5"
