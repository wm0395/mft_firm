from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from project.cli_registry import (
    _readiness_backtests,
    _readiness_missing_evidence,
    _readiness_research_runs,
    _readiness_snapshots,
    _signal_registration_status,
)
from project.cli_support import load_json
from project.cli_utils import (
    hypothesis_definition,
    hypothesis_definitions,
    hypothesis_signal_types,
    registered_signal_types,
)
from project.common.models import HypothesisDefinition
from project.common.models import strategy_spec_parameters
from project.data.repository import DataRepository
from project.hypotheses.catalog import validate_hypothesis_definition
from project.strategy_dossier import build_strategy_dossier


@dataclass(frozen=True)
class HypothesisCardView:
    hypothesis_id: str
    name: str
    status: str
    version: int
    explainability_level: str
    required_signals: tuple[str, ...]
    readiness: str
    blockers: tuple[str, ...]
    latest_backtest: str
    validation_failures: int


@dataclass(frozen=True)
class HypothesisColumnView:
    status: str
    cards: tuple[HypothesisCardView, ...]


@dataclass(frozen=True)
class HypothesisDetailView:
    hypothesis_id: str
    name: str
    status: str
    version: int
    explainability_level: str
    thesis: str
    horizon: str
    direction_policy: str
    required_signals: tuple[str, ...]
    readiness: str
    blockers: tuple[str, ...]
    latest_backtest: str
    validation_failures: int
    strategy_spec: dict[str, Any] | None
    dossier: dict[str, Any] | None


@dataclass(frozen=True)
class ReadinessView:
    blockers: tuple[str, ...]
    latest_backtest: str
    validation_failures: int


@dataclass(frozen=True)
class HypothesesPageView:
    columns: tuple[HypothesisColumnView, ...]
    selected_detail: HypothesisDetailView | None
    debug_payload: dict[str, Any]


def get_hypotheses_page_view(
    repository: DataRepository,
    selected_hypothesis_id: str | None = None,
) -> HypothesesPageView:
    definitions = hypothesis_definitions(repository)
    cards = tuple(_card_view(repository, definition) for definition in definitions)
    columns = tuple(
        HypothesisColumnView(
            status=status,
            cards=tuple(card for card in cards if card.status == status),
        )
        for status in ("draft", "testing", "active", "deprecated", "archived")
    )
    selected = _selected_definition(definitions, selected_hypothesis_id)
    detail = _detail_view(repository, selected) if selected is not None else None
    return HypothesesPageView(
        columns=columns,
        selected_detail=detail,
        debug_payload={
            "definitions": [definition.__dict__ for definition in definitions],
            "registry": _registry_payload(repository),
        },
    )


def _card_view(
    repository: DataRepository,
    definition: HypothesisDefinition,
) -> HypothesisCardView:
    readiness = _readiness(repository, definition.hypothesis_id)
    return HypothesisCardView(
        hypothesis_id=definition.hypothesis_id,
        name=definition.name,
        status=definition.status,
        version=definition.version,
        explainability_level=definition.explainability_level,
        required_signals=hypothesis_signal_types(repository, definition.hypothesis_id),
        readiness="ready" if not readiness.blockers else "not ready",
        blockers=readiness.blockers,
        latest_backtest=readiness.latest_backtest,
        validation_failures=readiness.validation_failures,
    )


def _detail_view(
    repository: DataRepository,
    definition: HypothesisDefinition,
) -> HypothesisDetailView:
    readiness = _readiness(repository, definition.hypothesis_id)
    strategy_spec = repository.get_strategy_spec(definition.hypothesis_id, definition.version)
    return HypothesisDetailView(
        hypothesis_id=definition.hypothesis_id,
        name=definition.name,
        status=definition.status,
        version=definition.version,
        explainability_level=definition.explainability_level,
        thesis=_strategy_parameter(strategy_spec, "thesis"),
        horizon=_strategy_parameter(strategy_spec, "holding_horizon"),
        direction_policy=definition.definition.get("direction_policy", ""),
        required_signals=hypothesis_signal_types(repository, definition.hypothesis_id),
        readiness="ready" if not readiness.blockers else "not ready",
        blockers=readiness.blockers,
        latest_backtest=readiness.latest_backtest,
        validation_failures=readiness.validation_failures,
        strategy_spec=strategy_spec.__dict__ if strategy_spec is not None else None,
        dossier=build_strategy_dossier(repository, definition.hypothesis_id),
    )


def _readiness(repository: DataRepository, hypothesis_id: str) -> ReadinessView:
    definition = hypothesis_definition(repository, hypothesis_id)
    if definition is None:
        return ReadinessView(("unknown_hypothesis",), "", 0)
    strategy_spec = repository.get_strategy_spec(hypothesis_id, definition.version)
    required_signals = hypothesis_signal_types(repository, hypothesis_id)
    registered_signals = registered_signal_types(repository) or ()
    signal_status = _signal_registration_status(required_signals, registered_signals)
    research_runs = _readiness_research_runs(repository, strategy_spec)
    backtests = _readiness_backtests(repository, hypothesis_id)
    snapshots = _readiness_snapshots(repository, strategy_spec)
    validation_errors = validate_hypothesis_definition(
        definition,
        registered_signals,
        strategy_spec,
    )
    blockers = _readiness_missing_evidence(
        strategy_spec,
        signal_status,
        research_runs,
        backtests,
        snapshots,
        validation_errors,
    )
    return ReadinessView(
        tuple(blockers),
        _latest_backtest(backtests),
        _validation_failure_count(repository, hypothesis_id),
    )


def _latest_backtest(backtests) -> str:
    if not backtests:
        return ""
    latest = backtests[-1]
    return f"{latest.hypothesis_id} {latest.total_return_pct:.2f}%"


def _validation_failure_count(repository: DataRepository, hypothesis_id: str) -> int:
    count = 0
    for evaluation in repository.get_hypothesis_evaluations(hypothesis_id=hypothesis_id):
        payload = load_json(evaluation.validation_result_json)
        if payload and not payload.get("is_valid", True):
            count += 1
    return count


def _selected_definition(
    definitions: tuple[HypothesisDefinition, ...],
    selected_hypothesis_id: str | None,
) -> HypothesisDefinition | None:
    if selected_hypothesis_id is not None:
        for definition in definitions:
            if definition.hypothesis_id == selected_hypothesis_id:
                return definition
    return definitions[0] if definitions else None


def _strategy_parameter(strategy_spec, name: str) -> str:
    if strategy_spec is None:
        return ""
    return str(strategy_spec_parameters(strategy_spec).get(name, ""))


def _registry_payload(repository: DataRepository) -> dict[str, Any]:
    from project.cli_utils import load_hypothesis_registry

    registry = load_hypothesis_registry(repository)
    return {"hypotheses": [definition.hypothesis_id for definition in registry.list_hypotheses()]}

