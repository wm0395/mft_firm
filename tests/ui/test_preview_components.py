from __future__ import annotations

from types import SimpleNamespace

from project.ui.components.launch_preview import render_launch_preview
from project.ui.components.trade_summary import render_trade_summary


class _FakeStreamlit:
    def __init__(self) -> None:
        self.subheaders: list[str] = []
        self.markdowns: list[tuple[str, bool]] = []
        self.infos: list[str] = []
        self.writes: list[str] = []

    def subheader(self, text: str) -> None:
        self.subheaders.append(text)

    def markdown(self, text: str, unsafe_allow_html: bool = False) -> None:
        self.markdowns.append((text, unsafe_allow_html))

    def info(self, text: str) -> None:
        self.infos.append(text)

    def write(self, text: object) -> None:
        self.writes.append(str(text))


def test_render_launch_preview_renders_summary_card() -> None:
    fake_st = _FakeStreamlit()
    launch = SimpleNamespace(
        hypotheses=(
            SimpleNamespace(
                hypothesis_id="hypothesis:rsi_mean_reversion",
                name="RSI Mean Reversion",
            ),
        )
    )
    captured: dict[str, object] = {}

    render_launch_preview(
        fake_st,
        launch,
        "NIFTY",
        "dataset_snapshot:demo",
        "hypothesis:rsi_mean_reversion",
        "2026-05-01",
        "2026-05-25",
        False,
        True,
        lambda cards: captured.setdefault("cards", cards),
    )

    assert fake_st.subheaders == ["Launch preview"]
    assert fake_st.markdowns and fake_st.markdowns[0][1] is True
    html = fake_st.markdowns[0][0]
    assert "Launch plan" in html
    assert "RSI Mean Reversion" in html
    assert "Includes draft hypotheses" in html
    cards = captured["cards"]
    assert [card.label for card in cards] == [
        "Asset",
        "Snapshot",
        "Hypothesis",
        "Window",
        "Policy",
    ]


def test_render_trade_summary_renders_summary_card() -> None:
    fake_st = _FakeStreamlit()

    render_trade_summary(
        fake_st,
        SimpleNamespace(
            asset_symbol="NIFTY",
            direction="long",
            confidence=0.82,
            hypothesis_name="RSI Mean Reversion",
            hypothesis_status="active",
            recommended_action="approve",
            recommended_reason="Strong reversal setup",
            decision_history=(SimpleNamespace(), SimpleNamespace()),
            approval_outcome=SimpleNamespace(state="ok"),
        ),
    )

    assert fake_st.markdowns and fake_st.markdowns[0][1] is True
    html = fake_st.markdowns[0][0]
    assert "Trade summary" in html
    assert "NIFTY long" in html
    assert "RSI Mean Reversion" in html
    assert "2 prior decisions" in html
    assert "approve" in html
