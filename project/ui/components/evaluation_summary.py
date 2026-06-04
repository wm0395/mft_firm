from __future__ import annotations

import html


def render_evaluation_summary(st, detail) -> None:
    markdown_fn = getattr(st, "markdown", None)
    if callable(markdown_fn):
        markdown_fn(_summary_html(detail), unsafe_allow_html=True)
        return
    st.write(f"Evaluation ID: {detail.evaluation_id}")
    st.write(f"Asset: {detail.asset_symbol} • Hypothesis: {detail.hypothesis_id}")
    st.write(
        f"Direction: {detail.direction} • Confidence: {detail.confidence:.2f}"
    )
    st.write(f"Trade ideas: {', '.join(detail.trade_ideas) or 'none'}")
    st.write(f"Decisions: {', '.join(detail.decisions) or 'none'}")
    st.write(f"Validation: {_validation_value(detail)}.")


def _summary_html(detail) -> str:
    trade_ideas_count = len(detail.trade_ideas)
    decisions_count = len(detail.decisions)
    rows = [
        "<section style='margin:0.9rem 0 1rem;padding:1rem 1.1rem;border:1px solid "
        "#e2e8f0;border-radius:14px;background:linear-gradient(180deg,#ffffff 0%,"
        "#f8fafc 100%);box-shadow:0 6px 18px rgba(15,23,42,0.05);'>",
        "<div style='color:#64748b;font-size:0.68rem;font-weight:700;"
        "letter-spacing:0.14em;text-transform:uppercase;margin-bottom:0.25rem;'>"
        "Selected evaluation</div>",
        f"<div style='color:#0f172a;font-size:1rem;font-weight:700;line-height:1.3;'>"
        f"{html.escape(detail.asset_symbol)} {html.escape(detail.direction)}</div>",
        f"<div style='color:#475569;font-size:0.85rem;line-height:1.55;margin-top:0.35rem;'>"
        f"{html.escape(detail.hypothesis_id)} • Confidence {detail.confidence:.2f}"
        "</div>",
        "<div style='display:flex;flex-wrap:wrap;gap:0.5rem;margin-top:0.85rem;'>",
        _summary_chip_html("Evaluation ID", detail.evaluation_id, "primary"),
        _summary_chip_html(
            "Trade ideas",
            f"{trade_ideas_count}",
            "ok" if trade_ideas_count else "warning",
        ),
        _summary_chip_html(
            "Decisions",
            f"{decisions_count}",
            "ok" if decisions_count else "warning",
        ),
        _summary_chip_html("Validation", _validation_value(detail), _validation_tone(detail)),
        "</div></section>",
    ]
    return "".join(rows)


def _summary_chip_html(label: str, value: str, tone: str) -> str:
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


def _validation_value(detail) -> str:
    if detail.validation is None:
        return "Missing"
    return "Passed" if detail.validation.get("is_valid", False) else "Failed"


def _validation_tone(detail) -> str:
    return "ok" if detail.validation and detail.validation.get("is_valid", False) else "warning"


def _tone_color(tone: str) -> str:
    if tone == "ok":
        return "#15803d"
    if tone == "warning":
        return "#b45309"
    return "#4f46e5"
