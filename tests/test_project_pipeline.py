from __future__ import annotations

from pathlib import Path

from project.common.models import Signal, TradeOutcome
from project.data.db import DuckDBAccess
from project.data.ingestion import build_raw_price_point
from project.data.repository import DataRepository
from project.data.schema import REQUIRED_TABLES
from project.hypotheses.engine import evaluate_hypotheses
from project.hypotheses.rsi_mean_reversion import RSIMeanReversionHypothesis
from project.learning.engine import analyze_hypothesis_performance
from project.signals.compute import moving_average, rsi, volatility
from project.signals.pipeline import compute_latest_price_signals
from project.signals.registry import default_signal_registry
from project.trade_engine.generator import generate_trade_ideas


def test_schema_initializes_required_tables(tmp_path: Path) -> None:
    db = DuckDBAccess(tmp_path / "mft.duckdb")
    repository = DataRepository(db)
    repository.initialize()

    rows = db.fetch_all("show tables")
    db.close()

    assert {row[0] for row in rows} == REQUIRED_TABLES


def test_signal_math_is_deterministic() -> None:
    prices = tuple(float(value) for value in range(1, 22))
    
    assert moving_average(prices, 20) == 11.5
    assert volatility(prices, 20) > 0
    assert rsi(prices, 14) == 100.0


def test_signal_hypothesis_trade_pipeline(tmp_path: Path) -> None:
    db = DuckDBAccess(tmp_path / "mft.duckdb")
    repository = DataRepository(db)
    repository.initialize()
    asset = repository.add_asset("nifty", "NIFTY 50", "index", "NSE")

    prices = [100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 90, 89, 88, 87, 86, 85, 84, 83, 82, 81, 80]
    for index, close in enumerate(prices, start=1):
        repository.ingest_raw(
            build_raw_price_point(asset.asset_id, f"2026-05-{index:02d}T00:00:00+00:00", close, "test")
        )

    signals = compute_latest_price_signals(repository, default_signal_registry(), asset.asset_id)
    outputs = evaluate_hypotheses(asset.asset_id, signals, (RSIMeanReversionHypothesis(),))
    ideas = generate_trade_ideas(outputs)
    db.close()

    assert {signal.signal_type for signal in signals} == {"rsi_14", "ma_3", "ma_5", "ma_20", "volatility_5", "volatility_20"}
    assert outputs[0].direction == "long"
    assert ideas[0].hypothesis_id == "hypothesis:rsi_mean_reversion"
    assert "rsi_14" in ideas[0].signals_snapshot


def test_hypothesis_evaluation_persistence(tmp_path: Path) -> None:
    db = DuckDBAccess(tmp_path / "mft.duckdb")
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
    assert len(signals) == 6  # rsi_14, ma_3, ma_5, ma_20, volatility_5, volatility_20
    
    # Evaluate hypotheses
    from project.hypotheses.rsi_mean_reversion import RSIMeanReversionHypothesis
    outputs = evaluate_hypotheses(asset.asset_id, signals, (RSIMeanReversionHypothesis(),))
    assert len(outputs) == 1
    assert outputs[0].direction == "long"
    assert outputs[0].confidence == 1.0  # RSI of 0.0 gives max confidence
    
    # Persist hypothesis evaluations (this happens in main.py run-batch)
    from project.data.models import HypothesisEvaluation
    import json
    import uuid
    
    evaluation_id = f"eval:{asset.asset_id}:{outputs[0].hypothesis_id}:{outputs[0].version}:{uuid.uuid4()}"
    evaluation = HypothesisEvaluation(
        evaluation_id=evaluation_id,
        asset_id=outputs[0].asset_id,
        hypothesis_id=outputs[0].hypothesis_id,
        hypothesis_version=outputs[0].version,
        timestamp="2026-05-06T00:00:00Z",
        direction=outputs[0].direction,
        confidence=outputs[0].confidence,
        signals_snapshot_json=json.dumps(dict(sorted(outputs[0].signals_snapshot.items())), sort_keys=True),
        explanation_json=json.dumps(outputs[0].explanation, sort_keys=True),
        generated_trade_idea=False,
        validation_result_json=None,
        created_at="2026-05-06T00:00:00Z",
    )
    
    # Persist the evaluation
    repository.persist_hypothesis_evaluation(evaluation)
    
    # Retrieve evaluations
    evaluations = repository.get_hypothesis_evaluations(asset_id=asset.asset_id)
    assert len(evaluations) == 1
    
    retrieved = evaluations[0]
    assert retrieved.evaluation_id == evaluation_id
    assert retrieved.asset_id == asset.asset_id
    assert retrieved.hypothesis_id == outputs[0].hypothesis_id
    assert retrieved.hypothesis_version == outputs[0].version
    assert retrieved.direction == "long"
    assert retrieved.confidence == 1.0
    assert retrieved.generated_trade_idea == False
    assert retrieved.validation_result_json is None
    
    # Verify JSON fields can be parsed
    signals_snapshot = json.loads(retrieved.signals_snapshot_json)
    explanation = json.loads(retrieved.explanation_json)
    assert "rsi_14" in signals_snapshot
    assert "hypothesis_id" in explanation
    
    db.close()