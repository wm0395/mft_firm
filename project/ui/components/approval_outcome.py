from __future__ import annotations

import html


def render_approval_outcome(st, outcome) -> None:
    with st.container(border=True):
        markdown_fn = getattr(st, "markdown", None)
        if callable(markdown_fn):
            markdown_fn(_outcome_html(outcome), unsafe_allow_html=True)
            return
        _surface_text(st, "Approval outcome")
        _surface_text(st, outcome.message)
        _surface_text(st, f"Outcome: {_state_label(outcome.state)}")
        if outcome.open_position_status is not None:
            _surface_text(st, f"Open position: {outcome.open_position_status}")
        if outcome.open_position_entry_price is not None:
            _surface_text(st, f"Entry price: {outcome.open_position_entry_price:.2f}")


def _outcome_html(outcome) -> str:
    rows = [
        "<section style='margin:0.9rem 0 1rem;padding:1rem 1.1rem;border:1px solid "
        "#e2e8f0;border-radius:14px;background:linear-gradient(180deg,#ffffff 0%,"
        "#f8fafc 100%);box-shadow:0 6px 18px rgba(15,23,42,0.05);'>",
        "<div style='color:#64748b;font-size:0.68rem;font-weight:700;"
        "letter-spacing:0.14em;text-transform:uppercase;margin-bottom:0.25rem;'>"
        "Approval outcome</div>",
        f"<div style='color:#0f172a;font-size:1rem;font-weight:700;line-height:1.3;'>"
        f"{html.escape(outcome.message)}</div>",
        f"<div style='color:#475569;font-size:0.85rem;line-height:1.55;margin-top:0.35rem;'>"
        f"Outcome: {html.escape(_state_label(outcome.state))}</div>",
        "<div style='display:flex;flex-wrap:wrap;gap:0.5rem;margin-top:0.85rem;'>",
        _chip_html("State", _state_label(outcome.state), _state_tone(outcome.state)),
    ]
    if outcome.open_position_status is not None:
        rows.append(_chip_html("Open position", outcome.open_position_status, "ok"))
    if outcome.open_position_entry_price is not None:
        rows.append(
            _chip_html(
                "Entry price",
                f"{outcome.open_position_entry_price:.2f}",
                "action",
            )
        )
    rows.append("</div></section>")
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


def _state_label(state: str) -> str:
    if state == "ok":
        return "Approved"
    if state == "warning":
        return "Warning"
    if state == "info":
        return "Info"
    return state.replace("_", " ").title()


def _state_tone(state: str) -> str:
    if state == "ok":
        return "ok"
    if state == "warning":
        return "warning"
    return "action"


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
