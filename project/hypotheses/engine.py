from __future__ import annotations

from project.common.models import HypothesisOutput, Signal
from project.hypotheses.interface import Hypothesis


def evaluate_hypotheses(
    asset_id: str,
    signals: tuple[Signal, ...],
    hypotheses: tuple[Hypothesis, ...],
) -> tuple[HypothesisOutput, ...]:
    return tuple(hypothesis.evaluate(asset_id, signals) for hypothesis in hypotheses)
