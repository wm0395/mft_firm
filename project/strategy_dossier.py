from __future__ import annotations

from typing import Any

from project.cli_utils import (
    hypothesis_definition,
    hypothesis_signal_types,
    registered_signal_types,
)
from project.common.models import StrategySpec, strategy_spec_missing_fields, strategy_spec_parameters
from project.data.repository import DataRepository
from project.hypotheses.catalog import validate_hypothesis_definition
from project.research_validation import (
    _latest_evidence_summary,
    _latest_snapshot_for_universe,
    tradeability_blockers,
)


def build_strategy_dossier(
    repository: DataRepository,
    hypothesis_id: str,
) -> dict[str, object] | None:
    return _strategy_dossier_payload(repository, hypothesis_id)


def _strategy_dossier_payload(
    repository: DataRepository,
    hypothesis_id: str,
) -> dict[str, object] | None:
    return _strategy_dossier_payload_data(repository, hypothesis_id)


def _strategy_dossier_payload_data(
    repository: DataRepository,
    hypothesis_id: str,
) -> dict[str, object] | None:
    return _strategy_dossier_payload_parts(repository, hypothesis_id)


def _strategy_dossier_payload_parts(
    repository: DataRepository,
    hypothesis_id: str,
) -> dict[str, object] | None:
    state = _strategy_dossier_state(repository, hypothesis_id)
    if state is None:
        return None
    (
        strategy_spec,
        latest_snapshot,
        latest_run,
        available_runs,
        available_backtests,
        best_backtest,
        latest_evidence,
        registered_signals,
        validation_errors,
        blockers,
        next_action,
        next_command,
        required_signals,
    ) = state
    return {
        **_strategy_dossier_core_payload(strategy_spec, latest_snapshot, blockers),
        **_strategy_dossier_detail_payload(
            repository,
            strategy_spec,
            latest_snapshot,
            latest_run,
            best_backtest,
            latest_evidence,
            required_signals,
            registered_signals,
            validation_errors,
            available_runs,
            available_backtests,
            next_action,
            next_command,
        ),
    }


def _strategy_dossier_state(
    repository: DataRepository,
    hypothesis_id: str,
) -> tuple[Any, ...] | None:
    strategy_spec = _latest_strategy_spec(repository, hypothesis_id)
    if strategy_spec is None:
        return None
    latest_snapshot = _latest_snapshot_for_universe(repository, strategy_spec.universe_id)
    available_runs = _available_research_runs(repository, strategy_spec.strategy_spec_id)
    latest_run = _latest_research_run(available_runs)
    available_backtests = _available_backtests(repository, strategy_spec)
    best_backtest = _best_backtest(repository, strategy_spec)
    latest_evidence = _latest_evidence_summary(repository, strategy_spec.strategy_spec_id, latest_snapshot.dataset_snapshot_id if latest_snapshot else None)
    registered_signals = registered_signal_types(repository) or ()
    validation_errors = _validation_errors(hypothesis_definition(repository, hypothesis_id), registered_signals, strategy_spec)
    blockers = tradeability_blockers(strategy_spec, latest_snapshot, latest_run, best_backtest, latest_evidence, validation_errors)
    next_action, next_command = _next_step(repository, strategy_spec, latest_snapshot)
    required_signals = hypothesis_signal_types(repository, hypothesis_id)
    return (
        strategy_spec,
        latest_snapshot,
        latest_run,
        available_runs,
        available_backtests,
        best_backtest,
        latest_evidence,
        registered_signals,
        validation_errors,
        blockers,
        next_action,
        next_command,
        required_signals,
    )


def _strategy_dossier_core_payload(
    strategy_spec: StrategySpec,
    latest_snapshot,
    blockers,
) -> dict[str, object]:
    return {
        "hypothesis_id": strategy_spec.hypothesis_id,
        "strategy_spec_id": strategy_spec.strategy_spec_id,
        "strategy_name": strategy_spec.name,
        "activation_status": "eligible" if not blockers else "research_only",
        "tradeability_status": "eligible" if not blockers else "blocked",
        "tradeability_blockers": blockers,
        "thesis": _parameter_text(strategy_spec, "thesis"),
        "bar_timeframe": _parameter_text(strategy_spec, "bar_timeframe"),
        "holding_horizon": strategy_spec_parameters(strategy_spec).get("holding_horizon"),
        "required_signals": tuple(
            str(signal)
            for signal in strategy_spec_parameters(strategy_spec).get("required_signals", ())
        ),
        "expected_failure_modes": _string_sequence(strategy_spec, "expected_failure_modes"),
        "dataset_snapshot_id": latest_snapshot.dataset_snapshot_id if latest_snapshot else None,
    }


def _strategy_dossier_detail_payload(
    repository: DataRepository,
    strategy_spec: StrategySpec,
    latest_snapshot,
    latest_run,
    best_backtest,
    latest_evidence,
    required_signals: tuple[str, ...],
    registered_signals: tuple[str, ...],
    validation_errors: tuple[str, ...],
    available_runs,
    available_backtests,
    next_action: str | None,
    next_command: str | None,
) -> dict[str, object]:
    return {
        "dataset_snapshot": _dataset_snapshot_payload(latest_snapshot),
        "provenance": _dataset_provenance_payload(repository, latest_snapshot),
        "research_run_id": latest_run.research_run_id if latest_run else None,
        "latest_research_run": None if latest_run is None else latest_run.__dict__,
        "best_backtest": _backtest_payload(best_backtest),
        "evidence_summary": _evidence_payload(latest_evidence),
        "signal_registration_status": _signal_registration_status(
            required_signals,
            registered_signals,
        ),
        "validation_errors": validation_errors,
        "available_research_runs": tuple(run.__dict__ for run in available_runs),
        "available_backtests": tuple(
            _backtest_payload(result) for result in available_backtests
        ),
        "next_action": next_action,
        "next_command": next_command,
        "strategy_spec": _strategy_spec_payload(strategy_spec),
    }


def _latest_strategy_spec(repository: DataRepository, hypothesis_id: str) -> StrategySpec | None:
    matches = tuple(
        spec for spec in repository.get_strategy_specs() if spec.hypothesis_id == hypothesis_id
    )
    return max(
        matches,
        key=lambda spec: (spec.hypothesis_version, spec.strategy_spec_id),
        default=None,
    )


def _available_research_runs(
    repository: DataRepository,
    strategy_spec_id: str,
):
    return tuple(
        sorted(
            (
                run
                for run in repository.get_research_runs()
                if run.strategy_spec_id == strategy_spec_id
            ),
            key=lambda run: (
                run.started_at or run.completed_at or "",
                run.completed_at or "",
                run.research_run_id or "",
            ),
        )
    )


def _latest_research_run(research_runs):
    return max(
        research_runs,
        key=lambda run: (
            run.started_at or run.completed_at or "",
            run.completed_at or "",
            run.research_run_id or "",
        ),
        default=None,
    )


def _available_backtests(repository: DataRepository, strategy_spec: StrategySpec):
    matches = tuple(
        result
        for result in repository.get_backtest_results()
        if result.strategy_spec_id == strategy_spec.strategy_spec_id
    )
    if matches:
        return tuple(
            sorted(
                matches,
                key=lambda result: (
                    result.start_timestamp or result.end_timestamp or "",
                    result.end_timestamp or "",
                    result.research_run_id or "",
                    result.dataset_snapshot_id or "",
                    result.hypothesis_id or "",
                ),
            )
        )
    fallback = tuple(
        result
        for result in repository.get_backtest_results()
        if result.hypothesis_id == strategy_spec.hypothesis_id
    )
    return tuple(
        sorted(
            fallback,
            key=lambda result: (
                result.start_timestamp or result.end_timestamp or "",
                result.end_timestamp or "",
                result.research_run_id or "",
                result.dataset_snapshot_id or "",
                result.hypothesis_id or "",
            ),
        )
    )


def _best_backtest(repository: DataRepository, strategy_spec: StrategySpec):
    by_spec = tuple(
        result
        for result in repository.get_backtest_results()
        if result.strategy_spec_id == strategy_spec.strategy_spec_id
    )
    matches = by_spec or tuple(
        result
        for result in repository.get_backtest_results()
        if result.hypothesis_id == strategy_spec.hypothesis_id
    )
    return max(
        matches,
        key=lambda result: (
            result.total_return_pct,
            result.sharpe_ratio,
            result.total_pnl,
            result.winning_trades,
            result.total_trades,
            result.research_run_id or "",
            result.dataset_snapshot_id or "",
        ),
        default=None,
    )


def _signal_registration_status(
    required_signals: tuple[str, ...],
    registered_signals: tuple[str, ...],
) -> tuple[dict[str, Any], ...]:
    return tuple(
        {"signal_type": signal_type, "registered": signal_type in registered_signals}
        for signal_type in required_signals
    )


def _validation_errors(
    definition,
    registered_signals: tuple[str, ...],
    strategy_spec: StrategySpec,
) -> tuple[str, ...]:
    if definition is None:
        return ("missing_hypothesis_definition",)
    return validate_hypothesis_definition(definition, registered_signals, strategy_spec)


def _next_step(
    repository: DataRepository,
    strategy_spec: StrategySpec,
    latest_snapshot,
) -> tuple[str, str]:
    if latest_snapshot is None:
        return (
            "Create a dataset snapshot, then run research.",
            f"mft research run {strategy_spec.hypothesis_id} RELIANCE --snapshot latest",
        )
    symbol = _snapshot_symbol(repository, latest_snapshot)
    return (
        "Run research.",
        f"mft research run {strategy_spec.hypothesis_id} {symbol} --snapshot latest",
    )


def _snapshot_symbol(repository: DataRepository, snapshot) -> str:
    assets = {asset.asset_id: asset.symbol for asset in repository.list_assets()}
    for asset_id in snapshot.asset_ids:
        if asset_id in assets:
            return assets[asset_id]
    return "RELIANCE"


def _strategy_spec_payload(strategy_spec: StrategySpec) -> dict[str, Any]:
    parameters = strategy_spec_parameters(strategy_spec)
    return {
        "strategy_spec_id": strategy_spec.strategy_spec_id,
        "universe_id": strategy_spec.universe_id,
        "hypothesis_id": strategy_spec.hypothesis_id,
        "hypothesis_version": strategy_spec.hypothesis_version,
        "name": strategy_spec.name,
        "parameters": parameters,
        "missing_fields": strategy_spec_missing_fields(strategy_spec),
    }


def _dataset_snapshot_payload(snapshot) -> dict[str, Any] | None:
    if snapshot is None:
        return None
    return {
        "dataset_snapshot_id": snapshot.dataset_snapshot_id,
        "universe_id": snapshot.universe_id,
        "captured_at": snapshot.captured_at,
        "data_start": snapshot.data_start,
        "data_end": snapshot.data_end,
        "asset_ids": snapshot.asset_ids,
    }


def _dataset_provenance_payload(
    repository: DataRepository,
    snapshot,
) -> dict[str, Any] | None:
    if snapshot is None:
        return None
    return repository.get_dataset_provenance(snapshot, "1d").__dict__


def _backtest_payload(backtest) -> dict[str, Any] | None:
    if backtest is None:
        return None
    payload = backtest.__dict__.copy()
    payload["metrics"] = backtest.performance_metrics()
    return payload


def _evidence_payload(summary) -> dict[str, Any] | None:
    if summary is None:
        return None
    return {
        "evidence_summary_id": summary.evidence_summary_id,
        "strategy_spec_id": summary.strategy_spec_id,
        "research_run_id": summary.research_run_id,
        "dataset_snapshot_id": summary.dataset_snapshot_id,
        "summary": summary.summary,
        "metrics": dict(summary.metrics),
        "created_at": summary.created_at,
    }


def _parameter_text(strategy_spec: StrategySpec, name: str) -> str | None:
    value = strategy_spec_parameters(strategy_spec).get(name)
    return None if value is None else str(value)


def _string_sequence(strategy_spec: StrategySpec, name: str) -> tuple[str, ...]:
    return tuple(
        str(signal)
        for signal in strategy_spec_parameters(strategy_spec).get(name, ())
    )
