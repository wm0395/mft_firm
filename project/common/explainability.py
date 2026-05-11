from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple

from project.common.models import Direction


@dataclass(frozen=True)
class SignalContribution:
    """Represents a signal's contribution to a hypothesis."""
    signal_type: str
    value: float
    weight: float  # How much this signal contributed to the decision (-1 to 1)
    interpretation: str  # Human readable interpretation


@dataclass(frozen=True)
class ConfidenceFactors:
    """Factors that contribute to the overall confidence."""
    base_confidence: float
    signal_agreement: float  # How much signals agree with each other (0 to 1)
    signal_strength: float   # Average strength of supporting signals (0 to 1)
    historical_accuracy: float  # Placeholder for future use (0 to 1)


@dataclass(frozen=True)
class ExplanationTree:
    """Complete explainability structure for a hypothesis output."""
    hypothesis_id: str
    version: int
    asset_id: str
    direction: Direction
    horizon: str
    timestamp: str  # When this explanation was generated
    
    # What triggered this hypothesis
    triggering_signals: Tuple[SignalContribution, ...]
    
    # Signals supporting the direction
    supporting_signals: Tuple[SignalContribution, ...]
    
    # Signals contradicting the direction
    contradicting_signals: Tuple[SignalContribution, ...]
    
    # What contributed to confidence
    confidence_factors: ConfidenceFactors
    
    # Validation information (to be filled in later)
    validation_passed: bool
    validation_reasons: Tuple[str, ...]
    
    # Rejection information (if applicable)
    rejection_reasons: Tuple[str, ...]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization with deterministic ordering."""
        return {
            "hypothesis_id": self.hypothesis_id,
            "version": self.version,
            "asset_id": self.asset_id,
            "direction": self.direction,
            "horizon": self.horizon,
            "timestamp": self.timestamp,
            "triggering_signals": [
                {
                    "signal_type": s.signal_type,
                    "value": s.value,
                    "weight": s.weight,
                    "interpretation": s.interpretation
                }
                for s in sorted(self.triggering_signals, key=lambda x: x.signal_type)
            ],
            "supporting_signals": [
                {
                    "signal_type": s.signal_type,
                    "value": s.value,
                    "weight": s.weight,
                    "interpretation": s.interpretation
                }
                for s in sorted(self.supporting_signals, key=lambda x: x.signal_type)
            ],
            "contradicting_signals": [
                {
                    "signal_type": s.signal_type,
                    "value": s.value,
                    "weight": s.weight,
                    "interpretation": s.interpretation
                }
                for s in sorted(self.contradicting_signals, key=lambda x: x.signal_type)
            ],
            "confidence_factors": {
                "base_confidence": self.confidence_factors.base_confidence,
                "signal_agreement": self.confidence_factors.signal_agreement,
                "signal_strength": self.confidence_factors.signal_strength,
                "historical_accuracy": self.confidence_factors.historical_accuracy
            },
            "validation_passed": self.validation_passed,
            "validation_reasons": sorted(list(self.validation_reasons)),
            "rejection_reasons": sorted(list(self.rejection_reasons))
        }


def create_empty_explanation(hypothesis_id: str, version: int, asset_id: str, 
                           direction: Direction, horizon: str, timestamp: str) -> ExplanationTree:
    """Create an empty explanation template."""
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
            historical_accuracy=0.0
        ),
        validation_passed=False,
        validation_reasons=(),
        rejection_reasons=()
    )


def create_rsi_explanation(rsi_value: float, direction: str, confidence: float, 
                         hypothesis_id: str, version: int, asset_id: str, 
                         horizon: str, timestamp: str) -> ExplanationTree:
    """Create an explanation for RSI mean reversion hypothesis."""
    # Determine if RSI is triggering the signal
    is_triggering = rsi_value <= 30.0 or rsi_value >= 70.0
    
    # Create the RSI signal contribution
    if rsi_value <= 30.0:
        # Long signal
        weight = (30.0 - rsi_value) / 30.0  # 0 to 1 as RSI goes from 30 to 0
        interpretation = f"RSI ({rsi_value:.1f}) indicates oversold conditions, supporting long direction"
    elif rsi_value >= 70.0:
        # Short signal
        weight = (rsi_value - 70.0) / 30.0  # 0 to 1 as RSI goes from 70 to 100
        interpretation = f"RSI ({rsi_value:.1f}) indicates overbought conditions, supporting short direction"
    else:
        # Flat/no signal
        weight = 0.0
        interpretation = f"RSI ({rsi_value:.1f}) in neutral range, no directional signal"
    
    rsi_contribution = SignalContribution(
        signal_type="rsi_14",
        value=rsi_value,
        weight=weight if direction != "flat" else 0.0,
        interpretation=interpretation
    )
    
    # For RSI mean reversion, we only have one signal
    if is_triggering and direction != "flat":
        triggering_signals = (rsi_contribution,)
        supporting_signals = (rsi_contribution,) if weight > 0 else ()
        contradicting_signals = ()
    else:
        triggering_signals = ()
        supporting_signals = ()
        contradicting_signals = (rsi_contribution,) if direction == "flat" else ()
    
    # Calculate confidence factors
    signal_agreement = 1.0  # Only one signal, so perfect agreement
    signal_strength = abs(rsi_contribution.weight)  # Strength of the signal
    
    confidence_factors = ConfidenceFactors(
        base_confidence=confidence,
        signal_agreement=signal_agreement,
        signal_strength=signal_strength,
        historical_accuracy=0.0  # Placeholder
    )
    
    return ExplanationTree(
        hypothesis_id=hypothesis_id,
        version=version,
        asset_id=asset_id,
        direction=direction,  # type: ignore
        horizon=horizon,
        timestamp=timestamp,
        triggering_signals=triggering_signals,
        supporting_signals=supporting_signals,
        contradicting_signals=contradicting_signals,
        confidence_factors=confidence_factors,
        validation_passed=False,  # Will be updated after validation
        validation_reasons=(),
        rejection_reasons=()
    )