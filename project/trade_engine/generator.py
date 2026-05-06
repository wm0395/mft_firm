from __future__ import annotations

from project.common.models import HypothesisOutput, TradeIdea


def generate_trade_ideas(outputs: tuple[HypothesisOutput, ...]) -> tuple[TradeIdea, ...]:
    ideas: list[TradeIdea] = []
    for output in outputs:
        if output.direction == "flat" or output.confidence <= 0:
            continue
        ideas.append(
            TradeIdea(
                trade_id=f"trade:{output.asset_id}:{output.hypothesis_id}:{output.version}",
                asset_id=output.asset_id,
                hypothesis_id=output.hypothesis_id,
                version=output.version,
                direction=output.direction,
                confidence=output.confidence,
                signals_snapshot=dict(sorted(output.signals_snapshot.items())),
            )
        )
    return tuple(ideas)
