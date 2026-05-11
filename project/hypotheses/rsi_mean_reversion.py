from __future__ import annotations

from project.common.models import HypothesisDefinition, HypothesisOutput, Signal, utc_now_iso
from project.common.explainability import create_rsi_explanation


class RSIMeanReversionHypothesis:
    definition = HypothesisDefinition(
        hypothesis_id="hypothesis:rsi_mean_reversion",
        name="RSI mean reversion",
        version=1,
        definition={"signal": "rsi_14", "long_below": 30.0, "short_above": 70.0, "horizon": "10d"},
        explainability_level="full",
        status="active",
    )

    def evaluate(self, asset_id: str, signals: tuple[Signal, ...]) -> HypothesisOutput:
        snapshot = {signal.signal_type: signal.value for signal in signals}
        if "rsi_14" not in snapshot:
            raise ValueError("rsi_14 signal is required")
        rsi_value = snapshot["rsi_14"]
        if rsi_value <= 30.0:
            direction = "long"
            confidence = (30.0 - rsi_value) / 30.0
        elif rsi_value >= 70.0:
            direction = "short"
            confidence = (rsi_value - 70.0) / 30.0
        else:
            direction = "flat"
            confidence = 0.0
        
        # Generate enhanced explanation
        explanation_tree = create_rsi_explanation(
            rsi_value=rsi_value,
            direction=direction,
            confidence=confidence,
            hypothesis_id=self.definition.hypothesis_id,
            version=self.definition.version,
            asset_id=asset_id,
            horizon="10d",
            timestamp=utc_now_iso()
        )
        
        return HypothesisOutput(
            hypothesis_id=self.definition.hypothesis_id,
            version=self.definition.version,
            asset_id=asset_id,
            direction=direction,
            horizon="10d",
            confidence=round(min(confidence, 1.0), 4),
            signals_snapshot=snapshot,
            explanation=explanation_tree.to_dict(),
        )
