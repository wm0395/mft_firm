from __future__ import annotations

from typing import Any
from types import SimpleNamespace

import project.ui.components.evidence_table as evidence_table_component
import project.ui.components.dossier_summary as dossier_summary_component
import project.ui.components.json_debug as json_debug_component
import project.ui.components.page_hero as page_hero_component
import project.ui.components.sidebar_focus as sidebar_focus_component
from project.ui.state import WorkflowContext


class _FakeBlock:
    def __init__(self, parent: "_FakeStreamlit") -> None:
        self._parent = parent

    def __enter__(self) -> "_FakeStreamlit":
        return self._parent

    def __exit__(self, *_args) -> bool:
        return False


class _FakeStreamlit:
    def __init__(self) -> None:
        self.sidebar = _FakeSidebar()
        self.container_calls: list[bool] = []
        self.columns_calls: list[int] = []
        self.expander_calls: list[tuple[str, bool]] = []
        self.markdowns: list[tuple[str, bool]] = []
        self.subheaders: list[str] = []
        self.captions: list[str] = []
        self.writes: list[str] = []
        self.warning_messages: list[str] = []
        self.codes: list[tuple[str, str]] = []
        self.dataframes: list[Any] = []

    def container(self, *_args, border: bool = False, **_kwargs):
        self.container_calls.append(border)
        return _FakeBlock(self)

    def expander(self, title: str, expanded: bool = False):
        self.expander_calls.append((title, expanded))
        return _FakeBlock(self)

    def columns(self, count: int):
        self.columns_calls.append(count)
        return tuple(_FakeBlock(self) for _ in range(count))

    def markdown(self, text: str, unsafe_allow_html: bool = False) -> None:
        self.markdowns.append((text, unsafe_allow_html))

    def subheader(self, text: str) -> None:
        self.subheaders.append(text)

    def caption(self, text: str) -> None:
        self.captions.append(text)

    def write(self, text: object) -> None:
        self.writes.append(str(text))

    def warning(self, text: str) -> None:
        self.warning_messages.append(text)

    def code(self, text: str, language: str = "text") -> None:
        self.codes.append((text, language))

    def dataframe(self, value: object, **_kwargs) -> None:
        self.dataframes.append(value)


class _FakeSidebar:
    def __init__(self) -> None:
        self.markdowns: list[tuple[str, bool]] = []
        self.captions: list[str] = []

    def markdown(self, text: str, unsafe_allow_html: bool = False) -> None:
        self.markdowns.append((text, unsafe_allow_html))

    def caption(self, text: str) -> None:
        self.captions.append(text)


def test_render_json_debug_summarizes_dict_payload(
    monkeypatch,
) -> None:
    fake_st = _FakeStreamlit()
    monkeypatch.setattr(
        json_debug_component, "get_streamlit", lambda: fake_st
    )

    json_debug_component.render_json_debug(
        "Debug payload",
        {
            "alpha": 1,
            "beta": 2,
            "gamma": 3,
            "delta": 4,
            "epsilon": 5,
        },
    )

    assert fake_st.expander_calls == [("Debug payload", False)]
    assert fake_st.markdowns and fake_st.markdowns[0][1] is True
    assert "Debug summary" in fake_st.markdowns[0][0]
    assert "Object payload with 5 top-level fields: alpha, beta, gamma, delta, ..." in fake_st.markdowns[0][0]
    assert fake_st.captions == ["Raw payload for inspection."]
    assert fake_st.codes[0][1] == "json"
    assert '"epsilon": 5' in fake_st.codes[0][0]


def test_render_json_debug_handles_missing_payload(
    monkeypatch,
) -> None:
    fake_st = _FakeStreamlit()
    monkeypatch.setattr(
        json_debug_component, "get_streamlit", lambda: fake_st
    )

    json_debug_component.render_json_debug("Debug payload", None)

    assert fake_st.expander_calls == [("Debug payload", False)]
    assert fake_st.captions == ["No debug payload."]
    assert fake_st.writes == []
    assert fake_st.codes == []


def test_render_dossier_summary_renders_compact_fact_rows(monkeypatch) -> None:
    fake_st = _FakeStreamlit()
    monkeypatch.setattr(
        dossier_summary_component, "render_status_cards", lambda *_args, **_kwargs: None
    )

    dossier_summary_component.render_dossier_summary(
        fake_st,
        {
            "strategy_name": "RSI Mean Reversion",
            "hypothesis_id": "hypothesis:rsi_mean_reversion",
            "tradeability_status": "eligible",
            "activation_status": "active",
            "dataset_snapshot_id": "dataset_snapshot:demo",
            "best_backtest": {
                "hypothesis_id": "hypothesis:rsi_mean_reversion",
                "total_return_pct": 12.345,
                "sharpe_ratio": 1.234,
                "total_trades": 7,
            },
            "next_action": "Promote hypothesis",
            "next_command": "promote-hypothesis",
            "evidence_summary": {"summary": "Breakout after mean reversion."},
            "tradeability_blockers": ("Missing validation",),
            "validation_errors": ("Beta mismatch",),
        },
    )

    assert fake_st.columns_calls == [2]
    assert len(fake_st.markdowns) == 2
    assert fake_st.markdowns[0][1] is True
    html = fake_st.markdowns[0][0]
    assert "Dossier at a glance" in html
    assert "RSI Mean Reversion" in html
    assert "1 blocker" in html
    assert "Validation" in html
    assert "Review note" in fake_st.markdowns[1][0]
    assert fake_st.writes == [
        "**Strategy**: RSI Mean Reversion",
        "**Tradeability**: eligible • active",
        "**Snapshot**: dataset_snapshot:demo",
        "**Best backtest**: hypothesis:rsi_mean_reversion • 12.35% / Sharpe 1.23 • 7 trades",
        "**Next step**: Next step: Promote hypothesis | Command: promote-hypothesis",
        "Evidence summary: Breakout after mean reversion.",
    ]
    assert fake_st.warning_messages == [
        "Blockers: Missing validation",
        "Validation errors: Beta mismatch",
    ]
    assert fake_st.captions == []


def test_render_dossier_summary_falls_back_without_markdown(monkeypatch) -> None:
    class _PlainStreamlit:
        def __init__(self) -> None:
            self.writes: list[str] = []
            self.captions: list[str] = []
            self.warning_messages: list[str] = []

        def write(self, text: object) -> None:
            self.writes.append(str(text))

        def caption(self, text: str) -> None:
            self.captions.append(text)

        def warning(self, text: str) -> None:
            self.warning_messages.append(text)

    fake_st = _PlainStreamlit()
    monkeypatch.setattr(
        dossier_summary_component, "render_status_cards", lambda *_args, **_kwargs: None
    )

    dossier_summary_component.render_dossier_summary(
        fake_st,
        {
            "strategy_name": "RSI Mean Reversion",
            "hypothesis_id": "hypothesis:rsi_mean_reversion",
            "tradeability_status": "blocked",
            "activation_status": "active",
            "dataset_snapshot_id": "dataset_snapshot:demo",
            "next_action": "Promote hypothesis",
            "next_command": "promote-hypothesis",
            "tradeability_blockers": ("Missing validation",),
            "validation_errors": ("Beta mismatch",),
        },
    )

    assert fake_st.writes[0] == "RSI Mean Reversion • blocked • 1 blocker"
    assert fake_st.writes[-1] == (
        "Read the summary above, then inspect the raw dossier JSON below."
    )
    assert fake_st.captions == []
    assert fake_st.warning_messages == [
        "Blockers: Missing validation",
        "Validation errors: Beta mismatch",
    ]


def test_render_page_hero_renders_summary_note_and_context(monkeypatch) -> None:
    fake_st = _FakeStreamlit()
    monkeypatch.setattr(page_hero_component, "get_streamlit", lambda: fake_st)

    page_hero_component.render_page_hero(
        "System health and the next recommended action.",
        "Next handoff: Run Research",
        context=(("Health", "Warning"), ("Warnings", 2), ("Activity", 3)),
    )

    assert fake_st.markdowns and fake_st.markdowns[0][1] is True
    html = fake_st.markdowns[0][0]
    assert "System health and the next recommended action." in html
    assert "Next handoff: Run Research" in html
    assert "ui-hero__note" in html
    assert "ui-hero__chip-label" in html
    assert "Health" in html
    assert "Warnings" in html


def test_render_sidebar_focus_renders_compact_summary_card(monkeypatch) -> None:
    fake_st = _FakeStreamlit()
    monkeypatch.setattr(
        sidebar_focus_component, "get_streamlit", lambda: fake_st
    )
    repository = SimpleNamespace(
        get_hypothesis=lambda hypothesis_id: SimpleNamespace(
            name="RSI Mean Reversion",
            status="ready",
        )
    )

    sidebar_focus_component.render_sidebar_focus(
        repository,
        {
            "selected_hypothesis_id": "hypothesis:rsi_mean_reversion",
            "workflow_context": WorkflowContext(
                source_page="Mission Control",
                target_page="Research",
                command="run-strategy-research",
                title="Run Research",
                explanation="Launch research for review.",
                button_label="Run Research",
            ),
        },
        "Research",
    )

    assert fake_st.sidebar.markdowns and fake_st.sidebar.markdowns[0][1] is True
    html = fake_st.sidebar.markdowns[0][0]
    assert "ui-sidebar-focus__title" in html
    assert "Research" in html
    assert "Launch research runs and review strategy dossiers." in html
    assert "Run Research" in html
    assert "RSI Mean Reversion" in html
    assert "ready" in html


def test_render_sidebar_focus_falls_back_to_captions(monkeypatch) -> None:
    class _CaptionOnlySidebar:
        def __init__(self) -> None:
            self.captions: list[str] = []

        def caption(self, text: str) -> None:
            self.captions.append(text)

    fake_st = SimpleNamespace(sidebar=_CaptionOnlySidebar())
    monkeypatch.setattr(
        sidebar_focus_component, "get_streamlit", lambda: fake_st
    )

    sidebar_focus_component.render_sidebar_focus(
        object(),
        {},
        "Mission Control",
    )

    assert fake_st.sidebar.captions == [
        "Current page: Mission Control",
        "Description: System health, warnings, and workflow handoff.",
        "Workflow: No active handoff.",
        "Selection: No focused item selected.",
    ]


def test_render_evidence_table_renders_inside_a_bordered_container(
    monkeypatch,
) -> None:
    fake_st = _FakeStreamlit()
    monkeypatch.setattr(
        evidence_table_component, "get_streamlit", lambda: fake_st
    )

    evidence_table_component.render_evidence_table(
        "Signal snapshot",
        [{"signal": "rsi", "value": 22.5}, {"signal": "close", "value": 110.0}],
    )

    assert fake_st.container_calls == [True]
    assert fake_st.subheaders == ["Signal snapshot"]
    assert fake_st.markdowns and fake_st.markdowns[0][1] is True
    assert "Evidence table" in fake_st.markdowns[0][0]
    assert "2 records ready for review." in fake_st.markdowns[0][0]
    assert "Columns: signal, value" in fake_st.markdowns[0][0]
    assert fake_st.captions == []
    assert fake_st.dataframes[0].to_dict(orient="records") == [
        {"signal": "rsi", "value": 22.5},
        {"signal": "close", "value": 110.0},
    ]


def test_render_evidence_table_shows_empty_state_in_a_bordered_container(
    monkeypatch,
) -> None:
    fake_st = _FakeStreamlit()
    monkeypatch.setattr(
        evidence_table_component, "get_streamlit", lambda: fake_st
    )

    evidence_table_component.render_evidence_table("Signal snapshot", ())

    assert fake_st.container_calls == [True]
    assert fake_st.subheaders == ["Signal snapshot"]
    assert fake_st.markdowns and fake_st.markdowns[0][1] is True
    assert "No records captured yet." in fake_st.markdowns[0][0]
    assert fake_st.captions == []
    assert fake_st.dataframes == []
