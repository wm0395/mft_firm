from __future__ import annotations

import argparse
from pathlib import Path
from typing import cast
from uuid import uuid4

from project.backtesting.engine import BacktestEngine
from project.backtesting.models import BacktestConfig
from project.cli_readonly import (
    advanced_report,
    backtest_results,
    hypothesis_performance,
    lineage_trace,
    list_rejected_hypotheses,
    position_management,
    regime_analysis,
    report_hypotheses,
    show_competition,
    show_explanation,
    show_signal_lineage,
    strategy_dossier,
    show_validation_failures,
    show_validation_path,
)
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
from project.common.models import DecisionAction, DecisionReason, Direction, HypothesisOutput, TradeIdea, utc_now_iso
from project.data.db import DuckDBAccess
from project.data.loader import load_ohlcv_csv
from project.data.market_collector_loader import load_market_collector_ohlcv
from project.data.repository import DataRepository
from project.data.yfinance_loader import load_default_yfinance_universe
from project.decision.models import Decision
from project.hypotheses.engine import evaluate_hypotheses
from project.replay.engine import ReplayEngine
from project.signals.pipeline import compute_latest_price_signals
from project.signals.registry import default_signal_registry
from project.trade_engine.generator import generate_trade_ideas
from project.cli_parsers import (
    add_database_argument,
    add_ingestion_commands,
    add_inspection_commands,
    add_pipeline_commands,
    add_report_commands,
    add_research_commands,
    add_setup_commands,
    add_trade_commands,
)
from project.validation.models import ValidationResult


READ_ONLY_COMMANDS = {
    "backtest-results",
    "hypothesis-performance",
    "lineage-trace",
    "list-rejected-hypotheses",
    "position-management",
    "report-hypotheses",
    "regime-analysis",
    "show-competition",
    "show-explanation",
    "show-hypothesis-evaluations",
    "show-signal-lineage",
    "show-trade-idea",
    "show-validation-failures",
    "show-validation-path",
    "strategy-dossier",
    "summarize-batch",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="project")
    subcommands = parser.add_subparsers(dest="command", required=True)
    add_setup_commands(subcommands)
    add_pipeline_commands(subcommands)
    add_ingestion_commands(subcommands)
    add_trade_commands(subcommands)
    add_report_commands(subcommands)
    add_research_commands(subcommands)
    add_inspection_commands(subcommands)
    add_database_argument(subcommands)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repository = DataRepository(
        DuckDBAccess(args.database, read_only=_is_read_only_command(args.command))
    )
    try:
        if args.command == "init-db":
            repository.initialize()
            _emit_success("init-db", {"schema": "initialized"})
            return 0
        return dispatch(args, repository)
    finally:
        repository.close()


def dispatch(args: argparse.Namespace, repository: DataRepository) -> int:
    if args.command in {"run-batch", "summarize-batch", "run-research-batch"}:
        return _dispatch_pipeline(repository, args)
    if args.command in {"load-yfinance-universe", "load-market-collector", "load-ohlcv-csv"}:
        return _dispatch_ingestion(repository, args)
    if args.command in {"review-trade-idea", "replay-evaluate", "backtest-hypothesis"}:
        return _dispatch_trade(repository, args)
    if args.command in {"report-hypotheses", "backtest-results", "hypothesis-performance"}:
        return _dispatch_reports(repository, args)
    if args.command in READ_ONLY_COMMANDS:
        return _dispatch_readonly(repository, args)
    raise ValueError(f"Unknown command: {args.command}")


def _dispatch_pipeline(repository: DataRepository, args: argparse.Namespace) -> int:
    if args.command == "run-batch":
        return run_batch(repository, args.asset_id, persist=True)
    if args.command == "summarize-batch":
        return run_batch(repository, args.asset_id, persist=False)
    return research_batch(repository)


def _dispatch_ingestion(repository: DataRepository, args: argparse.Namespace) -> int:
    if args.command == "load-yfinance-universe":
        return load_yfinance_universe(repository, args.period, args.interval)
    if args.command == "load-ohlcv-csv":
        return load_ohlcv_csv_command(repository, args.file_path, args.asset_symbol)
    return load_market_collector(repository, args.source_database, args.symbol, args.resolution)


def _dispatch_trade(repository: DataRepository, args: argparse.Namespace) -> int:
    if args.command == "review-trade-idea":
        return review_trade_idea(repository, args.trade_id, args.action, args.reason, args.notes)
    if args.command == "replay-evaluate":
        return replay_evaluate(repository, args.asset_symbol, args.timestamp, args.direction, args.hypothesis_id)
    return backtest_hypothesis(repository, args.hypothesis_id, args.asset_symbol, args.start_date, args.end_date)


def _dispatch_reports(repository: DataRepository, args: argparse.Namespace) -> int:
    if args.command == "report-hypotheses":
        return report_hypotheses(repository, args.horizon)
    if args.command == "backtest-results":
        return backtest_results(repository)
    return hypothesis_performance(repository)


def _dispatch_readonly(repository: DataRepository, args: argparse.Namespace) -> int:
    if args.command == "show-trade-idea":
        return show_trade_idea(repository, args.trade_id)
    if args.command == "show-hypothesis-evaluations":
        return show_hypothesis_evaluations(repository, args.asset_id, args.hypothesis_id)
    if args.command == "show-validation-failures":
        return show_validation_failures(repository)
    if args.command == "show-competition":
        return show_competition(repository, args.asset_id, args.direction)
    if args.command == "show-explanation":
        return show_explanation(repository, args.evaluation_id)
    if args.command == "show-signal-lineage":
        return show_signal_lineage(repository, args.asset_id)
    if args.command == "show-validation-path":
        return show_validation_path(repository, args.evaluation_id)
    if args.command == "list-rejected-hypotheses":
        return list_rejected_hypotheses(repository)
    if args.command == "regime-analysis":
        return regime_analysis(repository, args.asset_symbol)
    if args.command == "lineage-trace":
        return lineage_trace(repository, args.signal_type, args.hypothesis_id)
    if args.command == "position-management":
        return position_management(repository, args.asset_id, args.hypothesis_id, args.status)
    if args.command == "strategy-dossier":
        return strategy_dossier(repository, args.hypothesis_id)
    return advanced_report(repository, args.hypothesis_id, args.asset_id)


def run_batch(repository: DataRepository, asset_ref: str, persist: bool) -> int:
    asset = find_asset(repository, asset_ref)
    if asset is None:
        _emit_error("run-batch", f"Asset {asset_ref} not found")
        return 1
    signals = compute_latest_price_signals(repository, default_signal_registry(), asset.asset_id)
    outputs = evaluate_hypotheses(asset.asset_id, signals, hypotheses())
    validations = validate_outputs(repository, outputs)
    ideas = generate_trade_ideas(tuple(output for output, result in validations if result.is_valid))
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


def research_batch(repository: DataRepository) -> int:
    try:
        result = run_research_batch(repository)
    except ValueError as error:
        _emit_error("run-research-batch", error)
        return 1
    result["dossiers"] = tuple(
        dossier
        for hypothesis_id in ("hypothesis:rsi_mean_reversion", "hypothesis:ma_crossover")
        if (dossier := build_strategy_dossier(repository, hypothesis_id)) is not None
    )
    _emit_success("run-research-batch", result)
    return 0


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


def load_ohlcv_csv_command(repository: DataRepository, file_path: str, asset_symbol: str) -> int:
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


def review_trade_idea(
    repository: DataRepository,
    trade_id: str,
    action: str,
    reason: str | None,
    notes: str,
) -> int:
    trade_idea = next((idea for idea in repository.get_trade_ideas() if idea.trade_id == trade_id), None)
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
    trade_idea = next((idea for idea in repository.get_trade_ideas() if idea.trade_id == trade_id), None)
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
    emit([evaluation.__dict__ for evaluation in repository.get_hypothesis_evaluations(asset_id, hypothesis_id)])
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
    repository.persist_backtest_result(result)
    _emit_success("backtest-hypothesis", result.__dict__)
    return 0


def _is_read_only_command(command: str) -> bool:
    return command in READ_ONLY_COMMANDS


def _emit_success(command: str, payload: object) -> None:
    emit({"command": command, "result": payload, "status": "ok"})


def _emit_error(command: str, error: Exception | str) -> None:
    emit({"command": command, "error": str(error), "status": "error"})
