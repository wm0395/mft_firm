from __future__ import annotations

from collections import defaultdict
from project.common.models import HypothesisOutput, Signal
from project.hypotheses.interface import Hypothesis


def evaluate_hypotheses(
    asset_id: str,
    signals: tuple[Signal, ...],
    hypotheses: tuple[Hypothesis, ...],
) -> tuple[HypothesisOutput, ...]:
    # First, evaluate all hypotheses
    raw_outputs = tuple(hypothesis.evaluate(asset_id, signals) for hypothesis in hypotheses)
    
    # Group outputs by asset_id and direction to detect conflicts
    direction_groups = defaultdict(list)
    for output in raw_outputs:
        direction_groups[output.direction].append(output)
    
    # For each direction, if we have multiple hypotheses, rank them by confidence
    # and mark lower-ranked ones as having competing hypotheses
    enhanced_outputs = []
    for output in raw_outputs:
        # Get all outputs for the same direction
        same_direction_outputs = direction_groups[output.direction]
        
        # If there are multiple hypotheses in the same direction, sort by confidence
        if len(same_direction_outputs) > 1:
            sorted_outputs = sorted(same_direction_outputs, key=lambda x: x.confidence, reverse=True)
            # Find the rank of this output
            rank = next(i for i, out in enumerate(sorted_outputs) if out.hypothesis_id == output.hypothesis_id)
            is_primary = rank == 0  # Highest confidence is primary
            
            # Add competition info to explanation
            enhanced_explanation = dict(output.explanation)
            enhanced_explanation["competition"] = {
                "direction": output.direction,
                "competing_hypotheses_count": len(same_direction_outputs),
                "rank": rank,
                "is_primary": is_primary,
                "competing_hypotheses": [
                    {
                        "hypothesis_id": out.hypothesis_id,
                        "version": out.version,
                        "confidence": out.confidence
                    }
                    for out in sorted_outputs
                ]
            }
            
            # Create enhanced output
            enhanced_output = HypothesisOutput(
                hypothesis_id=output.hypothesis_id,
                version=output.version,
                asset_id=output.asset_id,
                direction=output.direction,
                horizon=output.horizon,
                confidence=output.confidence,
                signals_snapshot=output.signals_snapshot,
                explanation=enhanced_explanation,
            )
            enhanced_outputs.append(enhanced_output)
        else:
            # No competition, add empty competition info
            enhanced_explanation = dict(output.explanation)
            enhanced_explanation["competition"] = {
                "direction": output.direction,
                "competing_hypotheses_count": 1,
                "rank": 0,
                "is_primary": True,
                "competing_hypotheses": [
                    {
                        "hypothesis_id": output.hypothesis_id,
                        "version": output.version,
                        "confidence": output.confidence
                    }
                ]
            }
            
            enhanced_output = HypothesisOutput(
                hypothesis_id=output.hypothesis_id,
                version=output.version,
                asset_id=output.asset_id,
                direction=output.direction,
                horizon=output.horizon,
                confidence=output.confidence,
                signals_snapshot=output.signals_snapshot,
                explanation=enhanced_explanation,
            )
            enhanced_outputs.append(enhanced_output)
    
    return tuple(enhanced_outputs)