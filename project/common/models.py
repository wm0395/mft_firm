from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal


Direction = Literal["long", "short", "flat"]
HypothesisStatus = Literal["draft", "testing", "active", "deprecated", "archived"]
DecisionAction = Literal["approve", "reject", "watch"]
ResearchRunStatus = Literal["planned", "running", "completed", "failed"]
DecisionReason = Literal[
    "low_confidence",
    "conflicting_signals",
    "risk_constraints",
    "intuition_override",
    "market_conditions",
    "duplicate_exposure",
]


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class Asset:
    asset_id: str
    symbol: str
    name: str
    sector: str
    market: str
    is_active: bool
    created_at: str


@dataclass(frozen=True)
class RawDataPoint:
    data_id: str
    asset_id: str
    timestamp: str
    data_type: str
    value: dict[str, Any]
    source: str


@dataclass(frozen=True)
class SignalDefinition:
    signal_type: str
    category: str
    definition: str
    dependencies: tuple[str, ...]
    is_persistent: bool
    version: int


@dataclass(frozen=True)
class ResearchUniverse:
    universe_id: str
    name: str
    market: str
    description: str
    asset_ids: tuple[str, ...]


@dataclass(frozen=True)
class DatasetSnapshot:
    dataset_snapshot_id: str
    universe_id: str
    captured_at: str
    data_start: str
    data_end: str
    asset_ids: tuple[str, ...]


@dataclass(frozen=True)
class StrategySpec:
    strategy_spec_id: str
    universe_id: str
    hypothesis_id: str
    hypothesis_version: int
    name: str
    parameters: tuple[tuple[str, Any], ...]


STRATEGY_SPEC_REQUIRED_PARAMETERS = (
    "thesis",
    "bar_timeframe",
    "holding_horizon",
    "required_signals",
    "expected_failure_modes",
    "evidence_standard",
)


def strategy_spec_parameters(strategy_spec: StrategySpec) -> dict[str, Any]:
    return {key: value for key, value in strategy_spec.parameters}


def strategy_spec_missing_fields(strategy_spec: StrategySpec) -> tuple[str, ...]:
    missing = ["universe_id"] if not strategy_spec.universe_id else []
    parameters = strategy_spec_parameters(strategy_spec)
    for name in STRATEGY_SPEC_REQUIRED_PARAMETERS:
        if parameters.get(name) in (None, "", (), []):
            missing.append(name)
    return tuple(missing)


def strategy_spec_sequence_parameter(
    strategy_spec: StrategySpec,
    name: str,
) -> tuple[str, ...]:
    value = strategy_spec_parameters(strategy_spec).get(name)
    if isinstance(value, tuple):
        return tuple(str(item) for item in value)
    if isinstance(value, list):
        return tuple(str(item) for item in value)
    msg = f"strategy spec {name} must be a sequence"
    raise ValueError(msg)


@dataclass(frozen=True)
class StrategyEvidenceSummary:
    evidence_summary_id: str
    strategy_spec_id: str
    research_run_id: str
    dataset_snapshot_id: str
    summary: str
    metrics: tuple[tuple[str, Any], ...]
    created_at: str


@dataclass(frozen=True)
class ResearchRun:
    research_run_id: str
    strategy_spec_id: str
    dataset_snapshot_id: str
    started_at: str
    completed_at: str | None
    status: ResearchRunStatus
    notes: str


@dataclass(frozen=True)
class Signal:
    signal_type: str
    value: float
    encoding_type: str
    timestamp: str
    asset_id: str
    raw_reference: str
    metadata: dict[str, Any]
    is_persistent: bool


@dataclass(frozen=True)
class HypothesisDefinition:
    hypothesis_id: str
    name: str
    version: int
    definition: dict[str, Any]
    explainability_level: Literal["full", "partial", "opaque"]
    status: HypothesisStatus


@dataclass(frozen=True)
class HypothesisOutput:
    hypothesis_id: str
    version: int
    asset_id: str
    direction: Direction
    horizon: str
    confidence: float
    signals_snapshot: dict[str, float]
    explanation: dict[str, Any]
    timestamp: str = ""


@dataclass(frozen=True)
class TradeIdea:
    trade_id: str
    asset_id: str
    hypothesis_id: str
    version: int
    direction: Direction
    confidence: float
    signals_snapshot: dict[str, float]
    timestamp: str = ""


@dataclass(frozen=True)
class Decision:
    decision_id: str
    trade_id: str
    action: DecisionAction
    structured_reason: DecisionReason
    notes: str


@dataclass(frozen=True)
class Position:
    position_id: str
    trade_id: str
    entry_price: float
    exit_price: float | None
    pnl: float | None
    status: Literal["open", "closed"]


@dataclass(frozen=True)
class TradeOutcome:
    trade_id: str
    hypothesis_id: str
    pnl: float
    signals_snapshot: dict[str, float]
