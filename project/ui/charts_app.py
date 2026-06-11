from __future__ import annotations

from pathlib import Path

from project.data.repository import build_repository
from project.ui._streamlit import get_streamlit
from project.ui.pages.charts import render as render_charts
from project.ui.state import ensure_state


DEFAULT_DB_PATH = (
    Path(__file__).resolve().parents[3]
    / "runtime"
    / "market_collector_central"
    / "market.duckdb"
)


def main() -> None:
    st = get_streamlit()
    st.set_page_config(page_title="MFT Charts", layout="wide")
    ensure_state(st.session_state)
    st.sidebar.title("MFT Charts")
    st.sidebar.caption("Market-collector OHLCV charts")
    repository = _get_repository(st)
    if repository is None:
        return
    render_charts(repository)


def _get_repository(st):
    db_path = st.session_state.get("_charts_db_path")
    current_path = st.sidebar.text_input(
        "Database path",
        value=str(db_path or DEFAULT_DB_PATH),
    )
    repo = st.session_state.get("_charts_repository")
    if db_path != current_path or repo is None:
        st.session_state["_charts_db_path"] = current_path
        if repo is not None:
            try:
                repo.close()
            except Exception:
                pass
        try:
            st.session_state["_charts_repository"] = build_repository(Path(current_path))
        except Exception as exc:
            warning = getattr(st.sidebar, "warning", None)
            if callable(warning):
                warning(f"DB connection failed: {exc}")
            st.session_state["_charts_repository"] = None
            return None
    return st.session_state.get("_charts_repository")


if __name__ == "__main__":
    main()
