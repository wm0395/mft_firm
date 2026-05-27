from __future__ import annotations

from typing import Any

import project.ui.components.evidence_table as evidence_table_component
import project.ui.components.json_debug as json_debug_component
import project.ui.components.page_hero as page_hero_component


class _FakeBlock:
    def __init__(self, parent: "_FakeStreamlit") -> None:
        self._parent = parent

    def __enter__(self) -> "_FakeStreamlit":
        return self._parent

    def __exit__(self, *_args) -> bool:
        return False


class _FakeStreamlit:
    def __init__(self) -> None:
        self.container_calls: list[bool] = []
        self.expander_calls: list[tuple[str, bool]] = []
        self.markdowns: list[tuple[str, bool]] = []
        self.subheaders: list[str] = []
        self.captions: list[str] = []
        self.writes: list[str] = []
        self.codes: list[tuple[str, str]] = []
        self.dataframes: list[Any] = []

    def container(self, *_args, border: bool = False, **_kwargs):
        self.container_calls.append(border)
        return _FakeBlock(self)

    def expander(self, title: str, expanded: bool = False):
        self.expander_calls.append((title, expanded))
        return _FakeBlock(self)

    def markdown(self, text: str, unsafe_allow_html: bool = False) -> None:
        self.markdowns.append((text, unsafe_allow_html))

    def subheader(self, text: str) -> None:
        self.subheaders.append(text)

    def caption(self, text: str) -> None:
        self.captions.append(text)

    def write(self, text: object) -> None:
        self.writes.append(str(text))

    def code(self, text: str, language: str = "text") -> None:
        self.codes.append((text, language))

    def dataframe(self, value: object, **_kwargs) -> None:
        self.dataframes.append(value)


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
    assert fake_st.writes == [
        "Object payload with 5 top-level fields: alpha, beta, gamma, delta, ..."
    ]
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
    assert "ui-hero__chip-label" in html
    assert "Health" in html
    assert "Warnings" in html


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
    assert fake_st.captions == ["2 records"]
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
    assert fake_st.captions == ["No records captured yet."]
    assert fake_st.dataframes == []
