from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import project.ui.charts_app as charts_app


class _FakeSidebar:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self.titles: list[str] = []
        self.captions: list[str] = []
        self.text_input_args: tuple[str, str] | None = None
        self.warning_messages: list[str] = []

    def title(self, text: str) -> None:
        self.titles.append(text)

    def caption(self, text: str) -> None:
        self.captions.append(text)

    def text_input(self, label: str, value: str = "") -> str:
        self.text_input_args = (label, value)
        return self.db_path

    def warning(self, text: str) -> None:
        self.warning_messages.append(text)


class _FakeStreamlit:
    def __init__(self, db_path: str) -> None:
        self.session_state: dict[str, object] = {}
        self.sidebar = _FakeSidebar(db_path)
        self.page_config: dict[str, object] | None = None

    def set_page_config(self, **kwargs) -> None:
        self.page_config = kwargs


def test_main_builds_repository_and_renders_charts(monkeypatch) -> None:
    fake_st = _FakeStreamlit("charts.duckdb")
    built_paths: list[Path] = []
    repository = SimpleNamespace(close=lambda: None)
    rendered: list[object] = []

    monkeypatch.setattr(charts_app, "get_streamlit", lambda: fake_st)
    def _build_repository(path: Path):
        built_paths.append(path)
        return repository

    monkeypatch.setattr(charts_app, "build_repository", _build_repository)
    monkeypatch.setattr(
        charts_app,
        "render_charts",
        lambda repo: rendered.append(repo),
    )

    charts_app.main()

    assert fake_st.page_config == {
        "page_title": "MFT Charts",
        "layout": "wide",
    }
    assert fake_st.sidebar.titles == ["MFT Charts"]
    assert fake_st.sidebar.captions == ["Market-collector OHLCV charts"]
    assert fake_st.sidebar.text_input_args == (
        "Database path",
        str(charts_app.DEFAULT_DB_PATH),
    )
    assert built_paths == [Path("charts.duckdb")]
    assert rendered == [repository]


def test_main_shows_warning_when_repository_fails(monkeypatch) -> None:
    fake_st = _FakeStreamlit("charts.duckdb")

    monkeypatch.setattr(charts_app, "get_streamlit", lambda: fake_st)
    monkeypatch.setattr(
        charts_app,
        "build_repository",
        lambda _path: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    monkeypatch.setattr(charts_app, "render_charts", lambda *_args: None)

    charts_app.main()

    assert fake_st.sidebar.warning_messages == ["DB connection failed: boom"]
