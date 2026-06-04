from __future__ import annotations

import contextlib

import project.ui.components.evidence_table as evidence_table_component
import project.ui.components.json_debug as json_debug_component


class _PlainStreamlit:
    def __init__(self) -> None:
        self.captions: list[str] = []
        self.codes: list[tuple[str, str]] = []
        self.dataframes: list[object] = []
        self.writes: list[str] = []

    def container(self, **_kwargs):
        return contextlib.nullcontext()

    def expander(self, *_args, **_kwargs):
        return contextlib.nullcontext()

    def subheader(self, *_args, **_kwargs) -> None:
        return None

    def caption(self, text: str) -> None:
        self.captions.append(text)

    def write(self, text: object) -> None:
        self.writes.append(str(text))

    def code(self, text: str, language: str = "text") -> None:
        self.codes.append((text, language))

    def dataframe(self, value: object, **_kwargs) -> None:
        self.dataframes.append(value)


def test_render_json_debug_falls_back_without_markdown(
    monkeypatch,
) -> None:
    fake_st = _PlainStreamlit()
    monkeypatch.setattr(
        json_debug_component, "get_streamlit", lambda: fake_st
    )

    json_debug_component.render_json_debug(
        "Debug payload",
        {"alpha": 1, "beta": 2},
    )

    assert fake_st.writes == [
        "Object payload with 2 top-level fields: alpha, beta"
    ]
    assert fake_st.captions == ["Raw payload for inspection."]
    assert fake_st.codes and fake_st.codes[0][1] == "json"


def test_render_evidence_table_falls_back_without_markdown(
    monkeypatch,
) -> None:
    fake_st = _PlainStreamlit()
    monkeypatch.setattr(
        evidence_table_component, "get_streamlit", lambda: fake_st
    )

    evidence_table_component.render_evidence_table(
        "Signal snapshot",
        [{"signal": "rsi", "value": 22.5}],
    )

    assert fake_st.captions == ["1 record • Columns: signal, value"]
    assert fake_st.dataframes[0].to_dict(orient="records") == [
        {"signal": "rsi", "value": 22.5}
    ]
