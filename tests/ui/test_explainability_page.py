from __future__ import annotations

import contextlib
from types import SimpleNamespace

import project.ui.components.page_hero as page_hero_component
import project.ui.pages.explainability as explainability_page


class _FakeStreamlit:
    def __init__(self) -> None:
        self.session_state: dict[str, object] = {}
        self.titles: list[str] = []
        self.captions: list[str] = []
        self.subheaders: list[str] = []
        self.writes: list[str] = []
        self.info_messages: list[str] = []
        self.json_payloads: list[object] = []

    def title(self, text: str) -> None:
        self.titles.append(text)

    def caption(self, text: str) -> None:
        self.captions.append(text)

    def subheader(self, text: str) -> None:
        self.subheaders.append(text)

    def write(self, text: object) -> None:
        self.writes.append(str(text))

    def info(self, text: str) -> None:
        self.info_messages.append(text)

    def json(self, payload: object) -> None:
        self.json_payloads.append(payload)

    def selectbox(self, label: str, options, index: int = 0, **_kwargs) -> str:
        return options[index]

    def container(self, **_kwargs):
        return contextlib.nullcontext()


def test_explainability_page_renders_readable_summary_fallback(monkeypatch) -> None:
    fake_st = _FakeStreamlit()
    captured: dict[str, object] = {}
    view = SimpleNamespace(
        evaluations=("evaluation:demo",),
        selected_detail=SimpleNamespace(
            evaluation_id="evaluation:demo",
            asset_symbol="NIFTY",
            hypothesis_id="hypothesis:rsi_mean_reversion",
            direction="long",
            confidence=0.82,
            trade_ideas=("trade:1", "trade:2"),
            decisions=("decision:1",),
            validation={"is_valid": True},
            trace_steps=(SimpleNamespace(label="Signals", state="ok", detail="Trace"),),
            signals={"close": 100.0},
            trade_ideas_count=2,
            decisions_count=1,
            explanation={"summary": "demo"},
        ),
        debug_payload={"workflow": {"next_recommended_command": "run-strategy-research"}},
    )

    monkeypatch.setattr(
        explainability_page,
        "get_streamlit",
        lambda: fake_st,
    )
    monkeypatch.setattr(
        explainability_page,
        "get_explainability_page_view",
        lambda _repository, _current: view,
    )
    monkeypatch.setattr(
        explainability_page,
        "render_status_cards",
        lambda cards: captured.setdefault("cards", cards),
    )
    monkeypatch.setattr(
        explainability_page,
        "render_workflow_stepper",
        lambda steps: captured.setdefault("steps", steps),
    )
    monkeypatch.setattr(
        explainability_page,
        "render_evidence_table",
        lambda title, rows: captured.setdefault(f"table:{title}", rows),
    )
    monkeypatch.setattr(
        explainability_page,
        "render_json_debug",
        lambda title, payload: captured.setdefault("debug", (title, payload)),
    )

    explainability_page.render(object())

    assert fake_st.titles == ["Explainability"]
    assert fake_st.writes[:5] == [
        "Evaluation ID: evaluation:demo",
        "Asset: NIFTY • Hypothesis: hypothesis:rsi_mean_reversion",
        "Direction: long • Confidence: 0.82",
        "Trade ideas: trade:1, trade:2",
        "Decisions: decision:1",
    ]
    assert fake_st.writes[5] == "Validation: Passed."
    assert fake_st.info_messages == []
    assert fake_st.captions[0] == (
        "Use the trace to confirm how evidence becomes a trade idea and decision."
    )
    assert captured["debug"] == ("Raw JSON / Debug", view.debug_payload)


def test_explainability_page_renders_empty_state_callout(monkeypatch) -> None:
    class _MarkdownStreamlit(_FakeStreamlit):
        def __init__(self) -> None:
            super().__init__()
            self.markdowns: list[tuple[str, bool]] = []

        def markdown(self, text: str, unsafe_allow_html: bool = False) -> None:
            self.markdowns.append((text, unsafe_allow_html))

    fake_st = _MarkdownStreamlit()
    captured: dict[str, object] = {}
    view = SimpleNamespace(
        evaluations=(),
        selected_detail=None,
        debug_payload={"workflow": {"next_recommended_command": "run-strategy-research"}},
    )

    monkeypatch.setattr(explainability_page, "get_streamlit", lambda: fake_st)
    monkeypatch.setattr(page_hero_component, "get_streamlit", lambda: fake_st)
    monkeypatch.setattr(
        explainability_page,
        "get_explainability_page_view",
        lambda _repository, _current: view,
    )
    monkeypatch.setattr(
        explainability_page,
        "render_json_debug",
        lambda title, payload: captured.setdefault("debug", (title, payload)),
    )

    explainability_page.render(object())

    assert fake_st.titles == ["Explainability"]
    assert fake_st.markdowns[1][1] is True
    assert "No hypothesis evaluations available." in fake_st.markdowns[1][0]
    assert "Run research" in fake_st.markdowns[1][0]
    assert captured["debug"] == ("Raw JSON / Debug", view.debug_payload)


def test_explainability_page_renders_missing_validation_payload_callout(
    monkeypatch,
) -> None:
    class _MarkdownStreamlit(_FakeStreamlit):
        def __init__(self) -> None:
            super().__init__()
            self.markdowns: list[tuple[str, bool]] = []

        def markdown(self, text: str, unsafe_allow_html: bool = False) -> None:
            self.markdowns.append((text, unsafe_allow_html))

        def columns(self, count: int):
            return [contextlib.nullcontext() for _ in range(count)]

    fake_st = _MarkdownStreamlit()
    captured: dict[str, object] = {}
    view = SimpleNamespace(
        evaluations=("evaluation:demo",),
        selected_detail=SimpleNamespace(
            evaluation_id="evaluation:demo",
            asset_symbol="NIFTY",
            hypothesis_id="hypothesis:rsi_mean_reversion",
            direction="long",
            confidence=0.82,
            trade_ideas=("trade:1",),
            decisions=("decision:1",),
            validation=None,
            trace_steps=(SimpleNamespace(label="Signals", state="ok", detail="Trace"),),
            signals={"close": 100.0},
            explanation={"summary": "demo"},
        ),
        debug_payload={"workflow": {"next_recommended_command": "run-strategy-research"}},
    )

    monkeypatch.setattr(explainability_page, "get_streamlit", lambda: fake_st)
    monkeypatch.setattr(page_hero_component, "get_streamlit", lambda: fake_st)
    monkeypatch.setattr(
        explainability_page,
        "get_explainability_page_view",
        lambda _repository, _current: view,
    )
    monkeypatch.setattr(
        explainability_page,
        "render_status_cards",
        lambda cards: captured.setdefault("cards", cards),
    )
    monkeypatch.setattr(
        explainability_page,
        "render_workflow_stepper",
        lambda steps: captured.setdefault("steps", steps),
    )
    monkeypatch.setattr(
        explainability_page,
        "render_evidence_table",
        lambda title, rows: captured.setdefault(f"table:{title}", rows),
    )
    monkeypatch.setattr(
        explainability_page,
        "render_json_debug",
        lambda title, payload: captured.setdefault("debug", (title, payload)),
    )

    explainability_page.render(object())

    payload_html = next(
        html for html, unsafe in fake_st.markdowns if "No validation payload available." in html
    )
    assert "Run research with validation enabled" in payload_html
    assert "Validation" in payload_html
    assert captured["debug"] == ("Raw JSON / Debug", view.debug_payload)
