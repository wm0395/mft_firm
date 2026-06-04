from __future__ import annotations

import html


def render_decision_guidance(st, detail, auto_review: bool) -> None:
    markdown_fn = getattr(st, "markdown", None)
    if callable(markdown_fn):
        markdown_fn(_guidance_html(detail, auto_review), unsafe_allow_html=True)
        return
    for line in _guidance_lines(detail, auto_review):
        _surface_text(st, line)


def _guidance_html(detail, auto_review: bool) -> str:
    mode = "Automatic review" if auto_review else "Manual override"
    if auto_review:
        title = "Automatic review is on."
        summary = (
            f"The system recommendation will submit {detail.recommended_action} "
            f"with reason {detail.recommended_reason} unless you switch to manual "
            "override."
        )
        action = f"Use {detail.recommended_action}"
        reason = detail.recommended_reason
    else:
        title = "Manual override is active."
        summary = "Choose an explicit action and reason below before submitting."
        action = "Select approve, reject, or watch"
        reason = "Pick a reason below"
    rows = [
        "<section style='margin:0.75rem 0 0.9rem;padding:0.95rem 1rem;border:1px solid "
        "#e2e8f0;border-radius:14px;background:linear-gradient(180deg,#ffffff 0%,"
        "#f8fafc 100%);box-shadow:0 6px 18px rgba(15,23,42,0.05);'>",
        "<div style='color:#64748b;font-size:0.68rem;font-weight:700;"
        "letter-spacing:0.14em;text-transform:uppercase;margin-bottom:0.25rem;'>"
        "Decision guidance</div>",
        f"<div style='color:#0f172a;font-size:1rem;font-weight:700;line-height:1.3;'>"
        f"{html.escape(title)}</div>",
        f"<div style='color:#475569;font-size:0.85rem;line-height:1.55;margin-top:0.35rem;'>"
        f"{html.escape(summary)}</div>",
        "<div style='display:flex;flex-wrap:wrap;gap:0.5rem;margin-top:0.85rem;'>",
        _chip_html("Mode", mode, "ok" if auto_review else "action"),
        _chip_html("Action", action, "primary" if auto_review else "action"),
        _chip_html("Reason", reason, "ok" if auto_review else "warning"),
        _chip_html("Notes", "Optional context, rationale, or risk notes.", "ok"),
        "</div></section>",
    ]
    return "".join(rows)


def _guidance_lines(detail, auto_review: bool) -> tuple[str, ...]:
    if auto_review:
        return (
            "Decision guidance",
            f"The system recommendation will submit {detail.recommended_action} "
            f"with reason {detail.recommended_reason} unless you switch to manual override.",
            "Mode: Automatic review",
            f"Action: Use {detail.recommended_action}",
            f"Reason: {detail.recommended_reason}",
            "Notes: Optional context, rationale, or risk notes.",
        )
    return (
        "Decision guidance",
        "Choose an explicit action and reason below before submitting.",
        "Mode: Manual override",
        "Action: Select approve, reject, or watch",
        "Reason: Pick a reason below",
        "Notes: Optional context, rationale, or risk notes.",
    )


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


def _tone_color(tone: str) -> str:
    if tone == "ok":
        return "#15803d"
    if tone == "warning":
        return "#b45309"
    return "#4f46e5"


def _surface_text(st, text: str) -> None:
    write_fn = getattr(st, "write", None)
    if callable(write_fn):
        write_fn(text)
        return
    caption_fn = getattr(st, "caption", None)
    if callable(caption_fn):
        caption_fn(text)
