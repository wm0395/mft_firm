from __future__ import annotations

import contextlib
from pathlib import Path

import pytest

import project.ui.pages.trade_ideas as trade_ideas_page
from project.common.models import TradeIdea, utc_now_iso
from project.data.db import DuckDBAccess
from project.data.repository import DataRepository
from project.tracking.positions import open_position
from project.ui.views import trade_ideas as trade_ideas_views
from project.ui.views.trade_ideas import TradeIdeaDetailView
from project.ui_services.trade_idea_views import submit_trade_decision


def test_trade_ideas_detail_exposes_persisted_decision_history(
    tmp_path: Path,
) -> None:
    repository, trade = _repository_with_trade(tmp_path, {"close": 112.0})
    try:
        decision = submit_trade_decision(
            repository,
            trade.trade_id,
            "watch",
            "market_conditions",
            "persisted decision",
        )
        detail = trade_ideas_views.get_trade_idea_detail_view(repository, trade.trade_id)

        assert detail is not None
        assert detail.decision_history[0].decision_id == decision.decision_id
        assert detail.decision_history[0].action == "watch"
        assert detail.decision_history[0].structured_reason == "market_conditions"
        assert detail.decision_history[0].notes == "persisted decision"
        assert detail.decision_history[0].created_at == decision.created_at
        assert len(detail.decision_history) == 1
    finally:
        repository.close()


def test_trade_ideas_detail_render_shows_positive_approval_outcome_after_submit(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository, detail, fake_st, captured_tables = (
        _render_submitted_trade_detail(
            monkeypatch,
            tmp_path,
            {"close": 112.0, "entry_price": 111.0, "price": 110.0},
        )
    )
    try:
        assert detail is not None
        assert detail.approval_outcome.state == "ok"
        assert detail.approval_outcome.message == (
            "Approved and an open position exists for this trade."
        )
        assert detail.approval_outcome.open_position_status == "open"
        assert detail.approval_outcome.open_position_entry_price == 112.0
        assert captured_tables["Decision history"] == detail.decision_history
        assert fake_st.info_messages == ["No open trade ideas."]
        assert fake_st.warning_messages == []
        assert fake_st.captions[-2:] == ["Approval outcome", "Read-only review record"]
        assert fake_st.writes[-3:] == [
            "Approved and an open position exists for this trade.",
            "Open position status: open",
            "Entry price: 112.00",
        ]
        assert repository.get_positions(status="open") == (
            open_position(detail.trade_id, 112.0),
        )
    finally:
        repository.close()


def test_trade_ideas_detail_render_shows_no_position_warning_after_submit(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository, detail, fake_st, captured_tables = (
        _render_submitted_trade_detail(
            monkeypatch,
            tmp_path,
            {"close": 0.0},
        )
    )
    try:
        assert detail is not None
        assert detail.approval_outcome.state == "warning"
        assert detail.approval_outcome.message == (
            "Approved, but no open position exists for this trade."
        )
        assert detail.approval_outcome.open_position_status is None
        assert detail.approval_outcome.open_position_entry_price is None
        assert captured_tables["Decision history"] == detail.decision_history
        assert fake_st.info_messages == ["No open trade ideas."]
        assert fake_st.warning_messages == [detail.approval_outcome.message]
        assert fake_st.captions[-2:] == ["Approval outcome", "Read-only review record"]
        assert repository.get_positions(status="open") == ()
    finally:
        repository.close()


def _render_submitted_trade_detail(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    signals_snapshot: dict[str, object],
) -> tuple[
    DataRepository,
    TradeIdeaDetailView,
    _FakeStreamlit,
    dict[str, tuple[object, ...]],
]:
    repository, trade = _repository_with_trade(tmp_path, signals_snapshot)
    fake_st = _FakeStreamlit()
    captured_tables: dict[str, tuple[object, ...]] = {}
    submit_trade_decision(
        repository,
        trade.trade_id,
        "approve",
        "market_conditions",
        "persisted decision",
    )
    monkeypatch.setattr(
        trade_ideas_page,
        "render_evidence_table",
        lambda title, rows: captured_tables.setdefault(title, rows),
    )
    monkeypatch.setattr(
        trade_ideas_page, "render_json_debug", lambda *_args, **_kwargs: None
    )
    monkeypatch.setattr(
        trade_ideas_page, "render_status_cards", lambda *_args, **_kwargs: None
    )
    monkeypatch.setattr(trade_ideas_page, "get_streamlit", lambda: fake_st)
    fake_st.session_state["selected_trade_id"] = trade.trade_id
    trade_ideas_page.render(repository)
    detail = trade_ideas_views.get_trade_idea_detail_view(repository, trade.trade_id)
    assert detail is not None
    return repository, detail, fake_st, captured_tables


def _repository_with_trade(
    tmp_path: Path,
    signals_snapshot: dict[str, object],
) -> tuple[DataRepository, TradeIdea]:
    db = DuckDBAccess(tmp_path / "mft.duckdb")
    repository = DataRepository(db)
    repository.initialize()
    asset = repository.add_asset("AAPL", "Apple", "equity", "NASDAQ")
    trade = TradeIdea(
        trade_id="trade:demo",
        asset_id=asset.asset_id,
        hypothesis_id="hypothesis:demo",
        version=1,
        direction="long",
        confidence=0.75,
        signals_snapshot=signals_snapshot,  # type: ignore[arg-type]
        timestamp=utc_now_iso(),
    )
    repository.persist_trade_idea(trade)
    return repository, trade


class _FakeStreamlit:
    def __init__(self) -> None:
        self.session_state: dict[str, object] = {}
        self.info_messages: list[str] = []
        self.warning_messages: list[str] = []
        self.captions: list[str] = []
        self.writes: list[str] = []

    def title(self, *_args, **_kwargs) -> None:
        return None

    def caption(self, text: str) -> None:
        self.captions.append(text)

    def info(self, text: str) -> None:
        self.info_messages.append(text)

    def warning(self, text: str) -> None:
        self.warning_messages.append(text)

    def write(self, text: object) -> None:
        self.writes.append(str(text))

    def subheader(self, *_args, **_kwargs) -> None:
        return None

    def container(self, **_kwargs):
        return contextlib.nullcontext()

    def form(self, *_args, **_kwargs):
        return contextlib.nullcontext()

    def checkbox(self, *_args, **_kwargs) -> bool:
        raise AssertionError("checkbox should not be called for read-only details")

    def radio(self, *_args, **_kwargs):
        raise AssertionError("radio should not be called for read-only details")

    def selectbox(self, *_args, **_kwargs):
        raise AssertionError("selectbox should not be called for read-only details")

    def text_area(self, *_args, **_kwargs) -> str:
        raise AssertionError("text_area should not be called for read-only details")

    def form_submit_button(self, *_args, **_kwargs) -> bool:
        raise AssertionError(
            "form_submit_button should not be called for read-only details"
        )

    def json(self, *_args, **_kwargs) -> None:
        return None
