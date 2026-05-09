from __future__ import annotations

from project.common.models import DecisionAction, DecisionReason
from project.decision.models import Decision


class DecisionService:
    def __init__(self) -> None:
        pass

    def make_decision(
        self,
        trade_id: str,
        action: DecisionAction,
        structured_reason: DecisionReason,
        notes: str = "",
    ) -> Decision:
        """
        Make a decision on a trade idea.
        
        Args:
            trade_id: The trade idea to make a decision on
            action: The decision action (approve, reject, watch)
            structured_reason: The structured reason for the decision
            notes: Optional free-form notes
            
        Returns:
            Decision: The created decision (not persisted)
        """
        return Decision.create(
            trade_id=trade_id,
            action=action,
            structured_reason=structured_reason,
            notes=notes,
        )