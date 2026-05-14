from __future__ import annotations

from dataclasses import astuple, dataclass
from typing import Any, cast

from project.common.models import (
    DatasetSnapshot,
    ResearchRun,
    ResearchUniverse,
    StrategyEvidenceSummary,
    StrategySpec,
)
from project.data.ingestion import build_dataset_provenance
from project.data.models import (
    DataSourceMetadata,
    DatasetProvenance,
    DatasetSnapshotRecord,
    ResearchRunRecord,
    ResearchUniverseRecord,
    StrategyEvidenceSummaryRecord,
    StrategySpecRecord,
)
from project.data.db import DuckDBAccess
from project.data.schema import (
    UPSERT_DATASET_SNAPSHOT_SQL,
    UPSERT_RESEARCH_RUN_SQL,
    UPSERT_RESEARCH_UNIVERSE_SQL,
    UPSERT_STRATEGY_EVIDENCE_SUMMARY_SQL,
    UPSERT_STRATEGY_SPEC_SQL,
)


@dataclass(frozen=True)
class _SnapshotMetadataAdapter:
    metadata_value: DataSourceMetadata

    def metadata(self) -> DataSourceMetadata:
        return self.metadata_value


def _load_research_artifacts(statement: str, record_type: Any, db: Any) -> tuple[Any, ...]:
    return tuple(record_type(*row).to_artifact() for row in db.fetch_all(statement))


def _snapshot_symbol_mapping(
    snapshot: DatasetSnapshot,
    assets: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((asset_id, symbol) for asset_id, symbol in assets if asset_id in snapshot.asset_ids))


def _research_artifact_record(
    artifact: ResearchUniverse | DatasetSnapshot | StrategySpec | ResearchRun | StrategyEvidenceSummary,
) -> tuple[Any, str]:
    if isinstance(artifact, ResearchUniverse):
        return ResearchUniverseRecord.from_artifact(artifact), UPSERT_RESEARCH_UNIVERSE_SQL
    if isinstance(artifact, DatasetSnapshot):
        return DatasetSnapshotRecord.from_artifact(artifact), UPSERT_DATASET_SNAPSHOT_SQL
    if isinstance(artifact, StrategySpec):
        return StrategySpecRecord.from_artifact(artifact), UPSERT_STRATEGY_SPEC_SQL
    if isinstance(artifact, ResearchRun):
        return ResearchRunRecord.from_artifact(artifact), UPSERT_RESEARCH_RUN_SQL
    return StrategyEvidenceSummaryRecord.from_artifact(artifact), UPSERT_STRATEGY_EVIDENCE_SUMMARY_SQL


class RepositoryResearchMixin:
    _db: DuckDBAccess

    def persist_research_artifact(
        self,
        artifact: ResearchUniverse | DatasetSnapshot | StrategySpec | ResearchRun | StrategyEvidenceSummary,
    ) -> None:
        record, statement = _research_artifact_record(artifact)
        _db(self).execute(statement, astuple(record))

    def get_research_universes(self) -> tuple[ResearchUniverse, ...]:
        return _load_research_artifacts(
            """
            select universe_id, name, market, description, asset_ids_json
            from research_universes
            order by universe_id
            """,
            ResearchUniverseRecord,
            _db(self),
        )

    def get_dataset_snapshots(self) -> tuple[DatasetSnapshot, ...]:
        return _load_research_artifacts(
            """
            select dataset_snapshot_id, universe_id, captured_at, data_start,
                   data_end, asset_ids_json
            from dataset_snapshots
            order by captured_at, dataset_snapshot_id
            """,
            DatasetSnapshotRecord,
            _db(self),
        )

    def get_dataset_provenance(
        self,
        snapshot: DatasetSnapshot,
        bar_timeframe: str,
    ) -> DatasetProvenance:
        repository = cast(Any, self)
        assets = tuple((asset.asset_id, asset.symbol) for asset in repository.list_assets())
        sources = sorted(
            {
                point.source
                for asset_id in snapshot.asset_ids
                for point in repository.read_raw_values(asset_id, "price")
                if snapshot.data_start <= point.timestamp <= snapshot.data_end
            }
        )
        adapter = _SnapshotMetadataAdapter(
            metadata_value=DataSourceMetadata(
                source_name=",".join(sources),
                symbol_mapping=_snapshot_symbol_mapping(snapshot, assets),
                bar_timeframe=bar_timeframe,
            )
        )
        return build_dataset_provenance(adapter, snapshot.data_start, snapshot.data_end)

    def get_strategy_specs(self) -> tuple[StrategySpec, ...]:
        return _load_research_artifacts(
            """
            select strategy_spec_id, universe_id, hypothesis_id, hypothesis_version,
                   name, parameters_json
            from strategy_specs
            order by strategy_spec_id
            """,
            StrategySpecRecord,
            _db(self),
        )

    def get_strategy_spec(
        self,
        hypothesis_id: str,
        hypothesis_version: int,
    ) -> StrategySpec | None:
        for strategy_spec in self.get_strategy_specs():
            if strategy_spec.hypothesis_id != hypothesis_id:
                continue
            if strategy_spec.hypothesis_version == hypothesis_version:
                return strategy_spec
        return None

    def get_research_runs(self) -> tuple[ResearchRun, ...]:
        return _load_research_artifacts(
            """
            select research_run_id, strategy_spec_id, dataset_snapshot_id,
                   started_at, completed_at, status, notes
            from research_runs
            order by started_at, research_run_id
            """,
            ResearchRunRecord,
            _db(self),
        )

    def get_strategy_evidence_summaries(self) -> tuple[StrategyEvidenceSummary, ...]:
        return _load_research_artifacts(
            """
            select evidence_summary_id, strategy_spec_id, research_run_id,
                   dataset_snapshot_id, summary, metrics_json, created_at
            from strategy_evidence_summaries
            order by created_at, evidence_summary_id
            """,
            StrategyEvidenceSummaryRecord,
            _db(self),
        )


def _db(repository: Any) -> DuckDBAccess:
    return cast(DuckDBAccess, repository._db)
