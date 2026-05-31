from __future__ import annotations

import contextlib
from pathlib import Path
from typing import Any, cast

from project.common.models import TradeIdea, utc_now_iso
from project.data.repository import DataRepository
from project.tracking.positions import open_position
from project.ui import app
from project.ui.navigation import page_titles
from project.ui.pages import positions as positions_page
from project.ui.pages import charts as charts_page
from project.ui.pages import trading as trading_page
from project.ui.views.common import StatusCardView
from project.ui.views.positions import PositionDetailView, PositionsPageView
from project.ui_services.positions_views import get_positions_page_view
from tests.ui.test_views_support import _empty_repository, _seed_repository


class _FakeStreamlit:
    def __init__(self, selectbox_values: dict[str, str] | None = None) -> None:
        self.session_state: dict[str, object] = {}
        self.selectbox_values = selectbox_values or {}
        self.titles: list[str] = []
        self.captions: list[str] = []
        self.subheaders: list[str] = []
        self.writes: list[Any] = []
        self.infos: list[str] = []
        self.errors: list[str] = []
        self.dataframes: list[Any] = []
        self.json_payloads: list[Any] = []

    def title(self, text: str) -> None:
        self.titles.append(text)

    def caption(self, text: str) -> None:
        self.captions.append(text)

    def subheader(self, text: str) -> None:
        self.subheaders.append(text)

    def write(self, value: object) -> None:
        self.writes.append(value)

    def info(self, text: str) -> None:
        self.infos.append(text)

    def error(self, text: str) -> None:
        self.errors.append(text)

    def json(self, value: object) -> None:
        self.json_payloads.append(value)

    def dataframe(self, value: object, **_kwargs) -> None:
        self.dataframes.append(value)

    def selectbox(self, label: str, options, index: int = 0, **_kwargs) -> str:
        return self.selectbox_values.get(label, options[index])

    def container(self, **_kwargs):
        return contextlib.nullcontext()

    def expander(self, *_args, **_kwargs):
        return contextlib.nullcontext()


def test_positions_page_view_is_empty_for_empty_repository(tmp_path: Path) -> None:
    repository = _empty_repository(tmp_path)
    try:
        view = get_positions_page_view(repository)
        assert _position_counts(view) == (0, 0, 0)
        assert view.realized_pnl is None
    finally:
        repository.close()


def test_positions_page_view_exposes_open_and_closed_position_values(
    tmp_path: Path,
) -> None:
    repository, open_trade = _seed_positions_repository(tmp_path)
    try:
        view = get_positions_page_view(repository)
        positions: tuple[PositionDetailView, ...] = view.positions
        open_position_view = next(
            position for position in positions if position.status == "open"
        )
        closed_position_view = next(
            position for position in positions if position.status == "closed"
        )

        assert len(positions) == 2
        assert {position.status for position in positions} == {"open", "closed"}
        assert open_position_view.position_id == f"position:{open_trade.trade_id}"
        assert open_position_view.entry_price == 111.0
        assert open_position_view.exit_price is None
        assert open_position_view.pnl is None
        assert closed_position_view.position_id == "position:operator:1"
        assert closed_position_view.entry_price == 100.0
        assert closed_position_view.exit_price == 110.0
        assert closed_position_view.pnl == 10.0
    finally:
        repository.close()


def test_positions_page_render_shows_empty_state_for_empty_repository(
    monkeypatch,
    tmp_path: Path,
) -> None:
    repository = _empty_repository(tmp_path)
    fake_st = _FakeStreamlit()
    captured: dict[str, object] = {}
    try:
        _render_positions_page(monkeypatch, repository, fake_st, captured)
        view = cast(PositionsPageView, captured["view"])

        assert fake_st.titles == ["Positions"]
        assert fake_st.infos == ["No positions match the current filter."]
        assert fake_st.writes == []
        assert _card_values(cast(tuple[StatusCardView, ...], captured["cards"])) == (
            ("Positions", "0"),
            ("Open", "0"),
            ("Closed", "0"),
            ("Realized PnL", "n/a"),
        )
        assert fake_st.dataframes == []
        assert captured["table:Positions"] == ()
        assert view.positions == ()
    finally:
        repository.close()


def test_positions_page_render_shows_detail_and_rows_for_closed_position(
    monkeypatch,
    tmp_path: Path,
) -> None:
    repository, _ = _seed_positions_repository(tmp_path)
    fake_st = _FakeStreamlit(
        selectbox_values={
            "Status filter": "closed",
            "Position": "position:operator:1",
        }
    )
    captured: dict[str, object] = {}
    try:
        _render_positions_page(monkeypatch, repository, fake_st, captured)
        view = cast(PositionsPageView, captured["view"])
        rows = cast(Any, fake_st.dataframes[0]).to_dict(orient="records")
        detail = view.positions[0]

        assert _card_values(cast(tuple[StatusCardView, ...], captured["cards"])) == (
            ("Positions", "2"),
            ("Open", "1"),
            ("Closed", "1"),
            ("Realized PnL", "10.00"),
        )
        assert "Selected position" in fake_st.captions
        assert fake_st.writes == _summary_writes(detail) + _detail_writes(detail)
        assert rows == [_table_row(detail)]
        assert fake_st.json_payloads == [{"rsi_14": 22.5}]
    finally:
        repository.close()


def test_navigation_includes_positions_page() -> None:
    assert "Positions" in page_titles()
    assert "Positions" in app.PAGES
    assert app.PAGES["Positions"] is positions_page.render
    assert "Charts" in page_titles()
    assert "Trading" in page_titles()
    assert app.PAGES["Charts"] is charts_page.render
    assert app.PAGES["Trading"] is trading_page.render


def _render_positions_page(
    monkeypatch,
    repository: DataRepository,
    fake_st: _FakeStreamlit,
    captured: dict[str, object],
) -> None:
    monkeypatch.setattr(positions_page, "get_streamlit", lambda: fake_st)
    monkeypatch.setattr(
        positions_page,
        "get_positions_page_view",
        lambda _repository: _capture_view(
            captured, get_positions_page_view(repository)
        ),
    )
    monkeypatch.setattr(
        positions_page,
        "render_status_cards",
        lambda cards: captured.setdefault("cards", cards),
    )
    monkeypatch.setattr(
        positions_page,
        "render_evidence_table",
        lambda title, rows: captured.setdefault(f"table:{title}", rows),
    )
    monkeypatch.setattr(
        positions_page,
        "render_json_debug",
        lambda title, payload: captured.setdefault("debug", (title, payload)),
    )
    positions_page.render(repository)


def _card_values(cards: tuple[StatusCardView, ...]) -> tuple[tuple[str, str], ...]:
    return tuple((card.label, card.value) for card in cards)


def _position_counts(view: PositionsPageView) -> tuple[int, int, int]:
    return (
        len(view.positions),
        view.open_count,
        view.closed_count,
    )


def _table_row(detail: PositionDetailView) -> dict[str, str]:
    return {
        "position_id": detail.position_id,
        "trade_id": detail.trade_id,
        "asset_symbol": detail.asset_symbol,
        "hypothesis_name": detail.hypothesis_name,
        "direction": detail.direction,
        "status": detail.status,
        "entry_price": f"{detail.entry_price:.2f}",
        "exit_price": (
            "n/a" if detail.exit_price is None else f"{detail.exit_price:.2f}"
        ),
        "pnl": "n/a" if detail.pnl is None else f"{detail.pnl:.2f}",
        "trade_timestamp": detail.trade_timestamp,
    }


def _detail_writes(detail: PositionDetailView) -> list[str]:
    return [
        f"Position ID: {detail.position_id}",
        f"Trade ID: {detail.trade_id}",
        f"Asset: {detail.asset_symbol} {detail.asset_name}",
        f"Hypothesis: {detail.hypothesis_name} {detail.hypothesis_id}",
        f"Direction: {detail.direction}",
        f"Status: {detail.status}",
        f"Trade timestamp: {detail.trade_timestamp}",
        f"Entry price: {detail.entry_price:.2f}",
        (
            f"Exit price: "
            f"{('n/a' if detail.exit_price is None else f'{detail.exit_price:.2f}')}"
        ),
        f"PnL: {('n/a' if detail.pnl is None else f'{detail.pnl:.2f}')}",
    ]


def _summary_writes(detail: PositionDetailView) -> list[str]:
    outcome = "Open position"
    if detail.pnl is not None and detail.status != "open":
        outcome = f"{detail.pnl:.2f}"
    return [
        f"Position: {detail.position_id} • Trade {detail.trade_id}",
        f"Asset: {detail.asset_symbol} • {detail.asset_name or 'n/a'}",
        f"Hypothesis: {detail.hypothesis_name} • {detail.hypothesis_id or 'n/a'}",
        (
            f"Outcome: {outcome} • {detail.direction.title()} • "
            f"{detail.status.title()}"
        ),
    ]


def _capture_view(captured: dict[str, object], view: object) -> object:
    captured["view"] = view
    return view


def _seed_positions_repository(
    tmp_path: Path,
) -> tuple[DataRepository, TradeIdea]:
    repository, _, base_trade_id, _ = _seed_repository(tmp_path)
    base_trade = next(
        idea for idea in repository.get_trade_ideas() if idea.trade_id == base_trade_id
    )
    open_trade = TradeIdea(
        trade_id=f"{base_trade_id}:open",
        asset_id=base_trade.asset_id,
        hypothesis_id=base_trade.hypothesis_id,
        version=base_trade.version,
        direction=base_trade.direction,
        confidence=base_trade.confidence,
        signals_snapshot={"close": 111.0},
        timestamp=utc_now_iso(),
    )
    repository.persist_trade_idea(open_trade)
    repository.persist_position(open_position(open_trade.trade_id, 111.0))
    return repository, open_trade
