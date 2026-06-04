from __future__ import annotations

import html


def render_snapshot_result(st, result) -> None:
    markdown_fn = getattr(st, "markdown", None)
    if callable(markdown_fn):
        markdown_fn(_result_html(result), unsafe_allow_html=True)
        return
    universe_id = str(getattr(result, "universe_id", "n/a"))
    assets = tuple(getattr(result, "assets", ()))
    quality_status = getattr(result, "quality_status", "unknown")
    _surface_text(st, "Snapshot created")
    _surface_text(st, f"Snapshot: {result.dataset_snapshot_id}")
    _surface_text(st, f"Universe: {universe_id}")
    _surface_text(st, f"Assets: {_asset_list_text(assets)}")
    _surface_text(
        st,
        f"Window: {getattr(result, 'data_start', 'n/a')} -> "
        f"{getattr(result, 'data_end', 'n/a')}",
    )
    _surface_text(st, f"Quality: {str(quality_status).upper()}")
    _surface_text(st, f"Source: {_provenance_text(result)}")


def _result_html(result) -> str:
    snapshot = getattr(result, "dataset_snapshot", None)
    captured_at = getattr(snapshot, "captured_at", "")
    universe_id = str(getattr(result, "universe_id", "n/a"))
    assets = tuple(getattr(result, "assets", ()))
    quality_status = getattr(result, "quality_status", "unknown")
    return "".join(
        [
            "<section style='margin:0.9rem 0 1rem;padding:1rem 1.1rem;border:1px solid "
            "#e2e8f0;border-radius:14px;background:linear-gradient(180deg,#ffffff 0%,"
            "#f8fafc 100%);box-shadow:0 6px 18px rgba(15,23,42,0.05);'>",
            "<div style='color:#64748b;font-size:0.68rem;font-weight:700;"
            "letter-spacing:0.14em;text-transform:uppercase;margin-bottom:0.25rem;'>"
            "Snapshot created</div>",
            f"<div style='color:#0f172a;font-size:1rem;font-weight:700;line-height:1.3;'>"
            f"{html.escape(result.dataset_snapshot_id)}</div>",
            f"<div style='color:#475569;font-size:0.85rem;line-height:1.55;margin-top:0.35rem;'>"
            f"{html.escape(_result_note(result))}</div>",
            "<div style='display:flex;flex-wrap:wrap;gap:0.5rem;margin-top:0.85rem;'>",
            _chip_html("Universe", universe_id, "primary"),
            _chip_html("Assets", _asset_list_text(assets), _assets_tone(assets)),
            _chip_html("Window", _window_text(result), "ok"),
            _chip_html("Quality", str(quality_status).upper(), _quality_tone(quality_status)),
            _chip_html("Source", _provenance_text(result), "action"),
            _chip_html("Captured", str(captured_at or "n/a"), "action"),
            "</div></section>",
        ]
    )


def _result_note(result) -> str:
    source = _provenance_text(result)
    return f"Ready for research. Source: {source}."


def _asset_list_text(assets: tuple[str, ...]) -> str:
    if not assets:
        return "none selected"
    if len(assets) <= 3:
        return ", ".join(assets)
    remaining = len(assets) - 2
    return f"{assets[0]}, {assets[1]} (+{remaining} more)"


def _window_text(result) -> str:
    return (
        f"{getattr(result, 'data_start', 'n/a')} -> "
        f"{getattr(result, 'data_end', 'n/a')}"
    )


def _provenance_text(result) -> str:
    provenance = getattr(result, "provenance", None)
    if provenance is None:
        return "n/a"
    source_name = getattr(provenance, "source_name", "n/a")
    bar_timeframe = getattr(provenance, "bar_timeframe", "n/a")
    return f"{source_name} • {bar_timeframe}"


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


def _assets_tone(assets: tuple[str, ...]) -> str:
    return "ok" if assets else "warning"


def _quality_tone(quality_status: object) -> str:
    if str(quality_status) == "ok":
        return "ok"
    if str(quality_status) == "warn":
        return "action"
    return "warning"


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
