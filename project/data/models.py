from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class HypothesisEvaluation:
    evaluation_id: str
    asset_id: str
    hypothesis_id: str
    hypothesis_version: int
    timestamp: str  # ISO 8601 string
    direction: str  # "long", "short", "flat"
    confidence: float
    signals_snapshot_json: str  # JSON string of signals snapshot
    explanation_json: str  # JSON string of explanation
    generated_trade_idea: bool
    validation_result_json: str | None  # JSON string of validation result or None
    created_at: str  # ISO 8601 string

    @staticmethod
    def now() -> str:
        from datetime import timezone
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()