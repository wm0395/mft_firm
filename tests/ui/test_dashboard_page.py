from __future__ import annotations

import contextlib
from types import SimpleNamespace
from typing import cast

import project.ui.pages.dashboard as dashboard_page


class _FakeStreamlit:
    def __init__(self) -> None:
        self.titles: list[str] = []

    def title(self, text: str) -> None:
        self.titles.append(text)


class _MarkdownStreamlit:
    def __init__(self, search: str = "") -> None:
        self.markdowns: list[tuple[str, bool]] = []
        self.search = search

    def markdown(self, text: str, unsafe_allow_html: bool = False) -> None:
        self.markdowns.append((text, unsafe_allow_html))

    def text_input(self, *_args, **_kwargs) -> str:
        return self.search

    def container(self, **_kwargs):
        return contextlib.nullcontext()


def test_render_uses_summary_hero(monkeypatch) -> None:
    fake_st = _FakeStreamlit()
    captured: dict[str, object] = {}

    monkeypatch.setattr(dashboard_page, "get_streamlit", lambda: fake_st)
    monkeypatch.setattr(
        dashboard_page,
        "_load_assets",
        lambda _repository: [
            SimpleNamespace(
                symbol="NIFTY",
                sector="Index",
                is_active=True,
            ),
            SimpleNamespace(
                symbol="BANKNIFTY",
                sector="Index",
                is_active=False,
            ),
            SimpleNamespace(
                symbol="FINANCE",
                sector="Finance",
                is_active=True,
            ),
        ],
    )
    monkeypatch.setattr(
        dashboard_page,
        "_load_data_summary",
        lambda _repository: {
            "total_rows": 125_000,
            "data_start": SimpleNamespace(strftime=lambda fmt: "May 01, 2026"),
            "data_end": SimpleNamespace(strftime=lambda fmt: "May 31, 2026"),
        },
    )
    monkeypatch.setattr(
        dashboard_page,
        "render_page_hero",
        lambda summary, note, context: captured.update(
            summary=summary,
            note=note,
            context=tuple(context),
        ),
    )
    monkeypatch.setattr(dashboard_page, "_render_metrics", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        dashboard_page, "_render_quick_actions", lambda *_args, **_kwargs: None
    )
    monkeypatch.setattr(
        dashboard_page, "_render_research_suite", lambda *_args, **_kwargs: None
    )
    monkeypatch.setattr(dashboard_page, "_render_quality", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        dashboard_page, "_render_asset_table", lambda *_args, **_kwargs: None
    )

    dashboard_page.render(object())

    assert fake_st.titles == ["Dashboard"]
    assert captured["summary"] == (
        "Track coverage and concentration across the current asset universe."
    )
    assert captured["note"] == (
        "Top sectors: Index (2), Finance (1). Use quick actions below to jump into "
        "charts or trading."
    )
    assert captured["context"] == (
        ("Assets", 3),
        ("Active", 2),
        ("Rows", "125.0K"),
        ("Window", "May 01, 2026 – May 31, 2026"),
    )


def test_render_quality_uses_empty_state_when_no_assets(monkeypatch) -> None:
    fake_st = _MarkdownStreamlit()
    captured: dict[str, tuple[object, ...]] = {}

    monkeypatch.setattr(dashboard_page, "render_empty_state", lambda *args: captured.setdefault("empty", args))

    dashboard_page._render_quality(fake_st, object(), [])

    empty = cast(
        tuple[object, str, str, str, tuple[tuple[str, str, str], ...]],
        captured["empty"],
    )
    _, title, summary, note, chips = empty
    assert title == "No assets to check."
    assert "Add assets before running the quality report." in summary
    assert "at least one asset is registered" in note
    assert chips[0] == ("Assets", "0 registered", "warning")


def test_render_quality_uses_empty_state_when_report_unavailable(monkeypatch) -> None:
    fake_st = _MarkdownStreamlit()
    captured: dict[str, tuple[object, ...]] = {}
    assets = [SimpleNamespace(symbol="NIFTY")]

    monkeypatch.setattr(
        dashboard_page,
        "build_data_quality_report",
        lambda _repository, _symbols: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    monkeypatch.setattr(dashboard_page, "render_empty_state", lambda *args: captured.setdefault("empty", args))

    dashboard_page._render_quality(fake_st, object(), assets)

    empty = cast(
        tuple[object, str, str, str, tuple[tuple[str, str, str], ...]],
        captured["empty"],
    )
    _, title, summary, note, chips = empty
    assert title == "Data quality report unavailable."
    assert "current assets" in summary
    assert note == "Error: boom"
    assert chips[0] == ("Symbols checked", "1", "warning")


def test_render_asset_table_uses_empty_state_when_universe_missing(monkeypatch) -> None:
    fake_st = _MarkdownStreamlit()
    captured: dict[str, tuple[object, ...]] = {}

    monkeypatch.setattr(dashboard_page, "render_empty_state", lambda *args: captured.setdefault("empty", args))

    dashboard_page._render_asset_table(fake_st, [])

    empty = cast(
        tuple[object, str, str, str, tuple[tuple[str, str, str], ...]],
        captured["empty"],
    )
    _, title, summary, note, chips = empty
    assert title == "No assets registered."
    assert "Add assets to make the dashboard useful." in summary
    assert "asset universe is empty" in note
    assert chips[1] == ("Coverage", "Unavailable", "warning")


def test_render_asset_table_uses_empty_state_for_no_match(monkeypatch) -> None:
    fake_st = _MarkdownStreamlit("BANK")
    captured: dict[str, tuple[object, ...]] = {}
    assets = [
        SimpleNamespace(symbol="NIFTY", name="Nifty 50", sector="Index", market="NSE"),
        SimpleNamespace(symbol="FINANCE", name="Finance", sector="Finance", market="NSE"),
    ]

    monkeypatch.setattr(dashboard_page, "render_empty_state", lambda *args: captured.setdefault("empty", args))

    dashboard_page._render_asset_table(fake_st, assets)

    empty = cast(
        tuple[object, str, str, str, tuple[tuple[str, str, str], ...]],
        captured["empty"],
    )
    _, title, summary, note, chips = empty
    assert title == "No assets match your search."
    assert "Adjust the filter" in summary
    assert note == "2 assets are currently loaded."
    assert chips[0] == ("Results", "0", "warning")
