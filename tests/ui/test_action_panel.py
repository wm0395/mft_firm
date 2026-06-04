from __future__ import annotations

import contextlib

import project.ui.components.action_panel as action_panel_component


class _FakeStreamlit:
    def __init__(self) -> None:
        self.markdowns: list[tuple[str, bool]] = []
        self.subheaders: list[str] = []
        self.captions: list[str] = []
        self.writes: list[str] = []
        self.button_calls: list[tuple[str, str, str, bool, object]] = []

    def container(self, **_kwargs):
        return contextlib.nullcontext()

    def markdown(self, text: str, unsafe_allow_html: bool = False) -> None:
        self.markdowns.append((text, unsafe_allow_html))

    def subheader(self, text: str) -> None:
        self.subheaders.append(text)

    def caption(self, text: str) -> None:
        self.captions.append(text)

    def write(self, text: object) -> None:
        self.writes.append(str(text))

    def button(
        self,
        label: str,
        *,
        key: str,
        on_click=None,
        type: str = "secondary",
        disabled: bool = False,
    ) -> bool:
        self.button_calls.append((label, key, type, disabled, on_click))
        return not disabled


def test_render_action_panel_renders_summary_card(monkeypatch) -> None:
    fake_st = _FakeStreamlit()
    clicked: list[bool] = []

    monkeypatch.setattr(
        action_panel_component, "get_streamlit", lambda: fake_st
    )

    action_panel_component.render_action_panel(
        "Recommended next action",
        "Update the workflow context and move to the next page.",
        "Run Research",
        key="mission-control-action",
        on_click=lambda: clicked.append(True),
        target_page="Research",
    )

    assert fake_st.markdowns and fake_st.markdowns[0][1] is True
    html = fake_st.markdowns[0][0]
    assert "Recommended next step" in html
    assert "Recommended next action" in html
    assert "Update the workflow context and move to the next page." in html
    assert "Destination" in html
    assert "Research" in html
    assert "Run Research" in html
    assert clicked == []

    label, key, button_type, disabled, on_click = fake_st.button_calls[0]
    assert (label, key, button_type, disabled) == (
        "Run Research",
        "mission-control-action",
        "primary",
        False,
    )
    assert callable(on_click)


def test_render_action_panel_falls_back_without_markdown(monkeypatch) -> None:
    class _PlainStreamlit:
        def __init__(self) -> None:
            self.captions: list[str] = []
            self.subheaders: list[str] = []
            self.writes: list[str] = []
            self.button_calls: list[tuple[str, str, str, bool, object]] = []

        def container(self, **_kwargs):
            return contextlib.nullcontext()

        def subheader(self, text: str) -> None:
            self.subheaders.append(text)

        def caption(self, text: str) -> None:
            self.captions.append(text)

        def write(self, text: object) -> None:
            self.writes.append(str(text))

        def button(
            self,
            label: str,
            *,
            key: str,
            on_click=None,
            type: str = "secondary",
            disabled: bool = False,
        ) -> bool:
            self.button_calls.append((label, key, type, disabled, on_click))
            return not disabled

    fake_st = _PlainStreamlit()

    monkeypatch.setattr(
        action_panel_component, "get_streamlit", lambda: fake_st
    )

    action_panel_component.render_action_panel(
        "Recommended next action",
        "Update the workflow context and move to the next page.",
        "Run Research",
        key="mission-control-action",
        on_click=None,
        target_page="Research",
        disabled=True,
        disabled_reason="No recommended action is available.",
    )

    assert fake_st.subheaders == ["Recommended next action"]
    assert fake_st.captions == []
    assert fake_st.writes == [
        "Recommended next step",
        "Update the workflow context and move to the next page.",
        "Destination: Research",
        "Disabled: No recommended action is available.",
    ]
    assert fake_st.button_calls == [
        (
            "Run Research",
            "mission-control-action",
            "primary",
            True,
            None,
        )
    ]
