from __future__ import annotations

import html


def render_launch_requirements(st, launch) -> None:
    markdown_fn = getattr(st, "markdown", None)
    if callable(markdown_fn):
        markdown_fn(_requirements_html(launch), unsafe_allow_html=True)
        return
    _surface_text(st, _requirements_title(launch))
    _surface_text(st, _requirements_summary(launch))
    _surface_text(st, f"Missing: {_missing_text(launch)}")


def _requirements_html(launch) -> str:
    missing = _missing_items(launch)
    rows = [
        "<section style='margin:0.75rem 0 1rem;padding:1rem 1.1rem;border:1px dashed "
        "#cbd5e1;border-radius:14px;background:linear-gradient(180deg,#ffffff 0%,"
        "#f8fafc 100%);'>",
        "<div style='color:#64748b;font-size:0.68rem;font-weight:700;"
        "letter-spacing:0.14em;text-transform:uppercase;margin-bottom:0.25rem;'>"
        "Launch prerequisites</div>",
        f"<div style='color:#0f172a;font-size:1rem;font-weight:700;line-height:1.3;'>"
        f"{html.escape(_requirements_title(launch))}</div>",
        f"<div style='color:#475569;font-size:0.85rem;line-height:1.55;margin-top:0.35rem;'>"
        f"{html.escape(_requirements_summary(launch))}</div>",
        "<div style='display:flex;flex-wrap:wrap;gap:0.5rem;margin-top:0.85rem;'>",
        _chip_html("Assets", _count_text(launch, "assets"), _count_tone(launch, "assets")),
        _chip_html("Snapshots", _count_text(launch, "snapshots"), _count_tone(launch, "snapshots")),
        _chip_html("Hypotheses", _count_text(launch, "hypotheses"), _count_tone(launch, "hypotheses")),
        _chip_html("Missing", ", ".join(missing) or "none", "warning" if missing else "ok"),
        "</div></section>",
    ]
    return "".join(rows)


def _requirements_title(launch) -> str:
    missing = _missing_items(launch)
    if not missing:
        return "Launch prerequisites are ready."
    return "Launch is blocked until the missing inputs are added."


def _requirements_summary(launch) -> str:
    missing = _missing_items(launch)
    if not missing:
        return "You can proceed with the guided research run."
    return f"Add {', '.join(missing)} before launching research."


def _missing_items(launch) -> tuple[str, ...]:
    items: list[str] = []
    if not getattr(launch, "assets", ()):
        items.append("asset")
    if not getattr(launch, "snapshots", ()):
        items.append("dataset snapshot")
    if not getattr(launch, "hypotheses", ()):
        items.append("actionable hypothesis")
    return tuple(items)


def _missing_text(launch) -> str:
    missing = _missing_items(launch)
    return ", ".join(missing) if missing else "none"


def _count_text(launch, field: str) -> str:
    count = len(tuple(getattr(launch, field, ())))
    return f"{count} available" if count else "Missing"


def _count_tone(launch, field: str) -> str:
    return "ok" if len(tuple(getattr(launch, field, ()))) else "warning"


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
