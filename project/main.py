from __future__ import annotations

import argparse
import json

from project.data.db import DuckDBAccess
from project.data.repository import DataRepository
from project.hypotheses.engine import evaluate_hypotheses
from project.hypotheses.rsi_mean_reversion import RSIMeanReversionHypothesis
from project.signals.pipeline import compute_latest_price_signals
from project.signals.registry import default_signal_registry
from project.trade_engine.generator import generate_trade_ideas


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="project")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("init-db")
    run_parser = subcommands.add_parser("run-batch")
    run_parser.add_argument("asset_id")
    run_parser.add_argument("--database", default="project_mft.duckdb")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    db = DuckDBAccess(getattr(args, "database", "project_mft.duckdb"))
    repository = DataRepository(db)
    repository.initialize()

    if args.command == "init-db":
        print(json.dumps({"status": "ok", "schema": "initialized"}))
        db.close()
        return 0

    if args.command == "run-batch":
        signals = compute_latest_price_signals(repository, default_signal_registry(), args.asset_id)
        outputs = evaluate_hypotheses(args.asset_id, signals, (RSIMeanReversionHypothesis(),))
        ideas = generate_trade_ideas(outputs)
        for idea in ideas:
            repository.persist_trade_idea(idea)
        print(json.dumps({"signals": len(signals), "hypotheses": len(outputs), "trade_ideas": len(ideas)}))
        db.close()
        return 0

    db.close()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
