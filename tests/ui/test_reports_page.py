from __future__ import annotations

import contextlib
from types import SimpleNamespace

import project.ui.components.page_hero as page_hero_component
import project.ui.pages.reports as reports_page


class _MarkdownStreamlit:
    def __init__(self) -> None:
        self.titles: list[str] = []
        self.markdowns: list[tuple[str, bool]] = []
        self.info_messages: list[str] = []
        self.subheaders: list[str] = []
        self.captions: list[str] = []
        self.writes: list[str] = []

    def title(self, text: str) -> None:
        self.titles.append(text)

    def markdown(self, text: str, unsafe_allow_html: bool = False) -> None:
        self.markdowns.append((text, unsafe_allow_html))

    def info(self, text: str) -> None:
        self.info_messages.append(text)

    def subheader(self, text: str) -> None:
        self.subheaders.append(text)

    def caption(self, text: str) -> None:
        self.captions.append(text)

    def write(self, text: object) -> None:
        self.writes.append(str(text))

    def container(self, **_kwargs):
        return contextlib.nullcontext()


class _PlainStreamlit:
    def __init__(self) -> None:
        self.titles: list[str] = []
        self.info_messages: list[str] = []
        self.writes: list[str] = []

    def title(self, text: str) -> None:
        self.titles.append(text)

    def info(self, text: str) -> None:
        self.info_messages.append(text)

    def write(self, text: object) -> None:
        self.writes.append(str(text))

    def subheader(self, *_args, **_kwargs) -> None:
        return None

    def caption(self, *_args, **_kwargs) -> None:
        return None

    def container(self, **_kwargs):
        return contextlib.nullcontext()


def test_reports_render_missing_dossier_callout(monkeypatch) -> None:
    fake_st = _MarkdownStreamlit()
    captured_cards: list[tuple[object, ...]] = []

    monkeypatch.setattr(reports_page, "get_streamlit", lambda: fake_st)
    monkeypatch.setattr(page_hero_component, "get_streamlit", lambda: fake_st)
    monkeypatch.setattr(
        reports_page,
        "get_reports_page_view",
        lambda _repository: SimpleNamespace(
            backtests=(),
            performance=(),
            rejected=(),
            strategy_dossier=None,
            debug_payload={},
        ),
    )
    monkeypatch.setattr(
        reports_page,
        "render_status_cards",
        lambda cards: captured_cards.append(tuple(cards)),
    )
    monkeypatch.setattr(
        reports_page,
        "render_evidence_table",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        reports_page,
        "render_json_debug",
        lambda *_args, **_kwargs: None,
    )

    reports_page.render(object())

    assert fake_st.titles == ["Reports"]
    assert fake_st.info_messages == []
    assert captured_cards[0][0].label == "Backtests"
    assert captured_cards[1][0].label == "Dossier"
    assert captured_cards[1][0].value == "Missing"
    assert captured_cards[1][0].state == "warning"
    assert "Strategy dossier pending" in fake_st.markdowns[1][0]
    assert "Run research or record a new backtest" in fake_st.markdowns[1][0]


def test_reports_render_missing_dossier_falls_back_without_markdown(
    monkeypatch,
) -> None:
    fake_st = _PlainStreamlit()
    captured_cards: list[tuple[object, ...]] = []

    monkeypatch.setattr(reports_page, "get_streamlit", lambda: fake_st)
    monkeypatch.setattr(page_hero_component, "get_streamlit", lambda: fake_st)
    monkeypatch.setattr(
        reports_page,
        "get_reports_page_view",
        lambda _repository: SimpleNamespace(
            backtests=(),
            performance=(),
            rejected=(),
            strategy_dossier=None,
            debug_payload={},
        ),
    )
    monkeypatch.setattr(
        reports_page,
        "render_status_cards",
        lambda cards: captured_cards.append(tuple(cards)),
    )
    monkeypatch.setattr(
        reports_page,
        "render_evidence_table",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        reports_page,
        "render_json_debug",
        lambda *_args, **_kwargs: None,
    )

    reports_page.render(object())

    assert fake_st.titles == ["Reports"]
    assert fake_st.writes == [
        "No strategy dossier is available yet.",
        "Run research or record a new backtest to populate this section.",
        "Source: Latest research run or backtest",
        "Next step: Run research",
    ]
    assert captured_cards[1][0].label == "Dossier"
    assert captured_cards[1][0].value == "Missing"
