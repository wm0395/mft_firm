from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from project.cli_commands import _promote_hypothesis
from project.cli_utils import (
    hypothesis_definition,
    hypothesis_definitions,
    hypothesis_signal_types,
    registered_signal_types,
)
from project.cli_operator import _schema_initialized
from project.cli.context import CLIContext, open_repository
from project.cli.errors import CliError, CommandOutcome
from project.hypotheses.catalog import hypothesis_summary, validate_hypothesis_definition


def list_hypotheses(context: CLIContext) -> CommandOutcome:
    definitions = _load_definitions(context.database)
    payload = {"hypotheses": [hypothesis_summary(definition) for definition in definitions]}
    return CommandOutcome(payload, status="ok")


def check(context: CLIContext, hypothesis_id: str) -> CommandOutcome:
    definition = _load_definition(context.database, hypothesis_id)
    payload, missing_evidence = _build_readiness_payload(
        context.database,
        hypothesis_id,
        definition,
    )
    return CommandOutcome(payload, status="ok" if not missing_evidence else "warn")


def validate(context: CLIContext, hypothesis_id: str) -> CommandOutcome:
    definition = _load_definition(context.database, hypothesis_id)
    strategy_spec: Any = None
    registered_signals: tuple[str, ...] = ()
    if context.database.exists():
        with open_repository(context.database, read_only=True) as repository:
            if _schema_initialized(repository):
                strategy_spec = _strategy_spec(repository, definition)
                registered_signals = registered_signals_for(repository)
    errors = validate_hypothesis_definition(definition, registered_signals, strategy_spec)
    payload = {
        "hypothesis_id": definition.hypothesis_id,
        "version": definition.version,
        "valid": not errors,
        "reasons": list(errors),
        "status": definition.status,
    }
    return CommandOutcome(payload, status="ok")


def promote(context: CLIContext, hypothesis_id: str, to_status: str, force: bool) -> CommandOutcome:
    if not context.database.exists():
        raise CliError(
            "Database is not initialized.",
            why="Hypothesis promotion updates the local catalog.",
            next_action="Initialize the database.",
            command="mft setup init",
        )
    with open_repository(context.database, read_only=False) as repository:
        _ensure_catalog(repository)
        current = hypothesis_definition(repository, hypothesis_id)
        if current is None:
            raise CliError(
                f"Hypothesis {hypothesis_id} not found.",
                next_action="List the available hypotheses.",
                command="mft hypothesis list",
            )
        promoted = _promote_hypothesis(repository, current, to_status, force)
    payload = {
        "hypothesis_id": promoted.hypothesis_id,
        "previous_status": current.status,
        "new_status": promoted.status,
    }
    return CommandOutcome(payload, status="ok")


def _load_definitions(database: Path) -> tuple[Any, ...]:
    if not database.exists():
        return hypothesis_definitions(None)
    with open_repository(database, read_only=True) as repository:
        if not _schema_initialized(repository):
            return hypothesis_definitions(None)
        return hypothesis_definitions(repository)


def _load_definition(database: Path, hypothesis_id: str) -> Any:
    if not database.exists():
        definition = hypothesis_definition(None, hypothesis_id)
        if definition is None:
            raise CliError(
                f"Hypothesis {hypothesis_id} not found.",
                next_action="List the available hypotheses.",
                command="mft hypothesis list",
            )
        return definition
    with open_repository(database, read_only=True) as repository:
        if not _schema_initialized(repository):
            definition = hypothesis_definition(None, hypothesis_id)
            if definition is None:
                raise CliError(
                    f"Hypothesis {hypothesis_id} not found.",
                    next_action="List the available hypotheses.",
                    command="mft hypothesis list",
                )
            return definition
        definition = hypothesis_definition(repository, hypothesis_id)
        if definition is None:
            raise CliError(
                f"Hypothesis {hypothesis_id} not found.",
                next_action="List the available hypotheses.",
                command="mft hypothesis list",
            )
        return definition


def _strategy_spec(repository, definition) -> Any:
    if repository is None:
        return None
    return repository.get_strategy_spec(definition.hypothesis_id, definition.version)


def _signal_status(required_signals: tuple[str, ...], registered_signals: tuple[str, ...]) -> list[dict[str, Any]]:
    return [
        {"signal_type": signal_type, "registered": signal_type in registered_signals}
        for signal_type in required_signals
    ]


def _readiness_research_runs(repository, strategy_spec) -> tuple[Any, ...]:
    if repository is None or strategy_spec is None:
        return ()
    return tuple(
        run
        for run in repository.get_research_runs()
        if run.strategy_spec_id == strategy_spec.strategy_spec_id
    )


def _readiness_backtests(repository, hypothesis_id: str) -> tuple[Any, ...]:
    if repository is None:
        return ()
    return tuple(
        result
        for result in repository.get_backtest_results()
        if result.hypothesis_id == hypothesis_id
    )


def _readiness_snapshots(repository, strategy_spec) -> tuple[Any, ...]:
    if repository is None or strategy_spec is None:
        return ()
    return tuple(
        snapshot
        for snapshot in repository.get_dataset_snapshots()
        if snapshot.universe_id == strategy_spec.universe_id
    )


def _missing_evidence(
    strategy_spec,
    signal_status: list[dict[str, Any]],
    research_runs: tuple[Any, ...],
    backtests: tuple[Any, ...],
    snapshots: tuple[Any, ...],
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


def _next_step(database: Path, hypothesis_id: str, snapshots: tuple[Any, ...]) -> dict[str, str]:
    if snapshots:
        symbol = "RELIANCE"
        if database.exists():
            with open_repository(database, read_only=True) as repository:
                assets = {asset.asset_id: asset.symbol for asset in repository.list_assets()}
                for asset_id in snapshots[0].asset_ids:
                    symbol = assets.get(asset_id, symbol)
                    break
        return {
            "next_action": "Run research.",
            "next_command": f"mft research run {hypothesis_id} {symbol} --snapshot latest",
        }
    return {
        "next_action": "Create a dataset snapshot, then run research.",
        "next_command": f"mft research run {hypothesis_id} RELIANCE --snapshot latest",
    }


def _ensure_catalog(repository) -> None:
    if repository.get_hypotheses():
        return
    from project.cli_commands import _ensure_default_hypothesis_catalog

    _ensure_default_hypothesis_catalog(repository)


def registered_signals_for(repository) -> tuple[str, ...]:
    if repository is None:
        return ()
    return registered_signal_types(repository) or ()


def _build_readiness_payload(
    database: Path,
    hypothesis_id: str,
    definition,
) -> tuple[dict[str, Any], list[str]]:
    strategy_spec: Any = None
    required_signals: tuple[str, ...] = hypothesis_signal_types(None, hypothesis_id)
    registered_signals: tuple[str, ...] = ()
    signal_status = _signal_status(required_signals, registered_signals)
    research_runs: tuple[Any, ...] = ()
    backtests: tuple[Any, ...] = ()
    snapshots: tuple[Any, ...] = ()
    if database.exists():
        with open_repository(database, read_only=True) as repository:
            if _schema_initialized(repository):
                strategy_spec = _strategy_spec(repository, definition)
                required_signals = hypothesis_signal_types(repository, hypothesis_id)
                registered_signals = registered_signals_for(repository)
                signal_status = _signal_status(required_signals, registered_signals)
                research_runs = _readiness_research_runs(repository, strategy_spec)
                backtests = _readiness_backtests(repository, hypothesis_id)
                snapshots = _readiness_snapshots(repository, strategy_spec)
    validation_errors = validate_hypothesis_definition(
        definition,
        registered_signals,
        strategy_spec,
    )
    missing_evidence = _missing_evidence(
        strategy_spec,
        signal_status,
        research_runs,
        backtests,
        snapshots,
        validation_errors,
    )
    payload: dict[str, Any] = {
        "hypothesis_id": definition.hypothesis_id,
        "name": definition.name,
        "status": definition.status,
        "version": definition.version,
        "required_signals": list(required_signals),
        "signal_registration_status": signal_status,
        "strategy_spec_id": strategy_spec.strategy_spec_id if strategy_spec else None,
        "dataset_snapshot_ids": [snapshot.dataset_snapshot_id for snapshot in snapshots],
        "available_research_runs": [cast(Any, run).__dict__ for run in research_runs],
        "available_backtests": [cast(Any, backtest).__dict__ for backtest in backtests],
        "missing_evidence": missing_evidence,
        "validation_errors": list(validation_errors),
        "readiness": "ready" if not missing_evidence else "not_ready",
    }
    payload.update(_next_step(database, definition.hypothesis_id, snapshots))
    return payload, missing_evidence
