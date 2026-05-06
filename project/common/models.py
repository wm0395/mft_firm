from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal


Direction = Literal["long", "short", "flat"]
HypothesisStatus = Literal["draft", "testing", "active", "deprecated", "archived"]
DecisionAction = Literal["approve", "reject", "watch"]
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


@dataclass(frozen=True)
class TradeIdea:
    trade_id: str
    asset_id: str
    hypothesis_id: str
    version: int
    direction: Direction
    confidence: float
    signals_snapshot: dict[str, float]


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
