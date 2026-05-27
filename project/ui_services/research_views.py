from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime

from project.backtesting.models import BacktestConfig, BacktestResult
from project.backtesting.research_runner import (
    StrategyResearchRunResult,
    run_strategy_research,
)
from project.cli_operator import _workflow_status_payload
from project.common.models import (
    Asset,
    DatasetSnapshot,
    HypothesisDefinition,
    ResearchRun,
    StrategySpec,
)
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
    workflow_context: dict[str, object]
    launch: ResearchLaunchView
    strategy_dossier: dict[str, object] | None
    debug_payload: dict[str, object]


@dataclass(frozen=True)
class ResearchAssetView:
    symbol: str
    name: str
    market: str


@dataclass(frozen=True)
class ResearchSnapshotView:
    dataset_snapshot_id: str
    captured_at: str
    data_start: str
    data_end: str
    asset_count: int


@dataclass(frozen=True)
class ResearchHypothesisView:
    hypothesis_id: str
    name: str
    status: str
    version: int


@dataclass(frozen=True)
class ResearchLaunchView:
    assets: tuple[ResearchAssetView, ...]
    snapshots: tuple[ResearchSnapshotView, ...]
    hypotheses: tuple[ResearchHypothesisView, ...]
    default_asset_symbol: str | None
    default_dataset_snapshot_id: str | None
    default_hypothesis_id: str | None
    default_start_date: str
    default_end_date: str
    workflow_command: str
    workflow_note: str


def get_research_page_view(repository: DataRepository) -> ResearchPageView:
    view = _get_research_page_view(repository)
    workflow_context = _workflow_status_payload(repository)
    dossier = _latest_dossier(repository)
    launch = _launch_view(repository, workflow_context, dossier)
    return ResearchPageView(
        projects=view.projects,
        runs=view.runs,
        candidates=view.candidates,
        workflow_context=workflow_context,
        launch=launch,
        strategy_dossier=dossier,
        debug_payload={
            **view.debug_payload,
            "strategy_dossier": dossier,
            "workflow_context": workflow_context,
            "launch": asdict(launch),
        },
    )


def _launch_view(
    repository: DataRepository,
    workflow_context: dict[str, object],
    dossier: dict[str, object] | None,
) -> ResearchLaunchView:
    assets = tuple(repository.list_assets())
    snapshots = tuple(repository.get_dataset_snapshots())
    hypotheses = _launch_hypotheses(repository.get_hypotheses(), dossier)
    default_snapshot = _default_snapshot(snapshots)
    default_hypothesis = _default_hypothesis(hypotheses, dossier)
    default_asset = _default_asset_symbol(assets, default_snapshot)
    start_date, end_date = _default_dates(default_snapshot)
    return ResearchLaunchView(
        assets=_research_asset_views(assets),
        snapshots=_research_snapshot_views(snapshots),
        hypotheses=_research_hypothesis_views(hypotheses),
        default_asset_symbol=default_asset,
        default_dataset_snapshot_id=default_snapshot.dataset_snapshot_id
        if default_snapshot
        else None,
        default_hypothesis_id=default_hypothesis.hypothesis_id
        if default_hypothesis
        else None,
        default_start_date=start_date,
        default_end_date=end_date,
        workflow_command=str(workflow_context.get("next_recommended_command", "")),
        workflow_note=_workflow_note(workflow_context),
    )


def _research_asset_views(
    assets: tuple[Asset, ...],
) -> tuple[ResearchAssetView, ...]:
    return tuple(
        ResearchAssetView(asset.symbol, asset.name, asset.market) for asset in assets
    )


def _research_snapshot_views(
    snapshots: tuple[DatasetSnapshot, ...],
) -> tuple[ResearchSnapshotView, ...]:
    return tuple(
        ResearchSnapshotView(
            snapshot.dataset_snapshot_id,
            snapshot.captured_at,
            snapshot.data_start,
            snapshot.data_end,
            len(snapshot.asset_ids),
        )
        for snapshot in snapshots
    )


def _research_hypothesis_views(
    hypotheses: tuple[HypothesisDefinition, ...],
) -> tuple[ResearchHypothesisView, ...]:
    return tuple(
        ResearchHypothesisView(
            hypothesis.hypothesis_id,
            hypothesis.name,
            hypothesis.status,
            hypothesis.version,
        )
        for hypothesis in hypotheses
    )


def _launch_hypotheses(
    hypotheses: tuple[HypothesisDefinition, ...],
    dossier: dict[str, object] | None,
) -> tuple[HypothesisDefinition, ...]:
    actionable = tuple(
        hypothesis
        for hypothesis in hypotheses
        if hypothesis.status in {"active", "testing", "draft"}
    )
    if actionable:
        return actionable
    if dossier is not None:
        hypothesis_id = str(dossier.get("hypothesis_id", ""))
        for hypothesis in hypotheses:
            if hypothesis.hypothesis_id == hypothesis_id:
                return (hypothesis,)
    return hypotheses


def _default_snapshot(snapshots: tuple[DatasetSnapshot, ...]) -> DatasetSnapshot | None:
    return max(snapshots, key=_snapshot_sort_key, default=None)


def _default_hypothesis(
    hypotheses: tuple[HypothesisDefinition, ...],
    dossier: dict[str, object] | None,
) -> HypothesisDefinition | None:
    if dossier is not None:
        hypothesis_id = str(dossier.get("hypothesis_id", ""))
        for hypothesis in hypotheses:
            if hypothesis.hypothesis_id == hypothesis_id:
                return hypothesis
    for hypothesis in hypotheses:
        if hypothesis.hypothesis_id == "hypothesis:rsi_mean_reversion":
            return hypothesis
    return hypotheses[0] if hypotheses else None


def _default_asset_symbol(
    assets: tuple[Asset, ...],
    snapshot: DatasetSnapshot | None,
) -> str | None:
    if not assets:
        return None
    if snapshot is None:
        return assets[0].symbol
    snapshot_asset_ids = set(snapshot.asset_ids)
    for asset in assets:
        if asset.asset_id in snapshot_asset_ids:
            return asset.symbol
    return assets[0].symbol


def _default_dates(snapshot: DatasetSnapshot | None) -> tuple[str, str]:
    if snapshot is None:
        today = datetime.now(UTC).date().isoformat()
        return today, today
    return _date_only(snapshot.data_start), _date_only(snapshot.data_end)


def _date_only(value: str) -> str:
    return value[:10]


def _workflow_note(workflow_context: dict[str, object]) -> str:
    command = str(workflow_context.get("next_recommended_command", ""))
    if not command:
        return "Mission Control context unavailable."
    return f"Mission Control next action: {command}"


def _snapshot_sort_key(snapshot: DatasetSnapshot) -> tuple[str, str]:
    return (snapshot.captured_at, snapshot.dataset_snapshot_id)


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


def _strategy_spec_for_run(
    repository: DataRepository,
    strategy_spec_id: str,
) -> StrategySpec | None:
    for strategy_spec in repository.get_strategy_specs():
        if strategy_spec.strategy_spec_id == strategy_spec_id:
            return strategy_spec
    return None


def _latest_research_run(repository: DataRepository) -> ResearchRun | None:
    return max(repository.get_research_runs(), key=_research_run_sort_key, default=None)


def _latest_backtest(repository: DataRepository) -> BacktestResult | None:
    return max(
        repository.get_backtest_results(), key=_backtest_latest_sort_key, default=None
    )


def launch_research_run(
    repository: DataRepository,
    snapshot_id: str,
    hypothesis_id: str,
    asset_symbol: str,
    start_date: str,
    end_date: str,
    *,
    include_testing: bool,
    include_draft: bool,
) -> StrategyResearchRunResult:
    return run_strategy_research(
        repository,
        snapshot_id,
        hypothesis_id,
        asset_symbol,
        start_date,
        end_date,
        BacktestConfig(),
        include_testing=include_testing,
        include_draft=include_draft,
    )


def _research_run_sort_key(run: ResearchRun) -> tuple[str, str, str]:
    return (
        run.started_at or run.completed_at or "",
        run.completed_at or "",
        run.research_run_id or "",
    )


def _backtest_latest_sort_key(result: BacktestResult) -> tuple[str, str, str, str, str]:
    return (
        result.start_timestamp or result.end_timestamp or "",
        result.end_timestamp or "",
        result.research_run_id or "",
        result.dataset_snapshot_id or "",
        result.hypothesis_id or "",
    )
