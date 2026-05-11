from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class HypothesisMetrics:
    n_signals: int
    hit_rate: float
    mean_return: float
    median_return: float
    volatility: float
    sharpe_like_score: float
    max_drawdown: float

@dataclass(frozen=True)
class SignalEvaluation:
    signal_id: str
    hypothesis_id: str
    forward_return_1: float
    forward_return_5: float
    forward_return_20: float
    evaluation_timestamp: str
    experiment_id: str | None = None
    research_run_id: str | None = None

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
    experiment_id: str | None = None
    research_run_id: str | None = None
    dataset_snapshot_id: str | None = None

    @staticmethod
    def now() -> str:
        return datetime.now(UTC).replace(microsecond=0).isoformat()
