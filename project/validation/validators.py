from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any

from project.data.models import HypothesisEvaluation
from project.data.repository import DataRepository
from project.hypotheses.registry import HypothesisRegistry
from project.validation.models import ValidationResult


def confidence_validator(
    evaluation: HypothesisEvaluation,
    context: dict,
) -> ValidationResult:
    metrics = {"confidence_threshold": 0.55, "actual_confidence": evaluation.confidence}
    if evaluation.confidence >= 0.55:
        return _result(True, (), metrics)
    return _result(False, ("low_confidence",), metrics)


def hypothesis_status_validator(
    evaluation: HypothesisEvaluation,
    context: dict,
) -> ValidationResult:
    registry: HypothesisRegistry | None = context.get("hypothesis_registry")
    if registry is None:
        return _result(True, (), {})
    definition = registry.get_definition(evaluation.hypothesis_id)
    if definition is None:
        return _result(
            False,
            ("invalid_hypothesis_status",),
            {"hypothesis_id": evaluation.hypothesis_id},
        )
    allowed = ("testing", "active")
    metrics = {
        "hypothesis_id": evaluation.hypothesis_id,
        "hypothesis_status": definition.status,
        "allowed_statuses": list(allowed),
    }
    if definition.status not in allowed:
        return _result(False, ("invalid_hypothesis_status",), metrics)
    return _result(True, (), metrics)


def signal_freshness_validator(
    evaluation: HypothesisEvaluation,
    context: dict,
) -> ValidationResult:
    max_age_hours = float(context.get("max_signal_age_hours", 24))
    now = datetime.now(UTC)
    try:
        timestamp = _parse_timestamp(evaluation.timestamp)
    except ValueError as error:
        return _result(
            False,
            ("stale_signals",),
            {"error": str(error), "evaluation_timestamp": evaluation.timestamp},
        )
    age_hours = (now - timestamp).total_seconds() / 3600
    metrics = {
        "signal_age_hours": age_hours,
        "max_age_hours": max_age_hours,
        "evaluation_timestamp": evaluation.timestamp,
    }
    if age_hours > max_age_hours:
        return _result(False, ("stale_signals",), metrics)
    return _result(True, (), metrics)


def duplicate_exposure_validator(
    evaluation: HypothesisEvaluation,
    context: dict,
) -> ValidationResult:
    repository: DataRepository | None = context.get("repository")
    if repository is None:
        return _result(True, (), {})
    open_positions = repository.get_positions(
        asset_id=evaluation.asset_id,
        hypothesis_id=evaluation.hypothesis_id,
        direction=evaluation.direction,
        status="open",
    )
    pending_ideas = repository.get_open_trade_ideas(
        asset_id=evaluation.asset_id,
        hypothesis_id=evaluation.hypothesis_id,
        direction=evaluation.direction,
    )
    metrics = {
        "evaluation_asset_id": evaluation.asset_id,
        "evaluation_hypothesis_id": evaluation.hypothesis_id,
        "evaluation_direction": evaluation.direction,
        "open_positions_count": len(open_positions),
        "pending_trade_ideas_count": len(pending_ideas),
    }
    if open_positions or pending_ideas:
        return _result(False, ("duplicate_exposure",), metrics)
    return _result(True, (), metrics)


def malformed_signal_payload_validator(
    evaluation: HypothesisEvaluation,
    context: dict,
) -> ValidationResult:
    signals_snapshot, duplicate_signal_keys = _load_json_object(evaluation.signals_snapshot_json)
    if signals_snapshot is None:
        return _result(
            False,
            ("malformed_signal_payload",),
            {"error": "Invalid signals_snapshot_json"},
        )
    if duplicate_signal_keys:
        return _result(
            False,
            ("duplicate_signal_definitions",),
            {"duplicate_signals": duplicate_signal_keys},
        )
    if _load_json_object(evaluation.explanation_json)[0] is None:
        return _result(
            False,
            ("malformed_signal_payload",),
            {"error": "Invalid explanation_json"},
        )
    return _signal_dependency_validation(context.get("hypothesis_registry"), evaluation, signals_snapshot)


def inconsistent_timestamps_validator(
    evaluation: HypothesisEvaluation,
    context: dict,
) -> ValidationResult:
    now = datetime.now(UTC)
    try:
        timestamp = _parse_timestamp(evaluation.timestamp)
    except ValueError as error:
        return _result(
            False,
            ("inconsistent_timestamps",),
            {"error": f"Invalid timestamp format: {error}"},
        )
    future_threshold = now + timedelta(days=1)
    past_threshold = now - timedelta(days=7)
    if timestamp > future_threshold:
        return _result(
            False,
            ("inconsistent_timestamps",),
            {
                "evaluation_timestamp": evaluation.timestamp,
                "current_time": now.isoformat(),
                "issue": "timestamp_too_far_in_future",
            },
        )
    if timestamp < past_threshold:
        return _result(
            False,
            ("inconsistent_timestamps",),
            {
                "evaluation_timestamp": evaluation.timestamp,
                "current_time": now.isoformat(),
                "issue": "timestamp_too_far_in_past",
            },
        )
    return _result(True, (), {"evaluation_timestamp": evaluation.timestamp})


def confidence_out_of_range_validator(
    evaluation: HypothesisEvaluation,
    context: dict,
) -> ValidationResult:
    metrics = {"confidence": evaluation.confidence, "min_allowed": 0.0, "max_allowed": 1.0}
    if 0.0 <= evaluation.confidence <= 1.0:
        return _result(True, (), metrics)
    return _result(False, ("confidence_out_of_range",), metrics)


def invalid_hypothesis_version_validator(
    evaluation: HypothesisEvaluation,
    context: dict,
) -> ValidationResult:
    if evaluation.hypothesis_version < 1:
        return _result(
            False,
            ("invalid_hypothesis_version",),
            {"evaluation_version": evaluation.hypothesis_version},
        )
    registry: HypothesisRegistry | None = context.get("hypothesis_registry")
    if registry is None:
        return _result(True, (), {})
    definition = registry.get_definition(evaluation.hypothesis_id)
    if definition is None:
        return _result(True, (), {})
    if evaluation.hypothesis_version != definition.version:
        return _result(
            False,
            ("invalid_hypothesis_version",),
            {
                "evaluation_version": evaluation.hypothesis_version,
                "registered_version": definition.version,
                "hypothesis_id": evaluation.hypothesis_id,
            },
        )
    return _result(True, (), {})


def duplicate_signal_definitions_validator(
    evaluation: HypothesisEvaluation,
    context: dict,
) -> ValidationResult:
    registry: HypothesisRegistry | None = context.get("hypothesis_registry")
    if registry is None:
        return _result(True, (), {})
    if registry.get_definition(evaluation.hypothesis_id) is None:
        return _result(True, (), {})
    required_signals = registry.required_signals(evaluation.hypothesis_id)
    duplicate_signals = sorted({signal for signal in required_signals if required_signals.count(signal) > 1})
    if duplicate_signals:
        return _result(
            False,
            ("duplicate_signal_definitions",),
            {"duplicate_signals": duplicate_signals},
        )
    return _result(True, (), {})


def impossible_directional_conflicts_validator(
    evaluation: HypothesisEvaluation,
    context: dict,
) -> ValidationResult:
    allowed_directions = ("long", "short", "flat")
    metrics = {"direction": evaluation.direction}
    if evaluation.direction not in allowed_directions:
        metrics["allowed_directions"] = list(allowed_directions)
        return _result(False, ("impossible_directional_conflicts",), metrics)
    return _result(True, (), metrics)


def _load_json_object(payload: str | None) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    if not payload:
        return None, ()
    duplicate_keys: list[str] = []

    def object_pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        data: dict[str, Any] = {}
        for key, value in pairs:
            if key in data and key not in duplicate_keys:
                duplicate_keys.append(key)
            data[key] = value
        return data

    try:
        parsed = json.loads(payload, object_pairs_hook=object_pairs_hook)
    except (json.JSONDecodeError, TypeError):
        return None, ()
    if not isinstance(parsed, dict):
        return None, ()
    return parsed, tuple(duplicate_keys)


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _signal_dependency_validation(
    registry: HypothesisRegistry | None,
    evaluation: HypothesisEvaluation,
    signals_snapshot: dict[str, Any],
) -> ValidationResult:
    if registry is None:
        return _result(True, (), {})
    definition = registry.get_definition(evaluation.hypothesis_id)
    if definition is None:
        return _result(True, (), {})
    required_signals = registry.required_signals(evaluation.hypothesis_id)
    missing = [signal for signal in required_signals if signal not in signals_snapshot]
    if missing:
        return _result(
            False,
            ("missing_signal_dependencies",),
            {
                "missing_signals": missing,
                "required_signals": list(required_signals),
                "available_signals": list(signals_snapshot.keys()),
            },
        )
    return _result(True, (), {})


def _result(
    is_valid: bool,
    reasons: tuple[str, ...],
    metrics: dict[str, Any],
) -> ValidationResult:
    return ValidationResult(
        is_valid=is_valid,
        reasons=list(reasons),
        metrics=dict(metrics),
        validated_at=ValidationResult.now(),
    )
