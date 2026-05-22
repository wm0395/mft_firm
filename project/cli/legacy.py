from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable

from project.cli_commands import research_batch, run_batch
from project.cli_ingestion import (
    create_dataset_snapshot_command,
    load_ohlcv_csv_command,
    load_market_collector,
    load_yfinance_universe,
    sync_market_data_command,
)
from project.cli_parsers import (
    add_database_argument,
    add_ingestion_commands,
    add_inspection_commands,
    add_pipeline_commands,
    add_research_commands,
    add_research_lifecycle_commands,
    add_report_commands,
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
    report_hypotheses,
    regime_analysis,
    strategy_dossier,
    show_competition,
    show_explanation,
    show_signal_lineage,
    show_validation_failures,
    show_validation_path,
)
from project.cli_support import emit_error, emit_response
from project.cli_trade import (
    _governance_handlers,
    _research_handlers,
    backtest_hypothesis,
    replay_evaluate,
    review_trade_idea,
    show_hypothesis_evaluations,
    show_trade_idea,
)
from project.cli.context import open_repository
from project.data.repository import DataRepository


Handler = Callable[[argparse.Namespace], int]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mft")
    subcommands = parser.add_subparsers(dest="command", required=True)
    add_setup_commands(subcommands)
    add_pipeline_commands(subcommands)
    add_ingestion_commands(subcommands)
    add_trade_commands(subcommands)
    add_report_commands(subcommands)
    add_research_commands(subcommands)
    add_research_lifecycle_commands(subcommands)
    add_inspection_commands(subcommands)
    add_database_argument(subcommands)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    arguments = sys.argv[1:] if argv is None else list(argv)
    if not arguments:
        parser.print_help()
        return 0
    try:
        parsed = parser.parse_args(arguments)
    except SystemExit as error:
        return int(error.code or 0)
    handler = _handlers().get(parsed.command)
    if handler is None:
        emit_error(str(parsed.command), "unknown command")
        return 1
    return handler(parsed)


def _handlers() -> dict[str, Handler]:
    handlers: dict[str, Handler] = {"init-db": _init_db}
    handlers.update(_pipeline_handlers())
    handlers.update(_ingestion_handlers())
    handlers.update(_trade_handlers())
    handlers.update(_report_handlers())
    handlers.update(_governance_handlers())
    handlers.update(_inspection_handlers())
    handlers.update(_research_handlers())
    return handlers


def _pipeline_handlers() -> dict[str, Handler]:
    return {
        "run-batch": _repo_handler(
            "run-batch", False, lambda repo, ns: run_batch(repo, ns.asset_id, True)
        ),
        "summarize-batch": _repo_handler(
            "summarize-batch",
            True,
            lambda repo, ns: run_batch(repo, ns.asset_id, False),
        ),
        "run-research-batch": _repo_handler(
            "run-research-batch",
            False,
            lambda repo, ns: research_batch(
                repo, bool(ns.include_testing), bool(ns.include_draft)
            ),
        ),
    }


def _ingestion_handlers() -> dict[str, Handler]:
    return _market_data_ingestion_handlers() | _dataset_ingestion_handlers()


def _market_data_ingestion_handlers() -> dict[str, Handler]:
    return {
        "load-yfinance-universe": _repo_handler(
            "load-yfinance-universe",
            False,
            lambda repo, ns: load_yfinance_universe(repo, ns.period, ns.interval),
        ),
        "load-market-collector": _repo_handler(
            "load-market-collector",
            False,
            lambda repo, ns: load_market_collector(
                repo, ns.source_database, list(ns.symbol), ns.resolution
            ),
        ),
        "sync-market-data": _repo_handler(
            "sync-market-data",
            False,
            lambda repo, ns: sync_market_data_command(
                repo, list(ns.symbol), ns.resolution, ns.market_db_url_env
            ),
        ),
        "data-quality-report": _repo_handler(
            "data-quality-report",
            True,
            lambda repo, ns: data_quality_report(
                repo,
                list(ns.symbol),
                ns.resolution,
                ns.max_staleness_days,
                bool(ns.strict),
            ),
        ),
    }


def _dataset_ingestion_handlers() -> dict[str, Handler]:
    return {
        "create-dataset-snapshot": _repo_handler(
            "create-dataset-snapshot",
            False,
            lambda repo, ns: create_dataset_snapshot_command(
                repo,
                ns.name,
                ns.market,
                list(ns.symbol),
                ns.data_start,
                ns.data_end,
                ns.resolution,
                ns.description,
            ),
        ),
        "load-ohlcv-csv": _repo_handler(
            "load-ohlcv-csv",
            False,
            lambda repo, ns: load_ohlcv_csv_command(
                repo, ns.file_path, ns.asset_symbol
            ),
        ),
    }


def _trade_handlers() -> dict[str, Handler]:
    return {
        "review-trade-idea": _repo_handler(
            "review-trade-idea",
            False,
            lambda repo, ns: review_trade_idea(
                repo,
                ns.trade_id,
                getattr(ns, "action", None),
                getattr(ns, "reason", None),
                ns.notes,
            ),
        ),
        "show-trade-idea": _repo_handler(
            "show-trade-idea", True, lambda repo, ns: show_trade_idea(repo, ns.trade_id)
        ),
        "replay-evaluate": _repo_handler(
            "replay-evaluate",
            False,
            lambda repo, ns: replay_evaluate(
                repo, ns.asset_symbol, ns.timestamp, ns.direction, ns.hypothesis_id
            ),
        ),
        "backtest-hypothesis": _repo_handler(
            "backtest-hypothesis",
            False,
            lambda repo, ns: backtest_hypothesis(
                repo, ns.hypothesis_id, ns.asset_symbol, ns.start_date, ns.end_date
            ),
        ),
    }


def _report_handlers() -> dict[str, Handler]:
    return {
        "report-hypotheses": _repo_handler(
            "report-hypotheses",
            True,
            lambda repo, ns: report_hypotheses(repo, ns.horizon),
        ),
        "backtest-results": _repo_handler("backtest-results", True, lambda repo, ns: backtest_results(repo)),
        "hypothesis-performance": _repo_handler(
            "hypothesis-performance", True, lambda repo, ns: hypothesis_performance(repo)
        ),
        "strategy-dossier": _repo_handler(
            "strategy-dossier",
            True,
            lambda repo, ns: strategy_dossier(repo, ns.hypothesis_id),
        ),
        "advanced-report": _repo_handler(
            "advanced-report",
            True,
            lambda repo, ns: advanced_report(repo, ns.hypothesis_id, ns.asset_id),
        ),
    }


def _inspection_handlers() -> dict[str, Handler]:
    return _evaluation_handlers() | _diagnostic_handlers() | _position_handlers()


def _evaluation_handlers() -> dict[str, Handler]:
    return {
        "show-hypothesis-evaluations": _repo_handler(
            "show-hypothesis-evaluations",
            True,
            lambda repo, ns: show_hypothesis_evaluations(
                repo, ns.asset_id, ns.hypothesis_id
            ),
        ),
        "show-competition": _repo_handler(
            "show-competition",
            True,
            lambda repo, ns: show_competition(repo, ns.asset_id, ns.direction),
        ),
        "show-explanation": _repo_handler(
            "show-explanation",
            True,
            lambda repo, ns: show_explanation(repo, ns.evaluation_id),
        ),
        "show-signal-lineage": _repo_handler(
            "show-signal-lineage",
            True,
            lambda repo, ns: show_signal_lineage(repo, ns.asset_id),
        ),
        "show-validation-path": _repo_handler(
            "show-validation-path",
            True,
            lambda repo, ns: show_validation_path(repo, ns.evaluation_id),
        ),
        "show-validation-failures": _repo_handler(
            "show-validation-failures",
            True,
            lambda repo, ns: show_validation_failures(repo),
        ),
    }


def _diagnostic_handlers() -> dict[str, Handler]:
    return {
        "list-rejected-hypotheses": _repo_handler(
            "list-rejected-hypotheses",
            True,
            lambda repo, ns: list_rejected_hypotheses(repo),
        ),
        "regime-analysis": _repo_handler(
            "regime-analysis",
            True,
            lambda repo, ns: regime_analysis(repo, ns.asset_symbol),
        ),
        "lineage-trace": _repo_handler(
            "lineage-trace",
            True,
            lambda repo, ns: lineage_trace(repo, ns.signal_type, ns.hypothesis_id),
        ),
    }


def _position_handlers() -> dict[str, Handler]:
    return {
        "position-management": _repo_handler(
            "position-management",
            True,
            lambda repo, ns: position_management(
                repo, ns.asset_id, ns.hypothesis_id, ns.status
            ),
        ),
    }


def _repo_handler(
    command: str,
    read_only: bool,
    runner: Callable[[DataRepository, argparse.Namespace], int],
) -> Handler:
    def handler(args: argparse.Namespace) -> int:
        return _run_repo_command(command, args, read_only, runner)

    return handler


def _run_repo_command(
    command: str,
    args: argparse.Namespace,
    read_only: bool,
    runner: Callable[[DataRepository, argparse.Namespace], int],
) -> int:
    try:
        with open_repository(Path(args.database), read_only=read_only) as repository:
            return runner(repository, args)
    except Exception as error:
        emit_error(command, error)
        return 1


def _init_db(args: argparse.Namespace) -> int:
    try:
        with open_repository(Path(args.database), read_only=False) as repository:
            repository.initialize()
    except Exception as error:
        emit_error("init-db", error)
        return 1
    emit_response(
        "init-db", {"schema": "initialized", "database": str(Path(args.database))}
    )
    return 0
