from __future__ import annotations

from types import SimpleNamespace

import project.ui.pages.trading as trading_page


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


def test_render_uses_selected_section_only(monkeypatch) -> None:
    fake_st = _FakeStreamlit("💼 Positions")
    calls: list[str] = []

    monkeypatch.setattr(trading_page, "get_streamlit", lambda: fake_st)
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
