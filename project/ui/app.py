from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

if __name__ == "__main__" and __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from project.data.db import DuckDBAccess
from project.data.repository import DataRepository
from project.ui._streamlit import get_option_menu, get_streamlit
from project.ui.navigation import page_definition, page_titles
from project.ui.pages import data as data_page
from project.ui.pages import explainability as explainability_page
from project.ui.pages import hypotheses as hypotheses_page
from project.ui.pages import mission_control as mission_control_page
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
    "Explainability": explainability_page.render,
    "Reports": reports_page.render,
}

PAGE_ICONS = (
    "house",
    "database",
    "compass",
    "lightbulb",
    "card-list",
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
    ensure_state(st.session_state)
    st.sidebar.title("MFT UI")
    st.sidebar.caption("Operate the workflow, not the modules.")
    page = _render_navigation(st)
    set_selected_page(st.session_state, page)
    st.sidebar.caption(page_definition(page).description)
    st.sidebar.caption("Session-state page switching remains the source of truth.")
    database_path = st.sidebar.text_input("Database path", value="project_mft.duckdb")
    st.sidebar.caption("Mutating actions remain explicit inside each page.")
    repository = DataRepository(DuckDBAccess(Path(database_path)))
    try:
        PAGES[page](repository)
    finally:
        repository.close()


if __name__ == "__main__":
    main()
