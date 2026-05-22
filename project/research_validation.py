from __future__ import annotations

import json
from typing import Any

from project.common.models import (
    StrategySpec,
    HypothesisOutput,
    strategy_spec_missing_fields,
    strategy_spec_parameters,
    utc_now_iso,
)
from project.data.models import HypothesisEvaluation
from project.data.repository import DataRepository
from project.cli_utils import load_hypothesis_registry
from project.validation.engine import ValidationEngine
from project.validation.models import ValidationResult


def validate_outputs(
    repository: DataRepository,
    outputs: tuple[HypothesisOutput, ...],
) -> list[tuple[HypothesisOutput, ValidationResult]]:
    validation_engine = ValidationEngine()
    registry = load_hypothesis_registry(repository)
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
    timestamp_value = timestamp or output.timestamp or utc_now_iso()
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
    strategy_spec = repository.get_strategy_spec(output.hypothesis_id, output.version)
    if strategy_spec is None:
        return _invalid_research_gate(result, ("invalid_hypothesis_status",), {})
    reasons, metrics = _research_gate_issues(repository, output, strategy_spec)
    if not reasons:
        return result
    metrics["research_gate.strategy_spec_id"] = strategy_spec.strategy_spec_id
    metrics["research_gate.expected_horizon"] = strategy_spec_parameters(strategy_spec).get(
        "holding_horizon"
    )
    metrics["research_gate.output_horizon"] = output.horizon
    return _invalid_research_gate(result, tuple(reasons), metrics)


def _research_gate_issues(
    repository: DataRepository,
    output: HypothesisOutput,
    strategy_spec: StrategySpec,
) -> tuple[list[str], dict[str, Any]]:
    reasons: list[str] = []
    metrics: dict[str, Any] = {}
    snapshot = _latest_snapshot_for_universe(repository, strategy_spec.universe_id)
    if snapshot is None:
        reasons.append("missing_dataset_snapshot")
        return reasons, metrics
    metrics["research_gate.dataset_snapshot_id"] = snapshot.dataset_snapshot_id
    if output.asset_id not in snapshot.asset_ids:
        reasons.append("unsupported_universe")
    evidence = _latest_evidence_summary(
        repository,
        strategy_spec.strategy_spec_id,
        snapshot.dataset_snapshot_id,
    )
    if evidence is None:
        reasons.append("missing_strategy_evidence")
    parameters = strategy_spec_parameters(strategy_spec)
    if output.horizon != parameters.get("holding_horizon"):
        reasons.append("unsupported_horizon")
    return reasons, metrics


def _invalid_research_gate(
    result: ValidationResult,
    reasons: tuple[str, ...],
    metrics: dict[str, Any],
) -> ValidationResult:
    merged = list(dict.fromkeys([*result.reasons, *reasons]))
    merged_metrics = dict(result.metrics)
    merged_metrics.update(metrics)
    return ValidationResult(
        is_valid=False,
        reasons=merged,
        metrics=merged_metrics,
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
    return max(snapshots, key=_snapshot_sort_key, default=None)


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
    return max(matches, key=_evidence_sort_key, default=None)


def tradeability_blockers(
    strategy_spec: StrategySpec | None,
    latest_snapshot: object | None,
    latest_research_run: object | None,
    best_backtest: object | None,
    latest_evidence_summary: object | None,
    validation_errors: tuple[str, ...] = (),
) -> tuple[str, ...]:
    if strategy_spec is None:
        return ("missing_strategy_spec",)
    blockers = list(strategy_spec_missing_fields(strategy_spec))
    blockers.extend(_tradeability_blockers(
        latest_snapshot,
        latest_research_run,
        best_backtest,
        latest_evidence_summary,
    ))
    blockers.extend(validation_errors)
    return tuple(dict.fromkeys(blockers))


def _tradeability_blockers(
    latest_snapshot: object | None,
    latest_research_run: object | None,
    best_backtest: object | None,
    latest_evidence_summary: object | None,
) -> list[str]:
    blockers: list[str] = []
    if latest_snapshot is None:
        blockers.append("missing_dataset_snapshot")
    if latest_research_run is None:
        blockers.append("missing_research_run")
    elif getattr(latest_research_run, "status", "") != "completed":
        blockers.append("latest_research_run_not_completed")
    if best_backtest is None:
        blockers.append("missing_backtest_result")
    elif latest_research_run is not None and getattr(best_backtest, "research_run_id", None) not in (None, getattr(latest_research_run, "research_run_id", None)):
        blockers.append("best_backtest_not_on_latest_run")
    if latest_snapshot is not None and best_backtest is not None:
        if getattr(best_backtest, "dataset_snapshot_id", None) not in (None, getattr(latest_snapshot, "dataset_snapshot_id", None)):
            blockers.append("best_backtest_not_on_latest_snapshot")
    if latest_evidence_summary is None:
        blockers.append("missing_evidence_summary")
    elif latest_research_run is not None and getattr(latest_evidence_summary, "research_run_id", None) not in (None, getattr(latest_research_run, "research_run_id", None)):
        blockers.append("evidence_not_on_latest_run")
    if latest_snapshot is not None and latest_evidence_summary is not None and getattr(latest_evidence_summary, "dataset_snapshot_id", None) not in (None, getattr(latest_snapshot, "dataset_snapshot_id", None)):
        blockers.append("evidence_not_on_latest_snapshot")
    return blockers


def _snapshot_sort_key(snapshot) -> tuple[str, str]:
    return (snapshot.captured_at or snapshot.data_end or "", snapshot.dataset_snapshot_id or "")


def _evidence_sort_key(summary) -> tuple[str, str]:
    return (summary.created_at or "", summary.evidence_summary_id or "")
