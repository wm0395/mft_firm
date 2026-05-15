from __future__ import annotations

from dataclasses import replace
import json
from typing import Any

from project.common.models import HypothesisOutput, utc_now_iso, strategy_spec_parameters
from project.data.models import HypothesisEvaluation
from project.data.repository import DataRepository
from project.hypotheses.ma_crossover import MACrossoverHypothesis
from project.hypotheses.registry import HypothesisRegistry
from project.hypotheses.rsi_mean_reversion import RSIMeanReversionHypothesis
from project.validation.engine import ValidationEngine
from project.validation.models import ValidationResult


def validate_outputs(
    repository: DataRepository,
    outputs: tuple[HypothesisOutput, ...],
) -> list[tuple[HypothesisOutput, ValidationResult]]:
    validation_engine = ValidationEngine()
    registry = HypothesisRegistry()
    _register_strategy(registry, repository, RSIMeanReversionHypothesis.definition, ("rsi_14",))
    _register_strategy(registry, repository, MACrossoverHypothesis.definition, ("ma_5", "ma_20"))
    results: list[tuple[HypothesisOutput, ValidationResult]] = []
    for output in outputs:
        evaluation = evaluation_from_output(
            output,
            False,
            None,
            timestamp=_latest_price_timestamp(repository, output.asset_id),
        )
        result = validation_engine.validate(
            evaluation=evaluation,
            repository=repository,
            hypothesis_registry=registry,
            max_signal_age_hours=24,
        )
        results.append((output, _apply_research_gate(repository, output, result)))
    return results


def evaluation_from_output(
    output: HypothesisOutput,
    generated_trade_idea: bool,
    validation_payload: dict | None,
    timestamp: str | None = None,
    research_run_id: str | None = None,
    dataset_snapshot_id: str | None = None,
) -> HypothesisEvaluation:
    timestamp_value = timestamp or utc_now_iso()
    return HypothesisEvaluation(
        evaluation_id=f"eval:{output.asset_id}:{output.hypothesis_id}:{output.version}:{timestamp_value}",
        asset_id=output.asset_id,
        hypothesis_id=output.hypothesis_id,
        hypothesis_version=output.version,
        timestamp=timestamp_value,
        direction=output.direction,
        confidence=output.confidence,
        signals_snapshot_json=json.dumps(dict(sorted(output.signals_snapshot.items())), sort_keys=True),
        explanation_json=json.dumps(output.explanation, sort_keys=True),
        generated_trade_idea=generated_trade_idea,
        validation_result_json=json.dumps(validation_payload, sort_keys=True) if validation_payload else None,
        created_at=timestamp_value,
        research_run_id=research_run_id,
        dataset_snapshot_id=dataset_snapshot_id,
    )


def validation_payload(result: ValidationResult) -> dict:
    return {
        "is_valid": result.is_valid,
        "reasons": result.reasons,
        "metrics": result.metrics,
        "validated_at": result.validated_at,
    }


def _register_strategy(
    registry: HypothesisRegistry,
    repository: DataRepository,
    definition,
    signal_types: tuple[str, ...],
) -> None:
    strategy_spec = repository.get_strategy_spec(definition.hypothesis_id, definition.version)
    if strategy_spec is None:
        registry.register(replace(definition, status="draft"), signal_types)
        return
    try:
        registry.activate(definition, signal_types, strategy_spec)
    except ValueError:
        registry.register(replace(definition, status="draft"), signal_types)


def _latest_price_timestamp(repository: DataRepository, asset_id: str) -> str:
    try:
        points = repository.read_raw_values(asset_id, "price")
    except AttributeError:
        return utc_now_iso()
    if not points:
        return utc_now_iso()
    return points[-1].timestamp


def _apply_research_gate(
    repository: DataRepository,
    output: HypothesisOutput,
    result: ValidationResult,
) -> ValidationResult:
    reasons = list(result.reasons)
    metrics: dict[str, Any] = dict(result.metrics)
    strategy_spec = repository.get_strategy_spec(output.hypothesis_id, output.version)
    if strategy_spec is None:
        return result
    parameters = strategy_spec_parameters(strategy_spec)
    snapshot = _latest_snapshot_for_universe(repository, strategy_spec.universe_id)
    if snapshot is None:
        reasons.append("missing_dataset_snapshot")
    elif output.asset_id not in snapshot.asset_ids:
        reasons.append("unsupported_universe")
        metrics["research_gate.dataset_snapshot_id"] = snapshot.dataset_snapshot_id
    else:
        evidence = _latest_evidence_summary(
            repository,
            strategy_spec.strategy_spec_id,
            snapshot.dataset_snapshot_id,
        )
        if evidence is None:
            reasons.append("missing_strategy_evidence")
        metrics["research_gate.dataset_snapshot_id"] = snapshot.dataset_snapshot_id
    if output.horizon != parameters.get("holding_horizon"):
        reasons.append("unsupported_horizon")
    if not reasons:
        return result
    metrics["research_gate.strategy_spec_id"] = strategy_spec.strategy_spec_id
    metrics["research_gate.expected_horizon"] = parameters.get("holding_horizon")
    metrics["research_gate.output_horizon"] = output.horizon
    deduped_reasons = tuple(dict.fromkeys(reasons))
    return ValidationResult(
        is_valid=False,
        reasons=list(deduped_reasons),
        metrics=metrics,
        validated_at=result.validated_at,
    )


def _latest_snapshot_for_universe(
    repository: DataRepository,
    universe_id: str,
):
    snapshots = [
        snapshot
        for snapshot in repository.get_dataset_snapshots()
        if snapshot.universe_id == universe_id
    ]
    return snapshots[-1] if snapshots else None


def _latest_evidence_summary(
    repository: DataRepository,
    strategy_spec_id: str,
    dataset_snapshot_id: str | None,
):
    matches = [
        summary
        for summary in repository.get_strategy_evidence_summaries()
        if summary.strategy_spec_id == strategy_spec_id
        and (dataset_snapshot_id is None or summary.dataset_snapshot_id == dataset_snapshot_id)
    ]
    return matches[-1] if matches else None
