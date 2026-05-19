from __future__ import annotations

from project.cli.context import CLIContext, open_repository
from project.cli.errors import CommandOutcome


def review(context: CLIContext) -> CommandOutcome:
    if not context.database.exists():
        return CommandOutcome({"ideas": ()}, status="warn")
    with open_repository(context.database, read_only=True) as repository:
        ideas = repository.get_open_trade_ideas()
        assets = {asset.asset_id: asset.symbol for asset in repository.list_assets()}
    payload = {
        "ideas": [
            {
                "trade_id": idea.trade_id,
                "asset_id": idea.asset_id,
                "symbol": assets.get(idea.asset_id, idea.asset_id),
                "hypothesis_id": idea.hypothesis_id,
                "confidence": idea.confidence,
                "direction": idea.direction,
                "status": "needs review",
            }
            for idea in ideas
        ]
    }
    return CommandOutcome(payload, status="ok" if ideas else "warn")


def list_ideas(context: CLIContext) -> CommandOutcome:
    return review(context)
