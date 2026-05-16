from __future__ import annotations

from dataclasses import asdict
from dataclasses import replace
from typing import cast
from pathlib import Path
from uuid import uuid4

from project.backtesting.engine import BacktestEngine
from project.backtesting.models import BacktestConfig
from project.backtesting.research_runner import run_strategy_research as run_strategy_research_engine
from project.hypotheses.catalog import hypothesis_summary, validate_hypothesis_definition
from project.cli_support import (
    build_strategy_dossier,
    decision_action,
    decision_reason,
    emit,
    evaluation_from_output,
    find_asset,
    hypotheses,
    parse_datetime,
    run_research_batch,
    validate_outputs,
    validation_payload,
)
from project.cli_utils import (
    hypothesis_definition,
    hypothesis_definitions,
    hypothesis_signal_types,
    registered_signal_types,
)
from project.common.models import (
    DecisionAction,
    DecisionReason,
    Direction,
    HypothesisOutput,
    TradeIdea,
    utc_now_iso,
)
from project.data.loader import load_ohlcv_csv
from project.data.market_collector_loader import load_market_collector_ohlcv
from project.data.market_server_loader import (
    sync_market_data as sync_market_data_loader,
)
from project.data.snapshot_builder import create_dataset_snapshot as build_dataset_snapshot
from project.data.repository import DataRepository
from project.data.yfinance_loader import load_default_yfinance_universe
from project.decision.models import Decision
from project.hypotheses.engine import evaluate_hypotheses
from project.replay.engine import ReplayEngine
from project.signals.pipeline import compute_latest_price_signals
from project.signals.registry import DEFAULT_SIGNAL_DEFINITIONS, default_signal_registry
from project.trade_engine.generator import generate_trade_ideas
from project.validation.models import ValidationResult


def run_batch(repository: DataRepository, asset_ref: str, persist: bool) -> int:
    if persist:
        _ensure_default_hypothesis_catalog(repository)
    asset = find_asset(repository, asset_ref)
    if asset is None:
        _emit_error("run-batch", f"Asset {asset_ref} not found")
        return 1
    signals = compute_latest_price_signals(
        repository, default_signal_registry(), asset.asset_id
    )
    outputs = evaluate_hypotheses(asset.asset_id, signals, hypotheses(repository))
    validations = validate_outputs(repository, outputs)
    ideas = generate_trade_ideas(
        tuple(output for output, result in validations if result.is_valid)
    )
    if persist:
        with repository.transaction():
            repository.persist_signals(signals)
            _persist_run_batch(repository, validations, ideas)
    _emit_success(
        "run-batch",
        {
            "asset_id": asset.asset_id,
            "signals": len(signals),
            "hypotheses": len(outputs),
            "valid_hypotheses": sum(bool(result.is_valid) for _, result in validations),
            "trade_ideas": len(ideas),
            "persisted": persist,
        },
    )
    return 0


def research_batch(
    repository: DataRepository,
    include_testing: bool = False,
    include_draft: bool = False,
) -> int:
    _ensure_default_hypothesis_catalog(repository)
    try:
        result = run_research_batch(repository, include_testing, include_draft)
    except ValueError as error:
        _emit_error("run-research-batch", error)
        return 1
    result["dossiers"] = tuple(
        dossier
        for hypothesis_id in (
            "hypothesis:rsi_mean_reversion",
            "hypothesis:ma_crossover",
        )
        if (dossier := build_strategy_dossier(repository, hypothesis_id)) is not None
    )
    _emit_success("run-research-batch", result)
    return 0


def _ensure_default_hypothesis_catalog(repository: DataRepository) -> None:
    with repository.transaction():
        for signal_definition in DEFAULT_SIGNAL_DEFINITIONS:
            repository.persist_signal_definition(signal_definition)
        for entry in hypothesis_definitions():
            repository.persist_hypothesis_definition(entry)
            repository.persist_hypothesis_signal_map(
                entry.hypothesis_id,
                tuple(
                    signal
                    for signal in _required_signals(entry)
                ),
            )


def _promote_hypothesis(
    repository: DataRepository,
    definition,
    to_status: str,
    force: bool,
):
    if definition is None:
        raise ValueError("unknown hypothesis")
    errors = validate_hypothesis_definition(
        definition,
        registered_signal_types(repository),
        repository.get_strategy_spec(definition.hypothesis_id, definition.version),
    )
    if errors:
        raise ValueError("; ".join(errors))
    from project.hypotheses.lifecycle import promote_definition

    promoted = promote_definition(definition, to_status, force=force)
    repository.update_hypothesis_status(definition.hypothesis_id, promoted.status)
    return promoted


def _required_signals(definition) -> tuple[str, ...]:
    value = definition.definition.get("required_signals")
    if isinstance(value, tuple):
        return tuple(str(item) for item in value)
    if isinstance(value, list):
        return tuple(str(item) for item in value)
    return ()


def load_yfinance_universe(
    repository: DataRepository,
    period: str,
    interval: str,
) -> int:
    try:
        payload = load_default_yfinance_universe(repository, period, interval)
    except (RuntimeError, ValueError) as error:
        _emit_error("load-yfinance-universe", error)
        return 1
    _emit_success("load-yfinance-universe", payload)
    return 0


def load_market_collector(
    repository: DataRepository,
    source_database: str,
    symbols: list[str],
    resolution: str,
) -> int:
    try:
        payload = load_market_collector_ohlcv(
            repository,
            Path(source_database),
            tuple(symbols),
            resolution,
        )
    except (RuntimeError, ValueError) as error:
        _emit_error("load-market-collector", error)
        return 1
    _emit_success("load-market-collector", payload)
    return 0


def sync_market_data_command(
    repository: DataRepository,
    symbols: list[str],
    resolution: str,
    market_db_url_env: str,
) -> int:
    try:
        payload = sync_market_data_loader(
            repository,
            tuple(symbols),
            resolution,
            market_db_url_env,
        )
    except (RuntimeError, ValueError) as error:
        _emit_error("sync-market-data", error)
        return 1
    _emit_success("sync-market-data", payload)
    return 0


def load_ohlcv_csv_command(
    repository: DataRepository,
    file_path: str,
    asset_symbol: str,
) -> int:
    try:
        rows_loaded = load_ohlcv_csv(Path(file_path), asset_symbol, repository)
    except (OSError, RuntimeError, ValueError) as error:
        _emit_error("load-ohlcv-csv", error)
        return 1
    _emit_success(
        "load-ohlcv-csv",
        {
            "asset_symbol": asset_symbol.upper(),
            "file_path": file_path,
            "rows_loaded": rows_loaded,
        },
    )
    return 0


def create_dataset_snapshot_command(
    repository: DataRepository,
    name: str,
    market: str,
    symbols: list[str],
    data_start: str,
    data_end: str,
    resolution: str,
    description: str | None,
) -> int:
    try:
        result = build_dataset_snapshot(
            repository,
            name,
            market,
            tuple(symbols),
            data_start,
            data_end,
            resolution,
            description,
        )
    except (RuntimeError, ValueError) as error:
        _emit_error("create-dataset-snapshot", error)
        return 1
    _emit_success("create-dataset-snapshot", asdict(result))
    return 0


def review_trade_idea(
    repository: DataRepository,
    trade_id: str,
    action: str,
    reason: str | None,
    notes: str,
) -> int:
    trade_idea = next(
        (idea for idea in repository.get_trade_ideas() if idea.trade_id == trade_id),
        None,
    )
    if trade_idea is None:
        _emit_error("review-trade-idea", f"Trade idea {trade_id} not found")
        return 1
    decision = Decision(
        decision_id=f"decision:{uuid4()}",
        trade_id=trade_id,
        action=cast(DecisionAction, decision_action(action)),
        structured_reason=cast(DecisionReason, decision_reason(reason)),
        notes=notes,
        created_at=utc_now_iso(),
    )
    repository.persist_decision(decision)
    _emit_success("review-trade-idea", decision.__dict__)
    return 0


def show_trade_idea(repository: DataRepository, trade_id: str) -> int:
    trade_idea = next(
        (idea for idea in repository.get_trade_ideas() if idea.trade_id == trade_id),
        None,
    )
    if trade_idea is None:
        _emit_error("show-trade-idea", f"Trade idea {trade_id} not found")
        return 1
    emit(trade_idea.__dict__)
    return 0


def replay_evaluate(
    repository: DataRepository,
    asset_symbol: str,
    timestamp_text: str,
    direction: str,
    hypothesis_id: str,
) -> int:
    engine = ReplayEngine(repository)
    try:
        evaluation = engine.evaluate_signal(
            asset_symbol.upper(),
            parse_datetime(timestamp_text),
            cast(Direction, direction),
            hypothesis_id,
        )
    except ValueError as error:
        _emit_error("replay-evaluate", error)
        return 1
    repository.persist_signal_evaluation(evaluation)
    _emit_success("replay-evaluate", evaluation.__dict__)
    return 0


def show_hypothesis_evaluations(
    repository: DataRepository,
    asset_id: str | None,
    hypothesis_id: str | None,
) -> int:
    emit(
        [
            evaluation.__dict__
            for evaluation in repository.get_hypothesis_evaluations(
                asset_id, hypothesis_id
            )
        ]
    )
    return 0


def backtest_hypothesis(
    repository: DataRepository,
    hypothesis_id: str,
    asset_symbol: str,
    start_date: str,
    end_date: str,
) -> int:
    engine = BacktestEngine(repository)
    try:
        result = engine.run(
            hypothesis_id,
            asset_symbol.upper(),
            parse_datetime(f"{start_date}T00:00:00+00:00"),
            parse_datetime(f"{end_date}T23:59:59+00:00"),
            BacktestConfig(),
        )
    except ValueError as error:
        _emit_error("backtest-hypothesis", error)
        return 1
    enriched_result = replace(
        result,
        start_timestamp=parse_datetime(f"{start_date}T00:00:00+00:00").isoformat(),
        end_timestamp=parse_datetime(f"{end_date}T23:59:59+00:00").isoformat(),
        parameters=_config_parameters(BacktestConfig()),
    )
    repository.persist_backtest_result(enriched_result)
    _emit_success("backtest-hypothesis", enriched_result.__dict__)
    return 0


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
        _emit_error("run-strategy-research", error)
        return 1
    _emit_success("run-strategy-research", asdict(result))
    return 0


def list_hypotheses(repository: DataRepository) -> int:
    emit(
        [
            hypothesis_summary(definition)
            for definition in hypothesis_definitions(repository)
        ]
    )
    return 0


def show_hypothesis(repository: DataRepository, hypothesis_id: str) -> int:
    definition = hypothesis_definition(repository, hypothesis_id)
    if definition is None:
        _emit_error("show-hypothesis", f"Hypothesis {hypothesis_id} not found")
        return 1
    payload = hypothesis_summary(definition)
    payload["signal_map"] = [
        {"signal_type": signal_type, "role": "required"}
        for signal_type in hypothesis_signal_types(repository, hypothesis_id)
    ]
    payload["strategy_spec"] = (
        asdict(strategy_spec)
        if (strategy_spec := repository.get_strategy_spec(hypothesis_id, definition.version))
        else None
    )
    emit(payload)
    return 0


def validate_hypothesis(repository: DataRepository, hypothesis_id: str) -> int:
    definition = hypothesis_definition(repository, hypothesis_id)
    if definition is None:
        _emit_error("validate-hypothesis", f"Hypothesis {hypothesis_id} not found")
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
    emit(payload)
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
        _emit_error("promote-hypothesis", error)
        return 1
    _emit_success(
        "promote-hypothesis",
        {
            "hypothesis_id": promoted.hypothesis_id,
            "previous_status": current.status if current else None,
            "new_status": promoted.status,
        },
    )
    return 0


def _persist_run_batch(
    repository: DataRepository,
    validations: list[tuple[HypothesisOutput, ValidationResult]],
    ideas: tuple[TradeIdea, ...],
) -> None:
    idea_ids = {idea.hypothesis_id for idea in ideas}
    for idea in ideas:
        repository.persist_trade_idea(idea)
    for output, result in validations:
        repository.persist_hypothesis_evaluation(
            evaluation_from_output(
                output,
                output.hypothesis_id in idea_ids,
                validation_payload(result),
            )
        )


def _emit_success(command: str, payload: object) -> None:
    emit({"command": command, "result": payload, "status": "ok"})


def _emit_error(command: str, error: Exception | str) -> None:
    emit({"command": command, "error": str(error), "status": "error"})


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
