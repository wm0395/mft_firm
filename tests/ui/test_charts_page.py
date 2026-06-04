from __future__ import annotations

import contextlib
from datetime import UTC, date, datetime
from types import SimpleNamespace

import project.ui.components.page_hero as page_hero_component
import project.ui.pages.charts as charts_page


class _FakeStreamlit:
    def __init__(self, selectbox_values: dict[str, str] | None = None) -> None:
        self.session_state: dict[str, object] = {}
        self.selectbox_values = selectbox_values or {}
        self.titles: list[str] = []
        self.captions: list[str] = []
        self.markdowns: list[tuple[str, bool]] = []
        self.info_messages: list[str] = []

    def title(self, text: str) -> None:
        self.titles.append(text)

    def caption(self, text: str) -> None:
        self.captions.append(text)

    def markdown(self, text: str, unsafe_allow_html: bool = False) -> None:
        self.markdowns.append((text, unsafe_allow_html))

    def info(self, text: str) -> None:
        self.info_messages.append(text)

    def selectbox(self, label: str, options, index: int = 0, **_kwargs) -> str:
        return self.selectbox_values.get(label, options[index])

    def columns(self, count: int):
        return tuple(contextlib.nullcontext() for _ in range(count))

    def expander(self, *_args, **_kwargs):
        return contextlib.nullcontext()


class _MarkdownStreamlit(_FakeStreamlit):
    def __init__(self, selectbox_values: dict[str, str] | None = None) -> None:
        super().__init__(selectbox_values)
        self.markdowns: list[tuple[str, bool]] = []

    def markdown(self, text: str, unsafe_allow_html: bool = False) -> None:
        self.markdowns.append((text, unsafe_allow_html))


class _FixedDatetime(datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 5, 31, 12, 0, tzinfo=tz)


def test_render_uses_selected_range_for_fetch_data(monkeypatch) -> None:
    fake_st = _FakeStreamlit(
        selectbox_values={"Asset": "AAPL", "Range": "1M"},
    )
    captured: dict[str, object] = {}

    monkeypatch.setattr(charts_page, "get_streamlit", lambda: fake_st)
    monkeypatch.setattr(charts_page, "datetime", _FixedDatetime)
    monkeypatch.setattr(
        charts_page,
        "_load_assets",
        lambda _repository: [
            SimpleNamespace(
                symbol="AAPL",
                name="Apple",
                sector="Tech",
                market="NASDAQ",
            )
        ],
    )
    monkeypatch.setattr(
        charts_page,
        "_fetch_data",
        lambda _repository, symbol, start_date, end_date: captured.update(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
        )
        or [(datetime(2026, 5, 1, tzinfo=UTC), 1.0, 2.0, 0.5, 1.5, 1000.0)],
    )
    monkeypatch.setattr(charts_page, "_render_chart", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(charts_page, "_render_kpis", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(charts_page, "_render_raw_data", lambda *_args, **_kwargs: None)

    charts_page.render(object())

    assert fake_st.titles == ["Charts"]
    assert fake_st.session_state["selected_asset_symbol"] == "AAPL"
    assert fake_st.session_state["charts_range"] == "1M"
    assert captured["symbol"] == "AAPL"
    assert captured["start_date"] == date(2026, 5, 1)
    assert captured["end_date"] == date(2026, 5, 31)


def test_render_uses_summary_hero_for_selected_asset(monkeypatch) -> None:
    fake_st = _MarkdownStreamlit(
        selectbox_values={"Asset": "AAPL", "Range": "1M"},
    )

    monkeypatch.setattr(charts_page, "get_streamlit", lambda: fake_st)
    monkeypatch.setattr(page_hero_component, "get_streamlit", lambda: fake_st)
    monkeypatch.setattr(charts_page, "datetime", _FixedDatetime)
    monkeypatch.setattr(
        charts_page,
        "_load_assets",
        lambda _repository: [
            SimpleNamespace(
                symbol="AAPL",
                name="Apple",
                sector="Tech",
                market="NASDAQ",
            )
        ],
    )
    monkeypatch.setattr(
        charts_page,
        "_fetch_data",
        lambda _repository, symbol, start_date, end_date: [
            (datetime(2026, 5, 1, tzinfo=UTC), 1.0, 2.0, 0.5, 1.5, 1000.0)
        ],
    )
    monkeypatch.setattr(charts_page, "_render_chart", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(charts_page, "_render_kpis", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(charts_page, "_render_raw_data", lambda *_args, **_kwargs: None)

    charts_page.render(object())

    hero_html = next(html for html, unsafe in fake_st.markdowns if "Operator snapshot" in html)
    assert "Inspect AAPL — Apple at a glance." in hero_html
    assert "Chart, metrics, and raw data stay synchronized to the same filters." in hero_html
    assert "Range" in hero_html
    assert "1M" in hero_html
    assert "May 01, 2026" in hero_html


def test_render_uses_empty_state_when_no_assets(monkeypatch) -> None:
    fake_st = _FakeStreamlit()
    captured: dict[str, object] = {}

    monkeypatch.setattr(charts_page, "get_streamlit", lambda: fake_st)
    monkeypatch.setattr(page_hero_component, "get_streamlit", lambda: fake_st)
    monkeypatch.setattr(charts_page, "render_empty_state", lambda *args: captured.setdefault("empty", args))
    monkeypatch.setattr(charts_page, "_load_assets", lambda _repository: [])

    charts_page.render(object())

    _, title, summary, note, chips = captured["empty"]
    assert fake_st.titles == ["Charts"]
    assert title == "No assets available."
    assert "chart view" in summary
    assert "asset universe is populated" in note
    assert chips[0] == ("Assets", "0 registered", "warning")


def test_render_uses_empty_state_when_no_market_data(monkeypatch) -> None:
    fake_st = _MarkdownStreamlit(
        selectbox_values={"Asset": "AAPL", "Range": "1M"},
    )
    captured: dict[str, object] = {}

    monkeypatch.setattr(charts_page, "get_streamlit", lambda: fake_st)
    monkeypatch.setattr(page_hero_component, "get_streamlit", lambda: fake_st)
    monkeypatch.setattr(charts_page, "datetime", _FixedDatetime)
    monkeypatch.setattr(
        charts_page,
        "_load_assets",
        lambda _repository: [
            SimpleNamespace(
                symbol="AAPL",
                name="Apple",
                sector="Tech",
                market="NASDAQ",
            )
        ],
    )
    monkeypatch.setattr(
        charts_page,
        "_fetch_data",
        lambda _repository, symbol, start_date, end_date: [],
    )
    monkeypatch.setattr(charts_page, "_render_chart", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(charts_page, "_render_kpis", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(charts_page, "_render_raw_data", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(charts_page, "render_empty_state", lambda *args: captured.setdefault("empty", args))

    charts_page.render(object())

    _, title, summary, note, chips = captured["empty"]
    assert title == "No market data for AAPL."
    assert "selected range" in summary
    assert "widen the date window" in note.lower()
    assert chips[0] == ("Asset", "AAPL", "warning")


def test_get_date_range_all_returns_full_history(monkeypatch) -> None:
    monkeypatch.setattr(charts_page, "datetime", _FixedDatetime)

    start_date, end_date, label = charts_page._get_date_range("All")

    assert start_date is None
    assert end_date is None
    assert label == "Full history"
