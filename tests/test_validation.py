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
    confidence_validator,
    hypothesis_status_validator,
    signal_freshness_validator,
    duplicate_exposure_validator,
)


def test_confidence_validator() -> None:
    """Test confidence validator with various confidence values."""
    # Valid confidence
    evaluation = HypothesisEvaluation(
        evaluation_id="test",
        asset_id="asset:TEST",
        hypothesis_id="hypothesis:test",
        hypothesis_version=1,
        timestamp="2026-05-06T00:00:00Z",
        direction="long",
        confidence=0.6,  # Above threshold
        signals_snapshot_json='{"rsi_14": 30.0}',
        explanation_json='{"rule": "test"}',
        generated_trade_idea=False,
        validation_result_json=None,
        created_at="2026-05-06T00:00:00Z",
    )
    
    result = confidence_validator(evaluation, {})
    assert result.is_valid == True
    assert result.reasons == []
    assert result.metrics["actual_confidence"] == 0.6
    
    # Invalid confidence - create a new evaluation with low confidence
    evaluation_low = HypothesisEvaluation(
        evaluation_id="test",
        asset_id="asset:TEST",
        hypothesis_id="hypothesis:test",
        hypothesis_version=1,
        timestamp="2026-05-06T00:00:00Z",
        direction="long",
        confidence=0.5,  # Below threshold
        signals_snapshot_json='{"rsi_14": 30.0}',
        explanation_json='{"rule": "test"}',
        generated_trade_idea=False,
        validation_result_json=None,
        created_at="2026-05-06T00:00:00Z",
    )
    
    result = confidence_validator(evaluation_low, {})
    assert result.is_valid == False
    assert result.reasons == ["low_confidence"]
    assert result.metrics["actual_confidence"] == 0.5


def test_hypothesis_status_validator() -> None:
    """Test hypothesis status validator."""
    # Active hypothesis - should be valid
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
    
    registry = HypothesisRegistry()
    definition_active = HypothesisDefinition(
        hypothesis_id="hypothesis:test:active",
        name="Test Hypothesis Active",
        version=1,
        definition={},
        explainability_level="full",
        status="active"
    )
    registry.register(definition_active, ("rsi_14",))
    
    # Update evaluation to use the active hypothesis ID
    evaluation_active = HypothesisEvaluation(
        evaluation_id="test",
        asset_id="asset:TEST",
        hypothesis_id="hypothesis:test:active",
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
    
    result = hypothesis_status_validator(evaluation_active, {"hypothesis_registry": registry})
    assert result.is_valid == True
    assert result.reasons == []
    
    # Testing hypothesis - should be valid
    definition_testing = HypothesisDefinition(
        hypothesis_id="hypothesis:test:testing",
        name="Test Hypothesis Testing",
        version=1,
        definition={},
        explainability_level="full",
        status="testing"
    )
    registry.register(definition_testing, ("rsi_14",))
    
    # Update evaluation to use the testing hypothesis ID
    evaluation_testing = HypothesisEvaluation(
        evaluation_id="test",
        asset_id="asset:TEST",
        hypothesis_id="hypothesis:test:testing",
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
    
    result = hypothesis_status_validator(evaluation_testing, {"hypothesis_registry": registry})
    assert result.is_valid == True
    assert result.reasons == []
    
    # Deprecated hypothesis - should be invalid
    definition_deprecated = HypothesisDefinition(
        hypothesis_id="hypothesis:test:deprecated",
        name="Test Hypothesis Deprecated",
        version=1,
        definition={},
        explainability_level="full",
        status="deprecated"
    )
    registry.register(definition_deprecated, ("rsi_14",))
    
    # Update evaluation to use the deprecated hypothesis ID
    evaluation_deprecated = HypothesisEvaluation(
        evaluation_id="test",
        asset_id="asset:TEST",
        hypothesis_id="hypothesis:test:deprecated",
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
    
    result = hypothesis_status_validator(evaluation_deprecated, {"hypothesis_registry": registry})
    assert result.is_valid == False
    assert result.reasons == ["invalid_hypothesis_status"]
    
    # Missing hypothesis - should be invalid
    evaluation_no_hypothesis = HypothesisEvaluation(
        evaluation_id="test",
        asset_id="asset:TEST",
        hypothesis_id="hypothesis:missing",
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
    result = hypothesis_status_validator(evaluation_no_hypothesis, {"hypothesis_registry": registry})
    assert result.is_valid == False
    assert result.reasons == ["invalid_hypothesis_status"]


def test_signal_freshness_validator() -> None:
    """Test signal freshness validator."""
    # Fresh signal - should be valid
    evaluation = HypothesisEvaluation(
        evaluation_id="test",
        asset_id="asset:TEST",
        hypothesis_id="hypothesis:test",
        hypothesis_version=1,
        timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        direction="long",
        confidence=0.8,
        signals_snapshot_json='{"rsi_14": 30.0}',
        explanation_json='{"rule": "test"}',
        generated_trade_idea=False,
        validation_result_json=None,
        created_at="2026-05-06T00:00:00Z",
    )
    
    result = signal_freshness_validator(evaluation, {"max_signal_age_hours": 24})
    assert result.is_valid == True
    assert result.reasons == []
    
    # Stale signal - should be invalid (create new evaluation)
    stale_time = datetime.now(timezone.utc) - timedelta(hours=25)
    evaluation_stale = HypothesisEvaluation(
        evaluation_id="test",
        asset_id="asset:TEST",
        hypothesis_id="hypothesis:test",
        hypothesis_version=1,
        timestamp=stale_time.isoformat().replace("+00:00", "Z"),
        direction="long",
        confidence=0.8,
        signals_snapshot_json='{"rsi_14": 30.0}',
        explanation_json='{"rule": "test"}',
        generated_trade_idea=False,
        validation_result_json=None,
        created_at="2026-05-06T00:00:00Z",
    )
    
    result = signal_freshness_validator(evaluation_stale, {"max_signal_age_hours": 24})
    assert result.is_valid == False
    assert result.reasons == ["stale_signals"]
    assert result.metrics["signal_age_hours"] > 24


def test_duplicate_exposure_validator_no_repo() -> None:
    """Test duplicate exposure validator when no repository is provided."""
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
    
    # Should be valid when no repository provided
    result = duplicate_exposure_validator(evaluation, {})
    assert result.is_valid == True
    assert result.reasons == []
    # The note is in metrics only when repository is None
    assert "note" in result.metrics or len(result.metrics) == 0  # Either way is acceptable


def test_validation_engine_integration() -> None:
    """Test validation engine with all validators."""
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
        def get_positions(self, asset_id=None, hypothesis_id=None, direction=None, status=None):
            return ()  # No open positions
        def get_open_trade_ideas(self, asset_id=None, hypothesis_id=None, direction=None):
            return ()  # No pending trade ideas
    
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
    assert "confidence.actual_confidence" in result.metrics
    assert "hypothesis_status.hypothesis_status" in result.metrics
    assert "signal_freshness.signal_age_hours" in result.metrics
    assert "duplicate_exposure.pending_trade_ideas_count" in result.metrics


def test_validation_engine_with_failing_conditions() -> None:
    """Test validation engine when some validators fail."""
    # Low confidence evaluation
    evaluation = HypothesisEvaluation(
        evaluation_id="test",
        asset_id="asset:TEST",
        hypothesis_id="hypothesis:test",
        hypothesis_version=1,
        timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        direction="long",
        confidence=0.5,  # Below confidence threshold
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
        def get_positions(self, asset_id=None, hypothesis_id=None, direction=None, status=None):
            return ()  # No open positions
        def get_open_trade_ideas(self, asset_id=None, hypothesis_id=None, direction=None):
            return ()  # No pending trade ideas
    
    repository = MockRepository()
    engine = ValidationEngine()
    
    result = engine.validate(
        evaluation=evaluation,
        repository=repository,
        hypothesis_registry=registry,
        max_signal_age_hours=24,
    )
    
    # Should be invalid due to low confidence
    assert result.is_valid == False
    assert "low_confidence" in result.reasons
    assert len(result.reasons) == 1  # Only one failure reason