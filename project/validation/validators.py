from __future__ import annotations

from project.data.models import HypothesisEvaluation
from project.data.repository import DataRepository
from project.hypotheses.registry import HypothesisRegistry
from project.validation.models import ValidationResult


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
    Reject if existing open trade idea exists for:
    * same asset
    * same direction
    * same hypothesis
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
    
    # Get existing trade ideas for the same asset, hypothesis, and direction
    existing_trade_ideas = repository.get_trade_ideas(
        asset_id=evaluation.asset_id,
        hypothesis_id=evaluation.hypothesis_id,
        direction=evaluation.direction
    )
    
    # If there are existing trade ideas, reject to prevent duplicate exposure
    is_valid = len(existing_trade_ideas) == 0
    reasons = [] if is_valid else ["duplicate_exposure"]
    metrics = {
        "evaluation_asset_id": evaluation.asset_id,
        "evaluation_hypothesis_id": evaluation.hypothesis_id,
        "evaluation_direction": evaluation.direction,
        "existing_trade_ideas_count": len(existing_trade_ideas)
    }
    return ValidationResult(
        is_valid=is_valid,
        reasons=reasons,
        metrics=metrics,
        validated_at=ValidationResult.now(),
    )