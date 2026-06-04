from __future__ import annotations

import contextlib
from types import SimpleNamespace

import project.ui.pages.trading as trading_page
import project.ui.components.page_hero as page_hero_component


class _FakeStreamlit:
    def __init__(self, section: str = "📋 Trade Ideas") -> None:
        self.session_state: dict[str, object] = {}
        self.section = section
        self.titles: list[str] = []
        self.captions: list[str] = []

    def title(self, text: str) -> None:
        self.titles.append(text)

    def caption(self, text: str) -> None:
        self.captions.append(text)

    def selectbox(self, label: str, options, index: int = 0, **_kwargs) -> str:
        return self.section if self.section in options else options[index]


class _MarkdownStreamlit(_FakeStreamlit):
    def __init__(self, section: str = "📋 Trade Ideas") -> None:
        super().__init__(section)
        self.markdowns: list[tuple[str, bool]] = []
        self.dataframes: list[object] = []

    def markdown(self, text: str, unsafe_allow_html: bool = False) -> None:
        self.markdowns.append((text, unsafe_allow_html))

    def columns(self, count: int):
        return [_FakeColumn(self.markdowns) for _ in range(count)]

    def dataframe(self, value: object, **_kwargs) -> None:
        self.dataframes.append(value)

    def expander(self, *_args, **_kwargs):
        return contextlib.nullcontext()


class _FakeColumn:
    def __init__(self, markdowns: list[tuple[str, bool]]) -> None:
        self.markdowns = markdowns

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def markdown(self, text: str, unsafe_allow_html: bool = False) -> None:
        self.markdowns.append((text, unsafe_allow_html))


def test_render_uses_selected_section_only(monkeypatch) -> None:
    fake_st = _FakeStreamlit("💼 Positions")
    calls: list[str] = []

    monkeypatch.setattr(trading_page, "get_streamlit", lambda: fake_st)
    monkeypatch.setattr(page_hero_component, "get_streamlit", lambda: fake_st)
    monkeypatch.setattr(
        trading_page,
        "_render_trade_ideas",
        lambda *_args, **_kwargs: calls.append("trade_ideas"),
    )
    monkeypatch.setattr(
        trading_page,
        "_render_positions",
        lambda *_args, **_kwargs: calls.append("positions"),
    )
    monkeypatch.setattr(
        trading_page,
        "_render_reports",
        lambda *_args, **_kwargs: calls.append("reports"),
    )

    trading_page.render(SimpleNamespace())

    assert fake_st.titles == ["Trading"]
    assert fake_st.captions == ["Choose a section to load only the data you need."]
    assert fake_st.session_state["trading_section"] == "💼 Positions"
    assert calls == ["positions"]


def test_render_positions_uses_summary_hero(monkeypatch) -> None:
    fake_st = _MarkdownStreamlit("💼 Positions")
    positions = [
        {
            "Symbol": "NIFTY",
            "Direction": "long",
            "Status": "open",
            "Entry": "110.00",
            "Exit": "—",
            "PnL": "—",
        },
        {
            "Symbol": "BANKNIFTY",
            "Direction": "short",
            "Status": "closed",
            "Entry": "120.00",
            "Exit": "118.00",
            "PnL": "12.50",
        },
    ]

    monkeypatch.setattr(trading_page, "get_streamlit", lambda: fake_st)
    monkeypatch.setattr(page_hero_component, "get_streamlit", lambda: fake_st)
    monkeypatch.setattr(trading_page, "_fetch_positions", lambda _repository: positions)

    trading_page.render(SimpleNamespace())

    hero_html = next(
        html for html, unsafe in fake_st.markdowns if "Monitor open exposure" in html
    )
    assert "Open" in hero_html
    assert "Closed" in hero_html
    assert "+12.50" in hero_html
    assert fake_st.dataframes[0] == positions


def test_render_trade_ideas_uses_empty_state_for_closed_queue(monkeypatch) -> None:
    fake_st = _MarkdownStreamlit("📋 Trade Ideas")
    ideas = [
        {
            "Symbol": "NIFTY",
            "Direction": "long",
            "Confidence": "0.82",
            "Timestamp": "2025-06-01T10:00:00Z",
        }
    ]

    monkeypatch.setattr(trading_page, "get_streamlit", lambda: fake_st)
    monkeypatch.setattr(page_hero_component, "get_streamlit", lambda: fake_st)
    monkeypatch.setattr(trading_page, "_fetch_trade_ideas", lambda _repository: ideas)
    monkeypatch.setattr(trading_page, "_fetch_open_ideas", lambda _repository: [])

    trading_page.render(SimpleNamespace())

    empty_state_html = next(
        html for html, unsafe in fake_st.markdowns if "No open trade ideas." in html
    )
    assert "Open the history below" in empty_state_html
    assert "Reviewed" in empty_state_html
    assert fake_st.dataframes[0] == ideas


def test_render_trade_ideas_uses_empty_state_when_no_ideas_exist(monkeypatch) -> None:
    fake_st = _MarkdownStreamlit("📋 Trade Ideas")

    monkeypatch.setattr(trading_page, "get_streamlit", lambda: fake_st)
    monkeypatch.setattr(page_hero_component, "get_streamlit", lambda: fake_st)
    monkeypatch.setattr(trading_page, "_fetch_trade_ideas", lambda _repository: [])
    monkeypatch.setattr(trading_page, "_fetch_open_ideas", lambda _repository: [])

    trading_page.render(SimpleNamespace())

    empty_state_html = next(
        html for html, unsafe in fake_st.markdowns if "No trade ideas yet." in html
    )
    assert "Run strategy research" in empty_state_html


def test_render_positions_uses_empty_state_when_no_positions(monkeypatch) -> None:
    fake_st = _MarkdownStreamlit("💼 Positions")

    monkeypatch.setattr(trading_page, "get_streamlit", lambda: fake_st)
    monkeypatch.setattr(page_hero_component, "get_streamlit", lambda: fake_st)
    monkeypatch.setattr(trading_page, "_fetch_positions", lambda _repository: [])

    trading_page.render(SimpleNamespace())

    empty_state_html = next(
        html for html, unsafe in fake_st.markdowns if "No positions yet." in html
    )
    assert "Approve an idea" in empty_state_html


def test_render_reports_uses_empty_states_when_data_missing(monkeypatch) -> None:
    fake_st = _MarkdownStreamlit("📊 Reports")

    monkeypatch.setattr(trading_page, "get_streamlit", lambda: fake_st)
    monkeypatch.setattr(page_hero_component, "get_streamlit", lambda: fake_st)
    monkeypatch.setattr(trading_page, "_fetch_backtests", lambda _repository: [])
    monkeypatch.setattr(trading_page, "_fetch_outcomes", lambda _repository: [])

    trading_page.render(SimpleNamespace())

    assert any("No backtest results yet." in html for html, unsafe in fake_st.markdowns)
    assert any(
        "No trade outcomes recorded yet." in html
        for html, unsafe in fake_st.markdowns
    )
