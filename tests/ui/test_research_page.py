from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Literal, cast

from project.cli_utils import ensure_default_hypothesis_catalog
from project.common.models import DatasetSnapshot, ResearchUniverse
from project.data.db import DuckDBAccess
from project.data.repository import DataRepository
from project.ui.pages import research as research_page
from project.ui_services.research_views import get_research_page_view


class _FakeBlock:
    def __init__(self, parent: "_FakeStreamlit") -> None:
        self._parent = parent

    def __enter__(self) -> "_FakeStreamlit":
        return self._parent

    def __exit__(self, *_args) -> Literal[False]:
        return False


class _FakeStreamlit:
    def __init__(self, submitted: bool) -> None:
        self.submitted = submitted
        self.calls: list[tuple[object, ...]] = []
        self.code_calls: list[str] = []
        self.write_calls: list[object] = []

    def title(self, text: str) -> None:
        self.calls.append(("title", text))

    def caption(self, text: str) -> None:
        self.calls.append(("caption", text))

    def info(self, text: str) -> None:
        self.calls.append(("info", text))

    def success(self, text: str) -> None:
        self.calls.append(("success", text))

    def error(self, text: str) -> None:
        self.calls.append(("error", text))

    def subheader(self, text: str) -> None:
        self.calls.append(("subheader", text))

    def write(self, value) -> None:
        self.write_calls.append(value)

    def code(self, value: str, language: str = "") -> None:
        self.code_calls.append(value)

    def selectbox(self, label: str, options, index: int = 0):
        value = options[index]
        self.calls.append(("selectbox", label, value))
        return value

    def text_input(self, label: str, value: str = "") -> str:
        self.calls.append(("text_input", label, value))
        return value

    def form_submit_button(self, label: str) -> bool:
        self.calls.append(("submit", label))
        return self.submitted

    def container(self, border: bool = False) -> _FakeBlock:
        self.calls.append(("container", border))
        return _FakeBlock(self)

    def form(self, key: str) -> _FakeBlock:
        self.calls.append(("form", key))
        return _FakeBlock(self)


def test_research_page_view_exposes_guided_launch_context(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    try:
        view = get_research_page_view(repository)

        assert (
            view.workflow_context["next_recommended_command"] == "run-strategy-research"
        )
        assert view.launch.default_asset_symbol == "AAPL"
        assert (
            view.launch.default_dataset_snapshot_id == "dataset_snapshot:research:demo"
        )
        assert view.launch.default_hypothesis_id == "hypothesis:rsi_mean_reversion"
        assert view.launch.default_start_date == "2026-05-01"
        assert view.launch.default_end_date == "2026-05-05"
        assert view.launch.workflow_command == "run-strategy-research"
        assert (
            view.launch.workflow_note
            == "Mission Control next action: run-strategy-research"
        )
    finally:
        repository.close()


def test_research_page_launch_requires_explicit_submit(
    monkeypatch, tmp_path: Path
) -> None:
    repository = _repository(tmp_path)
    fake_st = _FakeStreamlit(submitted=False)
    launches: list[tuple[object, ...]] = []

    monkeypatch.setattr(research_page, "get_streamlit", lambda: fake_st)
    monkeypatch.setattr(
        research_page, "render_status_cards", lambda *_args, **_kwargs: None
    )
    monkeypatch.setattr(
        research_page, "render_evidence_table", lambda *_args, **_kwargs: None
    )
    monkeypatch.setattr(
        research_page, "render_json_debug", lambda *_args, **_kwargs: None
    )
    monkeypatch.setattr(
        research_page,
        "launch_research_run",
        _capture_launch(launches),
    )

    try:
        research_page.render(repository)

        assert launches == []
        assert fake_st.code_calls[0].startswith(
            "mft research run hypothesis:rsi_mean_reversion AAPL --snapshot dataset_snapshot:research:demo"
        )
    finally:
        repository.close()


def test_research_page_launch_executes_on_submit(monkeypatch, tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    fake_st = _FakeStreamlit(submitted=True)
    launches: list[tuple[object, ...]] = []

    monkeypatch.setattr(research_page, "get_streamlit", lambda: fake_st)
    monkeypatch.setattr(
        research_page, "render_status_cards", lambda *_args, **_kwargs: None
    )
    monkeypatch.setattr(
        research_page, "render_evidence_table", lambda *_args, **_kwargs: None
    )
    monkeypatch.setattr(
        research_page, "render_json_debug", lambda *_args, **_kwargs: None
    )

    def _launch(*args, **kwargs):
        launches.append(args + tuple(sorted(kwargs.items())))
        return SimpleNamespace(
            research_run_id="research_run:test:1", status="completed"
        )

    monkeypatch.setattr(research_page, "launch_research_run", _launch)

    try:
        research_page.render(repository)

        assert launches
        assert ("success", "Launched research run research_run:test:1") in fake_st.calls
        assert (
            cast(dict[str, object], fake_st.write_calls[-1])["research_run_id"]
            == "research_run:test:1"
        )
    finally:
        repository.close()


def _capture_launch(launches: list[tuple[object, ...]]):
    def _launch(*args, **kwargs):
        launches.append(args + tuple(sorted(kwargs.items())))
        return SimpleNamespace(
            research_run_id="research_run:test:1",
            status="completed",
        )

    return _launch


def _repository(tmp_path: Path) -> DataRepository:
    db = DuckDBAccess(tmp_path / "mft.duckdb")
    repository = DataRepository(db)
    repository.initialize()
    ensure_default_hypothesis_catalog(repository)
    asset = repository.add_asset("AAPL", "Apple", "equity", "NASDAQ")
    repository.persist_research_artifact(
        ResearchUniverse(
            universe_id="research_universe:demo",
            name="Demo Universe",
            market="NASDAQ",
            description="Fixture universe",
            asset_ids=(asset.asset_id,),
        )
    )
    repository.persist_research_artifact(
        DatasetSnapshot(
            dataset_snapshot_id="dataset_snapshot:research:demo",
            universe_id="research_universe:demo",
            captured_at="2026-05-05T00:00:00+00:00",
            data_start="2026-05-01T00:00:00+00:00",
            data_end="2026-05-05T00:00:00+00:00",
            asset_ids=(asset.asset_id,),
        )
    )
    return repository
