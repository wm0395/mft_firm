from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import json

from project.common.models import ResearchRun
from project.data.db import DuckDBAccess
from project.data.models import (
    ApprovalEventRecord,
    ParameterResultRecord,
    ParameterSetRecord,
    ResearchArtifactRecord,
    ResearchProjectRecord,
    StrategyCandidateRecord,
    StrategyVersionRecord,
    build_stable_hash,
)
from project.data.repository import DataRepository
from project.data.schema import REQUIRED_TABLES


def test_research_lifecycle_schema_initializes_required_tables(tmp_path: Path) -> None:
    repository, db = _repository(tmp_path)
    try:
        assert {row[0] for row in db.fetch_all("show tables")} == REQUIRED_TABLES
    finally:
        repository.close()


def test_research_lifecycle_round_trips_and_updates(tmp_path: Path) -> None:
    repository, _ = _repository(tmp_path)
    now = datetime.now(UTC).replace(microsecond=0).isoformat()

    project = ResearchProjectRecord(
        project_id="research_project:alpha",
        name="Alpha",
        description="Lifecycle project",
        status="draft",
        created_at=now,
        updated_at=now,
    )
    artifact_payload = {"kind": "note", "body": "seed"}
    artifact = ResearchArtifactRecord(
        artifact_id="research_artifact:alpha:note",
        project_id=project.project_id,
        research_run_id=None,
        artifact_type="note",
        payload_json=json.dumps(artifact_payload, sort_keys=True),
        content_hash=build_stable_hash(artifact_payload),
        created_at=now,
    )
    run = ResearchRun(
        research_run_id="research_run:alpha:1",
        strategy_spec_id="strategy_spec:alpha",
        dataset_snapshot_id="dataset_snapshot:alpha",
        started_at=now,
        completed_at=None,
        status="running",
        notes="initial run",
    )
    parameter_set = ParameterSetRecord(
        parameter_set_id="parameter_set:alpha:v1",
        project_id=project.project_id,
        strategy_version_id="strategy_version:alpha:v1",
        parameters_json=json.dumps({"bar_timeframe": "1d", "lookback": 14}, sort_keys=True),
        parameters_hash=build_stable_hash({"bar_timeframe": "1d", "lookback": 14}),
        created_at=now,
    )
    parameter_result = ParameterResultRecord(
        parameter_result_id="parameter_result:alpha:v1:sharpe",
        parameter_set_id=parameter_set.parameter_set_id,
        metric_name="sharpe",
        metric_value=1.25,
        created_at=now,
    )
    strategy_version = StrategyVersionRecord(
        strategy_version_id="strategy_version:alpha:v1",
        project_id=project.project_id,
        version=1,
        definition_json=json.dumps({"name": "alpha"}, sort_keys=True),
        status="draft",
        created_at=now,
        updated_at=now,
    )
    candidate = StrategyCandidateRecord(
        candidate_id="strategy_candidate:alpha:v1",
        project_id=project.project_id,
        strategy_version_id=strategy_version.strategy_version_id,
        label="candidate-a",
        status="proposed",
        created_at=now,
        promoted_at=None,
    )
    approval_event = ApprovalEventRecord(
        approval_event_id="approval_event:alpha:v1:approve",
        project_id=project.project_id,
        candidate_id=candidate.candidate_id,
        event_type="approval",
        actor="reviewer",
        reason="meets bar",
        created_at=now,
    )

    repository.persist_research_project(project)
    repository.persist_research_artifact(artifact)
    repository.persist_research_artifact(run)
    repository.persist_parameter_set(parameter_set)
    repository.persist_parameter_result(parameter_result)
    repository.persist_strategy_version(strategy_version)
    repository.persist_strategy_candidate(candidate)
    repository.persist_approval_event(approval_event)

    repository.update_research_run_status(run.research_run_id, "completed", now)
    repository.update_research_project_status(project.project_id, "active", now)
    repository.update_strategy_version_status(strategy_version.strategy_version_id, "active", now)
    repository.update_strategy_candidate_status(candidate.candidate_id, "promoted", now)

    assert repository.get_research_projects() == (
        ResearchProjectRecord(
            project_id=project.project_id,
            name=project.name,
            description=project.description,
            status="active",
            created_at=project.created_at,
            updated_at=now,
        ),
    )
    assert repository.get_research_artifacts(project.project_id) == (artifact,)
    assert repository.get_research_runs() == (
        ResearchRun(
            research_run_id=run.research_run_id,
            strategy_spec_id=run.strategy_spec_id,
            dataset_snapshot_id=run.dataset_snapshot_id,
            started_at=run.started_at,
            completed_at=now,
            status="completed",
            notes=run.notes,
        ),
    )
    assert repository.get_parameter_sets(parameter_set.strategy_version_id) == (parameter_set,)
    assert repository.get_parameter_results(parameter_set.parameter_set_id) == (parameter_result,)
    assert repository.get_strategy_versions(project.project_id) == (
        StrategyVersionRecord(
            strategy_version_id=strategy_version.strategy_version_id,
            project_id=strategy_version.project_id,
            version=strategy_version.version,
            definition_json=strategy_version.definition_json,
            status="active",
            created_at=strategy_version.created_at,
            updated_at=now,
        ),
    )
    assert repository.get_strategy_candidates(strategy_version.strategy_version_id) == (
        StrategyCandidateRecord(
            candidate_id=candidate.candidate_id,
            project_id=candidate.project_id,
            strategy_version_id=candidate.strategy_version_id,
            label=candidate.label,
            status="promoted",
            created_at=candidate.created_at,
            promoted_at=now,
        ),
    )
    assert repository.get_approval_events(candidate.candidate_id) == (approval_event,)
    repository.close()


def test_build_stable_hash_is_deterministic() -> None:
    first = build_stable_hash({"a": 1, "b": 2})
    second = build_stable_hash({"b": 2, "a": 1})
    assert first == second


def _repository(tmp_path: Path) -> tuple[DataRepository, DuckDBAccess]:
    db = DuckDBAccess(tmp_path / "mft.duckdb")
    repository = DataRepository(db)
    repository.initialize()
    return repository, db
