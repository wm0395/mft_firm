from __future__ import annotations

import argparse


def add_setup_commands(subcommands: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    subcommands.add_parser("init-db")


def add_pipeline_commands(subcommands: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    run_parser = subcommands.add_parser("run-batch")
    run_parser.add_argument("asset_id")
    summarize_parser = subcommands.add_parser("summarize-batch")
    summarize_parser.add_argument("asset_id")
    subcommands.add_parser("run-research-batch")


def add_ingestion_commands(subcommands: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    yfinance_parser = subcommands.add_parser("load-yfinance-universe")
    yfinance_parser.add_argument("--period", default="6mo")
    yfinance_parser.add_argument("--interval", default="1d")
    market_collector_parser = subcommands.add_parser("load-market-collector")
    market_collector_parser.add_argument("--source-database", required=True)
    market_collector_parser.add_argument("--symbol", action="append", default=[])
    market_collector_parser.add_argument("--resolution", default="1d")


def add_trade_commands(subcommands: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    review_parser = subcommands.add_parser("review-trade-idea")
    review_parser.add_argument("trade_id")
    review_parser.add_argument("action", choices=["approve", "reject", "watchlist"])
    review_parser.add_argument("--reason")
    review_parser.add_argument("--notes", default="")
    show_trade_parser = subcommands.add_parser("show-trade-idea")
    show_trade_parser.add_argument("trade_id")
    replay_parser = subcommands.add_parser("replay-evaluate")
    replay_parser.add_argument("asset_symbol")
    replay_parser.add_argument("timestamp")
    replay_parser.add_argument("direction", choices=["long", "short", "flat"])
    replay_parser.add_argument("hypothesis_id")
    backtest_parser = subcommands.add_parser("backtest-hypothesis")
    backtest_parser.add_argument("hypothesis_id")
    backtest_parser.add_argument("asset_symbol")
    backtest_parser.add_argument("start_date")
    backtest_parser.add_argument("end_date")


def add_report_commands(subcommands: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    report_parser = subcommands.add_parser("report-hypotheses")
    report_parser.add_argument("--horizon", type=int, choices=[1, 5, 20], default=20)
    subcommands.add_parser("backtest-results")
    subcommands.add_parser("hypothesis-performance")


def add_research_commands(subcommands: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    subcommands.add_parser("strategy-dossier").add_argument("hypothesis_id")


def add_inspection_commands(subcommands: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
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


def add_database_argument(subcommands: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    for command in subcommands.choices.values():
        command.add_argument("--database", default="project_mft.duckdb")
