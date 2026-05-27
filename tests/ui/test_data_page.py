from __future__ import annotations

import contextlib
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

from project.data.db import DuckDBAccess
from project.data.ingestion import build_raw_price_point
from project.data.repository import DataRepository
from project.ui.pages import data as data_page
from project.ui_services.data_views import get_data_page_view


def test_render_snapshot_form_prefills_guided_controls_and_creates_snapshot(
    tmp_path: Path,
) -> None:
    repository = _repository(tmp_path)
    asset = repository.add_asset("AAPL", "Apple", "equity", "NASDAQ")
    _seed_market_history(repository, asset.asset_id, asset.symbol)
    view = get_data_page_view(repository)
    fake_st = _FakeDataStreamlit(
        selected_symbols=("AAPL",),
        data_start=date(2026, 5, 1),
        data_end=date(2026, 5, 3),
        submit=True,
    )
    captured: dict[str, object] = {}
    original_create_snapshot = data_page.create_snapshot

    try:
        data_page.create_snapshot = _fake_create_snapshot(captured)  # type: ignore[assignment]
        data_page._render_snapshot_form(fake_st, repository, view)
    finally:
        data_page.create_snapshot = original_create_snapshot  # type: ignore[assignment]
        repository.close()

    assert view.default_snapshot.data_start == "2026-05-01"
    assert view.default_snapshot.data_end == "2026-05-03"
    assert view.workflow_next_command == "create-dataset-snapshot"
    assert fake_st.info_messages == [
        "Mission Control recommends creating a dataset snapshot."
    ]
    assert captured["args"] == (
        repository,
        "Operator Snapshot",
        "NSE",
        ("AAPL",),
        "2026-05-01",
        "2026-05-03",
        "1d",
        "Created from the MFT Operator Cockpit",
    )
    assert fake_st.error_messages == []
    assert fake_st.success_messages == ["Created snapshot dataset_snapshot:test"]


def test_render_snapshot_form_blocks_invalid_date_order(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    asset = repository.add_asset("AAPL", "Apple", "equity", "NASDAQ")
    _seed_market_history(repository, asset.asset_id, asset.symbol)
    view = get_data_page_view(repository)
    fake_st = _FakeDataStreamlit(
        selected_symbols=("AAPL",),
        data_start=date(2026, 5, 3),
        data_end=date(2026, 5, 1),
        submit=True,
    )
    captured: dict[str, object] = {}
    original_create_snapshot = data_page.create_snapshot

    try:
        data_page.create_snapshot = _fake_create_snapshot(captured)  # type: ignore[assignment]
        data_page._render_snapshot_form(fake_st, repository, view)
    finally:
        data_page.create_snapshot = original_create_snapshot  # type: ignore[assignment]
        repository.close()

    assert fake_st.error_messages == [
        "Data start must be on or before data end."
    ]
    assert fake_st.button_disabled is True
    assert captured == {}


def _fake_create_snapshot(captured: dict[str, object]):
    def fake_create_snapshot(
        repository: DataRepository,
        name: str,
        market: str,
        symbols: tuple[str, ...],
        data_start: str,
        data_end: str,
        resolution: str,
        description: str | None,
    ) -> SimpleNamespace:
        captured["args"] = (
            repository,
            name,
            market,
            symbols,
            data_start,
            data_end,
            resolution,
            description,
        )
        return SimpleNamespace(
            dataset_snapshot_id="dataset_snapshot:test",
            dataset_snapshot=SimpleNamespace(
                dataset_snapshot_id="dataset_snapshot:test",
                universe_id="research_universe:test",
            ),
        )

    return fake_create_snapshot


def _repository(tmp_path: Path) -> DataRepository:
    db = DuckDBAccess(tmp_path / "mft.duckdb")
    repository = DataRepository(db)
    repository.initialize()
    return repository


def _seed_market_history(repository: DataRepository, asset_id: str, symbol: str) -> None:
    base = datetime(2026, 5, 1, tzinfo=UTC)
    for index in range(3):
        timestamp = base + timedelta(days=index)
        close = 100.0 + float(index)
        repository.ingest_market_data(
            symbol,
            timestamp,
            close - 1.0,
            close + 1.0,
            close - 2.0,
            close,
            1000.0 + float(index),
        )
        repository.ingest_raw(
            build_raw_price_point(
                asset_id,
                timestamp.isoformat(),
                close,
                "csv:fixture",
            )
        )


class _FakeDataStreamlit:
    def __init__(
        self,
        *,
        selected_symbols: tuple[str, ...],
        data_start: date,
        data_end: date,
        submit: bool,
    ) -> None:
        self.selected_symbols = selected_symbols
        self.data_start = data_start
        self.data_end = data_end
        self.submit = submit
        self.info_messages: list[str] = []
        self.error_messages: list[str] = []
        self.success_messages: list[str] = []
        self.button_disabled = False

    def container(self, *_args, **_kwargs):
        return contextlib.nullcontext()

    def subheader(self, *_args, **_kwargs) -> None:
        return None

    def info(self, message: str) -> None:
        self.info_messages.append(message)

    def multiselect(self, *_args, **_kwargs) -> tuple[str, ...]:
        return self.selected_symbols

    def text_input(self, *_args, **_kwargs) -> str:
        label = _args[0]
        if label == "Snapshot name":
            return "Operator Snapshot"
        if label == "Market":
            return "NSE"
        if label == "Resolution":
            return "1d"
        raise AssertionError(label)

    def date_input(self, *_args, **_kwargs) -> date:
        label = _args[0]
        if label == "Data start":
            return self.data_start
        if label == "Data end":
            return self.data_end
        raise AssertionError(label)

    def text_area(self, *_args, **_kwargs) -> str:
        return "Created from the MFT Operator Cockpit"

    def error(self, message: str) -> None:
        self.error_messages.append(message)

    def button(self, *_args, disabled: bool = False, **_kwargs) -> bool:
        self.button_disabled = disabled
        return self.submit and not disabled

    def success(self, message: str) -> None:
        self.success_messages.append(message)

    def write(self, *_args, **_kwargs) -> None:
        return None
