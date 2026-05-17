from __future__ import annotations

from project.cli_support import (
    build_strategy_dossier,
    emit_error,
    emit_response,
    evaluation_from_output,
    find_asset,
    hypotheses,
    run_research_batch,
    validate_outputs,
    validation_payload,
)
from project.cli_utils import (
    hypothesis_definitions,
    registered_signal_types,
)
from project.common.models import (
    HypothesisOutput,
    HypothesisStatus,
    TradeIdea,
)
from typing import cast
from project.data.repository import DataRepository
from project.hypotheses.engine import evaluate_hypotheses
from project.signals.pipeline import compute_latest_price_signals
from project.signals.registry import DEFAULT_SIGNAL_DEFINITIONS, default_signal_registry
from project.trade_engine.generator import generate_trade_ideas
from project.validation.models import ValidationResult
from project.hypotheses.catalog import validate_hypothesis_definition


def run_batch(repository: DataRepository, asset_ref: str, persist: bool) -> int:
    if persist:
        _ensure_default_hypothesis_catalog(repository)
    asset = find_asset(repository, asset_ref)
    if asset is None:
        emit_error("run-batch", f"Asset {asset_ref} not found")
        return 1
    signals = compute_latest_price_signals(
        repository, default_signal_registry(), asset.asset_id
    )
    outputs = evaluate_hypotheses(asset.asset_id, signals, hypotheses(repository))
    validations = validate_outputs(repository, outputs)
    ideas = generate_trade_ideas(
        tuple(output for output, result in validations if result.is_valid)
    )
    if persist:
        with repository.transaction():
            repository.persist_signals(signals)
            _persist_run_batch(repository, validations, ideas)
    emit_response(
        "run-batch",
        {
            "asset_id": asset.asset_id,
            "signals": len(signals),
            "hypotheses": len(outputs),
            "valid_hypotheses": sum(bool(result.is_valid) for _, result in validations),
            "trade_ideas": len(ideas),
            "persisted": persist,
        },
    )
    return 0


def research_batch(
    repository: DataRepository,
    include_testing: bool = False,
    include_draft: bool = False,
) -> int:
    _ensure_default_hypothesis_catalog(repository)
    try:
        result = run_research_batch(repository, include_testing, include_draft)
    except ValueError as error:
        emit_error("run-research-batch", error)
        return 1
    result["dossiers"] = tuple(
        dossier
        for hypothesis_id in (
            "hypothesis:rsi_mean_reversion",
            "hypothesis:ma_crossover",
        )
        if (dossier := build_strategy_dossier(repository, hypothesis_id)) is not None
    )
    emit_response("run-research-batch", result)
    return 0


def _ensure_default_hypothesis_catalog(repository: DataRepository) -> None:
    with repository.transaction():
        for signal_definition in DEFAULT_SIGNAL_DEFINITIONS:
            repository.persist_signal_definition(signal_definition)
        for entry in hypothesis_definitions():
            repository.persist_hypothesis_definition(entry)
            repository.persist_hypothesis_signal_map(
                entry.hypothesis_id,
                tuple(signal for signal in _required_signals(entry)),
            )


def _promote_hypothesis(
    repository: DataRepository,
    definition,
    to_status: str,
    force: bool,
):
    if definition is None:
        raise ValueError("unknown hypothesis")
    errors = validate_hypothesis_definition(
        definition,
        registered_signal_types(repository),
        repository.get_strategy_spec(definition.hypothesis_id, definition.version),
    )
    if errors:
        raise ValueError("; ".join(errors))
    from project.hypotheses.lifecycle import promote_definition

    promoted = promote_definition(definition, cast(HypothesisStatus, to_status), force=force)
    repository.update_hypothesis_status(definition.hypothesis_id, promoted.status)
    return promoted


def _required_signals(definition) -> tuple[str, ...]:
    value = definition.definition.get("required_signals")
    if isinstance(value, tuple):
        return tuple(str(item) for item in value)
    if isinstance(value, list):
        return tuple(str(item) for item in value)
    return ()


def _persist_run_batch(
    repository: DataRepository,
    validations: list[tuple[HypothesisOutput, ValidationResult]],
    ideas: tuple[TradeIdea, ...],
) -> None:
    idea_ids = {idea.hypothesis_id for idea in ideas}
    for idea in ideas:
        repository.persist_trade_idea(idea)
    for output, result in validations:
        repository.persist_hypothesis_evaluation(
            evaluation_from_output(
                output,
                output.hypothesis_id in idea_ids,
                validation_payload(result),
            )
        )
