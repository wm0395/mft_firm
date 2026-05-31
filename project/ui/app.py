from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

if __name__ == "__main__" and __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from project.data.repository import build_repository
from project.ui._streamlit import get_streamlit
from project.ui.pages import charts as charts_page
from project.ui.pages import trading as trading_page
from project.ui.navigation import page_titles
from project.ui.pages import data as data_page
from project.ui.pages import explainability as explainability_page
from project.ui.pages import hypotheses as hypotheses_page
from project.ui.pages import mission_control as mission_control_page
from project.ui.pages import positions as positions_page
from project.ui.pages import reports as reports_page
from project.ui.pages import research as research_page
from project.ui.pages import trade_ideas as trade_ideas_page
from project.ui.components.sidebar_focus import render_sidebar_focus
from project.ui.state import ensure_state, set_selected_page


PAGES = {
    "Mission Control": mission_control_page.render,
    "Data": data_page.render,
    "Research": research_page.render,
    "Hypotheses": hypotheses_page.render,
    "Trade Ideas": trade_ideas_page.render,
    "Positions": positions_page.render,
    "Charts": charts_page.render,
    "Trading": trading_page.render,
    "Explainability": explainability_page.render,
    "Reports": reports_page.render,
}

_DEFAULT_DB = "project_mft.duckdb"


def _get_repository(st: Any) -> Any:
    db_path = st.session_state.get("_db_path")
    current_path = st.sidebar.text_input("Database path", value=db_path or _DEFAULT_DB)
    repo = st.session_state.get("_repository")
    if db_path != current_path or repo is None:
        st.session_state["_db_path"] = current_path
        if repo is not None:
            try:
                repo.close()
            except Exception:
                pass
        try:
            st.session_state["_repository"] = build_repository(Path(current_path))
        except Exception as e:
            warning_fn = getattr(st.sidebar, "warning", None)
            if callable(warning_fn):
                warning_fn(f"DB connection failed: {e}")
            st.session_state["_repository"] = None
            return None
    return st.session_state.get("_repository")


def _render_navigation(st: Any) -> str:
    options = page_titles()
    current = st.session_state.get("ui_page", options[0])
    current = current if current in options else options[0]
    index = options.index(current)
    return st.sidebar.radio("Section", options, index=index)


def main() -> None:
    st = get_streamlit()
    st.set_page_config(page_title="MFT Operator Cockpit", layout="wide")
    _apply_styles(st)
    ensure_state(st.session_state)

    st.sidebar.title("MFT Operator Cockpit")
    st.sidebar.caption("Multi-Factor Trading System")
    page = _render_navigation(st)
    set_selected_page(st.session_state, page)

    repository = _get_repository(st)
    if repository is None:
        warning_fn = getattr(st.sidebar, "warning", None)
        if callable(warning_fn):
            warning_fn("Cannot connect to database.")
        return

    try:
        render_fn = PAGES.get(page)
        if render_fn:
            render_fn(repository)
        render_sidebar_focus(repository, st.session_state, page)
    except Exception as e:
        st.error(f"Error: {e}")


def _apply_styles(st: Any) -> None:
    markdown = getattr(st, "markdown", None)
    if not callable(markdown):
        return
    markdown(
        """
<style>
:root {
  --primary: #6366f1;
  --primary-dark: #4f46e5;
  --primary-light: #eef2ff;
  --surface: #ffffff;
  --bg: #f8fafc;
  --text: #0f172a;
  --text-secondary: #475569;
  --text-muted: #94a3b8;
  --border: #e2e8f0;
  --border-light: #f1f5f9;
  --success: #22c55e;
  --success-bg: #f0fdf4;
  --warning: #f59e0b;
  --warning-bg: #fffbeb;
  --error: #ef4444;
  --error-bg: #fef2f2;
  --radius: 12px;
  --radius-sm: 8px;
  --shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
  --shadow-md: 0 4px 6px rgba(0,0,0,0.05), 0 2px 4px rgba(0,0,0,0.04);
  --shadow-lg: 0 10px 25px rgba(0,0,0,0.06), 0 4px 10px rgba(0,0,0,0.04);
}

html, body, [class*="css"] {
  font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
    "Segoe UI", sans-serif;
}

.block-container {
  padding: 1.5rem 2rem 3rem !important;
  max-width: 1400px;
}

h1 {
  font-size: 1.75rem;
  font-weight: 700;
  letter-spacing: -0.03em;
  color: var(--text);
  margin-bottom: 0.25rem !important;
}

h2 {
  font-size: 1.2rem;
  font-weight: 600;
  letter-spacing: -0.02em;
  color: var(--text);
  margin: 1.5rem 0 0.75rem !important;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--border);
}

h3 {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-secondary);
}

/* ---- SIDEBAR ---- */
div[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #ffffff 0%, #fafbfc 100%);
  border-right: 1px solid var(--border);
  padding: 0.5rem 0;
}

div[data-testid="stSidebar"] .sidebar-brand {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.25rem 1rem 0;
}

.sidebar-brand-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  color: white;
  font-size: 1rem;
  font-weight: 800;
  border-radius: 10px;
}

.sidebar-brand-text {
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--text);
  letter-spacing: -0.02em;
}

.sidebar-tagline {
  font-size: 0.72rem;
  color: var(--text-muted);
  margin: 0.15rem 0 0;
  padding: 0 1rem;
  letter-spacing: 0.02em;
}

.sidebar-divider {
  border: none;
  border-top: 1px solid var(--border);
  margin: 0.75rem 1rem;
}

/* ---- METRIC CARDS ---- */
div[data-testid="stMetric"] {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1rem 1.2rem;
  box-shadow: var(--shadow);
  transition: all 0.15s ease;
}

div[data-testid="stMetric"]:hover {
  box-shadow: var(--shadow-md);
  border-color: #cbd5e1;
}

div[data-testid="stMetric"] label {
  color: var(--text-muted);
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

div[data-testid="stMetric"] [data-testid="stMetricValue"] {
  font-size: 1.4rem;
  font-weight: 700;
  color: var(--text);
}

div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
  font-size: 0.8rem;
}

/* ---- BUTTONS ---- */
.stButton button {
  border-radius: var(--radius-sm);
  font-weight: 500;
  font-size: 0.85rem;
  transition: all 0.15s ease;
  border: 1px solid var(--border);
}

.stButton button[kind="primary"] {
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  border: none;
  color: white;
  box-shadow: 0 1px 3px rgba(99,102,241,0.3);
}

.stButton button[kind="primary"]:hover {
  box-shadow: 0 4px 12px rgba(99,102,241,0.4);
  transform: translateY(-1px);
}

/* ---- SELECT BOX ---- */
div[data-testid="stSelectbox"] label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
  border-radius: var(--radius-sm);
  border-color: var(--border);
}

/* ---- TEXT INPUT ---- */
div[data-testid="stTextInput"] label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

div[data-testid="stTextInput"] input {
  border-radius: var(--radius-sm);
  border-color: var(--border);
}

/* ---- DATA FRAME ---- */
div[data-testid="stDataFrame"] {
  border-radius: var(--radius);
  border: 1px solid var(--border);
  overflow: hidden;
}

/* ---- EXPANDER ---- */
div[data-testid="stExpander"] {
  border-radius: var(--radius);
  border: 1px solid var(--border);
  background: var(--surface);
}

/* ---- TABS ---- */
div[data-testid="stTabs"] button {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--text-secondary);
  padding: 0.4rem 1rem;
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
}

div[data-testid="stTabs"] button[aria-selected="true"] {
  color: var(--primary);
  font-weight: 600;
}

/* ---- INFO / WARNING / ERROR ---- */
div[data-testid="stInfo"] {
  background: var(--primary-light);
  border: 1px solid rgba(99,102,241,0.2);
  border-radius: var(--radius);
  color: var(--primary-dark);
}

div[data-testid="stWarning"] {
  background: var(--warning-bg);
  border: 1px solid rgba(245,158,11,0.2);
  border-radius: var(--radius);
}

div[data-testid="stError"] {
  background: var(--error-bg);
  border: 1px solid rgba(239,68,68,0.2);
  border-radius: var(--radius);
}

/* ---- HERO ---- */
.ui-hero {
  margin: 0 0 1.5rem;
  padding: 1.5rem 2rem;
  border-radius: 16px;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  box-shadow: 0 8px 32px rgba(15,23,42,0.12);
}

.ui-hero__eyebrow {
  color: #64748b;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  margin-bottom: 0.3rem;
}

.ui-hero__summary {
  color: #f1f5f9;
  font-size: 1.1rem;
  font-weight: 500;
  line-height: 1.6;
  margin-bottom: 0.1rem;
  max-width: 64ch;
}

.ui-hero__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.85rem;
}

.ui-hero__chip {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.28rem 0.65rem;
  border-radius: 999px;
  background: rgba(255,255,255,0.07);
  border: 1px solid rgba(255,255,255,0.1);
}

.ui-hero__chip-label {
  color: #94a3b8;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.ui-hero__chip-value {
  color: #f1f5f9;
  font-size: 0.8rem;
  font-weight: 700;
}

.ui-hero__note {
  margin-top: 0.9rem;
  padding-top: 0.8rem;
  border-top: 1px solid rgba(255,255,255,0.08);
  color: #cbd5e1;
  font-size: 0.78rem;
  line-height: 1.5;
}

/* ---- RECORD CARD ---- */
.ui-record-list {
  margin: 0.9rem 0 1rem;
}

.ui-record-list__eyebrow {
  color: var(--text-muted);
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  margin-bottom: 0.45rem;
}

.ui-record-list__grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.75rem;
}

.ui-record-card {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0.95rem 1rem;
  border-radius: 16px;
  border: 1px solid var(--border);
  background: var(--surface);
  box-shadow: 0 6px 18px rgba(15,23,42,0.05);
}

.ui-record-card__title {
  color: var(--text-muted);
  font-size: 0.64rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.ui-record-card__body {
  color: var(--text);
  font-size: 0.95rem;
  font-weight: 700;
  line-height: 1.35;
  word-break: break-word;
}

.ui-record-card__meta {
  color: var(--text-secondary);
  font-size: 0.82rem;
  line-height: 1.45;
  word-break: break-word;
}

.ui-record-card--success {
  background: linear-gradient(180deg, #f0fdf4 0%, #ffffff 100%);
  border-color: rgba(34,197,94,0.18);
}

.ui-record-card--success .ui-record-card__body {
  color: #15803d;
}

.ui-record-card--warning {
  background: linear-gradient(180deg, #fffbeb 0%, #ffffff 100%);
  border-color: rgba(245,158,11,0.18);
}

.ui-record-card--warning .ui-record-card__body {
  color: #b45309;
}

.ui-record-card--activity {
  background: linear-gradient(180deg, #eef2ff 0%, #ffffff 100%);
  border-color: rgba(99,102,241,0.18);
}

.ui-record-card--activity .ui-record-card__body {
  color: #4338ca;
}

/* ---- KPI CARD ---- */
.kpi-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1rem 1.2rem;
  box-shadow: var(--shadow);
  transition: all 0.15s ease;
}

.kpi-card:hover {
  box-shadow: var(--shadow-md);
}

.kpi-card__label {
  color: var(--text-muted);
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 0.15rem;
}

.kpi-card__value {
  color: var(--text);
  font-size: 1.35rem;
  font-weight: 700;
  line-height: 1.3;
}

.kpi-card__change {
  font-size: 0.8rem;
  font-weight: 600;
  margin-top: 0.15rem;
}

.kpi-card__change.positive { color: var(--success); }
.kpi-card__change.negative { color: var(--error); }
.kpi-card__change.neutral { color: var(--text-muted); }

/* ---- SECTION ---- */
.section-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.25rem 1.5rem;
  box-shadow: var(--shadow);
  margin-bottom: 1.25rem;
}

.section-card__title {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--border-light);
}

/* ---- STATUS BADGE ---- */
.badge {
  display: inline-flex;
  align-items: center;
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.04em;
}

.badge--ok { background: var(--success-bg); color: #15803d; }
.badge--warning { background: var(--warning-bg); color: #b45309; }
.badge--error { background: var(--error-bg); color: #dc2626; }
.badge--info { background: var(--primary-light); color: var(--primary-dark); }

/* ---- DIVIDER ---- */
hr.ui-divider {
  border: none;
  border-top: 1px solid var(--border);
  margin: 1.5rem 0;
}

/* ---- SEARCH ---- */
.search-box input {
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  padding: 0.4rem 0.75rem;
  font-size: 0.85rem;
  width: 100%;
}

/* ---- METRIC GRID ---- */
.metric-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 0.75rem;
  margin-bottom: 1.25rem;
}
</style>
""",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
