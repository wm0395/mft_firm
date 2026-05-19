from __future__ import annotations

from typing import Any

from project.cli_support import build_strategy_dossier
from project.cli.context import CLIContext, open_repository
from project.cli.errors import CommandOutcome


def backtests(context: CLIContext) -> CommandOutcome:
    if not context.database.exists():
        return CommandOutcome({"backtests": ()}, status="warn")
    with open_repository(context.database, read_only=True) as repository:
        payload = [result.__dict__ for result in repository.get_backtest_results()]
    return CommandOutcome({"backtests": payload}, status="ok")


def performance(context: CLIContext) -> CommandOutcome:
    if not context.database.exists():
        return CommandOutcome({"performance": {}}, status="warn")
    with open_repository(context.database, read_only=True) as repository:
        trade_outcomes = [outcome.__dict__ for outcome in repository.get_trade_outcomes()]
        signal_metrics: dict[str, list[Any]] = {}
        for evaluation in repository.get_signal_evaluations():
            signal_metrics.setdefault(evaluation.hypothesis_id, []).append(evaluation)
    return CommandOutcome(
        {
            "trade_outcomes": trade_outcomes,
            "signal_evaluations": {
                key: len(value) for key, value in signal_metrics.items()
            },
        },
        status="ok",
    )


def rejected(context: CLIContext) -> CommandOutcome:
    if not context.database.exists():
        return CommandOutcome({"rejected": ()}, status="warn")
    with open_repository(context.database, read_only=True) as repository:
        rejected_rows = []
        for evaluation in repository.get_hypothesis_evaluations():
            payload = load_json(evaluation.validation_result_json)
            if payload and not payload.get("is_valid", True):
                rejected_rows.append(
                    {
                        "evaluation_id": evaluation.evaluation_id,
                        "hypothesis_id": evaluation.hypothesis_id,
                        "asset_id": evaluation.asset_id,
                        "reasons": payload.get("reasons", []),
                    }
                )
    return CommandOutcome({"rejected": rejected_rows}, status="ok")


def dossier(context: CLIContext, hypothesis_id: str) -> CommandOutcome:
    if not context.database.exists():
        return CommandOutcome({"dossier": None}, status="warn")
    with open_repository(context.database, read_only=True) as repository:
        payload = build_strategy_dossier(repository, hypothesis_id)
    return CommandOutcome({"dossier": payload}, status="ok" if payload else "warn")


def load_json(payload: str | None) -> dict:
    if not payload:
        return {}
    from json import loads

    return loads(payload)
