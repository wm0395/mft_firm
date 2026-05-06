from __future__ import annotations

from project.common.models import Decision, DecisionReason, TradeIdea


VALID_REASONS: set[DecisionReason] = {
    "low_confidence",
    "conflicting_signals",
    "risk_constraints",
    "intuition_override",
    "market_conditions",
    "duplicate_exposure",
}


def decide_trade(trade: TradeIdea, minimum_confidence: float = 0.4) -> Decision:
    if trade.confidence < minimum_confidence:
        action = "reject"
        reason: DecisionReason = "low_confidence"
    else:
        action = "watch"
        reason = "market_conditions"
    return Decision(
        decision_id=f"decision:{trade.trade_id}",
        trade_id=trade.trade_id,
        action=action,
        structured_reason=reason,
        notes="",
    )
