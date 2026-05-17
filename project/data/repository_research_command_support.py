from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import json
import re

from project.common.models import utc_now_iso
from project.data.models import (
    ParameterResultRecord,
    ParameterSetRecord,
    ResearchArtifactRecord,
    ResearchProjectRecord,
    StrategyCandidateRecord,
    StrategyVersionRecord,
    build_stable_hash,
)


@dataclass(frozen=True)
class ParameterResearchBundle:
    strategy_version: StrategyVersionRecord
    parameter_set: ParameterSetRecord
    parameter_result: ParameterResultRecord
    artifact: ResearchArtifactRecord
    candidate: StrategyCandidateRecord
    research_run_id: str


@dataclass(frozen=True)
class _ParameterResearchContext:
    project_id: str
    parameter_hash: str
    strategy_version_id: str
    parameter_set: ParameterSetRecord
    parameters: dict[str, Any]
    hypothesis_id: str | None
    dataset_snapshot_id: str | None
    include_testing: bool
    include_draft: bool
    strategy_versions: tuple[StrategyVersionRecord, ...]
    created_at: str


def build_parameter_research_bundle(
    project: ResearchProjectRecord,
    parameters: dict[str, Any],
    hypothesis_id: str | None,
    dataset_snapshot_id: str | None,
    include_testing: bool,
    include_draft: bool,
    strategy_versions: tuple[StrategyVersionRecord, ...],
) -> ParameterResearchBundle:
    parameter_hash = parameter_research_hash(
        project.project_id,
        parameters,
        hypothesis_id,
        dataset_snapshot_id,
    )
    created_at = utc_now_iso()
    strategy_version_id = f"strategy_version:{project.project_id}:{parameter_hash}"
    parameter_set = build_parameter_set(
        project.project_id,
        strategy_version_id,
        parameters,
        parameter_hash,
        created_at,
    )
    return _parameter_research_bundle_from_context(
        _ParameterResearchContext(
            project_id=project.project_id,
            parameter_hash=parameter_hash,
            strategy_version_id=strategy_version_id,
            parameter_set=parameter_set,
            parameters=parameters,
            hypothesis_id=hypothesis_id,
            dataset_snapshot_id=dataset_snapshot_id,
            include_testing=include_testing,
            include_draft=include_draft,
            strategy_versions=strategy_versions,
            created_at=created_at,
        )
    )


def parameter_research_hash(
    project_id: str,
    parameters: dict[str, Any],
    hypothesis_id: str | None,
    dataset_snapshot_id: str | None,
) -> str:
    return build_stable_hash(
        {
            "project_id": project_id,
            "parameters": parameters,
            "hypothesis_id": hypothesis_id,
            "dataset_snapshot_id": dataset_snapshot_id,
        }
    )


def _parameter_research_bundle_from_context(
    context: _ParameterResearchContext,
) -> ParameterResearchBundle:
    research_run_id = f"research_run:{context.project_id}:{context.parameter_hash}"
    return ParameterResearchBundle(
        strategy_version=build_strategy_version(
            context.project_id,
            context.strategy_version_id,
            context.parameters,
            context.hypothesis_id,
            context.dataset_snapshot_id,
            context.strategy_versions,
            context.created_at,
        ),
        parameter_set=context.parameter_set,
        parameter_result=build_parameter_result(context.parameter_set, context.created_at),
        artifact=build_research_artifact(
            context.project_id,
            research_run_id,
            context.parameter_set.parameter_set_id,
            context.parameter_hash,
            context.hypothesis_id,
            context.dataset_snapshot_id,
            context.include_testing,
            context.include_draft,
            context.created_at,
        ),
        candidate=build_strategy_candidate(
            context.project_id,
            context.strategy_version_id,
            context.parameters,
            context.created_at,
            context.parameter_hash,
        ),
        research_run_id=research_run_id,
    )


def build_strategy_version(
    project_id: str,
    strategy_version_id: str,
    parameters: dict[str, Any],
    hypothesis_id: str | None,
    dataset_snapshot_id: str | None,
    strategy_versions: tuple[StrategyVersionRecord, ...],
    created_at: str,
) -> StrategyVersionRecord:
    return StrategyVersionRecord(
        strategy_version_id=strategy_version_id,
        project_id=project_id,
        version=next_strategy_version(strategy_versions),
        definition_json=json.dumps(
            {
                "project_id": project_id,
                "hypothesis_id": hypothesis_id,
                "dataset_snapshot_id": dataset_snapshot_id,
                "parameters": parameters,
            },
            sort_keys=True,
        ),
        status="draft",
        created_at=created_at,
        updated_at=created_at,
    )


def build_parameter_set(
    project_id: str,
    strategy_version_id: str,
    parameters: dict[str, Any],
    parameter_hash: str,
    created_at: str,
) -> ParameterSetRecord:
    return ParameterSetRecord(
        parameter_set_id=f"parameter_set:{project_id}:{parameter_hash}",
        project_id=project_id,
        strategy_version_id=strategy_version_id,
        parameters_json=json.dumps(parameters, sort_keys=True),
        parameters_hash=parameter_hash,
        created_at=created_at,
    )


def build_parameter_result(
    parameter_set: ParameterSetRecord,
    created_at: str,
) -> ParameterResultRecord:
    return ParameterResultRecord(
        parameter_result_id=f"parameter_result:{parameter_set.parameter_set_id}:parameter_count",
        parameter_set_id=parameter_set.parameter_set_id,
        metric_name="parameter_count",
        metric_value=float(len(json.loads(parameter_set.parameters_json))),
        created_at=created_at,
    )


def build_research_artifact(
    project_id: str,
    research_run_id: str,
    parameter_set_id: str,
    parameter_hash: str,
    hypothesis_id: str | None,
    dataset_snapshot_id: str | None,
    include_testing: bool,
    include_draft: bool,
    created_at: str,
) -> ResearchArtifactRecord:
    payload = {
        "project_id": project_id,
        "parameter_set_id": parameter_set_id,
        "parameter_hash": parameter_hash,
        "hypothesis_id": hypothesis_id,
        "dataset_snapshot_id": dataset_snapshot_id,
        "include_testing": include_testing,
        "include_draft": include_draft,
    }
    return ResearchArtifactRecord(
        artifact_id=research_run_id,
        project_id=project_id,
        research_run_id=research_run_id,
        artifact_type="parameter_research_run",
        payload_json=json.dumps(payload, sort_keys=True),
        content_hash=build_stable_hash(payload),
        created_at=created_at,
    )


def build_strategy_candidate(
    project_id: str,
    strategy_version_id: str,
    parameters: dict[str, Any],
    created_at: str,
    parameter_hash: str,
) -> StrategyCandidateRecord:
    return StrategyCandidateRecord(
        candidate_id=f"strategy_candidate:{project_id}:{parameter_hash}",
        project_id=project_id,
        strategy_version_id=strategy_version_id,
        label=parameters.get("label", "parameter-candidate"),
        status="proposed",
        created_at=created_at,
        promoted_at=None,
    )


def artifact_summary(artifact: ResearchArtifactRecord) -> dict[str, Any]:
    payload = json.loads(artifact.payload_json)
    return {
        "research_run_id": artifact.research_run_id,
        "research_project_id": artifact.project_id,
        "strategy_version_id": payload.get("strategy_version_id"),
        "parameter_set_id": payload.get("parameter_set_id"),
        "parameter_hash": payload.get("parameter_hash"),
    }


def project_lookup(
    projects: tuple[ResearchProjectRecord, ...],
    research_project_id: str,
) -> ResearchProjectRecord:
    for project in projects:
        if project.project_id == research_project_id:
            return project
    raise ValueError(f"research project not found: {research_project_id}")


def candidate_lookup(
    candidates: tuple[StrategyCandidateRecord, ...],
    candidate_id: str,
) -> StrategyCandidateRecord:
    for candidate in candidates:
        if candidate.candidate_id == candidate_id:
            return candidate
    raise ValueError(f"strategy candidate not found: {candidate_id}")


def parameter_research_artifacts(
    artifacts: tuple[ResearchArtifactRecord, ...],
) -> tuple[ResearchArtifactRecord, ...]:
    return tuple(
        artifact
        for artifact in artifacts
        if artifact.artifact_type == "parameter_research_run"
    )


def research_run_artifact(
    artifacts: tuple[ResearchArtifactRecord, ...],
    research_run_id: str,
) -> ResearchArtifactRecord:
    for artifact in artifacts:
        if artifact.research_run_id == research_run_id or artifact.artifact_id == research_run_id:
            return artifact
    raise ValueError(f"research run not found: {research_run_id}")


def project_runs(
    artifacts: tuple[ResearchArtifactRecord, ...],
) -> tuple[dict[str, Any], ...]:
    return tuple(artifact_summary(artifact) for artifact in parameter_research_artifacts(artifacts))


def project_id(name: str) -> str:
    return f"research_project:{slug(name)}"


def require_project_id(research_project_id: str | None) -> str:
    if research_project_id is None:
        raise ValueError("research project identifier is required")
    return research_project_id


def next_strategy_version(
    versions: tuple[StrategyVersionRecord, ...],
) -> int:
    return max((version.version for version in versions), default=0) + 1


def slug(value: str) -> str:
    slug_value = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug_value or "project"
