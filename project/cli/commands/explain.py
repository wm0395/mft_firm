from __future__ import annotations

from project.cli_support import build_strategy_dossier, load_json
from project.cli.context import CLIContext, open_repository
from project.cli.errors import CommandOutcome


def lineage(context: CLIContext, hypothesis_id: str | None, signal_type: str | None) -> CommandOutcome:
    if not context.database.exists():
        return CommandOutcome({"lineage": ()}, status="warn")
    with open_repository(context.database, read_only=True) as repository:
        rows = []
        for evaluation in repository.get_hypothesis_evaluations(hypothesis_id=hypothesis_id):
            signals = load_json(evaluation.signals_snapshot_json)
            if signal_type is not None and signal_type not in signals:
                continue
            rows.append(
                {
                    "evaluation_id": evaluation.evaluation_id,
                    "hypothesis_id": evaluation.hypothesis_id,
                    "asset_id": evaluation.asset_id,
                    "timestamp": evaluation.timestamp,
                    "signals": signals,
                }
            )
    return CommandOutcome({"lineage": rows}, status="ok")


def signal(context: CLIContext, asset_symbol: str) -> CommandOutcome:
    if not context.database.exists():
        return CommandOutcome({"signal_lineage": ()}, status="warn")
    with open_repository(context.database, read_only=True) as repository:
        asset = _asset_by_symbol(repository, asset_symbol)
        if asset is None:
            return CommandOutcome({"signal_lineage": ()}, status="warn")
        payload = [
            {
                "evaluation_id": evaluation.evaluation_id,
                "timestamp": evaluation.timestamp,
                "hypothesis_id": evaluation.hypothesis_id,
                "signals": sorted(load_json(evaluation.signals_snapshot_json).keys()),
            }
            for evaluation in repository.get_hypothesis_evaluations(asset_id=asset.asset_id)
        ]
    return CommandOutcome({"signal_lineage": payload}, status="ok")


def trade(context: CLIContext, hypothesis_id: str) -> CommandOutcome:
    if not context.database.exists():
        return CommandOutcome({"dossier": None}, status="warn")
    with open_repository(context.database, read_only=True) as repository:
        dossier = build_strategy_dossier(repository, hypothesis_id)
    return CommandOutcome({"dossier": dossier}, status="ok" if dossier else "warn")


def _asset_by_symbol(repository, asset_symbol: str):
    for asset in repository.list_assets():
        if asset.symbol == asset_symbol.upper():
            return asset
    return None
