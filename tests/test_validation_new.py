from __future__ import annotations

from datetime import datetime, timezone, timedelta
from uuid import uuid4

from project.common.models import HypothesisStatus
from project.data.models import HypothesisEvaluation
from project.data.repository import DataRepository
from project.hypotheses.registry import HypothesisRegistry, HypothesisDefinition
from project.validation.engine import ValidationEngine
from project.validation.models import ValidationResult
from project.validation.validators import (
    malformed_signal_payload_validator,
    inconsistent_timestamps_validator,
    confidence_out_of_range_validator,
    invalid_hypothesis_version_validator,
    duplicate_signal_definitions_validator,
    impossible_directional_conflicts_validator,
)


def test_malformed_signal_payload_validator() -> None:
    """Test malformed signal payload validator."""
    # Valid JSON
    evaluation = HypothesisEvaluation(
        evaluation_id="test",
        asset_id="asset:TEST",
        hypothesis_id="hypothesis:test",
        hypothesis_version=1,
        timestamp="2026-05-06T00:00:00Z",
        direction="long",
        confidence=0.8,
        signals_snapshot_json='{"rsi_14": 30.0}',
        explanation_json='{"rule": "test"}',
        generated_trade_idea=False,
        validation_result_json=None,
        created_at="2026-05-06T00:00:00Z",
    )
    
    result = malformed_signal_payload_validator(evaluation, {})
    assert result.is_valid == True
    assert result.reasons == []
    
    # Invalid signals_snapshot_json
    evaluation_bad_signals = HypothesisEvaluation(
        evaluation_id="test",
        asset_id="asset:TEST",
        hypothesis_id="hypothesis:test",
        hypothesis_version=1,
        timestamp="2026-05-06T00:00:00Z",
        direction="long",
        confidence=0.8,
        signals_snapshot_json='{"rsi_14":}',  # Invalid JSON
        explanation_json='{"rule": "test"}',
        generated_trade_idea=False,
        validation_result_json=None,
        created_at="2026-05-06T00:00:00Z",
    )
    
    result = malformed_signal_payload_validator(evaluation_bad_signals, {})
    assert result.is_valid == False
    assert "malformed_signal_payload" in result.reasons
    assert "Invalid signals_snapshot_json" in result.metrics["error"]
    
    # Invalid explanation_json
    evaluation_bad_explanation = HypothesisEvaluation(
        evaluation_id="test",
        asset_id="asset:TEST",
        hypothesis_id="hypothesis:test",
        hypothesis_version=1,
        timestamp="2026-05-06T00:00:00Z",
        direction="long",
        confidence=0.8,
        signals_snapshot_json='{"rsi_14": 30.0}',
        explanation_json='{"rule":}',  # Invalid JSON
        generated_trade_idea=False,
        validation_result_json=None,
        created_at="2026-05-06T00:00:00Z",
    )
    
    result = malformed_signal_payload_validator(evaluation_bad_explanation, {})
    assert result.is_valid == False
    assert "malformed_signal_payload" in result.reasons
    assert "Invalid explanation_json" in result.metrics["error"]


def test_inconsistent_timestamps_validator() -> None:
    """Test inconsistent timestamps validator."""
    now = datetime.now(timezone.utc)
    
    # Valid timestamp (recent)
    evaluation_recent = HypothesisEvaluation(
        evaluation_id="test",
        asset_id="asset:TEST",
        hypothesis_id="hypothesis:test",
        hypothesis_version=1,
        timestamp=now.isoformat().replace("+00:00", "Z"),
        direction="long",
        confidence=0.8,
        signals_snapshot_json='{"rsi_14": 30.0}',
        explanation_json='{"rule": "test"}',
        generated_trade_idea=False,
        validation_result_json=None,
        created_at="2026-05-06T00:00:00Z",
    )
    
    result = inconsistent_timestamps_validator(evaluation_recent, {})
    assert result.is_valid == True
    assert result.reasons == []
    
    # Too far in future
    future_time = now + timedelta(days=2)
    evaluation_future = HypothesisEvaluation(
        evaluation_id="test",
        asset_id="asset:TEST",
        hypothesis_id="hypothesis:test",
        hypothesis_version=1,
        timestamp=future_time.isoformat().replace("+00:00", "Z"),
        direction="long",
        confidence=0.8,
        signals_snapshot_json='{"rsi_14": 30.0}',
        explanation_json='{"rule": "test"}',
        generated_trade_idea=False,
        validation_result_json=None,
        created_at="2026-05-06T00:00:00Z",
    )
    
    result = inconsistent_timestamps_validator(evaluation_future, {})
    assert result.is_valid == False
    assert "inconsistent_timestamps" in result.reasons
    assert result.metrics["issue"] == "timestamp_too_far_in_future"
    
    # Too far in past
    past_time = now - timedelta(days=10)
    evaluation_past = HypothesisEvaluation(
        evaluation_id="test",
        asset_id="asset:TEST",
        hypothesis_id="hypothesis:test",
        hypothesis_version=1,
        timestamp=past_time.isoformat().replace("+00:00", "Z"),
        direction="long",
        confidence=0.8,
        signals_snapshot_json='{"rsi_14": 30.0}',
        explanation_json='{"rule": "test"}',
        generated_trade_idea=False,
        validation_result_json=None,
        created_at="2026-05-06T00:00:00Z",
    )
    
    result = inconsistent_timestamps_validator(evaluation_past, {})
    assert result.is_valid == False
    assert "inconsistent_timestamps" in result.reasons
    assert result.metrics["issue"] == "timestamp_too_far_in_past"
    
    # Invalid timestamp format
    evaluation_invalid = HypothesisEvaluation(
        evaluation_id="test",
        asset_id="asset:TEST",
        hypothesis_id="hypothesis:test",
        hypothesis_version=1,
        timestamp="not-a-timestamp",
        direction="long",
        confidence=0.8,
        signals_snapshot_json='{"rsi_14": 30.0}',
        explanation_json='{"rule": "test"}',
        generated_trade_idea=False,
        validation_result_json=None,
        created_at="2026-05-06T00:00:00Z",
    )
    
    result = inconsistent_timestamps_validator(evaluation_invalid, {})
    assert result.is_valid == False
    assert "inconsistent_timestamps" in result.reasons
    assert "Invalid timestamp format" in result.metrics["error"]


def test_confidence_out_of_range_validator() -> None:
    """Test confidence out of range validator."""
    # Valid confidence
    evaluation_valid = HypothesisEvaluation(
        evaluation_id="test",
        asset_id="asset:TEST",
        hypothesis_id="hypothesis:test",
        hypothesis_version=1,
        timestamp="2026-05-06T00:00:00Z",
        direction="long",
        confidence=0.8,  # Valid range
        signals_snapshot_json='{"rsi_14": 30.0}',
        explanation_json='{"rule": "test"}',
        generated_trade_idea=False,
        validation_result_json=None,
        created_at="2026-05-06T00:00:00Z",
    )
    
    result = confidence_out_of_range_validator(evaluation_valid, {})
    assert result.is_valid == True
    assert result.reasons == []
    
    # Too low confidence
    evaluation_low = HypothesisEvaluation(
        evaluation_id="test",
        asset_id="asset:TEST",
        hypothesis_id="hypothesis:test",
        hypothesis_version=1,
        timestamp="2026-05-06T00:00:00Z",
        direction="long",
        confidence=-0.1,  # Below valid range
        signals_snapshot_json='{"rsi_14": 30.0}',
        explanation_json='{"rule": "test"}',
        generated_trade_idea=False,
        validation_result_json=None,
        created_at="2026-05-06T00:00:00Z",
    )
    
    result = confidence_out_of_range_validator(evaluation_low, {})
    assert result.is_valid == False
    assert "confidence_out_of_range" in result.reasons
    assert result.metrics["confidence"] == -0.1
    assert result.metrics["min_allowed"] == 0.0
    assert result.metrics["max_allowed"] == 1.0
    
    # Too high confidence
    evaluation_high = HypothesisEvaluation(
        evaluation_id="test",
        asset_id="asset:TEST",
        hypothesis_id="hypothesis:test",
        hypothesis_version=1,
        timestamp="2026-05-06T00:00:00Z",
        direction="long",
        confidence=1.5,  # Above valid range
        signals_snapshot_json='{"rsi_14": 30.0}',
        explanation_json='{"rule": "test"}',
        generated_trade_idea=False,
        validation_result_json=None,
        created_at="2026-05-06T00:00:00Z",
    )
    
    result = confidence_out_of_range_validator(evaluation_high, {})
    assert result.is_valid == False
    assert "confidence_out_of_range" in result.reasons
    assert result.metrics["confidence"] == 1.5


def test_invalid_hypothesis_version_validator() -> None:
    """Test invalid hypothesis version validator."""
    # Valid version
    evaluation_valid = HypothesisEvaluation(
        evaluation_id="test",
        asset_id="asset:TEST",
        hypothesis_id="hypothesis:test",
        hypothesis_version=1,
        timestamp="2026-05-06T00:00:00Z",
        direction="long",
        confidence=0.8,
        signals_snapshot_json='{"rsi_14": 30.0}',
        explanation_json='{"rule": "test"}',
        generated_trade_idea=False,
        validation_result_json=None,
        created_at="2026-05-06T00:00:00Z",
    )
    
    registry = HypothesisRegistry()
    definition = HypothesisDefinition(
        hypothesis_id="hypothesis:test",
        name="Test Hypothesis",
        version=1,
        definition={},
        explainability_level="full",
        status="active"
    )
    registry.register(definition, ("rsi_14",))
    
    result = invalid_hypothesis_version_validator(evaluation_valid, {"hypothesis_registry": registry})
    assert result.is_valid == True
    assert result.reasons == []
    
    # Invalid version (too low)
    evaluation_wrong_version = HypothesisEvaluation(
        evaluation_id="test",
        asset_id="asset:TEST",
        hypothesis_id="hypothesis:test",
        hypothesis_version=0,  # Wrong version
        timestamp="2026-05-06T00:00:00Z",
        direction="long",
        confidence=0.8,
        signals_snapshot_json='{"rsi_14": 30.0}',
        explanation_json='{"rule": "test"}',
        generated_trade_idea=False,
        validation_result_json=None,
        created_at="2026-05-06T00:00:00Z",
    )
    
    result = invalid_hypothesis_version_validator(evaluation_wrong_version, {"hypothesis_registry": registry})
    assert result.is_valid == False
    assert "invalid_hypothesis_version" in result.reasons
    assert result.metrics["evaluation_version"] == 0
    assert result.metrics["registered_version"] == 1
    
    # Invalid version (too high)
    evaluation_wrong_version_high = HypothesisEvaluation(
        evaluation_id="test",
        asset_id="asset:TEST",
        hypothesis_id="hypothesis:test",
        hypothesis_version=2,  # Wrong version
        timestamp="2026-05-06T00:00:00Z",
        direction="long",
        confidence=0.8,
        signals_snapshot_json='{"rsi_14": 30.0}',
        explanation_json='{"rule": "test"}',
        generated_trade_idea=False,
        validation_result_json=None,
        created_at="2026-05-06T00:00:00Z",
    )
    
    result = invalid_hypothesis_version_validator(evaluation_wrong_version_high, {"hypothesis_registry": registry})
    assert result.is_valid == False
    assert "invalid_hypothesis_version" in result.reasons
    assert result.metrics["evaluation_version"] == 2
    assert result.metrics["registered_version"] == 1


def test_impossible_directional_conflicts_validator() -> None:
    """Test impossible directional conflicts validator."""
    # Valid direction
    evaluation_valid = HypothesisEvaluation(
        evaluation_id="test",
        asset_id="asset:TEST",
        hypothesis_id="hypothesis:test",
        hypothesis_version=1,
        timestamp="2026-05-06T00:00:00Z",
        direction="long",  # Valid direction
        confidence=0.8,
        signals_snapshot_json='{"rsi_14": 30.0}',
        explanation_json='{"rule": "test"}',
        generated_trade_idea=False,
        validation_result_json=None,
        created_at="2026-05-06T00:00:00Z",
    )
    
    result = impossible_directional_conflicts_validator(evaluation_valid, {})
    assert result.is_valid == True
    assert result.reasons == []
    
    # Invalid direction
    evaluation_invalid = HypothesisEvaluation(
        evaluation_id="test",
        asset_id="asset:TEST",
        hypothesis_id="hypothesis:test",
        hypothesis_version=1,
        timestamp="2026-05-06T00:00:00Z",
        direction="invalid_direction",  # Invalid direction
        confidence=0.8,
        signals_snapshot_json='{"rsi_14": 30.0}',
        explanation_json='{"rule": "test"}',
        generated_trade_idea=False,
        validation_result_json=None,
        created_at="2026-05-06T00:00:00Z",
    )
    
    result = impossible_directional_conflicts_validator(evaluation_invalid, {})
    assert result.is_valid == False
    assert "impossible_directional_conflicts" in result.reasons
    assert result.metrics["direction"] == "invalid_direction"
    assert "long" in result.metrics["allowed_directions"]
    assert "short" in result.metrics["allowed_directions"]
    assert "flat" in result.metrics["allowed_directions"]


def test_validation_engine_with_new_validators() -> None:
    """Test validation engine with all new validators."""
    # Valid evaluation
    evaluation = HypothesisEvaluation(
        evaluation_id="test",
        asset_id="asset:TEST",
        hypothesis_id="hypothesis:test",
        hypothesis_version=1,
        timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        direction="long",
        confidence=0.8,  # Above confidence threshold
        signals_snapshot_json='{"rsi_14": 30.0}',
        explanation_json='{"rule": "test"}',
        generated_trade_idea=False,
        validation_result_json=None,
        created_at="2026-05-06T00:00:00Z",
    )
    
    # Set up registry with active hypothesis
    registry = HypothesisRegistry()
    definition = HypothesisDefinition(
        hypothesis_id="hypothesis:test",
        name="Test Hypothesis",
        version=1,
        definition={},
        explainability_level="full",
        status="active"
    )
    registry.register(definition, ("rsi_14",))
    
    # Create mock repository
    class MockRepository:
        def get_trade_ideas(self, asset_id=None, hypothesis_id=None, direction=None):
            return ()  # No existing trade ideas
    
    repository = MockRepository()
    engine = ValidationEngine()
    
    result = engine.validate(
        evaluation=evaluation,
        repository=repository,
        hypothesis_registry=registry,
        max_signal_age_hours=24,
    )
    
    # Should be valid with all checks passing
    assert result.is_valid == True
    assert result.reasons == []
    # Check that we have metrics from validators that return metrics on success
    # Note: Some validators return empty metrics on success (e.g., malformed_signal_payload when valid)
    assert "confidence_out_of_range.confidence" in result.metrics
    assert "hypothesis_status.hypothesis_status" in result.metrics
    assert "signal_freshness.signal_age_hours" in result.metrics
    assert "signal_freshness.evaluation_timestamp" in result.metrics  # This one always returns timestamp
    assert "duplicate_exposure.existing_trade_ideas_count" in result.metrics
    assert "impossible_directional_conflicts.direction" in result.metrics
    
    # Check that we ran all validators by checking we have a reasonable number of metrics
    # (at least the ones that reliably return metrics on success)
    assert len(result.metrics) >= 6


def test_validation_engine_with_malformed_payload() -> None:
    """Test validation engine catches malformed payloads."""
    # Evaluation with invalid JSON
    evaluation = HypothesisEvaluation(
        evaluation_id="test",
        asset_id="asset:TEST",
        hypothesis_id="hypothesis:test",
        hypothesis_version=1,
        timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        direction="long",
        confidence=0.8,
        signals_snapshot_json='{"rsi_14":}',  # Invalid JSON
        explanation_json='{"rule": "test"}',
        generated_trade_idea=False,
        validation_result_json=None,
        created_at="2026-05-06T00:00:00Z",
    )
    
    # Set up registry
    registry = HypothesisRegistry()
    definition = HypothesisDefinition(
        hypothesis_id="hypothesis:test",
        name="Test Hypothesis",
        version=1,
        definition={},
        explainability_level="full",
        status="active"
    )
    registry.register(definition, ("rsi_14",))
    
    # Create mock repository
    class MockRepository:
        def get_trade_ideas(self, asset_id=None, hypothesis_id=None, direction=None):
            return ()
    
    repository = MockRepository()
    engine = ValidationEngine()
    
    result = engine.validate(
        evaluation=evaluation,
        repository=repository,
        hypothesis_registry=registry,
        max_signal_age_hours=24,
    )
    
    # Should be invalid due to malformed signal payload
    assert result.is_valid == False
    assert "malformed_signal_payload" in result.reasons
    assert len(result.reasons) >= 1  # At least this reason