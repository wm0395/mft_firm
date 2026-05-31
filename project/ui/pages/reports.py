from __future__ import annotations

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
            st.info("No strategy dossier is available yet.")
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
