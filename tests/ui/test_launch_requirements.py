from __future__ import annotations

from types import SimpleNamespace

from project.ui.components.launch_requirements import render_launch_requirements


class _MarkdownStreamlit:
    def __init__(self) -> None:
        self.markdowns: list[tuple[str, bool]] = []

    def markdown(self, text: str, unsafe_allow_html: bool = False) -> None:
        self.markdowns.append((text, unsafe_allow_html))


def test_render_launch_requirements_renders_summary_card() -> None:
    fake_st = _MarkdownStreamlit()
    launch = SimpleNamespace(assets=(), snapshots=(), hypotheses=())

    render_launch_requirements(fake_st, launch)

    assert fake_st.markdowns and fake_st.markdowns[0][1] is True
    html = fake_st.markdowns[0][0]
    assert "Launch is blocked until the missing inputs are added." in html
    assert "dataset snapshot" in html
    assert "actionable hypothesis" in html
    assert "Snapshots" in html


def test_render_launch_requirements_falls_back_without_markdown() -> None:
    class _PlainStreamlit:
        def __init__(self) -> None:
            self.writes: list[str] = []

        def write(self, text: object) -> None:
            self.writes.append(str(text))

    fake_st = _PlainStreamlit()
    launch = SimpleNamespace(assets=(), snapshots=(), hypotheses=())

    render_launch_requirements(fake_st, launch)

    assert fake_st.writes == [
        "Launch is blocked until the missing inputs are added.",
        "Add asset, dataset snapshot, actionable hypothesis before launching research.",
        "Missing: asset, dataset snapshot, actionable hypothesis",
    ]
