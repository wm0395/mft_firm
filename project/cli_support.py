from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

from project.common.models import Asset, DecisionAction, DecisionReason, HypothesisOutput, utc_now_iso
from project.data.models import HypothesisEvaluation
from project.data.repository import DataRepository
from project.hypotheses.ma_crossover import MACrossoverHypothesis
from project.hypotheses.registry import HypothesisRegistry
from project.hypotheses.rsi_mean_reversion import RSIMeanReversionHypothesis
from project.validation.engine import ValidationEngine
from project.validation.models import ValidationResult


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


def validate_outputs(
    repository: DataRepository,
    outputs: tuple[HypothesisOutput, ...],
) -> list[tuple[HypothesisOutput, ValidationResult]]:
    validation_engine = ValidationEngine()
    registry = HypothesisRegistry()
    registry.register(RSIMeanReversionHypothesis.definition, ("rsi_14",))
    registry.register(MACrossoverHypothesis.definition, ("ma_5", "ma_20"))
    return [
        (
            output,
            validation_engine.validate(
                evaluation=evaluation_from_output(output, False, None),
                repository=repository,
                hypothesis_registry=registry,
                max_signal_age_hours=24,
            ),
        )
        for output in outputs
    ]


def evaluation_from_output(
    output: HypothesisOutput,
    generated_trade_idea: bool,
    validation_payload: dict | None,
) -> HypothesisEvaluation:
    return HypothesisEvaluation(
        evaluation_id=f"eval:{output.asset_id}:{output.hypothesis_id}:{output.version}:{uuid4()}",
        asset_id=output.asset_id,
        hypothesis_id=output.hypothesis_id,
        hypothesis_version=output.version,
        timestamp=utc_now_iso(),
        direction=output.direction,
        confidence=output.confidence,
        signals_snapshot_json=json.dumps(dict(sorted(output.signals_snapshot.items())), sort_keys=True),
        explanation_json=json.dumps(output.explanation, sort_keys=True),
        generated_trade_idea=generated_trade_idea,
        validation_result_json=json.dumps(validation_payload, sort_keys=True) if validation_payload else None,
        created_at=utc_now_iso(),
    )


def validation_payload(result: ValidationResult) -> dict:
    return {
        "is_valid": result.is_valid,
        "reasons": result.reasons,
        "metrics": result.metrics,
        "validated_at": result.validated_at,
    }


def decision_action(value: str) -> DecisionAction:
    return cast(DecisionAction, {"approve": "approve", "reject": "reject", "watchlist": "watch"}[value])


def decision_reason(value: str | None) -> DecisionReason:
    return cast(DecisionReason, value or "market_conditions")
