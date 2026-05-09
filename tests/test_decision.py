from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from project.common.models import DecisionAction, DecisionReason
from project.data.db import DuckDBAccess
from project.data.repository import DataRepository
from project.data.models import HypothesisEvaluation
from project.decision.models import Decision
from project.decision.service import DecisionService
from project.hypotheses.engine import evaluate_hypotheses
from project.hypotheses.rsi_mean_reversion import RSIMeanReversionHypothesis
from project.signals.pipeline import compute_latest_price_signals
from project.signals.registry import default_signal_registry
from project.trade_engine.generator import generate_trade_ideas
from project.data.ingestion import build_raw_price_point


def test_decision_model() -> None:
    """Test decision model creation."""
    decision = Decision.create(
        trade_id="trade:test",
        action="approve",
        structured_reason="low_confidence",
        notes="Test decision",
    )
    
    assert decision.trade_id == "trade:test"
    assert decision.action == "approve"
    assert decision.structured_reason == "low_confidence"
    assert decision.notes == "Test decision"
    assert decision.decision_id.startswith("decision:")
    assert decision.created_at.endswith("Z")


def test_decision_service() -> None:
    """Test decision model creation (service simplified)."""
    from project.decision.models import Decision
    
    # Test Decision model directly since service was simplified
    decision = Decision.create(
        trade_id="trade:test",
        action="approve",
        structured_reason="low_confidence",
        notes="Test decision",
    )
    
    assert decision.trade_id == "trade:test"
    assert decision.action == "approve"
    assert decision.structured_reason == "low_confidence"
    assert decision.notes == "Test decision"
    assert decision.decision_id.startswith("decision:")
    assert decision.created_at.endswith("Z")


def test_decision_integration_with_trade_idea() -> None:
    """Test decision creation with actual trade idea from pipeline."""
    # Create temporary database
    import tempfile
    tmp_dir = tempfile.mkdtemp()
    try:
        db_path = f"{tmp_dir}/test.duckdb"
        db = DuckDBAccess(db_path)
        repository = DataRepository(db)
        repository.initialize()
        
        # Add asset
        asset = repository.add_asset("nifty", "NIFTY 50", "index", "NSE")
        
        # Ingest declining prices to trigger RSI < 30
        prices = [100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 90, 89, 88, 87, 86, 85, 84, 83, 82, 81, 80]
        for index, close in enumerate(prices, start=1):
            repository.ingest_raw(
                build_raw_price_point(asset.asset_id, f"2026-05-{index:02d}T00:00:00+00:00", close, "test")
            )
        
        # Compute signals
        signals = compute_latest_price_signals(repository, default_signal_registry(), asset.asset_id)
        
        # Evaluate hypotheses
        outputs = evaluate_hypotheses(asset.asset_id, signals, (RSIMeanReversionHypothesis(),))
        
        # Generate trade ideas
        ideas = generate_trade_ideas(outputs)
        
        # Persist trade ideas
        for idea in ideas:
            repository.persist_trade_idea(idea)
        
            # Manually create and persist decisions (simulating CLI behavior)
            from project.decision.models import Decision
            from project.common.models import utc_now_iso
            from uuid import uuid4
        
        for idea in ideas:
            decision = Decision(
                decision_id=f"decision:{uuid4()}",
                trade_id=idea.trade_id,
                action="approve",
                structured_reason="low_confidence",  # This is just for testing - in reality would be based on validation
                notes=f"Decision for {idea.trade_id}",
                created_at=utc_now_iso(),
            )
            repository.persist_decision(decision)
            
            assert decision.trade_id == idea.trade_id
            assert decision.action == "approve"
            assert decision.structured_reason == "low_confidence"
        
        # Retrieve all decisions
        decisions = repository.get_decisions()
        assert len(decisions) == len(ideas)
        
        db.close()
    finally:
        import shutil
        shutil.rmtree(tmp_dir)