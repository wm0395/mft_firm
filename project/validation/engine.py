from __future__ import annotations

from typing import Any

from project.data.models import HypothesisEvaluation
from project.data.repository import DataRepository
from project.hypotheses.registry import HypothesisRegistry
from project.validation.models import ValidationResult
from project.validation.validators import (
    confidence_validator,
    duplicate_exposure_validator,
    hypothesis_status_validator,
    signal_freshness_validator,
    malformed_signal_payload_validator,
    inconsistent_timestamps_validator,
    confidence_out_of_range_validator,
    invalid_hypothesis_version_validator,
    duplicate_signal_definitions_validator,
    impossible_directional_conflicts_validator,
)


class ValidationEngine:
    def __init__(self) -> None:
        # Validators are executed in this order
        # Order matters: basic validity checks first, then business logic
        self._validators = [
            malformed_signal_payload_validator,      # Check basic format first
            inconsistent_timestamps_validator,       # Check timestamp validity
            confidence_out_of_range_validator,       # Check confidence bounds
            invalid_hypothesis_version_validator,    # Check hypothesis version
            confidence_validator,                    # Check confidence threshold (business logic)
            hypothesis_status_validator,             # Check if hypothesis is active/testing
            signal_freshness_validator,              # Check if signals are fresh
            duplicate_exposure_validator,            # Check for duplicate exposures
            duplicate_signal_definitions_validator,  # Check for duplicate signal definitions (placeholder)
            impossible_directional_conflicts_validator, # Check for impossible directions
        ]

    def validate(
        self,
        evaluation: HypothesisEvaluation,
        repository: DataRepository,
        hypothesis_registry: HypothesisRegistry,
        max_signal_age_hours: int = 24,
    ) -> ValidationResult:
        """
        Execute all validators and aggregate results.
        
        Returns:
            ValidationResult: Combined validation result
        """
        context: dict[str, Any] = {
            "repository": repository,
            "hypothesis_registry": hypothesis_registry,
            "max_signal_age_hours": max_signal_age_hours,
        }
        
        all_reasons: list[str] = []
        all_metrics: dict[str, Any] = {}
        
        # Execute validators in order
        for validator in self._validators:
            result = validator(evaluation, context)
            all_reasons.extend(result.reasons)
            # Merge metrics with validator name as prefix
            validator_name = validator.__name__.replace("_validator", "")
            for key, value in result.metrics.items():
                all_metrics[f"{validator_name}.{key}"] = value
        
        is_valid = len(all_reasons) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            reasons=all_reasons,
            metrics=all_metrics,
            validated_at=ValidationResult.now(),
        )