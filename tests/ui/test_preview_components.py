from __future__ import annotations

import contextlib
from types import SimpleNamespace

from project.ui.components.approval_outcome import render_approval_outcome
from project.ui.components.decision_guidance import render_decision_guidance
from project.ui.components.decision_preview import render_decision_preview
from project.ui.components.launch_preview import render_launch_preview
from project.ui.components.trade_summary import render_trade_summary


class _FakeStreamlit:
    def __init__(self) -> None:
        self.subheaders: list[str] = []
        self.markdowns: list[tuple[str, bool]] = []
        self.infos: list[str] = []
        self.writes: list[str] = []

    def container(self, **_kwargs):
        return contextlib.nullcontext()

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
    assert "Review the exact command block below before submitting." in html
    cards = captured["cards"]
    assert [card.label for card in cards] == [
        "Asset",
        "Snapshot",
        "Hypothesis",
        "Window",
        "Policy",
    ]


def test_render_launch_preview_falls_back_without_markdown() -> None:
    class _PlainStreamlit:
        def __init__(self) -> None:
            self.subheaders: list[str] = []
            self.writes: list[str] = []

        def subheader(self, text: str) -> None:
            self.subheaders.append(text)

        def write(self, text: object) -> None:
            self.writes.append(str(text))

    fake_st = _PlainStreamlit()
    launch = SimpleNamespace(
        hypotheses=(
            SimpleNamespace(
                hypothesis_id="hypothesis:rsi_mean_reversion",
                name="RSI Mean Reversion",
            ),
        )
    )

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
        lambda cards: None,
    )

    assert fake_st.subheaders == ["Launch preview"]
    assert fake_st.writes == [
        "Ready to launch RSI Mean Reversion on NIFTY with dataset_snapshot:demo from 2026-05-01 to 2026-05-25. Includes draft hypotheses",
        "Review the exact command block below before submitting.",
        "Asset: NIFTY",
        "Snapshot: dataset_snapshot:demo",
        "Hypothesis: RSI Mean Reversion",
        "Window: 2026-05-01 -> 2026-05-25",
        "Policy: Includes draft hypotheses",
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


def test_render_trade_summary_falls_back_without_markdown() -> None:
    class _PlainStreamlit:
        def __init__(self) -> None:
            self.subheaders: list[str] = []
            self.writes: list[str] = []

        def subheader(self, text: str) -> None:
            self.subheaders.append(text)

        def write(self, text: object) -> None:
            self.writes.append(str(text))

    fake_st = _PlainStreamlit()

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

    assert fake_st.subheaders == ["Trade summary"]
    assert fake_st.writes == [
        "Trade idea: NIFTY long",
        "Confidence: 0.82 • active hypothesis",
        "Hypothesis: RSI Mean Reversion",
        "System recommendation: approve",
        "Reason: Strong reversal setup",
        "Decisions: 2 prior decisions",
        "Outcome: Ok",
    ]


def test_render_approval_outcome_renders_summary_card() -> None:
    fake_st = _FakeStreamlit()

    render_approval_outcome(
        fake_st,
        SimpleNamespace(
            state="ok",
            message="Approved and an open position exists for this trade.",
            open_position_status="open",
            open_position_entry_price=112.0,
        ),
    )

    assert fake_st.markdowns and fake_st.markdowns[0][1] is True
    html = fake_st.markdowns[0][0]
    assert "Approval outcome" in html
    assert "Approved and an open position exists for this trade." in html
    assert "Outcome: Approved" in html
    assert "Open position" in html
    assert "Entry price" in html


def test_render_decision_guidance_renders_summary_card() -> None:
    fake_st = _FakeStreamlit()

    render_decision_guidance(
        fake_st,
        SimpleNamespace(
            recommended_action="approve",
            recommended_reason="Strong reversal setup",
        ),
        True,
    )

    assert fake_st.markdowns and fake_st.markdowns[0][1] is True
    html = fake_st.markdowns[0][0]
    assert "Decision guidance" in html
    assert "Automatic review is on." in html
    assert "Use approve" in html
    assert "Strong reversal setup" in html


def test_render_decision_guidance_falls_back_without_markdown() -> None:
    class _PlainStreamlit:
        def __init__(self) -> None:
            self.writes: list[str] = []

        def write(self, text: object) -> None:
            self.writes.append(str(text))

    fake_st = _PlainStreamlit()

    render_decision_guidance(
        fake_st,
        SimpleNamespace(
            recommended_action="watch",
            recommended_reason="Market conditions",
        ),
        False,
    )

    assert fake_st.writes == [
        "Decision guidance",
        "Choose an explicit action and reason below before submitting.",
        "Mode: Manual override",
        "Action: Select approve, reject, or watch",
        "Reason: Pick a reason below",
        "Notes: Optional context, rationale, or risk notes.",
    ]


def test_render_decision_preview_renders_summary_card() -> None:
    fake_st = _FakeStreamlit()

    render_decision_preview(
        fake_st,
        SimpleNamespace(
            recommended_action="approve",
            recommended_reason="Strong reversal setup",
        ),
        True,
        None,
        None,
        None,
        "Keep risk tight",
    )

    assert fake_st.markdowns and fake_st.markdowns[0][1] is True
    html = fake_st.markdowns[0][0]
    assert "Decision preview" in html
    assert "Automatic review" in html
    assert "Approve" in html
    assert "Strong reversal setup" in html
    assert "Keep risk tight" in html
    assert "Notes are saved with the decision and shown in history." in html


def test_render_decision_preview_falls_back_without_markdown() -> None:
    class _PlainStreamlit:
        def __init__(self) -> None:
            self.captions: list[str] = []
            self.writes: list[str] = []

        def write(self, text: object) -> None:
            self.writes.append(str(text))

    fake_st = _PlainStreamlit()

    render_decision_preview(
        fake_st,
        SimpleNamespace(
            recommended_action="watch",
            recommended_reason="Market conditions",
        ),
        False,
        "watch",
        "market_conditions",
        "Market conditions",
        "",
    )

    assert fake_st.writes[:2] == [
        "Decision preview",
        "The selected action, reason, and notes will be submitted.",
    ]
    assert fake_st.writes == [
        "Decision preview",
        "The selected action, reason, and notes will be submitted.",
        "Mode: Manual override",
        "Action: Watch",
        "Reason: Market conditions",
        "Notes: No notes yet.",
        "Notes are saved with the decision and shown in history.",
    ]
