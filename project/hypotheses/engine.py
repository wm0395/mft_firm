from __future__ import annotations

from collections.abc import Iterable

from project.common.models import HypothesisOutput, Signal, utc_now_iso
from project.hypotheses.interface import Hypothesis


def evaluate_hypotheses(
    asset_id: str,
    signals: tuple[Signal, ...],
    hypotheses: tuple[Hypothesis, ...],
) -> tuple[HypothesisOutput, ...]:
    latest_timestamp = _latest_signal_timestamp(signals)
    raw_outputs = tuple(hypothesis.evaluate(asset_id, signals) for hypothesis in hypotheses)
    grouped = _group_outputs(raw_outputs)
    return tuple(
        _annotate_competition(output, grouped[output.direction], latest_timestamp)
        for output in raw_outputs
    )


def _group_outputs(outputs: tuple[HypothesisOutput, ...]) -> dict[str, tuple[HypothesisOutput, ...]]:
    grouped: dict[str, list[HypothesisOutput]] = {}
    for output in outputs:
        grouped.setdefault(output.direction, []).append(output)
    return {direction: tuple(items) for direction, items in grouped.items()}


def _annotate_competition(
    output: HypothesisOutput,
    competing: tuple[HypothesisOutput, ...],
    timestamp: str,
) -> HypothesisOutput:
    sorted_outputs = tuple(sorted(competing, key=lambda item: item.confidence, reverse=True))
    explanation = dict(output.explanation)
    explanation["competition"] = _competition_payload(output, sorted_outputs)
    return HypothesisOutput(
        hypothesis_id=output.hypothesis_id,
        version=output.version,
        asset_id=output.asset_id,
        direction=output.direction,
        horizon=output.horizon,
        confidence=output.confidence,
        signals_snapshot=output.signals_snapshot,
        explanation=explanation,
        timestamp=output.timestamp or timestamp,
    )


def _latest_signal_timestamp(signals: tuple[Signal, ...]) -> str:
    if not signals:
        return utc_now_iso()
    return max(signals, key=lambda signal: signal.timestamp).timestamp


def _competition_payload(
    output: HypothesisOutput,
    competing: tuple[HypothesisOutput, ...],
) -> dict[str, object]:
    rank = _competition_rank(output, competing)
    return {
        "direction": output.direction,
        "competing_hypotheses_count": len(competing),
        "rank": rank,
        "is_primary": rank == 0,
        "competing_hypotheses": _competition_candidates(competing),
    }


def _competition_rank(
    output: HypothesisOutput,
    competing: tuple[HypothesisOutput, ...],
) -> int:
    for index, item in enumerate(competing):
        if item.hypothesis_id == output.hypothesis_id:
            return index
    return 0


def _competition_candidates(outputs: Iterable[HypothesisOutput]) -> list[dict[str, object]]:
    return [
        {
            "hypothesis_id": item.hypothesis_id,
            "version": item.version,
            "confidence": item.confidence,
        }
        for item in outputs
    ]
