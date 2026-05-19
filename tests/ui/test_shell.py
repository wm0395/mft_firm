from __future__ import annotations

from pathlib import Path

from project.ui import app
from project.ui.pages.mission_control import _navigate_to_action


class _FakeSidebar:
    def __init__(self, selected_page: str) -> None:
        self.selected_page = selected_page
        self.radio_args: tuple[str, tuple[str, ...], int] | None = None
        self.text_input_args: tuple[str, str] | None = None

    def title(self, *_args, **_kwargs) -> None:
        return None

    def caption(self, *_args, **_kwargs) -> None:
        return None

    def radio(self, label: str, options, index: int = 0):
        self.radio_args = (label, tuple(options), index)
        return self.selected_page

    def text_input(self, label: str, value: str = "") -> str:
        self.text_input_args = (label, value)
        return "cockpit.duckdb"


class _FakeStreamlit:
    def __init__(self, selected_page: str) -> None:
        self.session_state: dict[str, object] = {}
        self.sidebar = _FakeSidebar(selected_page)
        self.page_config: dict[str, object] | None = None
        self.rerun_calls = 0

    def set_page_config(self, **kwargs) -> None:
        self.page_config = kwargs

    def rerun(self) -> None:
        self.rerun_calls += 1


class _FakeRepository:
    def __init__(self, db) -> None:
        self.db = db
        self.closed = False

    def close(self) -> None:
        self.closed = True


def test_app_main_seeds_state_and_dispatches_selected_page(monkeypatch) -> None:
    fake_st = _FakeStreamlit("Research")
    render_calls: list[str] = []

    def _make_render(page: str):
        def _render(_repository) -> None:
            render_calls.append(page)

        return _render

    monkeypatch.setattr(app, "get_streamlit", lambda: fake_st)
    monkeypatch.setattr(app, "DuckDBAccess", lambda path: Path(path))
    monkeypatch.setattr(app, "DataRepository", _FakeRepository)
    monkeypatch.setattr(
        app,
        "PAGES",
        {page: _make_render(page) for page in app.PAGES},
    )
    fake_st.session_state["ui_page"] = "missing-page"

    app.main()

    assert fake_st.page_config == {"page_title": "MFT Operator Cockpit", "layout": "wide"}
    assert fake_st.session_state["ui_page"] == "Research"
    assert fake_st.session_state["selected_hypothesis_id"] == ""
    assert fake_st.session_state["selected_trade_id"] == ""
    assert fake_st.session_state["selected_evaluation_id"] == ""
    assert fake_st.session_state["selected_research_project_id"] == ""
    assert fake_st.sidebar.radio_args == (
        "Section",
        (
            "Mission Control",
            "Data",
            "Research",
            "Hypotheses",
            "Trade Ideas",
            "Explainability",
            "Reports",
        ),
        0,
    )
    assert fake_st.sidebar.text_input_args == ("Database path", "project_mft.duckdb")
    assert render_calls == ["Research"]


def test_navigate_to_action_routes_to_expected_page(monkeypatch) -> None:
    fake_st = _FakeStreamlit("Mission Control")
    cases = {
        "sync-market-data": "Data",
        "create-dataset-snapshot": "Data",
        "init-db": "Data",
        "hypothesis-readiness": "Hypotheses",
        "run-strategy-research": "Research",
        "anything-else": "Trade Ideas",
    }

    for command, expected_page in cases.items():
        fake_st.session_state.clear()
        _navigate_to_action(fake_st, command)
        assert fake_st.session_state["ui_page"] == expected_page
        assert fake_st.rerun_calls == 1
        fake_st.rerun_calls = 0
