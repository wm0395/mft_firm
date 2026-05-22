from __future__ import annotations

from pathlib import Path

from project.data.db import DuckDBAccess
from project.data.repository import DataRepository
from project.cli_trade import review_trade_idea
from project.decision.system import DecisionContext, decide_trade
from project.decision.models import Decision
from project.hypotheses.engine import evaluate_hypotheses
from project.hypotheses.rsi_mean_reversion import RSIMeanReversionHypothesis
from project.signals.pipeline import compute_latest_price_signals
from project.signals.registry import default_signal_registry
from project.trade_engine.generator import generate_trade_ideas
from project.data.ingestion import build_raw_price_point
from project.common.models import TradeIdea


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


def test_decide_trade_approves_tradeable_high_confidence_idea() -> None:
    idea = _trade_idea(confidence=0.8)

    decision = decide_trade(idea, minimum_confidence=0.6)

    assert decision.trade_id == idea.trade_id
    assert decision.action == "approve"
    assert decision.structured_reason == "market_conditions"
    assert decision.created_at.endswith("Z")


def test_decide_trade_rejects_explicit_tradeability_blockers() -> None:
    idea = _trade_idea(confidence=0.8)

    duplicate = decide_trade(idea, context=DecisionContext(has_duplicate_exposure=True))
    risk = decide_trade(idea, context=DecisionContext(risk_limit_breached=True))
    closed_market = decide_trade(idea, context=DecisionContext(market_is_tradeable=False))
    low_confidence = decide_trade(_trade_idea(confidence=0.2), minimum_confidence=0.4)

    assert duplicate.action == "reject"
    assert duplicate.structured_reason == "duplicate_exposure"
    assert risk.action == "reject"
    assert risk.structured_reason == "risk_constraints"
    assert closed_market.action == "watch"
    assert closed_market.structured_reason == "market_conditions"
    assert low_confidence.action == "reject"
    assert low_confidence.structured_reason == "low_confidence"


def test_review_trade_idea_defaults_to_shared_decision_rules(tmp_path: Path) -> None:
    db = DuckDBAccess(tmp_path / "test.duckdb")
    repository = DataRepository(db)
    repository.initialize()
    idea = _trade_idea(confidence=0.2)
    repository.persist_trade_idea(idea)

    try:
        exit_code = review_trade_idea(repository, idea.trade_id, notes="auto")
        decision = repository.get_decisions(idea.trade_id)[0]
    finally:
        db.close()

    expected = decide_trade(idea)
    assert exit_code == 0
    assert decision[2] == expected.action
    assert decision[3] == expected.structured_reason
    assert decision[4] == "auto"


def test_decision_integration_with_trade_idea(tmp_path: Path) -> None:
    repository, ideas = _prepare_decision_integration(tmp_path)
    try:
        _persist_decision_integration(repository, ideas)
        decisions = repository.get_decisions()
    finally:
        repository.close()

    assert len(decisions) == len(ideas)


def _prepare_decision_integration(
    tmp_path: Path,
) -> tuple[DataRepository, tuple[TradeIdea, ...]]:
    repository = DataRepository(DuckDBAccess(tmp_path / "test.duckdb"))
    repository.initialize()
    asset = repository.add_asset("nifty", "NIFTY 50", "index", "NSE")
    _ingest_declining_prices(repository, asset.asset_id)
    signals = compute_latest_price_signals(
        repository, default_signal_registry(), asset.asset_id
    )
    outputs = evaluate_hypotheses(
        asset.asset_id, signals, (RSIMeanReversionHypothesis(),)
    )
    ideas = generate_trade_ideas(outputs)
    for idea in ideas:
        repository.persist_trade_idea(idea)
    return repository, ideas


def _ingest_declining_prices(repository: DataRepository, asset_id: str) -> None:
    prices = [100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 90, 89, 88, 87, 86, 85, 84, 83, 82, 81, 80]
    for index, close in enumerate(prices, start=1):
        repository.ingest_raw(
            build_raw_price_point(
                asset_id,
                f"2026-05-{index:02d}T00:00:00+00:00",
                close,
                "test",
            )
        )


def _persist_decision_integration(
    repository: DataRepository, ideas: tuple[TradeIdea, ...]
) -> None:
    for idea in ideas:
        decision = Decision.create(
            trade_id=idea.trade_id,
            action="approve",
            structured_reason="low_confidence",
            notes=f"Decision for {idea.trade_id}",
        )
        repository.persist_decision(decision)
        assert decision.trade_id == idea.trade_id
        assert decision.action == "approve"
        assert decision.structured_reason == "low_confidence"


def _trade_idea(confidence: float) -> TradeIdea:
    return TradeIdea(
        trade_id="trade:test",
        asset_id="asset:NIFTY",
        hypothesis_id="hypothesis:test",
        version=1,
        direction="long",
        confidence=confidence,
        signals_snapshot={"rsi": 25.0},
        timestamp="2026-05-21T00:00:00+00:00",
    )
