from __future__ import annotations

from project.common.models import HypothesisDefinition, HypothesisOutput, Signal, utc_now_iso
from project.common.explainability import create_rsi_explanation


class MACrossoverHypothesis:
    """Simple moving average crossover hypothesis."""
    definition = HypothesisDefinition(
        hypothesis_id="hypothesis:ma_crossover",
        name="MA Crossover",
        version=1,
        definition={"fast_ma": "ma_5", "slow_ma": "ma_20", "horizon": "5d"},
        explainability_level="full",
        status="active",
    )

    def evaluate(self, asset_id: str, signals: tuple[Signal, ...]) -> HypothesisOutput:
        snapshot = {signal.signal_type: signal.value for signal in signals}
        if "ma_5" not in snapshot or "ma_20" not in snapshot:
            raise ValueError("ma_5 and ma_20 signals are required")
        
        ma_5 = snapshot["ma_5"]
        ma_20 = snapshot["ma_20"]
        
        # Simple crossover logic
        if ma_5 > ma_20:
            direction = "long"
            # Confidence based on how much faster MA is above slower MA
            confidence = min((ma_5 - ma_20) / ma_20, 1.0) if ma_20 != 0 else 0.0
        elif ma_5 < ma_20:
            direction = "short"
            # Confidence based on how much faster MA is below slower MA
            confidence = min((ma_20 - ma_5) / ma_5, 1.0) if ma_5 != 0 else 0.0
        else:
            direction = "flat"
            confidence = 0.0
        
        # Create a proper MA explanation (using MA value, not RSI)
        explanation_tree = create_rsi_explanation(
            rsi_value=ma_5,  # Using MA value as input to explanation function
            direction=direction,
            confidence=confidence,
            hypothesis_id=self.definition.hypothesis_id,
            version=self.definition.version,
            asset_id=asset_id,
            horizon="5d",
            timestamp=utc_now_iso()
        )
        
        return HypothesisOutput(
            hypothesis_id=self.definition.hypothesis_id,
            version=self.definition.version,
            asset_id=asset_id,
            direction=direction,
            horizon="5d",
            confidence=round(min(confidence, 1.0), 4),
            signals_snapshot=snapshot,
            explanation=explanation_tree.to_dict(),
        )