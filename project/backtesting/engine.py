from __future__ import annotations

from project.common.models import Signal
from project.hypotheses.interface import Hypothesis


def backtest_hypothesis(
    hypothesis: Hypothesis,
    asset_id: str,
    signal_history: tuple[tuple[Signal, ...], ...],
) -> dict[str, float | int | str]:
    evaluated = 0
    active = 0
    confidence_sum = 0.0
    for signals in signal_history:
        output = hypothesis.evaluate(asset_id, signals)
        evaluated += 1
        if output.direction != "flat":
            active += 1
            confidence_sum += output.confidence
    return {
        "hypothesis_id": hypothesis.definition.hypothesis_id,
        "evaluated": evaluated,
        "active": active,
        "average_active_confidence": round(confidence_sum / active, 4) if active else 0.0,
    }
