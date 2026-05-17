from __future__ import annotations

from dataclasses import asdict

from project.backtesting.models import BacktestConfig
from project.backtesting.models import BacktestResult
from project.backtesting.research_runner import (
    run_strategy_research as run_strategy_research_engine,
)
from project.cli_commands import _ensure_default_hypothesis_catalog, _promote_hypothesis
from project.cli_support import emit_error, emit_response
from project.cli_utils import (
    hypothesis_definition,
    hypothesis_definitions,
    hypothesis_signal_types,
    registered_signal_types,
)
from project.common.models import DatasetSnapshot, ResearchRun, StrategySpec
from project.data.repository import DataRepository
from project.hypotheses.catalog import hypothesis_summary, validate_hypothesis_definition


def run_strategy_research(
    repository: DataRepository,
    dataset_snapshot_id: str,
    hypothesis_id: str,
    asset_symbol: str,
    start_date: str,
    end_date: str,
    slippage_bps: float,
    position_size: float,
    exit_horizon: int | None,
    include_testing: bool = False,
    include_draft: bool = False,
) -> int:
    _ensure_default_hypothesis_catalog(repository)
    config = BacktestConfig(
        slippage_bps=slippage_bps,
        position_size=position_size,
        exit_horizon=exit_horizon,
    )
    try:
        result = run_strategy_research_engine(
            repository,
            dataset_snapshot_id,
            hypothesis_id,
            asset_symbol.upper(),
            start_date,
            end_date,
            config,
            include_testing=include_testing,
            include_draft=include_draft,
        )
    except (RuntimeError, ValueError) as error:
        emit_error("run-strategy-research", error)
        return 1
    emit_response("run-strategy-research", asdict(result))
    return 0


def list_hypotheses(repository: DataRepository) -> int:
    emit_response(
        "list-hypotheses",
        [hypothesis_summary(definition) for definition in hypothesis_definitions(repository)],
    )
    return 0


def show_hypothesis(repository: DataRepository, hypothesis_id: str) -> int:
    definition = hypothesis_definition(repository, hypothesis_id)
    if definition is None:
        emit_error("show-hypothesis", f"Hypothesis {hypothesis_id} not found")
        return 1
    payload = hypothesis_summary(definition)
    payload["signal_map"] = [
        {"signal_type": signal_type, "role": "required"}
        for signal_type in hypothesis_signal_types(repository, hypothesis_id)
    ]
    payload["strategy_spec"] = (
        asdict(strategy_spec)
        if (
            strategy_spec := repository.get_strategy_spec(
                hypothesis_id, definition.version
            )
        )
        else None
    )
    emit_response("show-hypothesis", payload)
    return 0


def validate_hypothesis(repository: DataRepository, hypothesis_id: str) -> int:
    definition = hypothesis_definition(repository, hypothesis_id)
    if definition is None:
        emit_error("validate-hypothesis", f"Hypothesis {hypothesis_id} not found")
        return 1
    errors = validate_hypothesis_definition(
        definition,
        registered_signal_types(repository),
        repository.get_strategy_spec(hypothesis_id, definition.version),
    )
    payload = {
        "hypothesis_id": definition.hypothesis_id,
        "version": definition.version,
        "valid": not errors,
        "reasons": list(errors),
        "status": definition.status,
    }
    emit_response("validate-hypothesis", payload)
    return 0


def hypothesis_readiness(repository: DataRepository, hypothesis_id: str) -> int:
    definition = hypothesis_definition(repository, hypothesis_id)
    if definition is None:
        emit_error("hypothesis-readiness", f"Hypothesis {hypothesis_id} not found")
        return 1
    strategy_spec = repository.get_strategy_spec(hypothesis_id, definition.version)
    required_signals = hypothesis_signal_types(repository, hypothesis_id)
    registered_signals = registered_signal_types(repository) or ()
    signal_status = _signal_registration_status(required_signals, registered_signals)
    research_runs = _readiness_research_runs(repository, strategy_spec)
    backtests = _readiness_backtests(repository, hypothesis_id)
    snapshots = _readiness_snapshots(repository, strategy_spec)
    validation_errors = validate_hypothesis_definition(
        definition,
        registered_signals,
        strategy_spec,
    )
    missing_evidence = _readiness_missing_evidence(
        strategy_spec,
        signal_status,
        research_runs,
        backtests,
        snapshots,
        validation_errors,
    )
    result = {
        "hypothesis_id": definition.hypothesis_id,
        "name": definition.name,
        "status": definition.status,
        "version": definition.version,
        "required_signals": list(required_signals),
        "signal_registration_status": signal_status,
        "strategy_spec_id": strategy_spec.strategy_spec_id if strategy_spec else None,
        "dataset_snapshot_ids": [snapshot.dataset_snapshot_id for snapshot in snapshots],
        "available_research_runs": [run.__dict__ for run in research_runs],
        "available_backtests": [backtest.__dict__ for backtest in backtests],
        "missing_evidence": missing_evidence,
        "validation_errors": list(validation_errors),
        "readiness": "ready" if not missing_evidence else "not_ready",
    }
    emit_response(
        "hypothesis-readiness", result, status="ok" if not missing_evidence else "warn"
    )
    return 0


def promote_hypothesis(
    repository: DataRepository,
    hypothesis_id: str,
    to_status: str,
    force: bool = False,
) -> int:
    _ensure_default_hypothesis_catalog(repository)
    current = hypothesis_definition(repository, hypothesis_id)
    try:
        promoted = _promote_hypothesis(repository, current, to_status, force)
    except ValueError as error:
        emit_error("promote-hypothesis", error)
        return 1
    emit_response(
        "promote-hypothesis",
        {
            "hypothesis_id": promoted.hypothesis_id,
            "previous_status": current.status if current else None,
            "new_status": promoted.status,
        },
    )
    return 0


def _signal_registration_status(
    required_signals: tuple[str, ...],
    registered_signals: tuple[str, ...],
) -> list[dict[str, object]]:
    return [
        {"signal_type": signal_type, "registered": signal_type in registered_signals}
        for signal_type in required_signals
    ]


def _readiness_research_runs(
    repository: DataRepository,
    strategy_spec: StrategySpec | None,
) -> tuple[ResearchRun, ...]:
    if strategy_spec is None:
        return ()
    return tuple(
        run
        for run in repository.get_research_runs()
        if run.strategy_spec_id == strategy_spec.strategy_spec_id
    )


def _readiness_backtests(
    repository: DataRepository,
    hypothesis_id: str,
) -> tuple[BacktestResult, ...]:
    return tuple(
        result
        for result in repository.get_backtest_results()
        if result.hypothesis_id == hypothesis_id
    )


def _readiness_snapshots(
    repository: DataRepository,
    strategy_spec: StrategySpec | None,
) -> tuple[DatasetSnapshot, ...]:
    if strategy_spec is None:
        return ()
    return tuple(
        snapshot
        for snapshot in repository.get_dataset_snapshots()
        if snapshot.universe_id == strategy_spec.universe_id
    )


def _readiness_missing_evidence(
    strategy_spec: StrategySpec | None,
    signal_status: list[dict[str, object]],
    research_runs: tuple[ResearchRun, ...],
    backtests: tuple[BacktestResult, ...],
    snapshots: tuple[DatasetSnapshot, ...],
    validation_errors: tuple[str, ...],
) -> list[str]:
    missing = list(validation_errors)
    if strategy_spec is None:
        missing.append("missing_strategy_spec")
    if not all(item["registered"] for item in signal_status):
        missing.append("unregistered_required_signals")
    if not research_runs:
        missing.append("missing_research_runs")
    if not backtests:
        missing.append("missing_backtests")
    if not snapshots:
        missing.append("missing_dataset_snapshots")
    return list(dict.fromkeys(missing))
