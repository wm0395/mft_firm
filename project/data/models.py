from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import json

from project.common.models import (
    DatasetSnapshot,
    HypothesisDefinition,
    ResearchRun,
    ResearchRunStatus,
    ResearchUniverse,
    StrategyEvidenceSummary,
    StrategySpec,
    SignalDefinition,
)


def _json_object_from_pairs(
    pairs: tuple[tuple[str, object], ...],
    field_name: str,
) -> str:
    payload: dict[str, object] = {}
    for key, value in pairs:
        if key in payload:
            msg = f"duplicate {field_name} key: {key}"
            raise ValueError(msg)
        payload[key] = value
    return json.dumps(payload, sort_keys=True)


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


@dataclass(frozen=True)
class ResearchUniverseRecord:
    universe_id: str
    name: str
    market: str
    description: str
    asset_ids_json: str

    @classmethod
    def from_artifact(cls, artifact: ResearchUniverse) -> "ResearchUniverseRecord":
        return cls(
            universe_id=artifact.universe_id,
            name=artifact.name,
            market=artifact.market,
            description=artifact.description,
            asset_ids_json=json.dumps(sorted(artifact.asset_ids)),
        )

    def to_artifact(self) -> ResearchUniverse:
        return ResearchUniverse(
            universe_id=self.universe_id,
            name=self.name,
            market=self.market,
            description=self.description,
            asset_ids=tuple(json.loads(self.asset_ids_json)),
        )


@dataclass(frozen=True)
class DatasetSnapshotRecord:
    dataset_snapshot_id: str
    universe_id: str
    captured_at: str
    data_start: str
    data_end: str
    asset_ids_json: str

    @classmethod
    def from_artifact(cls, artifact: DatasetSnapshot) -> "DatasetSnapshotRecord":
        return cls(
            dataset_snapshot_id=artifact.dataset_snapshot_id,
            universe_id=artifact.universe_id,
            captured_at=artifact.captured_at,
            data_start=artifact.data_start,
            data_end=artifact.data_end,
            asset_ids_json=json.dumps(sorted(artifact.asset_ids)),
        )

    def to_artifact(self) -> DatasetSnapshot:
        return DatasetSnapshot(
            dataset_snapshot_id=self.dataset_snapshot_id,
            universe_id=self.universe_id,
            captured_at=self.captured_at,
            data_start=self.data_start,
            data_end=self.data_end,
            asset_ids=tuple(json.loads(self.asset_ids_json)),
        )


@dataclass(frozen=True)
class DatasetProvenance:
    snapshot_identity: str
    source_name: str
    bar_timeframe: str
    symbol_mapping: tuple[tuple[str, str], ...]
    coverage_start: str
    coverage_end: str


@dataclass(frozen=True)
class DataSourceMetadata:
    source_name: str
    symbol_mapping: tuple[tuple[str, str], ...]
    bar_timeframe: str


@dataclass(frozen=True)
class StrategySpecRecord:
    strategy_spec_id: str
    universe_id: str
    hypothesis_id: str
    hypothesis_version: int
    name: str
    parameters_json: str

    @classmethod
    def from_artifact(cls, artifact: StrategySpec) -> "StrategySpecRecord":
        return cls(
            strategy_spec_id=artifact.strategy_spec_id,
            universe_id=artifact.universe_id,
            hypothesis_id=artifact.hypothesis_id,
            hypothesis_version=artifact.hypothesis_version,
            name=artifact.name,
            parameters_json=_json_object_from_pairs(
                artifact.parameters,
                "strategy parameter",
            ),
        )

    def to_artifact(self) -> StrategySpec:
        return StrategySpec(
            strategy_spec_id=self.strategy_spec_id,
            universe_id=self.universe_id,
            hypothesis_id=self.hypothesis_id,
            hypothesis_version=self.hypothesis_version,
            name=self.name,
            parameters=tuple(sorted(json.loads(self.parameters_json).items())),
        )


@dataclass(frozen=True)
class StrategyEvidenceSummaryRecord:
    evidence_summary_id: str
    strategy_spec_id: str
    research_run_id: str
    dataset_snapshot_id: str
    summary: str
    metrics_json: str
    created_at: str

    @classmethod
    def from_artifact(
        cls,
        artifact: StrategyEvidenceSummary,
    ) -> "StrategyEvidenceSummaryRecord":
        return cls(
            evidence_summary_id=artifact.evidence_summary_id,
            strategy_spec_id=artifact.strategy_spec_id,
            research_run_id=artifact.research_run_id,
            dataset_snapshot_id=artifact.dataset_snapshot_id,
            summary=artifact.summary,
            metrics_json=_json_object_from_pairs(
                artifact.metrics,
                "strategy metric",
            ),
            created_at=artifact.created_at,
        )

    def to_artifact(self) -> StrategyEvidenceSummary:
        return StrategyEvidenceSummary(
            evidence_summary_id=self.evidence_summary_id,
            strategy_spec_id=self.strategy_spec_id,
            research_run_id=self.research_run_id,
            dataset_snapshot_id=self.dataset_snapshot_id,
            summary=self.summary,
            metrics=tuple(sorted(json.loads(self.metrics_json).items())),
            created_at=self.created_at,
        )


@dataclass(frozen=True)
class HypothesisDefinitionRecord:
    hypothesis_id: str
    name: str
    version: int
    definition_json: str
    explainability_level: str
    status: str

    @classmethod
    def from_artifact(cls, artifact: HypothesisDefinition) -> "HypothesisDefinitionRecord":
        return cls(
            hypothesis_id=artifact.hypothesis_id,
            name=artifact.name,
            version=artifact.version,
            definition_json=json.dumps(artifact.definition, sort_keys=True),
            explainability_level=artifact.explainability_level,
            status=artifact.status,
        )

    def to_artifact(self) -> HypothesisDefinition:
        return HypothesisDefinition(
            hypothesis_id=self.hypothesis_id,
            name=self.name,
            version=self.version,
            definition=json.loads(self.definition_json),
            explainability_level=self.explainability_level,
            status=self.status,
        )


@dataclass(frozen=True)
class SignalDefinitionRecord:
    signal_type: str
    category: str
    definition: str
    dependencies_json: str
    is_persistent: bool
    version: int

    @classmethod
    def from_artifact(cls, artifact: SignalDefinition) -> "SignalDefinitionRecord":
        return cls(
            signal_type=artifact.signal_type,
            category=artifact.category,
            definition=artifact.definition,
            dependencies_json=json.dumps(artifact.dependencies, sort_keys=True),
            is_persistent=artifact.is_persistent,
            version=artifact.version,
        )

    def to_artifact(self) -> SignalDefinition:
        return SignalDefinition(
            signal_type=self.signal_type,
            category=self.category,
            definition=self.definition,
            dependencies=tuple(json.loads(self.dependencies_json)),
            is_persistent=self.is_persistent,
            version=self.version,
        )


@dataclass(frozen=True)
class ResearchRunRecord:
    research_run_id: str
    strategy_spec_id: str
    dataset_snapshot_id: str
    started_at: str
    completed_at: str | None
    status: ResearchRunStatus
    notes: str

    @classmethod
    def from_artifact(cls, artifact: ResearchRun) -> "ResearchRunRecord":
        return cls(
            research_run_id=artifact.research_run_id,
            strategy_spec_id=artifact.strategy_spec_id,
            dataset_snapshot_id=artifact.dataset_snapshot_id,
            started_at=artifact.started_at,
            completed_at=artifact.completed_at,
            status=artifact.status,
            notes=artifact.notes,
        )

    def to_artifact(self) -> ResearchRun:
        return ResearchRun(
            research_run_id=self.research_run_id,
            strategy_spec_id=self.strategy_spec_id,
            dataset_snapshot_id=self.dataset_snapshot_id,
            started_at=self.started_at,
            completed_at=self.completed_at,
            status=self.status,
            notes=self.notes,
        )
