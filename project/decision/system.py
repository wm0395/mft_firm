from __future__ import annotations

from dataclasses import dataclass

from project.common.models import DecisionAction, DecisionReason, TradeIdea
from project.decision.models import Decision


@dataclass(frozen=True)
class DecisionContext:
    has_duplicate_exposure: bool = False
    risk_limit_breached: bool = False
    market_is_tradeable: bool = True

VALID_REASONS: set[DecisionReason] = {
    "low_confidence",
    "conflicting_signals",
    "risk_constraints",
    "intuition_override",
    "market_conditions",
    "duplicate_exposure",
}


def decide_trade(
    trade: TradeIdea,
    minimum_confidence: float = 0.4,
    context: DecisionContext | None = None,
) -> Decision:
    decision_context = context or DecisionContext()
    action: DecisionAction
    if trade.confidence < minimum_confidence:
        action = "reject"
        reason: DecisionReason = "low_confidence"
    elif decision_context.has_duplicate_exposure:
        action = "reject"
        reason = "duplicate_exposure"
    elif decision_context.risk_limit_breached:
        action = "reject"
        reason = "risk_constraints"
    elif not decision_context.market_is_tradeable:
        action = "watch"
        reason = "market_conditions"
    else:
        action = "approve"
        reason = "market_conditions"
    return Decision.create(
        trade_id=trade.trade_id,
        action=action,
        structured_reason=reason,
    )
