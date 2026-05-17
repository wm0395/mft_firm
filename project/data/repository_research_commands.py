from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import json
from typing import Any

from project.common.models import utc_now_iso
from project.data.db import DuckDBAccess
from project.data.models import (
    ApprovalEventRecord,
    ResearchArtifactRecord,
    ResearchProjectRecord,
    build_stable_hash,
)
from project.data.repository_research_command_support import (
    artifact_summary,
    build_parameter_research_bundle,
    candidate_lookup,
    parameter_research_artifacts,
    project_id as build_project_id,
    project_lookup,
    project_runs,
    require_project_id,
    research_run_artifact,
)


class RepositoryResearchProjectCommandMixin:
    _db: DuckDBAccess

    def create_research_project(
        self,
        *,
        name: str,
        description: str = "",
        research_project_id: str | None = None,
        dataset_snapshot_id: str | None = None,
    ) -> ResearchProjectRecord:
        project = ResearchProjectRecord(
            project_id=research_project_id or build_project_id(name),
            name=name,
            description=description,
            status="draft",
            created_at=utc_now_iso(),
            updated_at=utc_now_iso(),
        )
        self.persist_research_project(project)
        if dataset_snapshot_id is not None:
            self.persist_research_artifact(
                ResearchArtifactRecord(
                    artifact_id=f"{project.project_id}:bootstrap",
                    project_id=project.project_id,
                    research_run_id=None,
                    artifact_type="project_bootstrap",
                    payload_json=json.dumps(
                        {"dataset_snapshot_id": dataset_snapshot_id}, sort_keys=True
                    ),
                    content_hash=build_stable_hash(
                        {
                            "dataset_snapshot_id": dataset_snapshot_id,
                            "project_id": project.project_id,
                        }
                    ),
                    created_at=project.created_at,
                )
            )
        return project

    def list_research_projects(self) -> tuple[ResearchProjectRecord, ...]:
        return self.get_research_projects()

    def show_research_project(self, research_project_id: str) -> dict[str, Any]:
        project = project_lookup(self.get_research_projects(), research_project_id)
        artifacts = self.get_research_artifacts(research_project_id)
        runs = project_runs(artifacts)
        return {
            "project": project,
            "artifact_count": len(artifacts),
            "run_count": len(runs),
            "runs": runs,
        }

    def export_research_pack(
        self,
        *,
        research_project_id: str,
        output_dir: str | Path | None = None,
    ) -> dict[str, Any]:
        project = self.show_research_project(research_project_id)["project"]
        export_root = Path(output_dir or "reports/research") / research_project_id
        export_root.mkdir(parents=True, exist_ok=True)
        files = {
            "project.json": export_root / "project.json",
            "research_runs.json": export_root / "research_runs.json",
            "artifacts.json": export_root / "artifacts.json",
            "manifest.json": export_root / "manifest.json",
        }
        payloads = {
            "project.json": asdict(project),
            "research_runs.json": self.list_research_runs(
                research_project_id=research_project_id
            ),
            "artifacts.json": [asdict(artifact) for artifact in self.get_research_artifacts(research_project_id)],
        }
        for name, path in files.items():
            path.write_text(json.dumps(payloads[name], indent=2, sort_keys=True), encoding="utf-8")
        manifest = {
            "research_project_id": research_project_id,
            "output_dir": str(export_root),
            "files": [name for name in files],
        }
        files["manifest.json"].write_text(
            json.dumps(manifest, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return manifest


class RepositoryResearchRunCommandMixin:
    _db: DuckDBAccess

    def run_parameter_research(
        self,
        *,
        parameters: dict[str, Any],
        research_project_id: str | None = None,
        hypothesis_id: str | None = None,
        dataset_snapshot_id: str | None = None,
        include_testing: bool = False,
        include_draft: bool = False,
    ) -> dict[str, Any]:
        project = project_lookup(
            self.get_research_projects(),
            require_project_id(research_project_id),
        )
        bundle = build_parameter_research_bundle(
            project,
            parameters,
            hypothesis_id,
            dataset_snapshot_id,
            include_testing,
            include_draft,
            self.get_strategy_versions(project.project_id),
        )
        self.persist_strategy_version(bundle.strategy_version)
        self.persist_parameter_set(bundle.parameter_set)
        self.persist_parameter_result(bundle.parameter_result)
        self.persist_research_artifact(bundle.artifact)
        self.persist_strategy_candidate(bundle.candidate)
        return {
            "research_project_id": project.project_id,
            "research_run_id": bundle.research_run_id,
            "parameter_set_id": bundle.parameter_set.parameter_set_id,
            "strategy_version_id": bundle.strategy_version.strategy_version_id,
            "strategy_candidate_id": bundle.candidate.candidate_id,
            "parameter_count": len(parameters),
            "include_testing": include_testing,
            "include_draft": include_draft,
        }

    def list_research_runs(
        self,
        research_project_id: str | None = None,
    ) -> tuple[dict[str, Any], ...]:
        artifacts = self._parameter_research_artifacts(research_project_id)
        return tuple(artifact_summary(artifact) for artifact in artifacts)

    def show_research_run(self, research_run_id: str) -> dict[str, Any]:
        artifact = research_run_artifact(
            self._parameter_research_artifacts(None),
            research_run_id,
        )
        payload = json.loads(artifact.payload_json)
        return {
            "artifact": artifact,
            "payload": payload,
        }

    def _parameter_research_artifacts(
        self,
        research_project_id: str | None,
    ) -> tuple[ResearchArtifactRecord, ...]:
        return parameter_research_artifacts(self.get_research_artifacts(research_project_id))


class RepositoryResearchCandidateCommandMixin:
    _db: DuckDBAccess

    def compare_research_runs(self, research_run_ids: tuple[str, ...]) -> dict[str, Any]:
        artifacts = self._parameter_research_artifacts(None)
        selected = [
            artifact
            for artifact in artifacts
            if artifact.research_run_id in research_run_ids
        ]
        if len(selected) < 2:
            raise ValueError("compare-research-runs requires at least two known research runs")
        return {
            "research_run_ids": list(research_run_ids),
            "runs": [artifact_summary(artifact) for artifact in selected],
        }

    def promote_strategy_candidate(
        self,
        *,
        strategy_candidate_id: str,
        to_status: str,
        force: bool = False,
    ) -> dict[str, Any]:
        candidate = candidate_lookup(self.get_strategy_candidates(), strategy_candidate_id)
        promoted_at = utc_now_iso()
        self.update_strategy_candidate_status(candidate.candidate_id, to_status, promoted_at)
        self.persist_approval_event(
            ApprovalEventRecord(
                approval_event_id=f"approval_event:{candidate.candidate_id}:{to_status}",
                project_id=candidate.project_id,
                candidate_id=candidate.candidate_id,
                event_type="promotion",
                actor="cli",
                reason="promoted via CLI",
                created_at=promoted_at,
            )
        )
        self.update_strategy_version_status(candidate.strategy_version_id, to_status, promoted_at)
        return {
            "strategy_candidate_id": candidate.candidate_id,
            "previous_status": candidate.status,
            "new_status": to_status,
            "force": force,
        }
