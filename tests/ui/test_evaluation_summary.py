from __future__ import annotations

from types import SimpleNamespace

from project.ui.components.evaluation_summary import render_evaluation_summary


class _FakeStreamlit:
    def __init__(self) -> None:
        self.markdowns: list[tuple[str, bool]] = []
        self.writes: list[str] = []

    def markdown(self, text: str, unsafe_allow_html: bool = False) -> None:
        self.markdowns.append((text, unsafe_allow_html))

    def write(self, text: object) -> None:
        self.writes.append(str(text))


def test_render_evaluation_summary_renders_summary_card() -> None:
    fake_st = _FakeStreamlit()

    render_evaluation_summary(
        fake_st,
        SimpleNamespace(
            evaluation_id="evaluation:demo",
            asset_symbol="NIFTY",
            direction="long",
            confidence=0.82,
            hypothesis_id="hypothesis:rsi_mean_reversion",
            trade_ideas=("trade:1", "trade:2"),
            decisions=("decision:1",),
            validation={"is_valid": True},
        ),
    )

    assert fake_st.markdowns and fake_st.markdowns[0][1] is True
    html = fake_st.markdowns[0][0]
    assert "Selected evaluation" in html
    assert "NIFTY long" in html
    assert "evaluation:demo" in html
    assert "2" in html
    assert "Passed" in html


def test_render_evaluation_summary_falls_back_without_markdown() -> None:
    class _PlainStreamlit:
        def __init__(self) -> None:
            self.writes: list[str] = []
            self.infos: list[str] = []

        def write(self, text: object) -> None:
            self.writes.append(str(text))

        def info(self, text: str) -> None:
            self.infos.append(text)

    fake_st = _PlainStreamlit()

    render_evaluation_summary(
        fake_st,
        SimpleNamespace(
            evaluation_id="evaluation:demo",
            asset_symbol="NIFTY",
            direction="long",
            confidence=0.82,
            hypothesis_id="hypothesis:rsi_mean_reversion",
            trade_ideas=("trade:1",),
            decisions=(),
            validation=None,
        ),
    )

    assert fake_st.writes == [
        "Evaluation ID: evaluation:demo",
        "Asset: NIFTY • Hypothesis: hypothesis:rsi_mean_reversion",
        "Direction: long • Confidence: 0.82",
        "Trade ideas: trade:1",
        "Decisions: none",
        "Validation: Missing.",
    ]
