from __future__ import annotations

import html


def render_trade_summary(st, detail) -> None:
    markdown_fn = getattr(st, "markdown", None)
    if callable(markdown_fn):
        markdown_fn(_summary_html(detail), unsafe_allow_html=True)
        return
    st.subheader(f"Trade idea: {detail.asset_symbol} {detail.direction}")
    st.caption(
        f"Confidence {detail.confidence:.2f} • {detail.hypothesis_status} hypothesis"
    )
    st.write(f"Hypothesis: {detail.hypothesis_name}")
    st.write(f"System recommendation: {detail.recommended_action}")
    st.caption(f"Reason: {detail.recommended_reason}")


def _summary_html(detail) -> str:
    rows = [
        "<section style='margin:0.9rem 0 1rem;padding:1rem 1.1rem;border:1px solid "
        "#e2e8f0;border-radius:14px;background:linear-gradient(180deg,#ffffff 0%,"
        "#f8fafc 100%);box-shadow:0 6px 18px rgba(15,23,42,0.05);'>",
        "<div style='color:#64748b;font-size:0.68rem;font-weight:700;"
        "letter-spacing:0.14em;text-transform:uppercase;margin-bottom:0.25rem;'>"
        "Trade summary</div>",
        f"<div style='color:#0f172a;font-size:1rem;font-weight:700;line-height:1.3;'>"
        f"{html.escape(detail.asset_symbol)} {html.escape(detail.direction)}</div>",
        f"<div style='color:#475569;font-size:0.85rem;line-height:1.55;margin-top:0.35rem;'>"
        f"{html.escape(detail.hypothesis_name)} • {html.escape(detail.hypothesis_status)}"
        " hypothesis</div>",
        "<div style='display:flex;flex-wrap:wrap;gap:0.5rem;margin-top:0.85rem;'>",
        _summary_chip_html(
            "Confidence",
            f"{detail.confidence:.2f}",
            _confidence_tone(detail.confidence),
        ),
        _summary_chip_html("Recommendation", detail.recommended_action, "action"),
        _summary_chip_html("Reason", detail.recommended_reason, "primary"),
        _summary_chip_html(
            "Decisions",
            _decision_history_text(detail),
            "ok" if detail.decision_history else "warning",
        ),
        _summary_chip_html(
            "Outcome",
            detail.approval_outcome.state.title(),
            _outcome_tone(detail.approval_outcome.state),
        ),
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


def _decision_history_text(detail) -> str:
    count = len(detail.decision_history)
    if count == 0:
        return "No prior decisions"
    label = "decision" if count == 1 else "decisions"
    return f"{count} prior {label}"


def _confidence_tone(confidence: float) -> str:
    if confidence >= 0.75:
        return "ok"
    if confidence >= 0.5:
        return "action"
    return "warning"


def _outcome_tone(state: str) -> str:
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
