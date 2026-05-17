from __future__ import annotations

from dataclasses import astuple
from typing import Any, cast

from project.data.db import DuckDBAccess
from project.data.models import (
    ApprovalEventRecord,
    ParameterResultRecord,
    ParameterSetRecord,
    ResearchArtifactRecord,
    ResearchProjectRecord,
    StrategyCandidateRecord,
    StrategyVersionRecord,
)
from project.data.repository_research import _db, _rows


UPSERT_RESEARCH_PROJECT_SQL = (
    "insert into research_projects values (?, ?, ?, ?, ?, ?) on conflict(project_id) "
    "do update set name = excluded.name, description = excluded.description, "
    "status = excluded.status, created_at = excluded.created_at, "
    "updated_at = excluded.updated_at"
)
UPSERT_RESEARCH_ARTIFACT_SQL = (
    "insert into research_artifacts values (?, ?, ?, ?, ?, ?, ?) on conflict(artifact_id) "
    "do update set project_id = excluded.project_id, research_run_id = excluded.research_run_id, "
    "artifact_type = excluded.artifact_type, payload_json = excluded.payload_json, "
    "content_hash = excluded.content_hash, created_at = excluded.created_at"
)
UPSERT_PARAMETER_SET_SQL = (
    "insert into parameter_sets values (?, ?, ?, ?, ?, ?) on conflict(parameter_set_id) "
    "do update set project_id = excluded.project_id, strategy_version_id = excluded.strategy_version_id, "
    "parameters_json = excluded.parameters_json, parameters_hash = excluded.parameters_hash, "
    "created_at = excluded.created_at"
)
UPSERT_PARAMETER_RESULT_SQL = (
    "insert into parameter_results values (?, ?, ?, ?, ?) on conflict(parameter_result_id) "
    "do update set parameter_set_id = excluded.parameter_set_id, metric_name = excluded.metric_name, "
    "metric_value = excluded.metric_value, created_at = excluded.created_at"
)
UPSERT_STRATEGY_VERSION_SQL = (
    "insert into strategy_versions values (?, ?, ?, ?, ?, ?, ?) on conflict(strategy_version_id) "
    "do update set project_id = excluded.project_id, version = excluded.version, "
    "definition_json = excluded.definition_json, status = excluded.status, "
    "created_at = excluded.created_at, updated_at = excluded.updated_at"
)
UPSERT_STRATEGY_CANDIDATE_SQL = (
    "insert into strategy_candidates values (?, ?, ?, ?, ?, ?, ?) on conflict(candidate_id) "
    "do update set project_id = excluded.project_id, strategy_version_id = excluded.strategy_version_id, "
    "label = excluded.label, status = excluded.status, created_at = excluded.created_at, "
    "promoted_at = excluded.promoted_at"
)
UPSERT_APPROVAL_EVENT_SQL = (
    "insert into approval_events values (?, ?, ?, ?, ?, ?, ?) on conflict(approval_event_id) "
    "do update set project_id = excluded.project_id, candidate_id = excluded.candidate_id, "
    "event_type = excluded.event_type, actor = excluded.actor, reason = excluded.reason, "
    "created_at = excluded.created_at"
)


class RepositoryResearchRunMixin:
    _db: DuckDBAccess

    def update_research_run_status(
        self,
        research_run_id: str,
        status: str,
        completed_at: str | None = None,
    ) -> None:
        statement = (
            "update research_runs set status = ?, completed_at = ? where research_run_id = ?"
            if completed_at is not None
            else "update research_runs set status = ? where research_run_id = ?"
        )
        params = (
            (status, completed_at, research_run_id)
            if completed_at is not None
            else (status, research_run_id)
        )
        _db(self).execute(statement, params)


class RepositoryResearchProjectMixin:
    _db: DuckDBAccess

    def persist_research_project(self, project: ResearchProjectRecord) -> None:
        _db(self).execute(UPSERT_RESEARCH_PROJECT_SQL, astuple(project))

    def get_research_projects(self) -> tuple[ResearchProjectRecord, ...]:
        return cast(
            tuple[ResearchProjectRecord, ...],
            _rows(
                "select project_id, name, description, status, created_at, updated_at "
                "from research_projects order by created_at, project_id",
                ResearchProjectRecord,
                _db(self),
            ),
        )

    def update_research_project_status(
        self,
        project_id: str,
        status: str,
        updated_at: str,
    ) -> None:
        _db(self).execute(
            "update research_projects set status = ?, updated_at = ? where project_id = ?",
            (status, updated_at, project_id),
        )

    def get_research_artifacts(
        self,
        project_id: str | None = None,
    ) -> tuple[ResearchArtifactRecord, ...]:
        statement = (
            "select artifact_id, project_id, research_run_id, artifact_type, "
            "payload_json, content_hash, created_at from research_artifacts"
        )
        parameters: tuple[Any, ...] = ()
        if project_id is not None:
            statement += " where project_id = ?"
            parameters = (project_id,)
        return cast(
            tuple[ResearchArtifactRecord, ...],
            _rows(
                statement + " order by created_at, artifact_id",
                ResearchArtifactRecord,
                _db(self),
                parameters,
            ),
        )


class RepositoryParameterMixin:
    _db: DuckDBAccess

    def persist_parameter_set(self, parameter_set: ParameterSetRecord) -> None:
        _db(self).execute(UPSERT_PARAMETER_SET_SQL, astuple(parameter_set))

    def get_parameter_sets(
        self,
        strategy_version_id: str | None = None,
    ) -> tuple[ParameterSetRecord, ...]:
        statement = (
            "select parameter_set_id, project_id, strategy_version_id, parameters_json, "
            "parameters_hash, created_at from parameter_sets"
        )
        parameters: tuple[Any, ...] = ()
        if strategy_version_id is not None:
            statement += " where strategy_version_id = ?"
            parameters = (strategy_version_id,)
        return cast(
            tuple[ParameterSetRecord, ...],
            _rows(
                statement + " order by created_at, parameter_set_id",
                ParameterSetRecord,
                _db(self),
                parameters,
            ),
        )

    def persist_parameter_result(self, parameter_result: ParameterResultRecord) -> None:
        _db(self).execute(UPSERT_PARAMETER_RESULT_SQL, astuple(parameter_result))

    def get_parameter_results(
        self,
        parameter_set_id: str,
    ) -> tuple[ParameterResultRecord, ...]:
        return cast(
            tuple[ParameterResultRecord, ...],
            _rows(
                "select parameter_result_id, parameter_set_id, metric_name, metric_value, "
                "created_at from parameter_results where parameter_set_id = ? "
                "order by created_at, parameter_result_id",
                ParameterResultRecord,
                _db(self),
                (parameter_set_id,),
            ),
        )


class RepositoryStrategyLifecycleMixin:
    _db: DuckDBAccess

    def persist_strategy_version(self, strategy_version: StrategyVersionRecord) -> None:
        _db(self).execute(UPSERT_STRATEGY_VERSION_SQL, astuple(strategy_version))

    def get_strategy_versions(
        self,
        project_id: str | None = None,
    ) -> tuple[StrategyVersionRecord, ...]:
        statement = (
            "select strategy_version_id, project_id, version, definition_json, status, "
            "created_at, updated_at from strategy_versions"
        )
        parameters: tuple[Any, ...] = ()
        if project_id is not None:
            statement += " where project_id = ?"
            parameters = (project_id,)
        return cast(
            tuple[StrategyVersionRecord, ...],
            _rows(
                statement + " order by created_at, strategy_version_id",
                StrategyVersionRecord,
                _db(self),
                parameters,
            ),
        )

    def update_strategy_version_status(
        self,
        strategy_version_id: str,
        status: str,
        updated_at: str,
    ) -> None:
        _db(self).execute(
            "update strategy_versions set status = ?, updated_at = ? where strategy_version_id = ?",
            (status, updated_at, strategy_version_id),
        )

    def persist_strategy_candidate(self, candidate: StrategyCandidateRecord) -> None:
        _db(self).execute(UPSERT_STRATEGY_CANDIDATE_SQL, astuple(candidate))

    def get_strategy_candidates(
        self,
        strategy_version_id: str | None = None,
    ) -> tuple[StrategyCandidateRecord, ...]:
        statement = (
            "select candidate_id, project_id, strategy_version_id, label, status, "
            "created_at, promoted_at from strategy_candidates"
        )
        parameters: tuple[Any, ...] = ()
        if strategy_version_id is not None:
            statement += " where strategy_version_id = ?"
            parameters = (strategy_version_id,)
        return cast(
            tuple[StrategyCandidateRecord, ...],
            _rows(
                statement + " order by created_at, candidate_id",
                StrategyCandidateRecord,
                _db(self),
                parameters,
            ),
        )

    def update_strategy_candidate_status(
        self,
        candidate_id: str,
        status: str,
        promoted_at: str | None = None,
    ) -> None:
        if promoted_at is None:
            _db(self).execute(
                "update strategy_candidates set status = ? where candidate_id = ?",
                (status, candidate_id),
            )
            return
        _db(self).execute(
            "update strategy_candidates set status = ?, promoted_at = ? where candidate_id = ?",
            (status, promoted_at, candidate_id),
        )

    def persist_approval_event(self, approval_event: ApprovalEventRecord) -> None:
        _db(self).execute(UPSERT_APPROVAL_EVENT_SQL, astuple(approval_event))

    def get_approval_events(
        self,
        candidate_id: str | None = None,
    ) -> tuple[ApprovalEventRecord, ...]:
        statement = (
            "select approval_event_id, project_id, candidate_id, event_type, actor, reason, "
            "created_at from approval_events"
        )
        parameters: tuple[Any, ...] = ()
        if candidate_id is not None:
            statement += " where candidate_id = ?"
            parameters = (candidate_id,)
        return cast(
            tuple[ApprovalEventRecord, ...],
            _rows(
                statement + " order by created_at, approval_event_id",
                ApprovalEventRecord,
                _db(self),
                parameters,
            ),
        )
