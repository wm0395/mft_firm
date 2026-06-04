from __future__ import annotations

import html
from collections.abc import Sequence


def render_empty_state(
    st,
    title: str,
    summary: str,
    note: str,
    chips: Sequence[tuple[str, str, str]] = (),
) -> None:
    markdown_fn = getattr(st, "markdown", None)
    if callable(markdown_fn):
        markdown_fn(_empty_state_html(title, summary, note, chips), unsafe_allow_html=True)
        return
    _surface_text(st, title)
    _surface_text(st, summary)
    _surface_text(st, note)
    for label, value, _tone in chips:
        _surface_text(st, f"{label}: {value}")


def _empty_state_html(
    title: str,
    summary: str,
    note: str,
    chips: Sequence[tuple[str, str, str]],
) -> str:
    rows = [
        "<section style='margin:0.75rem 0 1rem;padding:1rem 1.1rem;border:1px dashed "
        "#cbd5e1;border-radius:14px;background:linear-gradient(180deg,#ffffff 0%,"
        "#f8fafc 100%);'>",
        "<div style='color:#64748b;font-size:0.68rem;font-weight:700;"
        "letter-spacing:0.14em;text-transform:uppercase;margin-bottom:0.25rem;'>"
        "Empty state</div>",
        f"<div style='color:#0f172a;font-size:1rem;font-weight:700;line-height:1.3;'>"
        f"{html.escape(title)}</div>",
        f"<div style='color:#475569;font-size:0.85rem;line-height:1.55;margin-top:0.35rem;'>"
        f"{html.escape(summary)}</div>",
        f"<div style='color:#475569;font-size:0.82rem;line-height:1.5;margin-top:0.35rem;'>"
        f"{html.escape(note)}</div>",
        "<div style='display:flex;flex-wrap:wrap;gap:0.5rem;margin-top:0.85rem;'>",
    ]
    rows.extend(_chip_html(label, value, tone) for label, value, tone in chips)
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
