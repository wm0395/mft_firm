from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import cast

from project.common.models import (
    Asset,
    DecisionAction,
    DecisionReason,
    HypothesisDefinition,
)
from project.data.models import HypothesisEvaluation
from project.data.repository import DataRepository
from project.hypotheses.catalog import (
    default_hypothesis_catalog,
    list_hypotheses as catalog_list_hypotheses,
    research_hypotheses as catalog_research_hypotheses,
)
from project.hypotheses.interface import Hypothesis
from project.hypotheses.registry import HypothesisRegistry
from project.signals.registry import DEFAULT_SIGNAL_DEFINITIONS


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


def hypotheses(
    repository: DataRepository | None = None,
    include_testing: bool = False,
    include_draft: bool = False,
) -> tuple[Hypothesis, ...]:
    if repository is None:
        return catalog_research_hypotheses(include_testing, include_draft)
    registry = load_hypothesis_registry(repository)
    return _selected_hypotheses(registry, include_testing, include_draft)


def hypothesis_definitions(repository: DataRepository | None = None) -> tuple[HypothesisDefinition, ...]:
    if repository is None:
        return catalog_list_hypotheses()
    get_hypotheses = getattr(repository, "get_hypotheses", None)
    if not callable(get_hypotheses):
        return catalog_list_hypotheses()
    definitions = {definition.hypothesis_id: definition for definition in get_hypotheses()}
    if not definitions:
        return catalog_list_hypotheses()
    return tuple(
        definitions.get(entry.definition.hypothesis_id, entry.definition)
        for entry in default_hypothesis_catalog()
    )


def ensure_default_hypothesis_catalog(repository: DataRepository) -> None:
    with repository.transaction():
        for signal_definition in DEFAULT_SIGNAL_DEFINITIONS:
            repository.persist_signal_definition(signal_definition)
        for definition in hypothesis_definitions():
            repository.persist_hypothesis_definition(definition)
            repository.persist_hypothesis_signal_map(
                definition.hypothesis_id,
                hypothesis_signal_types(None, definition.hypothesis_id),
            )


def hypothesis_definition(
    repository: DataRepository | None,
    hypothesis_id: str,
) -> HypothesisDefinition | None:
    for definition in hypothesis_definitions(repository):
        if definition.hypothesis_id == hypothesis_id:
            return definition
    return None


def hypothesis_signal_types(
    repository: DataRepository | None,
    hypothesis_id: str,
) -> tuple[str, ...]:
    if repository is not None:
        get_signal_map = getattr(repository, "get_hypothesis_signal_map", None)
        if callable(get_signal_map):
            signal_map = tuple(
                signal_type
                for signal_type, _ in get_signal_map(hypothesis_id)
            )
            if signal_map:
                return signal_map
    for entry in default_hypothesis_catalog():
        if entry.definition.hypothesis_id == hypothesis_id:
            return entry.required_signals
    return ()


def registered_signal_types(repository: DataRepository | None) -> tuple[str, ...] | None:
    if repository is None:
        return None
    get_signal_definitions = getattr(repository, "get_signal_definitions", None)
    if not callable(get_signal_definitions):
        return tuple(signal.signal_type for signal in DEFAULT_SIGNAL_DEFINITIONS)
    signal_definitions = get_signal_definitions()
    if signal_definitions:
        return tuple(signal.signal_type for signal in signal_definitions)
    return tuple(signal.signal_type for signal in DEFAULT_SIGNAL_DEFINITIONS)


def load_hypothesis_registry(repository: DataRepository | None = None) -> HypothesisRegistry:
    registry = HypothesisRegistry()
    for definition in hypothesis_definitions(repository):
        registry.register(definition, hypothesis_signal_types(repository, definition.hypothesis_id))
    return registry


def _selected_hypotheses(
    registry: HypothesisRegistry,
    include_testing: bool,
    include_draft: bool,
) -> tuple[Hypothesis, ...]:
    implementations = {
        entry.definition.hypothesis_id: entry.hypothesis
        for entry in default_hypothesis_catalog()
    }
    selected: list[Hypothesis] = []
    for definition in registry.research_hypotheses(include_testing, include_draft):
        implementation = implementations.get(definition.hypothesis_id)
        if implementation is not None:
            selected.append(implementation)
    return tuple(selected)


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
