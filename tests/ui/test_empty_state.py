from __future__ import annotations

from project.ui.components.empty_state import render_empty_state


class _MarkdownStreamlit:
    def __init__(self) -> None:
        self.markdowns: list[tuple[str, bool]] = []

    def markdown(self, text: str, unsafe_allow_html: bool = False) -> None:
        self.markdowns.append((text, unsafe_allow_html))


def test_render_empty_state_renders_summary_card() -> None:
    fake_st = _MarkdownStreamlit()

    render_empty_state(
        fake_st,
        "No open trade ideas.",
        "The review queue is currently clear.",
        "Closed reviews stay accessible when selected from session state.",
        (
            ("Queue", "0 open", "warning"),
            ("Reviewed", "12 closed", "ok"),
        ),
    )

    assert fake_st.markdowns and fake_st.markdowns[0][1] is True
    html = fake_st.markdowns[0][0]
    assert "Empty state" in html
    assert "No open trade ideas." in html
    assert "The review queue is currently clear." in html
    assert "Closed reviews stay accessible" in html
    assert "Queue" in html
    assert "0 open" in html


def test_render_empty_state_falls_back_without_markdown() -> None:
    class _PlainStreamlit:
        def __init__(self) -> None:
            self.writes: list[str] = []

        def write(self, text: object) -> None:
            self.writes.append(str(text))

    fake_st = _PlainStreamlit()

    render_empty_state(
        fake_st,
        "No hypothesis evaluations available.",
        "Generate an evaluation to inspect signal lineage.",
        "Run research to populate this page.",
        (
            ("Evaluations", "0 recorded", "warning"),
            ("Next step", "Run research", "ok"),
        ),
    )

    assert fake_st.writes == [
        "No hypothesis evaluations available.",
        "Generate an evaluation to inspect signal lineage.",
        "Run research to populate this page.",
        "Evaluations: 0 recorded",
        "Next step: Run research",
    ]
