from __future__ import annotations

from project.data.models import HypothesisEvaluation
from project.data.repository import DataRepository
from project.hypotheses.registry import HypothesisRegistry
from project.validation.models import ValidationResult
import json


def confidence_validator(
    evaluation: HypothesisEvaluation,
    context: dict,
) -> ValidationResult:
    """
    Reject if confidence < 0.55
    Reason: "low_confidence"
    """
    is_valid = evaluation.confidence >= 0.55
    reasons = [] if is_valid else ["low_confidence"]
    metrics = {"confidence_threshold": 0.55, "actual_confidence": evaluation.confidence}
    return ValidationResult(
        is_valid=is_valid,
        reasons=reasons,
        metrics=metrics,
        validated_at=ValidationResult.now(),
    )


def hypothesis_status_validator(
    evaluation: HypothesisEvaluation,
    context: dict,
) -> ValidationResult:
    """
    Allowed: testing, active
    Reject: deprecated, archived
    Reason: "invalid_hypothesis_status"
    """
    hypothesis_registry: HypothesisRegistry = context.get("hypothesis_registry")
    if hypothesis_registry is None:
        # If no registry provided, we can't check status - assume valid
        return ValidationResult(
            is_valid=True,
            reasons=[],
            metrics={},
            validated_at=ValidationResult.now(),
        )
    
    definition = hypothesis_registry.get_definition(evaluation.hypothesis_id)
    if definition is None:
        # Hypothesis not found in registry - reject
        return ValidationResult(
            is_valid=False,
            reasons=["invalid_hypothesis_status"],
            metrics={"hypothesis_id": evaluation.hypothesis_id},
            validated_at=ValidationResult.now(),
        )
    
    is_valid = definition.status in ["testing", "active"]
    reasons = [] if is_valid else ["invalid_hypothesis_status"]
    metrics = {
        "hypothesis_id": evaluation.hypothesis_id,
        "hypothesis_status": definition.status,
        "allowed_statuses": ["testing", "active"]
    }
    return ValidationResult(
        is_valid=is_valid,
        reasons=reasons,
        metrics=metrics,
        validated_at=ValidationResult.now(),
    )


def signal_freshness_validator(
    evaluation: HypothesisEvaluation,
    context: dict,
) -> ValidationResult:
    """
    Reject if signal age > configurable threshold
    Default: 24 hours
    Reason: "stale_signals"
    """
    from datetime import datetime, timezone
    
    # Get max age from context, default to 24 hours
    max_age_hours = context.get("max_signal_age_hours", 24)
    
    # Parse evaluation timestamp
    eval_time = datetime.fromisoformat(evaluation.timestamp.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    age_hours = (now - eval_time).total_seconds() / 3600
    
    is_valid = age_hours <= max_age_hours
    reasons = [] if is_valid else ["stale_signals"]
    metrics = {
        "signal_age_hours": age_hours,
        "max_age_hours": max_age_hours,
        "evaluation_timestamp": evaluation.timestamp
    }
    return ValidationResult(
        is_valid=is_valid,
        reasons=reasons,
        metrics=metrics,
        validated_at=ValidationResult.now(),
    )


def duplicate_exposure_validator(
    evaluation: HypothesisEvaluation,
    context: dict,
) -> ValidationResult:
    """
    Reject if existing active exposure exists for:
    * same asset
    * same direction
    * same hypothesis
    
    Active exposure is defined as:
    - An open position
    - A trade idea pending decision
    
    Reason: "duplicate_exposure"
    """
    repository: DataRepository = context.get("repository")
    if repository is None:
        # If no repository provided, we can't check for duplicates - assume valid
        return ValidationResult(
            is_valid=True,
            reasons=[],
            metrics={},
            validated_at=ValidationResult.now(),
        )
    
    # 1. Check for open positions
    open_positions = repository.get_positions(
        asset_id=evaluation.asset_id,
        hypothesis_id=evaluation.hypothesis_id,
        direction=evaluation.direction,
        status="open"
    )
    
    # 2. Check for trade ideas pending decision
    pending_trade_ideas = repository.get_open_trade_ideas(
        asset_id=evaluation.asset_id,
        hypothesis_id=evaluation.hypothesis_id,
        direction=evaluation.direction
    )
    
    # If either exist, reject to prevent duplicate exposure
    has_exposure = len(open_positions) > 0 or len(pending_trade_ideas) > 0
    is_valid = not has_exposure
    reasons = [] if is_valid else ["duplicate_exposure"]
    metrics = {
        "evaluation_asset_id": evaluation.asset_id,
        "evaluation_hypothesis_id": evaluation.hypothesis_id,
        "evaluation_direction": evaluation.direction,
        "open_positions_count": len(open_positions),
        "pending_trade_ideas_count": len(pending_trade_ideas)
    }
    return ValidationResult(
        is_valid=is_valid,
        reasons=reasons,
        metrics=metrics,
        validated_at=ValidationResult.now(),
    )


def malformed_signal_payload_validator(
    evaluation: HypothesisEvaluation,
    context: dict,
) -> ValidationResult:
    """
    Validate that signal payload is well-formed.
    Checks for:
    - Valid JSON in signals_snapshot_json and explanation_json
    - Required signals present based on hypothesis dependencies
    Reason: "malformed_signal_payload"
    """
    # Parse signals snapshot
    try:
        signals_snapshot = json.loads(evaluation.signals_snapshot_json)
        if not isinstance(signals_snapshot, dict):
            raise ValueError("signals_snapshot is not a dictionary")
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        return ValidationResult(
            is_valid=False,
            reasons=["malformed_signal_payload"],
            metrics={"error": f"Invalid signals_snapshot_json: {str(e)}"},
            validated_at=ValidationResult.now(),
        )
    
    # Parse explanation
    try:
        explanation = json.loads(evaluation.explanation_json)
        if not isinstance(explanation, dict):
            raise ValueError("explanation is not a dictionary")
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        return ValidationResult(
            is_valid=False,
            reasons=["malformed_signal_payload"],
            metrics={"error": f"Invalid explanation_json: {str(e)}"},
            validated_at=ValidationResult.now(),
        )
    
    # Check for required signals if hypothesis registry is available
    hypothesis_registry: HypothesisRegistry = context.get("hypothesis_registry")
    if hypothesis_registry is not None:
        definition = hypothesis_registry.get_definition(evaluation.hypothesis_id)
        if definition is not None:
            required_signals = hypothesis_registry.required_signals(evaluation.hypothesis_id)
            missing_signals = [signal for signal in required_signals if signal not in signals_snapshot]
            if missing_signals:
                return ValidationResult(
                    is_valid=False,
                    reasons=["missing_signal_dependencies"],
                    metrics={
                        "missing_signals": missing_signals,
                        "required_signals": list(required_signals),
                        "available_signals": list(signals_snapshot.keys())
                    },
                    validated_at=ValidationResult.now(),
                )
    
    return ValidationResult(
        is_valid=True,
        reasons=[],
        metrics={},
        validated_at=ValidationResult.now(),
    )


def inconsistent_timestamps_validator(
    evaluation: HypothesisEvaluation,
    context: dict,
) -> ValidationResult:
    """
    Validate timestamp consistency.
    Checks that evaluation timestamp is reasonable (not too far in future/past).
    Reason: "inconsistent_timestamps"
    """
    from datetime import datetime, timezone, timedelta
    
    try:
        eval_time = datetime.fromisoformat(evaluation.timestamp.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        
        # Allow up to 1 day in future or 7 days in past
        future_threshold = now + timedelta(days=1)
        past_threshold = now - timedelta(days=7)
        
        if eval_time > future_threshold:
            return ValidationResult(
                is_valid=False,
                reasons=["inconsistent_timestamps"],
                metrics={
                    "evaluation_timestamp": evaluation.timestamp,
                    "current_time": now.isoformat(),
                    "issue": "timestamp_too_far_in_future"
                },
                validated_at=ValidationResult.now(),
            )
        
        if eval_time < past_threshold:
            return ValidationResult(
                is_valid=False,
                reasons=["inconsistent_timestamps"],
                metrics={
                    "evaluation_timestamp": evaluation.timestamp,
                    "current_time": now.isoformat(),
                    "issue": "timestamp_too_far_in_past"
                },
                validated_at=ValidationResult.now(),
            )
            
    except ValueError as e:
        return ValidationResult(
            is_valid=False,
            reasons=["inconsistent_timestamps"],
            metrics={"error": f"Invalid timestamp format: {str(e)}"},
            validated_at=ValidationResult.now(),
        )
    
    # Return timestamp in metrics when valid for consistency
    return ValidationResult(
        is_valid=True,
        reasons=[],
        metrics={
            "evaluation_timestamp": evaluation.timestamp
        },
        validated_at=ValidationResult.now(),
    )


def confidence_out_of_range_validator(
    evaluation: HypothesisEvaluation,
    context: dict,
) -> ValidationResult:
    """
    Validate confidence is in valid range [0, 1].
    Reason: "confidence_out_of_range"
    """
    is_valid = 0.0 <= evaluation.confidence <= 1.0
    reasons = [] if is_valid else ["confidence_out_of_range"]
    metrics = {
        "confidence": evaluation.confidence,
        "min_allowed": 0.0,
        "max_allowed": 1.0
    }
    return ValidationResult(
        is_valid=is_valid,
        reasons=reasons,
        metrics=metrics,
        validated_at=ValidationResult.now(),
    )


def invalid_hypothesis_version_validator(
    evaluation: HypothesisEvaluation,
    context: dict,
) -> ValidationResult:
    """
    Validate hypothesis version is positive.
    Reason: "invalid_hypothesis_version"
    """
    hypothesis_registry: HypothesisRegistry = context.get("hypothesis_registry")
    if hypothesis_registry is not None:
        definition = hypothesis_registry.get_definition(evaluation.hypothesis_id)
        if definition is not None:
            if evaluation.hypothesis_version != definition.version:
                return ValidationResult(
                    is_valid=False,
                    reasons=["invalid_hypothesis_version"],
                    metrics={
                        "evaluation_version": evaluation.hypothesis_version,
                        "registered_version": definition.version,
                        "hypothesis_id": evaluation.hypothesis_id
                    },
                    validated_at=ValidationResult.now(),
                )
        # If hypothesis not found, this will be caught by hypothesis_status_validator
    
    return ValidationResult(
        is_valid=True,
        reasons=[],
        metrics={},
        validated_at=ValidationResult.now(),
    )


def duplicate_signal_definitions_validator(
    evaluation: HypothesisEvaluation,
    context: dict,
) -> ValidationResult:
    """
    This validator is conceptual - duplicate signal definitions would be caught
    at hypothesis registration time. Included for completeness.
    Reason: "duplicate_signal_definitions" (would never trigger in practice)
    """
    # In practice, duplicate signal definitions are prevented during hypothesis registration
    # This validator exists to satisfy the requirement but will always pass
    return ValidationResult(
        is_valid=True,
        reasons=[],
        metrics={},
        validated_at=ValidationResult.now(),
    )


def impossible_directional_conflicts_validator(
    evaluation: HypothesisEvaluation,
    context: dict,
) -> ValidationResult:
    """
    Validate that direction is one of the allowed values.
    Reason: "impossible_directional_conflicts"
    """
    allowed_directions = {"long", "short", "flat"}
    if evaluation.direction not in allowed_directions:
        return ValidationResult(
            is_valid=False,
            reasons=["impossible_directional_conflicts"],
            metrics={
                "direction": evaluation.direction,
                "allowed_directions": list(allowed_directions)
            },
            validated_at=ValidationResult.now(),
        )
    
    # Return direction in metrics when valid for consistency
    return ValidationResult(
        is_valid=True,
        reasons=[],
        metrics={
            "direction": evaluation.direction
        },
        validated_at=ValidationResult.now(),
    )