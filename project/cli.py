from __future__ import annotations

import argparse

from project import cli_commands
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
from project.cli_readonly import (
    advanced_report,
    backtest_results,
    data_quality_report,
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
    strategy_dossier,
)
from project.data.db import DuckDBAccess
from project.data.repository import DataRepository


READ_ONLY_COMMANDS = {
    "backtest-results",
    "data-quality-report",
    "hypothesis-readiness",
    "hypothesis-performance",
    "lineage-trace",
    "list-rejected-hypotheses",
    "list-hypotheses",
    "position-management",
    "report-hypotheses",
    "regime-analysis",
    "show-competition",
    "show-explanation",
    "show-hypothesis",
    "show-hypothesis-evaluations",
    "show-signal-lineage",
    "show-trade-idea",
    "show-validation-failures",
    "show-validation-path",
    "validate-hypothesis",
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
            cli_commands._emit_success("init-db", {"schema": "initialized"})
            return 0
        return dispatch(args, repository)
    finally:
        repository.close()


def dispatch(args: argparse.Namespace, repository: DataRepository) -> int:
    if args.command in {"run-batch", "summarize-batch", "run-research-batch"}:
        return _dispatch_pipeline(repository, args)
    if args.command in {
        "load-yfinance-universe",
        "load-market-collector",
        "load-ohlcv-csv",
        "create-dataset-snapshot",
        "sync-market-data",
    }:
        return _dispatch_ingestion(repository, args)
    if args.command in {"review-trade-idea", "replay-evaluate", "backtest-hypothesis"}:
        return _dispatch_trade(repository, args)
    if args.command in {"run-strategy-research", "promote-hypothesis"}:
        return _dispatch_governance(repository, args)
    if args.command in {
        "report-hypotheses",
        "backtest-results",
        "hypothesis-performance",
    }:
        return _dispatch_reports(repository, args)
    if args.command in READ_ONLY_COMMANDS:
        return _dispatch_readonly(repository, args)
    raise ValueError(f"Unknown command: {args.command}")


def _dispatch_pipeline(repository: DataRepository, args: argparse.Namespace) -> int:
    if args.command == "run-batch":
        return cli_commands.run_batch(repository, args.asset_id, persist=True)
    if args.command == "summarize-batch":
        return cli_commands.run_batch(repository, args.asset_id, persist=False)
    return cli_commands.research_batch(
        repository,
        args.include_testing,
        args.include_draft,
    )


def _dispatch_governance(repository: DataRepository, args: argparse.Namespace) -> int:
    if args.command == "run-strategy-research":
        return cli_commands.run_strategy_research(
            repository,
            args.dataset_snapshot_id,
            args.hypothesis_id,
            args.asset_symbol,
            args.start_date,
            args.end_date,
            args.slippage_bps,
            args.position_size,
            args.exit_horizon,
            args.include_testing,
            args.include_draft,
        )
    return cli_commands.promote_hypothesis(
        repository,
        args.hypothesis_id,
        args.to,
        args.force,
    )


def _dispatch_ingestion(repository: DataRepository, args: argparse.Namespace) -> int:
    if args.command == "load-yfinance-universe":
        return cli_commands.load_yfinance_universe(
            repository, args.period, args.interval
        )
    if args.command == "load-ohlcv-csv":
        return cli_commands.load_ohlcv_csv_command(
            repository, args.file_path, args.asset_symbol
        )
    if args.command == "create-dataset-snapshot":
        return cli_commands.create_dataset_snapshot_command(
            repository,
            args.name,
            args.market,
            args.symbol,
            args.data_start,
            args.data_end,
            args.resolution,
            args.description,
        )
    if args.command == "sync-market-data":
        return cli_commands.sync_market_data_command(
            repository, args.symbol, args.resolution, args.market_db_url_env
        )
    return cli_commands.load_market_collector(
        repository, args.source_database, args.symbol, args.resolution
    )


def _dispatch_trade(repository: DataRepository, args: argparse.Namespace) -> int:
    if args.command == "review-trade-idea":
        return cli_commands.review_trade_idea(
            repository, args.trade_id, args.action, args.reason, args.notes
        )
    if args.command == "replay-evaluate":
        return cli_commands.replay_evaluate(
            repository,
            args.asset_symbol,
            args.timestamp,
            args.direction,
            args.hypothesis_id,
        )
    return cli_commands.backtest_hypothesis(
        repository,
        args.hypothesis_id,
        args.asset_symbol,
        args.start_date,
        args.end_date,
    )


def _dispatch_reports(repository: DataRepository, args: argparse.Namespace) -> int:
    if args.command == "report-hypotheses":
        return report_hypotheses(repository, args.horizon)
    if args.command == "backtest-results":
        return backtest_results(repository)
    return hypothesis_performance(repository)


def _dispatch_readonly(repository: DataRepository, args: argparse.Namespace) -> int:
    if args.command in {
        "list-hypotheses",
        "show-hypothesis",
        "validate-hypothesis",
        "hypothesis-readiness",
    }:
        return _dispatch_readonly_registry(repository, args)
    if args.command in {
        "show-trade-idea",
        "show-hypothesis-evaluations",
        "show-validation-failures",
        "show-competition",
        "show-explanation",
        "show-signal-lineage",
        "show-validation-path",
        "list-rejected-hypotheses",
        "regime-analysis",
        "lineage-trace",
        "position-management",
        "strategy-dossier",
    }:
        return _dispatch_readonly_inspection(repository, args)
    if args.command == "data-quality-report":
        return data_quality_report(
            repository, args.symbol, args.resolution, args.max_staleness_days
        )
    return advanced_report(repository, args.hypothesis_id, args.asset_id)


def _dispatch_readonly_registry(repository: DataRepository, args: argparse.Namespace) -> int:
    if args.command == "list-hypotheses":
        return cli_commands.list_hypotheses(repository)
    if args.command == "show-hypothesis":
        return cli_commands.show_hypothesis(repository, args.hypothesis_id)
    return cli_commands.validate_hypothesis(repository, args.hypothesis_id)


def _dispatch_readonly_inspection(repository: DataRepository, args: argparse.Namespace) -> int:
    if args.command == "show-trade-idea":
        return cli_commands.show_trade_idea(repository, args.trade_id)
    if args.command == "show-hypothesis-evaluations":
        return cli_commands.show_hypothesis_evaluations(
            repository, args.asset_id, args.hypothesis_id
        )
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
        return position_management(
            repository, args.asset_id, args.hypothesis_id, args.status
        )
    return strategy_dossier(repository, args.hypothesis_id)


def _is_read_only_command(command: str) -> bool:
    return command in READ_ONLY_COMMANDS
