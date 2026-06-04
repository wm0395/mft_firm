from __future__ import annotations

import html

from project.ui._streamlit import get_streamlit
from project.ui.components.evidence_table import render_evidence_table
from project.ui.components.dossier_summary import render_dossier_summary
from project.ui.components.json_debug import render_json_debug
from project.ui.components.page_hero import render_page_hero
from project.ui.components.status_card import render_status_cards
from project.ui.views.common import StatusCardView
from project.ui_services.reports_views import get_reports_page_view


def render(repository) -> None:
    st = get_streamlit()
    view = get_reports_page_view(repository)
    st.title("Reports")
    render_page_hero(
        f"{len(view.backtests)} backtests, {len(view.performance)} performance rows, "
        f"{len(view.rejected)} rejected evaluations.",
        _hero_note(view.strategy_dossier),
        context=(
            ("Backtests", len(view.backtests)),
            ("Performance", len(view.performance)),
            ("Rejected", len(view.rejected)),
            (
                "Dossier",
                "Ready" if view.strategy_dossier is not None else "Missing",
            ),
        ),
    )
    render_status_cards(_cards(view))
    _render_dossier(st, view.strategy_dossier)
    _render_table_section(
        st,
        "Backtest Results",
        "Historical backtests for each hypothesis.",
        view.backtests,
    )
    _render_table_section(
        st,
        "Hypothesis Performance",
        "Aggregated trade outcomes by hypothesis.",
        view.performance,
    )
    _render_table_section(
        st,
        "Rejected Hypotheses",
        "Invalid evaluations and rejection reasons.",
        view.rejected,
    )
    render_json_debug("Raw JSON / Debug", view.debug_payload)


def _cards(view) -> tuple[StatusCardView, ...]:
    return (
        StatusCardView(
            "Backtests",
            str(len(view.backtests)),
            "ok" if view.backtests else "warning",
            "Stored backtest results",
        ),
        StatusCardView(
            "Performance",
            str(len(view.performance)),
            "ok" if view.performance else "warning",
            "Hypothesis performance rows",
        ),
        StatusCardView(
            "Rejected",
            str(len(view.rejected)),
            "warning" if view.rejected else "ok",
            "Invalid evaluations",
        ),
        StatusCardView(
            "Dossier",
            "Ready" if view.strategy_dossier is not None else "Missing",
            "ok" if view.strategy_dossier is not None else "warning",
            "Canonical strategy dossier",
        ),
    )


def _render_dossier(st, dossier: dict[str, object] | None) -> None:
    with st.container(border=True):
        st.subheader("Canonical Strategy Dossier")
        if dossier is None:
            render_status_cards(
                (
                    StatusCardView(
                        "Dossier",
                        "Missing",
                        "warning",
                        "Build a backtest or research run to populate this section.",
                    ),
                )
            )
            markdown_fn = getattr(st, "markdown", None)
            if callable(markdown_fn):
                markdown_fn(_missing_dossier_html(), unsafe_allow_html=True)
            else:
                _surface_text(st, "No strategy dossier is available yet.")
                _surface_text(
                    st,
                    "Run research or record a new backtest to populate this section.",
                )
                _surface_text(
                    st,
                    "Source: Latest research run or backtest",
                )
                _surface_text(st, "Next step: Run research")
            return
        render_dossier_summary(st, dossier)
        st.caption("Use the summary and tables below to compare the supporting evidence.")
        render_json_debug("Canonical Strategy Dossier", dossier)


def _render_table_section(st, title: str, note: str, rows) -> None:
    with st.container(border=True):
        st.caption(note)
        render_evidence_table(title, rows)


def _hero_note(dossier: dict[str, object] | None) -> str:
    if dossier is None:
        return "No strategy dossier available yet."
    strategy_name = str(dossier.get("strategy_name") or dossier.get("hypothesis_id") or "Strategy dossier")
    tradeability = str(dossier.get("tradeability_status") or "unknown")
    blockers = _dossier_strings(dossier.get("tradeability_blockers"))
    if blockers:
        blocker_text = f"{len(blockers)} blocker{'s' if len(blockers) != 1 else ''}"
        return f"{strategy_name} • {tradeability} • {blocker_text}"
    return f"{strategy_name} • {tradeability}"

def _dossier_strings(value: object) -> tuple[str, ...]:
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value)
    if value:
        return (str(value),)
    return ()


def _missing_dossier_html() -> str:
    return "".join(
        [
            "<section style='margin:0.75rem 0 1rem;padding:1rem 1.1rem;border:1px dashed "
            "#cbd5e1;border-radius:14px;background:linear-gradient(180deg,#ffffff 0%,"
            "#f8fafc 100%);'>",
            "<div style='color:#64748b;font-size:0.68rem;font-weight:700;"
            "letter-spacing:0.14em;text-transform:uppercase;margin-bottom:0.25rem;'>"
            "Strategy dossier pending</div>",
            "<div style='color:#0f172a;font-size:1rem;font-weight:700;line-height:1.3;'>"
            "No strategy dossier is available yet.</div>",
            "<div style='color:#475569;font-size:0.85rem;line-height:1.55;margin-top:0.35rem;'>"
            "Run research or record a new backtest to generate the canonical dossier "
            "summary for this page.</div>",
            "<div style='display:flex;flex-wrap:wrap;gap:0.5rem;margin-top:0.85rem;'>",
            _missing_chip_html("Source", "Latest research run or backtest", "action"),
            _missing_chip_html("Next step", "Run research", "ok"),
            "</div></section>",
        ]
    )


def _missing_chip_html(label: str, value: str, tone: str) -> str:
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


def _surface_text(st, text: str) -> None:
    write_fn = getattr(st, "write", None)
    if callable(write_fn):
        write_fn(text)
        return
    caption_fn = getattr(st, "caption", None)
    if callable(caption_fn):
        caption_fn(text)


def _tone_color(tone: str) -> str:
    if tone == "ok":
        return "#15803d"
    if tone == "warning":
        return "#b45309"
    return "#4f46e5"
