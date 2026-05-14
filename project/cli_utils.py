from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import cast

from project.common.models import (
    Asset,
    DecisionAction,
    DecisionReason,
)
from project.data.repository import DataRepository
from project.data.models import HypothesisEvaluation
from project.hypotheses.rsi_mean_reversion import RSIMeanReversionHypothesis
from project.hypotheses.ma_crossover import MACrossoverHypothesis


RESEARCH_UNIVERSE_SYMBOLS = ("NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY")


def emit(payload: object) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def parse_datetime(value: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


def load_json(payload: str | None) -> dict:
    if not payload:
        return {}
    return json.loads(payload)


def find_asset(repository: DataRepository, asset_ref: str) -> Asset | None:
    for asset in repository.list_assets():
        if asset.asset_id == asset_ref or asset.symbol == asset_ref.upper():
            return asset
    return None


def find_evaluation(repository: DataRepository, evaluation_id: str) -> HypothesisEvaluation | None:
    for evaluation in repository.get_hypothesis_evaluations():
        if evaluation.evaluation_id == evaluation_id:
            return evaluation
    return None


def hypotheses() -> tuple[RSIMeanReversionHypothesis, MACrossoverHypothesis]:
    return (RSIMeanReversionHypothesis(), MACrossoverHypothesis())


def research_assets(repository: DataRepository) -> tuple[Asset, ...]:
    allowed = set(RESEARCH_UNIVERSE_SYMBOLS)
    assets = [
        asset
        for asset in repository.list_assets()
        if asset.symbol in allowed and asset.market == "NSE"
    ]
    return tuple(sorted(assets, key=lambda item: item.symbol))


def decision_action(value: str) -> DecisionAction:
    return cast(DecisionAction, {"approve": "approve", "reject": "reject", "watchlist": "watch"}[value])


def decision_reason(value: str | None) -> DecisionReason:
    return cast(DecisionReason, value or "market_conditions")
