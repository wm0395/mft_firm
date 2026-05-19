from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from project.data.repository import DataRepository


@dataclass(frozen=True)
class ResearchProjectView:
    project_id: str
    name: str
    status: str
    description: str
    artifact_count: int


@dataclass(frozen=True)
class ResearchRunView:
    research_run_id: str
    strategy_spec_id: str
    dataset_snapshot_id: str
    status: str
    started_at: str
    completed_at: str | None
    notes: str


@dataclass(frozen=True)
class StrategyCandidateView:
    candidate_id: str
    project_id: str
    strategy_version_id: str
    label: str
    status: str
    created_at: str
    promoted_at: str | None


@dataclass(frozen=True)
class ResearchPageView:
    projects: tuple[ResearchProjectView, ...]
    runs: tuple[ResearchRunView, ...]
    candidates: tuple[StrategyCandidateView, ...]
    debug_payload: dict[str, Any]


def get_research_page_view(repository: DataRepository) -> ResearchPageView:
    projects = repository.get_research_projects()
    runs = repository.get_research_runs()
    candidates = repository.get_strategy_candidates()
    return ResearchPageView(
        projects=_project_views(repository, projects),
        runs=_run_views(runs),
        candidates=_candidate_views(candidates),
        debug_payload=_debug_payload(projects, runs),
    )


def _project_views(
    repository: DataRepository,
    projects,
) -> tuple[ResearchProjectView, ...]:
    return tuple(
        ResearchProjectView(
            project.project_id,
            project.name,
            project.status,
            project.description,
            _artifact_count(repository, project.project_id),
        )
        for project in projects
    )


def _run_views(runs) -> tuple[ResearchRunView, ...]:
    return tuple(
        ResearchRunView(
            run.research_run_id,
            run.strategy_spec_id,
            run.dataset_snapshot_id,
            run.status,
            run.started_at,
            run.completed_at,
            run.notes,
        )
        for run in runs
    )


def _candidate_views(
    candidates,
) -> tuple[StrategyCandidateView, ...]:
    return tuple(
        StrategyCandidateView(
            candidate.candidate_id,
            candidate.project_id,
            candidate.strategy_version_id,
            candidate.label,
            candidate.status,
            candidate.created_at,
            candidate.promoted_at,
        )
        for candidate in candidates
    )


def _debug_payload(projects, runs) -> dict[str, object]:
    return {
        "projects": [project.__dict__ for project in projects],
        "runs": [run.__dict__ for run in runs],
    }


def _artifact_count(repository: DataRepository, project_id: str) -> int:
    return len(repository.get_research_artifacts(project_id))
