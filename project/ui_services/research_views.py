from __future__ import annotations

from dataclasses import dataclass

from project.data.repository import DataRepository
from project.strategy_dossier import build_strategy_dossier
from project.ui.views.research import (
    ResearchProjectView,
    ResearchRunView,
    StrategyCandidateView,
    get_research_page_view as _get_research_page_view,
)


@dataclass(frozen=True)
class ResearchPageView:
    projects: tuple[ResearchProjectView, ...]
    runs: tuple[ResearchRunView, ...]
    candidates: tuple[StrategyCandidateView, ...]
    strategy_dossier: dict[str, object] | None
    debug_payload: dict[str, object]


def get_research_page_view(repository: DataRepository) -> ResearchPageView:
    view = _get_research_page_view(repository)
    dossier = _latest_dossier(repository)
    return ResearchPageView(
        projects=view.projects,
        runs=view.runs,
        candidates=view.candidates,
        strategy_dossier=dossier,
        debug_payload={**view.debug_payload, "strategy_dossier": dossier},
    )


def _latest_dossier(repository: DataRepository) -> dict[str, object] | None:
    hypothesis_id = _latest_hypothesis_id(repository)
    return build_strategy_dossier(repository, hypothesis_id) if hypothesis_id else None


def _latest_hypothesis_id(repository: DataRepository) -> str | None:
    if (run := _latest_research_run(repository)) is not None:
        spec = _strategy_spec_for_run(repository, run.strategy_spec_id)
        if spec is not None:
            return spec.hypothesis_id
    backtest = _latest_backtest(repository)
    return backtest.hypothesis_id if backtest is not None else None


def _strategy_spec_for_run(repository: DataRepository, strategy_spec_id: str):
    for strategy_spec in repository.get_strategy_specs():
        if strategy_spec.strategy_spec_id == strategy_spec_id:
            return strategy_spec
    return None


def _latest_research_run(repository: DataRepository):
    return max(repository.get_research_runs(), key=_research_run_sort_key, default=None)


def _latest_backtest(repository: DataRepository):
    return max(repository.get_backtest_results(), key=_backtest_latest_sort_key, default=None)


def _research_run_sort_key(run) -> tuple[str, str, str]:
    return (run.started_at or run.completed_at or "", run.completed_at or "", run.research_run_id or "")


def _backtest_latest_sort_key(result) -> tuple[str, str, str, str, str]:
    return (
        result.start_timestamp or result.end_timestamp or "",
        result.end_timestamp or "",
        result.research_run_id or "",
        result.dataset_snapshot_id or "",
        result.hypothesis_id or "",
    )
