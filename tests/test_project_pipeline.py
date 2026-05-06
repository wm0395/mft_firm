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

    assert {signal.signal_type for signal in signals} == {"rsi_14", "ma_20", "volatility_20"}
    assert outputs[0].direction == "long"
    assert ideas[0].hypothesis_id == "hypothesis:rsi_mean_reversion"
    assert "rsi_14" in ideas[0].signals_snapshot


def test_hypothesis_consumes_signals_only() -> None:
    signal = Signal(
        signal_type="rsi_14",
        value=25.0,
        encoding_type="numeric",
        timestamp="2026-05-06T00:00:00+00:00",
        asset_id="asset:NIFTY",
        raw_reference="raw:1",
        metadata={"version": 1},
        is_persistent=True,
    )

    output = RSIMeanReversionHypothesis().evaluate("asset:NIFTY", (signal,))

    assert output.direction == "long"
    assert output.confidence > 0


def test_learning_groups_outcomes_by_hypothesis() -> None:
    outcomes = (
        TradeOutcome("trade:1", "hypothesis:rsi_mean_reversion", 1.5, {"rsi_14": 25.0}),
        TradeOutcome("trade:2", "hypothesis:rsi_mean_reversion", -0.5, {"rsi_14": 75.0}),
    )

    performance = analyze_hypothesis_performance(outcomes)

    assert performance["hypothesis:rsi_mean_reversion"]["trades"] == 2
    assert performance["hypothesis:rsi_mean_reversion"]["total_pnl"] == 1.0
