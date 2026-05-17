from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4
import re

from project.backtesting.engine import BacktestEngine
from project.backtesting.models import BacktestConfig, BacktestResult
from project.common.models import (
    Asset,
    DatasetSnapshot,
    ResearchRun,
    StrategyEvidenceSummary,
    StrategySpec,
    strategy_spec_parameters,
    utc_now_iso,
)
from project.data.repository import DataRepository
from project.hypotheses.catalog import get_hypothesis, get_hypothesis_implementation
from project.research.config import ResearchConfig
from project.research.runner import ResearchRunRequest, ResearchRunResult, run_research as run_parameter_grid_research_core


@dataclass(frozen=True)
class StrategyResearchRunResult:
    research_run_id: str
    strategy_spec_id: str
    dataset_snapshot_id: str
    hypothesis_id: str
    asset_id: str
    metrics: dict[str, Any]
    status: str


def run_strategy_research(
    repository: DataRepository,
    dataset_snapshot_id: str,
    hypothesis_id: str,
    asset_symbol: str,
    start_date: str,
    end_date: str,
    config: BacktestConfig | None = None,
    include_testing: bool = False,
    include_draft: bool = False,
) -> StrategyResearchRunResult:
    config_value = config or BacktestConfig()
    snapshot = _require_snapshot(repository, dataset_snapshot_id)
    asset = _require_asset(repository, asset_symbol)
    _ensure_asset_in_snapshot(asset, snapshot)
    start_timestamp, end_timestamp = _normalize_range(start_date, end_date)
    _ensure_range_within_snapshot(start_timestamp, end_timestamp, snapshot)
    hypothesis = _require_hypothesis(hypothesis_id, include_testing, include_draft, repository)
    strategy_spec = _build_strategy_spec(repository, hypothesis, snapshot)
    repository.persist_research_artifact(strategy_spec)
    research_run = _start_research_run(
        strategy_spec.strategy_spec_id,
        hypothesis.definition.hypothesis_id,
        snapshot.dataset_snapshot_id,
        asset.asset_id,
        start_date,
        end_date,
    )
    repository.persist_research_artifact(research_run)
    try:
        return _complete_research_run(
            repository,
            research_run,
            strategy_spec,
            asset,
            hypothesis.definition.hypothesis_id,
            hypothesis.definition.version,
            start_timestamp,
            end_timestamp,
            config_value,
        )
    except Exception as error:
        _fail_research_run(repository, research_run, error)
        raise RuntimeError(
            f"strategy research run {research_run.research_run_id} failed: {error}"
        ) from error


def run_parameter_grid_research(
    repository: DataRepository,
    config: ResearchConfig,
    output_dir: str | Path,
) -> ResearchRunResult:
    return run_parameter_grid_research_core(
        repository,
        ResearchRunRequest(config=config, output_dir=Path(output_dir)),
    )


def _complete_research_run(
    repository: DataRepository,
    research_run: ResearchRun,
    strategy_spec: StrategySpec,
    asset: Asset,
    hypothesis_id: str,
    hypothesis_version: int,
    start_timestamp: datetime,
    end_timestamp: datetime,
    config: BacktestConfig,
) -> StrategyResearchRunResult:
    engine = BacktestEngine(repository)
    backtest_result = engine.run(
        hypothesis_id,
        asset.symbol,
        start_timestamp,
        end_timestamp,
        config,
    )
    enriched_result = _backtest_result_with_context(
        backtest_result,
        strategy_spec.strategy_spec_id,
        research_run.research_run_id,
        research_run.dataset_snapshot_id,
        hypothesis_version,
        start_timestamp,
        end_timestamp,
        config,
    )
    summary = _evidence_summary(enriched_result, strategy_spec, asset, research_run)
    completed_run = replace(
        research_run,
        completed_at=utc_now_iso(),
        status="completed",
        notes=_success_notes(asset, enriched_result),
    )
    with repository.transaction():
        repository.persist_backtest_result(enriched_result)
        repository.persist_research_artifact(summary)
        repository.persist_research_artifact(completed_run)
    return StrategyResearchRunResult(
        research_run_id=research_run.research_run_id,
        strategy_spec_id=strategy_spec.strategy_spec_id,
        dataset_snapshot_id=research_run.dataset_snapshot_id,
        hypothesis_id=hypothesis_id,
        asset_id=asset.asset_id,
        metrics=enriched_result.performance_metrics(),
        status="completed",
    )


def _backtest_result_with_context(
    result: BacktestResult,
    strategy_spec_id: str,
    research_run_id: str,
    dataset_snapshot_id: str,
    hypothesis_version: int,
    start_timestamp: datetime,
    end_timestamp: datetime,
    config: BacktestConfig,
) -> BacktestResult:
    return replace(
        result,
        hypothesis_version=hypothesis_version,
        strategy_spec_id=strategy_spec_id,
        research_run_id=research_run_id,
        dataset_snapshot_id=dataset_snapshot_id,
        start_timestamp=_iso_timestamp(start_timestamp),
        end_timestamp=_iso_timestamp(end_timestamp),
        parameters=_config_parameters(config),
    )


def _evidence_summary(
    result: BacktestResult,
    strategy_spec: StrategySpec,
    asset: Asset,
    research_run: ResearchRun,
) -> StrategyEvidenceSummary:
    summary = (
        f"{strategy_spec.hypothesis_id} on {research_run.dataset_snapshot_id} "
        f"for {asset.symbol} completed with {result.total_trades} trades "
        f"and {result.win_rate:.2%} win rate."
    )
    return StrategyEvidenceSummary(
        evidence_summary_id=f"strategy_evidence_summary:{research_run.research_run_id}",
        strategy_spec_id=strategy_spec.strategy_spec_id,
        research_run_id=research_run.research_run_id,
        dataset_snapshot_id=research_run.dataset_snapshot_id,
        summary=summary,
        metrics=tuple(sorted(result.performance_metrics().items())),
        created_at=utc_now_iso(),
    )


def _start_research_run(
    strategy_spec_id: str,
    hypothesis_id: str,
    dataset_snapshot_id: str,
    asset_id: str,
    start_date: str,
    end_date: str,
) -> ResearchRun:
    research_run_id = _research_run_id(hypothesis_id, dataset_snapshot_id)
    notes = (
        f"Running {hypothesis_id} strategy research for {asset_id} "
        f"from {start_date} to {end_date}."
    )
    return ResearchRun(
        research_run_id=research_run_id,
        strategy_spec_id=strategy_spec_id,
        dataset_snapshot_id=dataset_snapshot_id,
        started_at=utc_now_iso(),
        completed_at=None,
        status="running",
        notes=notes,
    )


def _fail_research_run(
    repository: DataRepository,
    research_run: ResearchRun,
    error: Exception,
) -> None:
    failed_run = replace(
        research_run,
        completed_at=utc_now_iso(),
        status="failed",
        notes=str(error),
    )
    repository.persist_research_artifact(failed_run)


def _build_strategy_spec(
    repository: DataRepository,
    hypothesis: Any,
    snapshot: DatasetSnapshot,
) -> StrategySpec:
    hypothesis_id = getattr(hypothesis.definition, "hypothesis_id")
    hypothesis_version = getattr(hypothesis.definition, "version")
    existing = _find_strategy_spec(
        repository,
        hypothesis_id,
        hypothesis_version,
        snapshot.universe_id,
    )
    template = hypothesis.strategy_spec(snapshot.universe_id)
    parameters = _strategy_spec_parameters(template, snapshot)
    strategy_spec_id = existing.strategy_spec_id if existing else _strategy_spec_id(
        hypothesis_id,
        snapshot.universe_id,
        hypothesis_version,
    )
    return StrategySpec(
        strategy_spec_id=strategy_spec_id,
        universe_id=snapshot.universe_id,
        hypothesis_id=hypothesis_id,
        hypothesis_version=hypothesis_version,
        name=f"{getattr(hypothesis.definition, 'name')} on {snapshot.universe_id}",
        parameters=parameters,
    )


def _strategy_spec_parameters(template: StrategySpec, snapshot: DatasetSnapshot) -> tuple[tuple[str, object], ...]:
    parameters = strategy_spec_parameters(template)
    parameters["intended_universe"] = snapshot.asset_ids
    return tuple(sorted(parameters.items()))


def _find_strategy_spec(
    repository: DataRepository,
    hypothesis_id: str,
    hypothesis_version: int,
    universe_id: str,
) -> StrategySpec | None:
    for strategy_spec in repository.get_strategy_specs():
        if strategy_spec.hypothesis_id != hypothesis_id:
            continue
        if strategy_spec.hypothesis_version != hypothesis_version:
            continue
        if strategy_spec.universe_id == universe_id:
            return strategy_spec
    return None


def _require_snapshot(repository: DataRepository, dataset_snapshot_id: str) -> DatasetSnapshot:
    for snapshot in repository.get_dataset_snapshots():
        if snapshot.dataset_snapshot_id == dataset_snapshot_id:
            return snapshot
    raise ValueError(f"dataset snapshot not found: {dataset_snapshot_id}")


def _require_asset(repository: DataRepository, asset_symbol: str) -> Asset:
    for asset in repository.list_assets():
        if asset.symbol == asset_symbol.upper():
            return asset
    raise ValueError(f"asset not found for symbol: {asset_symbol}")


def _require_hypothesis(
    hypothesis_id: str,
    include_testing: bool,
    include_draft: bool,
    repository: DataRepository,
) -> Any:
    definition = repository.get_hypothesis(hypothesis_id) or get_hypothesis(hypothesis_id)
    if definition is None:
        raise ValueError(f"unsupported hypothesis: {hypothesis_id}")
    if definition.status not in _allowed_statuses(include_testing, include_draft):
        raise ValueError(
            f"hypothesis {hypothesis_id} is {definition.status} and cannot be evaluated"
        )
    hypothesis = get_hypothesis_implementation(hypothesis_id)
    if hypothesis is None:
        raise ValueError(f"unsupported hypothesis: {hypothesis_id}")
    return hypothesis


def _ensure_asset_in_snapshot(asset: Asset, snapshot: DatasetSnapshot) -> None:
    if asset.asset_id not in snapshot.asset_ids:
        raise ValueError(
            f"asset {asset.symbol} is not included in dataset snapshot {snapshot.dataset_snapshot_id}"
        )


def _ensure_range_within_snapshot(
    start_timestamp: datetime,
    end_timestamp: datetime,
    snapshot: DatasetSnapshot,
) -> None:
    snapshot_start = _parse_timestamp(snapshot.data_start)
    snapshot_end = _parse_timestamp(snapshot.data_end)
    if start_timestamp < snapshot_start or end_timestamp > snapshot_end:
        raise ValueError(
            "requested date range is outside dataset snapshot range "
            f"{snapshot.data_start} to {snapshot.data_end}"
        )


def _normalize_range(start_date: str, end_date: str) -> tuple[datetime, datetime]:
    start_timestamp = _parse_day_bound(start_date, end=False)
    end_timestamp = _parse_day_bound(end_date, end=True)
    if end_timestamp < start_timestamp:
        raise ValueError("end-date must not be earlier than start-date")
    return start_timestamp, end_timestamp


def _parse_day_bound(value: str, end: bool) -> datetime:
    suffix = "23:59:59" if end else "00:00:00"
    return _parse_timestamp(f"{value}T{suffix}+00:00")


def _parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


def _iso_timestamp(value: datetime) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat()


def _strategy_spec_id(hypothesis_id: str, universe_id: str, version: int) -> str:
    return f"strategy_spec:{_slugify(hypothesis_id)}:{_slugify(universe_id)}:v{version}"


def _research_run_id(hypothesis_id: str, dataset_snapshot_id: str) -> str:
    return (
        f"research_run:{_slugify(hypothesis_id)}:{_slugify(dataset_snapshot_id)}:{uuid4().hex[:8]}"
    )


def _config_parameters(config: BacktestConfig) -> tuple[tuple[str, object], ...]:
    return tuple(
        sorted(
            {
                "slippage_bps": config.slippage_bps,
                "position_size": config.position_size,
                "exit_horizon": config.exit_horizon,
            }.items()
        )
    )


def _success_notes(asset: Asset, result: BacktestResult) -> str:
    return (
        f"Completed strategy research for {asset.symbol} with {result.total_trades} "
        f"trades on {result.dataset_snapshot_id}."
    )


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.strip().lower())
    return slug.strip("_") or "item"


def _allowed_statuses(include_testing: bool, include_draft: bool) -> set[str]:
    allowed = {"active"}
    if include_testing:
        allowed.add("testing")
    if include_draft:
        allowed.add("draft")
    return allowed
