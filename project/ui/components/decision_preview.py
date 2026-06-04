from __future__ import annotations

import html


def render_decision_preview(
    st,
    detail,
    auto_review: bool,
    action: str | None,
    reason: str | None,
    reason_label: str | None,
    notes: str,
) -> None:
    mode_text, action_text, reason_text, notes_text, guidance = _decision_preview_values(
        detail,
        auto_review,
        action,
        reason,
        reason_label,
        notes,
    )
    markdown_fn = getattr(st, "markdown", None)
    if callable(markdown_fn):
        markdown_fn(
            _decision_preview_html(mode_text, action_text, reason_text, notes_text, guidance),
            unsafe_allow_html=True,
        )
        return
    _surface_text(st, "Decision preview")
    _surface_text(st, guidance)
    _surface_text(st, f"Mode: {mode_text}")
    _surface_text(st, f"Action: {action_text}")
    _surface_text(st, f"Reason: {reason_text}")
    _surface_text(st, f"Notes: {notes_text}")
    _surface_text(st, "Notes are saved with the decision and shown in history.")


def _decision_preview_values(
    detail,
    auto_review: bool,
    action: str | None,
    reason: str | None,
    reason_label: str | None,
    notes: str,
) -> tuple[str, str, str, str, str]:
    if auto_review:
        return (
            "Automatic review",
            detail.recommended_action.title(),
            detail.recommended_reason,
            notes.strip() or "No notes yet.",
            "The system recommendation will be submitted with the notes below.",
        )
    action_text = (action or "n/a").title()
    reason_text = reason_label or reason or "n/a"
    return (
        "Manual override",
        action_text,
        reason_text,
        notes.strip() or "No notes yet.",
        "The selected action, reason, and notes will be submitted.",
    )


def _decision_preview_html(
    mode_text: str,
    action_text: str,
    reason_text: str,
    notes_text: str,
    guidance: str,
) -> str:
    rows = [
        "<section style='margin:0.85rem 0 0.35rem;padding:0.95rem 1rem;border:1px "
        "solid #e2e8f0;border-radius:14px;background:linear-gradient(180deg,#ffffff "
        "0%,#f8fafc 100%);box-shadow:0 6px 18px rgba(15,23,42,0.05);'>",
        "<div style='color:#64748b;font-size:0.68rem;font-weight:700;"
        "letter-spacing:0.14em;text-transform:uppercase;margin-bottom:0.25rem;'>"
        "Decision preview</div>",
        f"<div style='color:#0f172a;font-size:1rem;font-weight:700;line-height:1.3;'>"
        f"{html.escape(mode_text)}</div>",
        f"<div style='color:#475569;font-size:0.85rem;line-height:1.55;margin-top:0.35rem;'>"
        f"{html.escape(guidance)}</div>",
        "<div style='display:flex;flex-wrap:wrap;gap:0.5rem;margin-top:0.85rem;'>",
        _decision_chip_html("Action", action_text, "action"),
        _decision_chip_html("Reason", reason_text, "primary"),
        _decision_chip_html(
            "Notes",
            notes_text,
            "ok" if notes_text != "No notes yet." else "warning",
        ),
        "</div>",
        "<div style='color:#64748b;font-size:0.78rem;line-height:1.45;margin-top:0.7rem;'>",
        "Notes are saved with the decision and shown in history.",
        "</div>",
        "</section>",
    ]
    return "".join(rows)


def _decision_chip_html(label: str, value: str, tone: str) -> str:
    return "".join(
        [
            "<div style='display:flex;flex-direction:column;gap:0.1rem;padding:0.55rem "
            "0.7rem;border-radius:12px;background:#ffffff;border:1px solid #e2e8f0;"
            "min-width:120px;'>",
            f"<div style='color:#64748b;font-size:0.62rem;font-weight:700;"
            f"letter-spacing:0.12em;text-transform:uppercase;'>{html.escape(label)}</div>",
            f"<div style='color:{_tone_color(tone)};font-size:0.84rem;font-weight:700;"
            f"line-height:1.35;white-space:pre-line;word-break:break-word;'>{html.escape(value)}</div>",
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
