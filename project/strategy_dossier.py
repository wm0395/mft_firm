from __future__ import annotations

from project.common.models import strategy_spec_parameters
from project.data.repository import DataRepository


RESEARCH_BAR_TIMEFRAME = "1d"


def build_strategy_dossier(
    repository: DataRepository,
    hypothesis_id: str,
) -> dict[str, object] | None:
    strategy_spec = next(
        (spec for spec in repository.get_strategy_specs() if spec.hypothesis_id == hypothesis_id),
        None,
    )
    if strategy_spec is None:
        return None
    snapshots = [
        snapshot
        for snapshot in repository.get_dataset_snapshots()
        if snapshot.universe_id == strategy_spec.universe_id
    ]
    latest_snapshot = snapshots[-1] if snapshots else None
    latest_evidence = _latest_evidence_summary(
        repository,
        strategy_spec.strategy_spec_id,
        latest_snapshot.dataset_snapshot_id if latest_snapshot else None,
    )
    latest_run = _latest_research_run(repository, strategy_spec.strategy_spec_id)
    provenance = (
        repository.get_dataset_provenance(latest_snapshot, RESEARCH_BAR_TIMEFRAME).__dict__
        if latest_snapshot is not None
        else None
    )
    return _strategy_dossier_payload(strategy_spec, latest_snapshot, latest_evidence, latest_run, provenance)


def _strategy_dossier_payload(
    strategy_spec,
    latest_snapshot,
    latest_evidence,
    latest_run,
    provenance,
) -> dict[str, object]:
    parameters = strategy_spec_parameters(strategy_spec)
    return {
        "hypothesis_id": strategy_spec.hypothesis_id,
        "strategy_spec_id": strategy_spec.strategy_spec_id,
        "strategy_name": strategy_spec.name,
        "activation_status": "eligible" if latest_evidence is not None else "research_only",
        "thesis": parameters.get("thesis"),
        "bar_timeframe": parameters.get("bar_timeframe"),
        "holding_horizon": parameters.get("holding_horizon"),
        "required_signals": list(parameters.get("required_signals", ())),
        "expected_failure_modes": list(parameters.get("expected_failure_modes", ())),
        "dataset_snapshot_id": latest_snapshot.dataset_snapshot_id if latest_snapshot else None,
        "provenance": provenance,
        "research_run_id": latest_run.research_run_id if latest_run else None,
        "evidence_summary": (
            {
                "summary": latest_evidence.summary,
                "metrics": dict(latest_evidence.metrics),
                "created_at": latest_evidence.created_at,
            }
            if latest_evidence is not None
            else None
        ),
    }


def _latest_evidence_summary(repository: DataRepository, strategy_spec_id: str, dataset_snapshot_id: str | None):
    matches = [
        summary
        for summary in repository.get_strategy_evidence_summaries()
        if summary.strategy_spec_id == strategy_spec_id
        and (dataset_snapshot_id is None or summary.dataset_snapshot_id == dataset_snapshot_id)
    ]
    return matches[-1] if matches else None


def _latest_research_run(repository: DataRepository, strategy_spec_id: str):
    matches = [
        run
        for run in repository.get_research_runs()
        if run.strategy_spec_id == strategy_spec_id
    ]
    return matches[-1] if matches else None
