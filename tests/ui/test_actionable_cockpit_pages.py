from __future__ import annotations

import contextlib
from datetime import date
from collections.abc import Callable
from typing import cast
from types import SimpleNamespace

from project.ui.pages import data as data_page
from project.ui.pages import mission_control as mission_control_page
from project.ui.pages import research as research_page
from project.ui.views.common import StatusCardView, WorkflowStepView


class _FakeStreamlit:
    def __init__(
        self,
        *,
        selectbox_values: dict[str, str] | None = None,
        multiselect_values: dict[str, list[str]] | None = None,
        date_values: dict[str, date] | None = None,
        text_inputs: dict[str, str] | None = None,
        text_areas: dict[str, str] | None = None,
        submit: bool = True,
    ) -> None:
        self.session_state: dict[str, object] = {}
        self.selectbox_values = selectbox_values or {}
        self.multiselect_values = multiselect_values or {}
        self.date_values = date_values or {}
        self.text_inputs = text_inputs or {}
        self.text_areas = text_areas or {}
        self.submit = submit
        self.titles: list[str] = []
        self.captions: list[str] = []
        self.subheaders: list[str] = []
        self.writes: list[object] = []
        self.info_messages: list[str] = []
        self.codes: list[tuple[str, str]] = []
        self.success_messages: list[str] = []
        self.error_messages: list[str] = []
        self.button_calls: list[tuple[str, str, bool]] = []
        self.rerun_calls = 0

    def title(self, text: str) -> None:
        self.titles.append(text)

    def caption(self, text: str) -> None:
        self.captions.append(text)

    def subheader(self, text: str) -> None:
        self.subheaders.append(text)

    def write(self, value) -> None:
        self.writes.append(value)

    def info(self, text: str) -> None:
        self.info_messages.append(text)

    def code(self, value: str, language: str = "text") -> None:
        self.codes.append((value, language))

    def success(self, text: str) -> None:
        self.success_messages.append(text)

    def error(self, text: str) -> None:
        self.error_messages.append(text)

    def rerun(self) -> None:
        self.rerun_calls += 1

    def container(self, **_kwargs):
        return contextlib.nullcontext()

    def form(self, *_args, **_kwargs):
        return contextlib.nullcontext()

    def selectbox(self, label: str, options, index: int = 0) -> str:
        return self.selectbox_values.get(label, options[index])

    def multiselect(self, label: str, options, default, format_func):
        return self.multiselect_values.get(label, default)

    def date_input(self, label: str, value: date) -> date:
        return self.date_values.get(label, value)

    def text_input(self, label: str, value: str = "") -> str:
        return self.text_inputs.get(label, value)

    def text_area(self, label: str, value: str = "") -> str:
        return self.text_areas.get(label, value)

    def form_submit_button(self, *_args, **_kwargs) -> bool:
        return self.submit

    def button(self, label: str, type: str = "secondary", disabled: bool = False) -> bool:
        self.button_calls.append((label, type, disabled))
        return self.submit and not disabled


def test_mission_control_render_wires_action_context(monkeypatch) -> None:
    fake_st = _FakeStreamlit()
    captured: dict[str, object] = {}
    view = _mission_control_view()

    monkeypatch.setattr(mission_control_page, "get_streamlit", lambda: fake_st)
    monkeypatch.setattr(
        mission_control_page,
        "get_mission_control_view",
        lambda _repository: view,
    )
    monkeypatch.setattr(
        mission_control_page,
        "render_status_cards",
        lambda cards: captured.setdefault("cards", cards),
    )
    monkeypatch.setattr(
        mission_control_page,
        "render_workflow_stepper",
        lambda steps: captured.setdefault("steps", steps),
    )
    monkeypatch.setattr(
        mission_control_page,
        "render_json_debug",
        lambda title, payload: captured.setdefault("debug", (title, payload)),
    )
    monkeypatch.setattr(
        mission_control_page,
        "render_action_panel",
        lambda title, explanation, button_label, *, key, on_click, **kwargs: captured.update(
            action_panel=(title, explanation, button_label, key, on_click, kwargs)
        ),
    )

    mission_control_page.render(object())

    assert fake_st.titles == ["MFT Mission Control"]
    assert fake_st.captions[0] == "Health: Warning"
    assert fake_st.writes == [
        "No dataset snapshot exists: Research runs need reproducible dataset snapshots.",
        "Latest research run: completed",
    ]
    action_panel = cast(
        tuple[str, str, str, str, Callable[[], None] | None, dict[str, object]],
        captured["action_panel"],
    )
    assert action_panel[:4] == (
        "Recommended next action",
        "No research run exists yet.",
        "Run Research",
        "mission-control-action",
    )
    assert action_panel[5]["target_page"] == "Research"
    assert action_panel[5]["disabled"] is False
    assert action_panel[5]["disabled_reason"] is None

    on_click = action_panel[4]
    assert on_click is not None
    on_click()

    assert fake_st.session_state["ui_page"] == "Research"
    assert fake_st.rerun_calls == 1
    assert captured["debug"] == ("Raw JSON / Debug", view.debug_payload)


def test_mission_control_render_uses_html_summary_when_available(
    monkeypatch,
) -> None:
    class _MarkdownStreamlit(_FakeStreamlit):
        def __init__(self) -> None:
            super().__init__()
            self.markdowns: list[tuple[str, bool]] = []

        def markdown(self, text: str, unsafe_allow_html: bool = False) -> None:
            self.markdowns.append((text, unsafe_allow_html))

    fake_st = _MarkdownStreamlit()
    captured: dict[str, object] = {}
    view = _mission_control_view()

    monkeypatch.setattr(mission_control_page, "get_streamlit", lambda: fake_st)
    monkeypatch.setattr(
        mission_control_page,
        "get_mission_control_view",
        lambda _repository: view,
    )
    monkeypatch.setattr(
        mission_control_page,
        "render_status_cards",
        lambda cards: captured.setdefault("cards", cards),
    )
    monkeypatch.setattr(
        mission_control_page,
        "render_workflow_stepper",
        lambda steps: captured.setdefault("steps", steps),
    )
    monkeypatch.setattr(
        mission_control_page,
        "render_json_debug",
        lambda title, payload: captured.setdefault("debug", (title, payload)),
    )
    monkeypatch.setattr(
        mission_control_page,
        "render_action_panel",
        lambda title, explanation, button_label, *, key, on_click, **kwargs: captured.update(
            action_panel=(title, explanation, button_label, key, on_click, kwargs)
        ),
    )

    mission_control_page.render(object())

    summary_html = next(
        html for html, unsafe in fake_st.markdowns if "Current posture" in html
    )
    assert "Health" in summary_html
    assert "Run Research" in summary_html
    assert "No research run exists yet." in summary_html
    assert "Warnings" in summary_html
    assert "Activity" in summary_html


def test_data_render_submits_structured_snapshot_payload(monkeypatch) -> None:
    repository = object()
    fake_st = _FakeStreamlit(
        multiselect_values={"Assets": ["NIFTY", "BANKNIFTY"]},
        date_values={
            "Data start": date(2026, 5, 1),
            "Data end": date(2026, 5, 25),
        },
        text_inputs={
            "Snapshot name": "Operator Snapshot",
            "Market": "NSE",
            "Resolution": "1d",
        },
        text_areas={
            "Description": "",
        },
    )
    captured: dict[str, object] = {}
    view = _data_view()

    monkeypatch.setattr(data_page, "get_streamlit", lambda: fake_st)
    monkeypatch.setattr(data_page, "get_data_page_view", lambda _repository: view)
    monkeypatch.setattr(
        data_page,
        "render_status_cards",
        lambda cards: captured.setdefault("cards", cards),
    )
    monkeypatch.setattr(
        data_page,
        "render_workflow_stepper",
        lambda steps: captured.setdefault("steps", steps),
    )
    monkeypatch.setattr(
        data_page,
        "render_evidence_table",
        lambda title, rows: captured.setdefault(f"table:{title}", rows),
    )
    monkeypatch.setattr(
        data_page,
        "render_json_debug",
        lambda title, payload: captured.setdefault("debug", (title, payload)),
    )
    monkeypatch.setattr(
        data_page,
        "create_snapshot",
        lambda *args: _capture_snapshot_args(captured, args),
    )
    monkeypatch.setattr(
        data_page,
        "render_snapshot_result",
        lambda _st, result: captured.setdefault("snapshot_result", result),
    )

    data_page.render(repository)

    cards = cast(tuple[StatusCardView, ...], captured["cards"])
    steps = cast(tuple[WorkflowStepView, ...], captured["steps"])
    assert [card.label for card in cards] == [
        "Assets",
        "Quality",
        "Snapshots",
        "Freshness",
    ]
    assert [step.label for step in steps] == [
        "Data Overview",
        "Market Data Sync",
        "Data Quality",
        "Dataset Snapshots",
        "Asset Universe",
    ]
    assert fake_st.writes[:6] == [
        "Mission Control recommends creating a dataset snapshot.",
        "Prepare a reproducible cut of the current universe before launching research.",
        "Review the draft values below, then create the snapshot when the inputs look right.",
        "Next step: Confirm inputs",
        "Assets: 2 available",
        "Snapshots: 1 existing",
    ]
    assert fake_st.info_messages == []
    assert fake_st.button_calls == [("Create Snapshot", "primary", False)]
    assert captured["snapshot_args"] == (
        repository,
        "Operator Snapshot",
        "NSE",
        ("NIFTY", "BANKNIFTY"),
        "2026-05-01",
        "2026-05-25",
        "1d",
        None,
    )
    assert captured["snapshot_result"].dataset_snapshot_id == "dataset_snapshot:demo"
    assert fake_st.success_messages == ["Created snapshot dataset_snapshot:demo"]
    assert fake_st.error_messages == []
    assert captured["debug"] == ("Raw JSON / Debug", view.debug_payload)


def test_data_render_uses_html_snapshot_preview_when_available(
    monkeypatch,
) -> None:
    class _MarkdownStreamlit(_FakeStreamlit):
        def __init__(self, **kwargs) -> None:
            super().__init__(**kwargs)
            self.markdowns: list[tuple[str, bool]] = []

        def markdown(self, text: str, unsafe_allow_html: bool = False) -> None:
            self.markdowns.append((text, unsafe_allow_html))

    repository = object()
    fake_st = _MarkdownStreamlit(
        multiselect_values={"Assets": ["NIFTY", "BANKNIFTY"]},
        date_values={
            "Data start": date(2026, 5, 1),
            "Data end": date(2026, 5, 25),
        },
        text_inputs={
            "Snapshot name": "Operator Snapshot",
            "Market": "NSE",
            "Resolution": "1d",
        },
        text_areas={
            "Description": "",
        },
    )
    captured: dict[str, object] = {}
    view = _data_view()

    monkeypatch.setattr(data_page, "get_streamlit", lambda: fake_st)
    monkeypatch.setattr(data_page, "get_data_page_view", lambda _repository: view)
    monkeypatch.setattr(
        data_page,
        "render_status_cards",
        lambda cards: captured.setdefault("cards", cards),
    )
    monkeypatch.setattr(
        data_page,
        "render_workflow_stepper",
        lambda steps: captured.setdefault("steps", steps),
    )
    monkeypatch.setattr(
        data_page,
        "render_evidence_table",
        lambda title, rows: captured.setdefault(f"table:{title}", rows),
    )
    monkeypatch.setattr(
        data_page,
        "render_json_debug",
        lambda title, payload: captured.setdefault("debug", (title, payload)),
    )
    monkeypatch.setattr(
        data_page,
        "create_snapshot",
        lambda *args: _capture_snapshot_args(captured, args),
    )

    data_page.render(repository)

    guidance_html = next(
        html
        for html, unsafe in fake_st.markdowns
        if "Mission Control recommends creating a dataset snapshot." in html
    )
    assert "Confirm inputs" in guidance_html
    assert fake_st.info_messages == []
    preview_html = next(html for html, unsafe in fake_st.markdowns if "Snapshot draft" in html)
    assert "Operator Snapshot" in preview_html
    assert "BANKNIFTY" in preview_html
    assert "Readiness" in preview_html


def test_data_render_blocks_invalid_snapshot_submission(monkeypatch) -> None:
    repository = object()
    fake_st = _FakeStreamlit(
        multiselect_values={"Assets": []},
        date_values={
            "Data start": date(2026, 5, 25),
            "Data end": date(2026, 5, 24),
        },
    )
    captured: dict[str, object] = {}
    view = _data_view()

    monkeypatch.setattr(data_page, "get_streamlit", lambda: fake_st)
    monkeypatch.setattr(data_page, "get_data_page_view", lambda _repository: view)
    monkeypatch.setattr(data_page, "render_status_cards", lambda cards: None)
    monkeypatch.setattr(data_page, "render_workflow_stepper", lambda steps: None)
    monkeypatch.setattr(data_page, "render_evidence_table", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        data_page,
        "render_json_debug",
        lambda title, payload: captured.setdefault("debug", (title, payload)),
    )
    monkeypatch.setattr(
        data_page,
        "create_snapshot",
        lambda *args: _capture_snapshot_args(captured, args),
    )

    data_page.render(repository)

    assert fake_st.error_messages == [
        "Select at least one asset before creating a snapshot.",
        "Data start must be on or before data end.",
    ]
    assert fake_st.button_calls == [("Create Snapshot", "primary", True)]
    assert "snapshot_args" not in captured
    assert captured["debug"] == ("Raw JSON / Debug", view.debug_payload)


def test_research_render_keeps_guided_surface_readable(monkeypatch) -> None:
    fake_st = _FakeStreamlit(submit=False)
    captured: dict[str, object] = {}
    view = _research_view()

    monkeypatch.setattr(research_page, "get_streamlit", lambda: fake_st)
    monkeypatch.setattr(
        research_page,
        "get_research_page_view",
        lambda _repository: view,
    )
    monkeypatch.setattr(
        research_page,
        "render_status_cards",
        lambda cards: captured.setdefault("cards", cards),
    )
    monkeypatch.setattr(
        research_page,
        "render_evidence_table",
        lambda title, rows: captured.setdefault(f"table:{title}", rows),
    )
    monkeypatch.setattr(
        research_page,
        "render_json_debug",
        lambda title, payload: captured.setdefault(
            f"debug:{title}", payload
        ),
    )

    research_page.render(object())

    assert fake_st.titles == ["Research"]
    assert fake_st.writes[:7] == [
        "Ready to launch RSI Mean Reversion on NIFTY with dataset_snapshot:demo from 2026-05-01 to 2026-05-25. Production hypotheses only",
        "Review the exact command block below before submitting.",
        "Asset: NIFTY",
        "Snapshot: dataset_snapshot:demo",
        "Hypothesis: RSI Mean Reversion",
        "Window: 2026-05-01 -> 2026-05-25",
        "Policy: Production hypotheses only",
    ]
    assert fake_st.captions == [
        "Launch flags: include_testing=False, include_draft=False",
        "Project records tied to strategy work.",
        "Historical run executions and outcomes.",
        "Draft and promoted candidates in review.",
        "Snapshot choices available for launch.",
        "Actionable hypotheses in scope for launch.",
    ]
    assert "Read the summary above, then inspect the raw dossier JSON below." in fake_st.writes
    assert fake_st.codes == [
        (
            "mft research run hypothesis:rsi_mean_reversion NIFTY --snapshot "
            "dataset_snapshot:demo\nstart-date=2026-05-01 end-date=2026-05-25\n"
            "safe-call=project.backtesting.research_runner.run_strategy_research",
            "bash",
        )
    ]
    cards = cast(tuple[StatusCardView, ...], captured["cards"])
    assert [card.label for card in cards] == [
        "Projects",
        "Runs",
        "Candidates",
        "Snapshots",
        "Hypotheses",
    ]
    assert list(captured) == [
        "cards",
        "debug:Canonical Strategy Dossier",
        "table:Research Projects",
        "table:Research Runs",
        "table:Strategy Candidates",
        "table:Dataset Snapshots",
        "table:Launch Hypotheses",
        "debug:Raw JSON / Debug",
    ]


def _mission_control_view() -> SimpleNamespace:
    return SimpleNamespace(
        health="Warning",
        cards=(SimpleNamespace(label="System Health", value="OK", state="ok", detail="Healthy"),),
        workflow_steps=(
            SimpleNamespace(label="Setup", state="ok", detail="Database schema and health"),
        ),
        recommended_action=SimpleNamespace(
            explanation="No research run exists yet.",
            button_label="Run Research",
            command="run-strategy-research",
            target_page="Research",
            is_executable=True,
            disabled_reason=None,
        ),
        warnings=(
            SimpleNamespace(
                title="No dataset snapshot exists",
                why_it_matters="Research runs need reproducible dataset snapshots.",
                recommended_action="Create a dataset snapshot from the Data page.",
            ),
        ),
        recent_activity=(
            SimpleNamespace(
                title="Latest research run",
                detail="completed",
                timestamp="2026-05-24T00:00:00+00:00",
            ),
        ),
        debug_payload={"workflow": {"next_recommended_command": "run-strategy-research"}},
    )


def _data_view() -> SimpleNamespace:
    return SimpleNamespace(
        assets=(
            SimpleNamespace(
                symbol="NIFTY",
                name="NIFTY 50",
                market="NSE",
                sector="index",
                created_at="2026-05-24T00:00:00+00:00",
            ),
            SimpleNamespace(
                symbol="BANKNIFTY",
                name="BANK NIFTY",
                market="NSE",
                sector="index",
                created_at="2026-05-24T00:00:00+00:00",
            ),
        ),
        quality_rows=(
            SimpleNamespace(
                symbol="NIFTY",
                status="ok",
                row_count=25,
                latest_timestamp="2026-05-25T00:00:00+00:00",
                issues="",
            ),
        ),
        snapshots=(
            SimpleNamespace(
                dataset_snapshot_id="dataset_snapshot:demo",
                universe_id="research_universe:demo",
                captured_at="2026-05-25T00:00:00+00:00",
                data_start="2026-05-01",
                data_end="2026-05-25",
                asset_count=2,
            ),
        ),
        default_snapshot=SimpleNamespace(
            name="Operator Snapshot",
            market="NSE",
            symbols=("NIFTY", "BANKNIFTY"),
            data_start="2026-05-01",
            data_end="2026-05-25",
            resolution="1d",
            description="Created from the MFT Operator Cockpit",
        ),
        quality_status="ok",
        workflow_next_command="create-dataset-snapshot",
        debug_payload={
            "assets": [],
            "snapshots": [],
            "workflow": {"next_recommended_command": "create-dataset-snapshot"},
        },
    )


def _snapshot_result() -> SimpleNamespace:
    return SimpleNamespace(
        dataset_snapshot_id="dataset_snapshot:demo",
        dataset_snapshot=SimpleNamespace(
            dataset_snapshot_id="dataset_snapshot:demo",
            universe_id="research_universe:demo",
            asset_ids=("NIFTY", "BANKNIFTY", "FINANCE"),
        ),
    )


def _capture_snapshot_args(
    captured: dict[str, object], args: tuple[object, ...]
) -> SimpleNamespace:
    captured["snapshot_args"] = args
    return _snapshot_result()


def _research_view() -> SimpleNamespace:
    launch = SimpleNamespace(
        assets=(
            SimpleNamespace(symbol="NIFTY", name="NIFTY 50", market="NSE"),
        ),
        snapshots=(
            SimpleNamespace(
                dataset_snapshot_id="dataset_snapshot:demo",
                captured_at="2026-05-25T00:00:00+00:00",
                data_start="2026-05-01",
                data_end="2026-05-25",
                asset_count=1,
            ),
        ),
        hypotheses=(
            SimpleNamespace(
                hypothesis_id="hypothesis:rsi_mean_reversion",
                name="RSI Mean Reversion",
                status="active",
                version=1,
            ),
        ),
        default_asset_symbol="NIFTY",
        default_dataset_snapshot_id="dataset_snapshot:demo",
        default_hypothesis_id="hypothesis:rsi_mean_reversion",
        default_start_date="2026-05-01",
        default_end_date="2026-05-25",
        workflow_command="run-strategy-research",
        workflow_note="Mission Control next action: run-strategy-research",
    )
    return SimpleNamespace(
        projects=(
            SimpleNamespace(
                project_id="research_project:operator",
                name="Operator Research",
                status="active",
                description="Fixture research project",
                artifact_count=2,
            ),
        ),
        runs=(
            SimpleNamespace(
                research_run_id="research_run:operator:1",
                strategy_spec_id="strategy_spec:operator:1",
                dataset_snapshot_id="dataset_snapshot:demo",
                status="completed",
                started_at="2026-05-24T00:00:00+00:00",
                completed_at="2026-05-24T00:00:00+00:00",
                notes="Fixture run",
            ),
        ),
        candidates=(
            SimpleNamespace(
                candidate_id="strategy_candidate:operator",
                project_id="research_project:operator",
                strategy_version_id="strategy_version:operator",
                label="Operator Candidate",
                status="draft",
                created_at="2026-05-24T00:00:00+00:00",
                promoted_at=None,
            ),
        ),
        launch=launch,
        strategy_dossier={"hypothesis_id": "hypothesis:rsi_mean_reversion"},
        debug_payload={
            "projects": [],
            "runs": [],
            "strategy_dossier": {},
            "workflow_context": {"next_recommended_command": "run-strategy-research"},
            "launch": {},
        },
    )
