from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

if __name__ == "__main__" and __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from project.data.repository import build_repository
from project.ui._streamlit import get_option_menu, get_streamlit
from project.ui.components.sidebar_focus import render_sidebar_focus
from project.ui.navigation import page_titles
from project.ui.pages import data as data_page
from project.ui.pages import explainability as explainability_page
from project.ui.pages import hypotheses as hypotheses_page
from project.ui.pages import mission_control as mission_control_page
from project.ui.pages import positions as positions_page
from project.ui.pages import reports as reports_page
from project.ui.pages import research as research_page
from project.ui.pages import trade_ideas as trade_ideas_page
from project.ui.state import ensure_state, set_selected_page


PAGES = {
    "Mission Control": mission_control_page.render,
    "Data": data_page.render,
    "Research": research_page.render,
    "Hypotheses": hypotheses_page.render,
    "Trade Ideas": trade_ideas_page.render,
    "Positions": positions_page.render,
    "Explainability": explainability_page.render,
    "Reports": reports_page.render,
}

PAGE_ICONS = (
    "house",
    "database",
    "compass",
    "lightbulb",
    "card-list",
    "briefcase",
    "diagram-3",
    "bar-chart",
)

MENU_STYLES = {
    "container": {"padding": "0!important", "background-color": "transparent"},
    "icon": {"color": "#64748b", "font-size": "15px"},
    "nav-link": {
        "font-size": "0.95rem",
        "text-align": "left",
        "margin": "0px",
        "--hover-color": "#f1f5f9",
    },
    "nav-link-selected": {"background-color": "#e2e8f0", "color": "#0f172a"},
}


def _selected_page(st: Any, options: tuple[str, ...]) -> str:
    current = st.session_state["ui_page"]
    return current if current in options else options[0]


def _render_navigation(st: Any) -> str:
    options = page_titles()
    current = _selected_page(st, options)
    index = options.index(current)
    option_menu = get_option_menu()
    if option_menu is None:
        return st.sidebar.radio("Section", options, index=index)
    try:
        return option_menu(
            "Section",
            options,
            icons=PAGE_ICONS,
            menu_icon="grid",
            default_index=index,
            styles=MENU_STYLES,
        )
    except Exception:
        return st.sidebar.radio("Section", options, index=index)


def main() -> None:
    st = get_streamlit()
    st.set_page_config(page_title="MFT Operator Cockpit", layout="wide")
    _apply_page_styles(st)
    ensure_state(st.session_state)
    st.sidebar.title("MFT UI")
    st.sidebar.caption("Operate the workflow, not the modules.")
    page = _render_navigation(st)
    set_selected_page(st.session_state, page)
    st.sidebar.caption("Session-state page switching remains the source of truth.")
    database_path = st.sidebar.text_input("Database path", value="project_mft.duckdb")
    repository = build_repository(Path(database_path))
    st.sidebar.caption("Mutating actions remain explicit inside each page.")
    try:
        PAGES[page](repository)
        render_sidebar_focus(repository, st.session_state, page)
    finally:
        repository.close()


def _apply_page_styles(st: Any) -> None:
    markdown = getattr(st, "markdown", None)
    if not callable(markdown):
        return
    markdown(
        """
        <style>
        .block-container {
            padding-top: 1.35rem;
            padding-bottom: 2rem;
        }
        h1, h2, h3 {
            letter-spacing: -0.02em;
        }
        div[data-testid="stMetric"] {
            background: linear-gradient(
                180deg,
                rgba(248, 250, 252, 0.95),
                rgba(241, 245, 249, 0.85)
            );
            border: 1px solid rgba(148, 163, 184, 0.22);
            border-radius: 16px;
            padding: 0.8rem 0.95rem;
        }
        div[data-testid="stMetric"] label {
            color: #475569;
        }
        div[data-testid="stExpander"] {
            border-radius: 14px;
        }
        .ui-hero {
            margin: 0 0 1rem 0;
            padding: 1rem 1.1rem;
            border-radius: 20px;
            border: 1px solid rgba(148, 163, 184, 0.24);
            background: linear-gradient(
                135deg,
                rgba(15, 23, 42, 0.96),
                rgba(30, 41, 59, 0.9)
            );
            box-shadow: 0 14px 28px rgba(15, 23, 42, 0.08);
        }
        .ui-hero__eyebrow {
            color: #cbd5e1;
            font-size: 0.72rem;
            letter-spacing: 0.18em;
            text-transform: uppercase;
        }
        .ui-hero__summary {
            color: #f8fafc;
            font-size: 1rem;
            line-height: 1.55;
            margin-top: 0.4rem;
        }
        .ui-hero__chips {
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin-top: 0.72rem;
        }
        .ui-hero__chip {
            display: inline-flex;
            align-items: center;
            gap: 0.42rem;
            padding: 0.32rem 0.6rem;
            border-radius: 999px;
            border: 1px solid rgba(148, 163, 184, 0.22);
            background: rgba(255, 255, 255, 0.08);
        }
        .ui-hero__chip-label {
            color: #cbd5e1;
            font-size: 0.68rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
        }
        .ui-hero__chip-value {
            color: #f8fafc;
            font-size: 0.82rem;
            font-weight: 600;
        }
        .ui-hero__note {
            display: inline-flex;
            margin-top: 0.65rem;
            padding: 0.34rem 0.6rem;
            border-radius: 999px;
            background: rgba(59, 130, 246, 0.16);
            border: 1px solid rgba(96, 165, 250, 0.32);
            color: #dbeafe;
            font-size: 0.82rem;
        }
        .ui-sidebar-focus {
            margin: 0.35rem 0 0.9rem;
            padding: 0.9rem 0.95rem;
            border-radius: 18px;
            border: 1px solid rgba(148, 163, 184, 0.22);
            background: rgba(255, 255, 255, 0.82);
            box-shadow: 0 10px 22px rgba(15, 23, 42, 0.05);
        }
        .ui-sidebar-focus__eyebrow {
            color: #475569;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.16em;
            margin-bottom: 0.55rem;
            text-transform: uppercase;
        }
        .ui-sidebar-focus__row {
            display: flex;
            flex-direction: column;
            gap: 0.2rem;
            padding-top: 0.55rem;
        }
        .ui-sidebar-focus__row + .ui-sidebar-focus__row {
            border-top: 1px solid rgba(148, 163, 184, 0.16);
            margin-top: 0.55rem;
        }
        .ui-sidebar-focus__label {
            color: #64748b;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
        }
        .ui-sidebar-focus__value {
            color: #0f172a;
            font-size: 0.92rem;
            line-height: 1.45;
        }
        .ui-stepper {
            margin: 0.35rem 0 1rem;
        }
        .ui-stepper__eyebrow {
            color: #475569;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.16em;
            margin-bottom: 0.75rem;
            text-transform: uppercase;
        }
        .ui-stepper__grid {
            display: grid;
            gap: 0.75rem;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        }
        .ui-stepper__card {
            padding: 0.9rem 0.95rem;
            border-radius: 18px;
            border: 1px solid rgba(148, 163, 184, 0.18);
            background: rgba(255, 255, 255, 0.86);
            box-shadow: 0 10px 22px rgba(15, 23, 42, 0.05);
        }
        .ui-stepper__card--ok {
            border-color: rgba(34, 197, 94, 0.22);
        }
        .ui-stepper__card--ok .ui-stepper__state {
            background: rgba(34, 197, 94, 0.12);
            color: #166534;
        }
        .ui-stepper__card--warning {
            border-color: rgba(245, 158, 11, 0.28);
        }
        .ui-stepper__card--warning .ui-stepper__state {
            background: rgba(245, 158, 11, 0.12);
            color: #92400e;
        }
        .ui-stepper__card--action-required {
            border-color: rgba(59, 130, 246, 0.28);
        }
        .ui-stepper__card--action-required .ui-stepper__state {
            background: rgba(59, 130, 246, 0.12);
            color: #1d4ed8;
        }
        .ui-stepper__card--unknown {
            border-color: rgba(148, 163, 184, 0.22);
        }
        .ui-stepper__card--unknown .ui-stepper__state {
            background: rgba(148, 163, 184, 0.12);
            color: #475569;
        }
        .ui-stepper__header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.5rem;
            margin-bottom: 0.7rem;
        }
        .ui-stepper__index {
            color: #64748b;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.12em;
        }
        .ui-stepper__state {
            padding: 0.22rem 0.5rem;
            border-radius: 999px;
            background: rgba(148, 163, 184, 0.12);
            color: #475569;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }
        .ui-stepper__label {
            color: #0f172a;
            font-size: 0.96rem;
            font-weight: 700;
            line-height: 1.35;
            margin-bottom: 0.35rem;
        }
        .ui-stepper__detail {
            color: #475569;
            font-size: 0.88rem;
            line-height: 1.45;
        }
        .ui-record-list {
            margin-top: 0.25rem;
        }
        .ui-record-list__eyebrow {
            color: #475569;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.16em;
            margin-bottom: 0.75rem;
            text-transform: uppercase;
        }
        .ui-record-list__grid {
            display: grid;
            gap: 0.75rem;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        }
        .ui-record-card {
            padding: 0.9rem 0.95rem;
            border-radius: 18px;
            border: 1px solid rgba(148, 163, 184, 0.18);
            background: rgba(255, 255, 255, 0.88);
            box-shadow: 0 10px 22px rgba(15, 23, 42, 0.05);
        }
        .ui-record-card--warning {
            border-color: rgba(245, 158, 11, 0.26);
        }
        .ui-record-card--success {
            border-color: rgba(34, 197, 94, 0.26);
            background: rgba(34, 197, 94, 0.05);
        }
        .ui-record-card--activity {
            border-color: rgba(59, 130, 246, 0.22);
        }
        .ui-record-card__title {
            color: #0f172a;
            font-size: 0.95rem;
            font-weight: 700;
            line-height: 1.35;
            margin-bottom: 0.35rem;
        }
        .ui-record-card__body {
            color: #475569;
            font-size: 0.88rem;
            line-height: 1.45;
            margin-bottom: 0.55rem;
        }
        .ui-record-card__meta {
            color: #64748b;
            font-size: 0.76rem;
            font-weight: 600;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }
        div[data-testid="stSidebar"] {
            background: linear-gradient(
                180deg,
                rgba(248, 250, 252, 0.98),
                rgba(241, 245, 249, 0.96)
            );
            border-right: 1px solid rgba(148, 163, 184, 0.18);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
