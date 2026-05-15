from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from project.common.models import Direction


@dataclass(frozen=True)
class SignalContribution:
    signal_type: str
    value: float
    direction: Direction
    weight: float
    interpretation: str


@dataclass(frozen=True)
class ConfidenceFactors:
    base_confidence: float
    signal_agreement: float
    signal_strength: float
    historical_accuracy: float


@dataclass(frozen=True)
class ExplanationTree:
    hypothesis_id: str
    version: int
    asset_id: str
    direction: Direction
    horizon: str
    timestamp: str
    triggering_signals: tuple[SignalContribution, ...]
    supporting_signals: tuple[SignalContribution, ...]
    contradicting_signals: tuple[SignalContribution, ...]
    confidence_factors: ConfidenceFactors
    validation_passed: bool
    validation_reasons: tuple[str, ...]
    rejection_reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "version": self.version,
            "asset_id": self.asset_id,
            "direction": self.direction,
            "horizon": self.horizon,
            "timestamp": self.timestamp,
            "triggering_signals": _signal_dicts(self.triggering_signals),
            "supporting_signals": _signal_dicts(self.supporting_signals),
            "contradicting_signals": _signal_dicts(self.contradicting_signals),
            "confidence_factors": {
                "base_confidence": self.confidence_factors.base_confidence,
                "signal_agreement": self.confidence_factors.signal_agreement,
                "signal_strength": self.confidence_factors.signal_strength,
                "historical_accuracy": self.confidence_factors.historical_accuracy,
            },
            "validation_passed": self.validation_passed,
            "validation_reasons": sorted(list(self.validation_reasons)),
            "rejection_reasons": sorted(list(self.rejection_reasons)),
        }


def create_empty_explanation(
    hypothesis_id: str,
    version: int,
    asset_id: str,
    direction: Direction,
    horizon: str,
    timestamp: str,
) -> ExplanationTree:
    return ExplanationTree(
        hypothesis_id=hypothesis_id,
        version=version,
        asset_id=asset_id,
        direction=direction,
        horizon=horizon,
        timestamp=timestamp,
        triggering_signals=(),
        supporting_signals=(),
        contradicting_signals=(),
        confidence_factors=ConfidenceFactors(
            base_confidence=0.0,
            signal_agreement=0.0,
            signal_strength=0.0,
            historical_accuracy=0.0,
        ),
        validation_passed=False,
        validation_reasons=(),
        rejection_reasons=(),
    )


def create_rsi_explanation(
    rsi_value: float,
    direction: Direction,
    confidence: float,
    hypothesis_id: str,
    version: int,
    asset_id: str,
    horizon: str,
    timestamp: str,
) -> ExplanationTree:
    signal_direction, weight, interpretation = _rsi_signal_profile(rsi_value)
    contribution = SignalContribution("rsi_14", rsi_value, signal_direction, weight, interpretation)
    triggering_signals, supporting_signals, contradicting_signals = _single_signal_sets(
        direction,
        contribution,
    )
    return _build_explanation_tree(
        hypothesis_id,
        version,
        asset_id,
        direction,
        horizon,
        timestamp,
        triggering_signals,
        supporting_signals,
        contradicting_signals,
        confidence,
    )


def create_ma_crossover_explanation(
    ma_fast: float,
    ma_slow: float,
    direction: Direction,
    confidence: float,
    hypothesis_id: str,
    version: int,
    asset_id: str,
    horizon: str,
    timestamp: str,
) -> ExplanationTree:
    fast, slow = _ma_contributions(ma_fast, ma_slow)
    triggering_signals, supporting_signals, contradicting_signals = _ma_signal_sets(
        direction,
        fast,
        slow,
    )
    return _build_explanation_tree(
        hypothesis_id,
        version,
        asset_id,
        direction,
        horizon,
        timestamp,
        triggering_signals,
        supporting_signals,
        contradicting_signals,
        confidence,
    )


def _build_explanation_tree(
    hypothesis_id: str,
    version: int,
    asset_id: str,
    direction: Direction,
    horizon: str,
    timestamp: str,
    triggering_signals: tuple[SignalContribution, ...],
    supporting_signals: tuple[SignalContribution, ...],
    contradicting_signals: tuple[SignalContribution, ...],
    confidence: float,
) -> ExplanationTree:
    contributions = triggering_signals + supporting_signals + contradicting_signals
    return ExplanationTree(
        hypothesis_id=hypothesis_id,
        version=version,
        asset_id=asset_id,
        direction=direction,
        horizon=horizon,
        timestamp=timestamp,
        triggering_signals=triggering_signals,
        supporting_signals=supporting_signals,
        contradicting_signals=contradicting_signals,
        confidence_factors=_confidence_factors(confidence, direction, contributions),
        validation_passed=False,
        validation_reasons=(),
        rejection_reasons=(),
    )


def _confidence_factors(
    base_confidence: float,
    direction: Direction,
    contributions: tuple[SignalContribution, ...],
) -> ConfidenceFactors:
    if not contributions:
        signal_agreement = 1.0 if direction == "flat" else 0.0
        return ConfidenceFactors(base_confidence, signal_agreement, 0.0, 0.0)
    aligned = [item for item in contributions if item.direction == direction]
    signal_agreement = round(len(aligned) / len(contributions), 4)
    signal_strength = round(sum(abs(item.weight) for item in contributions) / len(contributions), 4)
    return ConfidenceFactors(base_confidence, signal_agreement, signal_strength, 0.0)


def _rsi_signal_profile(rsi_value: float) -> tuple[Direction, float, str]:
    if rsi_value <= 30.0:
        return "long", round((30.0 - rsi_value) / 30.0, 4), (
            f"RSI ({rsi_value:.1f}) indicates oversold conditions, supporting long direction"
        )
    if rsi_value >= 70.0:
        return "short", round((rsi_value - 70.0) / 30.0, 4), (
            f"RSI ({rsi_value:.1f}) indicates overbought conditions, supporting short direction"
        )
    return "flat", 0.0, f"RSI ({rsi_value:.1f}) in neutral range, no directional signal"


def _ma_signal_profile(ma_fast: float, ma_slow: float) -> tuple[Direction, Direction, float, float]:
    spread = abs(ma_fast - ma_slow)
    base = max(abs(ma_fast), abs(ma_slow), 1.0)
    weight = round(min(spread / base, 1.0), 4)
    if ma_fast > ma_slow:
        return "long", "long", weight, round(weight * 0.5, 4)
    if ma_fast < ma_slow:
        return "short", "short", weight, round(weight * 0.5, 4)
    return "flat", "flat", 0.0, 0.0


def _single_signal_sets(
    direction: Direction,
    contribution: SignalContribution,
) -> tuple[tuple[SignalContribution, ...], tuple[SignalContribution, ...], tuple[SignalContribution, ...]]:
    if contribution.direction == "flat" or direction == "flat":
        return (), (), ()
    if contribution.direction == direction:
        return (contribution,), (contribution,), ()
    return (), (), (contribution,)


def _ma_contributions(ma_fast: float, ma_slow: float) -> tuple[SignalContribution, SignalContribution]:
    fast_direction, slow_direction, fast_weight, slow_weight = _ma_signal_profile(ma_fast, ma_slow)
    return (
        SignalContribution(
            "ma_5",
            ma_fast,
            fast_direction,
            fast_weight,
            _ma_interpretation("ma_5", ma_fast, ma_slow, fast_direction),
        ),
        SignalContribution(
            "ma_20",
            ma_slow,
            slow_direction,
            slow_weight,
            _ma_interpretation("ma_20", ma_fast, ma_slow, slow_direction),
        ),
    )


def _ma_signal_sets(
    direction: Direction,
    fast: SignalContribution,
    slow: SignalContribution,
) -> tuple[tuple[SignalContribution, ...], tuple[SignalContribution, ...], tuple[SignalContribution, ...]]:
    if direction == "flat":
        return (), (), ()
    if fast.direction == direction:
        return (fast,), (slow,), ()
    return (), (), (fast, slow)


def _ma_interpretation(
    signal_type: str,
    ma_fast: float,
    ma_slow: float,
    direction: Direction,
) -> str:
    if direction == "flat":
        return f"{signal_type} equals the opposing moving average, indicating no directional edge"
    if signal_type == "ma_5":
        comparison = "above" if ma_fast > ma_slow else "below"
        return f"Fast MA ({ma_fast:.2f}) is {comparison} slow MA ({ma_slow:.2f})"
    comparison = "below" if ma_fast > ma_slow else "above"
    return f"Slow MA ({ma_slow:.2f}) is {comparison} fast MA ({ma_fast:.2f})"


def _signal_dicts(contributions: tuple[SignalContribution, ...]) -> list[dict[str, Any]]:
    return [
        {
            "signal_type": item.signal_type,
            "value": item.value,
            "direction": item.direction,
            "weight": item.weight,
            "interpretation": item.interpretation,
        }
        for item in sorted(contributions, key=lambda item: item.signal_type)
    ]
