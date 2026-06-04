from __future__ import annotations

from types import SimpleNamespace

from project.ui.components.hypothesis_summary import render_hypothesis_summary


class _MarkdownStreamlit:
    def __init__(self) -> None:
        self.markdowns: list[tuple[str, bool]] = []
        self.writes: list[str] = []
        self.captions: list[str] = []

    def markdown(self, text: str, unsafe_allow_html: bool = False) -> None:
        self.markdowns.append((text, unsafe_allow_html))

    def write(self, text: object) -> None:
        self.writes.append(str(text))

    def caption(self, text: str) -> None:
        self.captions.append(text)


def test_render_hypothesis_summary_renders_summary_card() -> None:
    fake_st = _MarkdownStreamlit()

    render_hypothesis_summary(
        fake_st,
        SimpleNamespace(
            name="RSI Mean Reversion",
            hypothesis_id="hypothesis:rsi_mean_reversion",
            status="active",
            version=1,
            explainability_level="high",
            readiness="ready",
            latest_backtest="hypothesis:rsi_mean_reversion 12.35%",
            validation_failures=0,
            blockers=(),
        ),
    )

    assert fake_st.markdowns and fake_st.markdowns[0][1] is True
    html = fake_st.markdowns[0][0]
    assert "Selected hypothesis" in html
    assert "RSI Mean Reversion" in html
    assert "Ready" in html
    assert "Validation" in html


def test_render_hypothesis_summary_falls_back_without_markdown() -> None:
    class _PlainStreamlit:
        def __init__(self) -> None:
            self.writes: list[str] = []
            self.captions: list[str] = []

        def write(self, text: object) -> None:
            self.writes.append(str(text))

        def caption(self, text: str) -> None:
            self.captions.append(text)

    fake_st = _PlainStreamlit()

    render_hypothesis_summary(
        fake_st,
        SimpleNamespace(
            name="RSI Mean Reversion",
            hypothesis_id="hypothesis:rsi_mean_reversion",
            status="testing",
            version=1,
            explainability_level="medium",
            readiness="not ready",
            latest_backtest="",
            validation_failures=1,
            blockers=("Missing validation",),
        ),
    )

    assert fake_st.captions == ["Selected hypothesis"]
    assert fake_st.writes == [
        "Hypothesis: RSI Mean Reversion • hypothesis:rsi_mean_reversion",
        "Status: testing • v1 • medium",
        "Readiness: not ready",
        "Latest backtest: none",
        "Validation failures: 1",
        "Blockers: Missing validation",
    ]
