from __future__ import annotations

import argparse
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
    show_validation_failures,
    show_validation_path,
)
from project.cli_support import (
    decision_action,
    decision_reason,
    emit,
    evaluation_from_output,
    find_asset,
    hypotheses,
    parse_datetime,
    validate_outputs,
    validation_payload,
)
from project.common.models import Direction, utc_now_iso
from project.data.db import DuckDBAccess
from project.data.repository import DataRepository
from project.decision.models import Decision
from project.hypotheses.engine import evaluate_hypotheses
from project.replay.engine import ReplayEngine
from project.signals.pipeline import compute_latest_price_signals
from project.signals.registry import default_signal_registry
from project.trade_engine.generator import generate_trade_ideas


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="project")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("init-db")
    run_parser = subcommands.add_parser("run-batch")
    run_parser.add_argument("asset_id")
    review_parser = subcommands.add_parser("review-trade-idea")
    review_parser.add_argument("trade_id")
    review_parser.add_argument("action", choices=["approve", "reject", "watchlist"])
    review_parser.add_argument("--reason")
    review_parser.add_argument("--notes", default="")
    show_trade_parser = subcommands.add_parser("show-trade-idea")
    show_trade_parser.add_argument("trade_id")
    summarize_parser = subcommands.add_parser("summarize-batch")
    summarize_parser.add_argument("asset_id")
    replay_parser = subcommands.add_parser("replay-evaluate")
    replay_parser.add_argument("asset_symbol")
    replay_parser.add_argument("timestamp")
    replay_parser.add_argument("direction", choices=["long", "short", "flat"])
    replay_parser.add_argument("hypothesis_id")
    evaluations_parser = subcommands.add_parser("show-hypothesis-evaluations")
    evaluations_parser.add_argument("--asset-id")
    evaluations_parser.add_argument("--hypothesis-id")
    competition_parser = subcommands.add_parser("show-competition")
    competition_parser.add_argument("--asset-id")
    competition_parser.add_argument("--direction", choices=["long", "short", "flat"])
    explanation_parser = subcommands.add_parser("show-explanation")
    explanation_parser.add_argument("evaluation_id")
    lineage_parser = subcommands.add_parser("show-signal-lineage")
    lineage_parser.add_argument("asset_id")
    validation_path_parser = subcommands.add_parser("show-validation-path")
    validation_path_parser.add_argument("evaluation_id")
    subcommands.add_parser("show-validation-failures")
    subcommands.add_parser("list-rejected-hypotheses")
    report_parser = subcommands.add_parser("report-hypotheses")
    report_parser.add_argument("--horizon", type=int, choices=[1, 5, 20], default=20)
    subcommands.add_parser("backtest-results")
    backtest_parser = subcommands.add_parser("backtest-hypothesis")
    backtest_parser.add_argument("hypothesis_id")
    backtest_parser.add_argument("asset_symbol")
    backtest_parser.add_argument("start_date")
    backtest_parser.add_argument("end_date")
    subcommands.add_parser("hypothesis-performance")
    regime_parser = subcommands.add_parser("regime-analysis")
    regime_parser.add_argument("asset_symbol")
    trace_parser = subcommands.add_parser("lineage-trace")
    trace_parser.add_argument("--signal-type")
    trace_parser.add_argument("--hypothesis-id")
    positions_parser = subcommands.add_parser("position-management")
    positions_parser.add_argument("--asset-id")
    positions_parser.add_argument("--hypothesis-id")
    positions_parser.add_argument("--status", choices=["open", "closed"])
    advanced_report_parser = subcommands.add_parser("advanced-report")
    advanced_report_parser.add_argument("hypothesis_id")
    advanced_report_parser.add_argument("--asset-id")
    for command in subcommands.choices.values():
        command.add_argument("--database", default="project_mft.duckdb")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repository = DataRepository(DuckDBAccess(args.database))
    repository.initialize()
    try:
        return dispatch(args, repository)
    finally:
        repository._db.close()


def dispatch(args: argparse.Namespace, repository: DataRepository) -> int:
    if args.command == "init-db":
        emit({"status": "ok", "schema": "initialized"})
        return 0
    if args.command == "run-batch":
        return run_batch(repository, args.asset_id, persist=True)
    if args.command == "summarize-batch":
        return run_batch(repository, args.asset_id, persist=False)
    if args.command == "review-trade-idea":
        return review_trade_idea(repository, args.trade_id, args.action, args.reason, args.notes)
    if args.command == "show-trade-idea":
        return show_trade_idea(repository, args.trade_id)
    if args.command == "replay-evaluate":
        return replay_evaluate(repository, args.asset_symbol, args.timestamp, args.direction, args.hypothesis_id)
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
    if args.command == "report-hypotheses":
        return report_hypotheses(repository, args.horizon)
    if args.command == "backtest-results":
        return backtest_results(repository)
    if args.command == "backtest-hypothesis":
        return backtest_hypothesis(repository, args.hypothesis_id, args.asset_symbol, args.start_date, args.end_date)
    if args.command == "hypothesis-performance":
        return hypothesis_performance(repository)
    if args.command == "regime-analysis":
        return regime_analysis(repository, args.asset_symbol)
    if args.command == "lineage-trace":
        return lineage_trace(repository, args.signal_type, args.hypothesis_id)
    if args.command == "position-management":
        return position_management(repository, args.asset_id, args.hypothesis_id, args.status)
    return advanced_report(repository, args.hypothesis_id, args.asset_id)


def run_batch(repository: DataRepository, asset_ref: str, persist: bool) -> int:
    asset = find_asset(repository, asset_ref)
    if asset is None:
        emit({"error": f"Asset {asset_ref} not found"})
        return 1
    signals = compute_latest_price_signals(repository, default_signal_registry(), asset.asset_id)
    outputs = evaluate_hypotheses(asset.asset_id, signals, hypotheses())
    validations = validate_outputs(repository, outputs)
    ideas = generate_trade_ideas(tuple(output for output, result in validations if result.is_valid))
    if persist:
        idea_ids = {idea.hypothesis_id for idea in ideas}
        for idea in ideas:
            repository.persist_trade_idea(idea)
        for output, result in validations:
            repository.persist_hypothesis_evaluation(
                evaluation_from_output(output, output.hypothesis_id in idea_ids, validation_payload(result))
            )
    emit(
        {
            "asset_id": asset.asset_id,
            "signals": len(signals),
            "hypotheses": len(outputs),
            "valid_hypotheses": sum(bool(result.is_valid) for _, result in validations),
            "trade_ideas": len(ideas),
            "persisted": persist,
        }
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
        emit({"error": f"Trade idea {trade_id} not found"})
        return 1
    decision = Decision(
        decision_id=f"decision:{uuid4()}",
        trade_id=trade_id,
        action=decision_action(action),
        structured_reason=decision_reason(reason),
        notes=notes,
        created_at=utc_now_iso(),
    )
    repository.persist_decision(decision)
    emit(decision.__dict__)
    return 0


def show_trade_idea(repository: DataRepository, trade_id: str) -> int:
    trade_idea = next((idea for idea in repository.get_trade_ideas() if idea.trade_id == trade_id), None)
    if trade_idea is None:
        emit({"error": f"Trade idea {trade_id} not found"})
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
        emit({"error": str(error)})
        return 1
    repository.persist_signal_evaluation(evaluation)
    emit(evaluation.__dict__)
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
        emit({"error": str(error)})
        return 1
    repository.persist_backtest_result(result)
    emit(result.__dict__)
    return 0
