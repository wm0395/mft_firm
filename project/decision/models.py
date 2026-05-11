from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from project.common.models import DecisionAction, DecisionReason


@dataclass(frozen=True)
class Decision:
    decision_id: str
    trade_id: str
    action: DecisionAction
    structured_reason: DecisionReason
    notes: str
    created_at: str  # ISO 8601 string

    @staticmethod
    def create(trade_id: str, action: DecisionAction, structured_reason: DecisionReason, notes: str = "") -> "Decision":
        return Decision(
            decision_id=f"decision:{uuid4()}",
            trade_id=trade_id,
            action=action,
            structured_reason=structured_reason,
            notes=notes,
            created_at=datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        )
