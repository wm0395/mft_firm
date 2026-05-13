from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
from typing import Any, cast

import pytest

from project.common.models import (
    DatasetSnapshot,
    ResearchRun,
    ResearchUniverse,
    StrategyEvidenceSummary,
    StrategySpec,
)
from project.cli_support import build_strategy_dossier, run_research_batch
from project.data.db import DuckDBAccess
from project.data.ingestion import (
    build_dataset_provenance,
    build_dataset_snapshot_identity,
    build_raw_price_point,
)
from project.data.loader import CsvSourceMetadataAdapter
from project.data.models import (
    HypothesisEvaluation,
    StrategyEvidenceSummaryRecord,
    StrategySpecRecord,
)
from project.data.repository import DataRepository
from project.data.schema import REQUIRED_TABLES
from project.hypotheses.engine import evaluate_hypotheses
from project.hypotheses.rsi_mean_reversion import RSIMeanReversionHypothesis
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
    asset = repository.add_asset("nifty", "NIFTY 50", "index", "NSE")
    banknifty = repository.add_asset("banknifty", "NIFTY BANK", "index", "NSE")
    hypothesis = RSIMeanReversionHypothesis()
    universe = ResearchUniverse(
        universe_id="research_universe:indian_indexes",
        name="Indian Index Universe",
        market="NSE",
        description="Canonical NSE index research universe",
        asset_ids=(asset.asset_id, banknifty.asset_id),
    )
    dataset_snapshot = DatasetSnapshot(
        dataset_snapshot_id="dataset_snapshot:indian_indexes:2026-05-06",
        universe_id=universe.universe_id,
        captured_at="2026-05-06T00:00:00+00:00",
        data_start="2026-05-01T00:00:00+00:00",
        data_end="2026-05-06T00:00:00+00:00",
        asset_ids=(banknifty.asset_id, asset.asset_id),
    )
    strategy_spec = StrategySpec(
        strategy_spec_id="strategy_spec:rsi_mean_reversion:nse:v1",
        universe_id=universe.universe_id,
        hypothesis_id=hypothesis.definition.hypothesis_id,
        hypothesis_version=hypothesis.definition.version,
        name="NSE RSI Mean Reversion",
        parameters=(("lookback", 14), ("risk_bucket", "index")),
    )
    research_run = ResearchRun(
        research_run_id="research_run:rsi_mean_reversion:2026-05-06",
        strategy_spec_id=strategy_spec.strategy_spec_id,
        dataset_snapshot_id=dataset_snapshot.dataset_snapshot_id,
        started_at="2026-05-06T00:00:00+00:00",
        completed_at="2026-05-06T00:15:00+00:00",
        status="completed",
        notes="Deterministic regression run",
    )
    evidence_summary = StrategyEvidenceSummary(
        evidence_summary_id="strategy_evidence_summary:rsi_mean_reversion:2026-05-06",
        strategy_spec_id=strategy_spec.strategy_spec_id,
        research_run_id=research_run.research_run_id,
        dataset_snapshot_id=dataset_snapshot.dataset_snapshot_id,
        summary="RSI oversold setup produces a single long idea on the test fixture.",
        metrics=(("confidence", 1.0), ("trade_ideas", 1)),
        created_at="2026-05-06T00:16:00+00:00",
    )
    for artifact in (universe, dataset_snapshot, strategy_spec, research_run, evidence_summary):
        repository.persist_research_artifact(artifact)

    prices = [100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 90, 89, 88, 87, 86, 85, 84, 83, 82, 81, 80]
    for index, close in enumerate(prices, start=1):
        repository.ingest_raw(
            build_raw_price_point(asset.asset_id, f"2026-05-{index:02d}T00:00:00+00:00", close, "test")
        )

    signals = compute_latest_price_signals(repository, default_signal_registry(), asset.asset_id)
    assert len(signals) == 6
    outputs = evaluate_hypotheses(asset.asset_id, signals, (hypothesis,))
    assert len(outputs) == 1
    output = outputs[0]
    assert output.direction == "long"
    assert output.confidence == 1.0

    evaluation = HypothesisEvaluation(
        evaluation_id="eval:asset:NIFTY:hypothesis:rsi_mean_reversion:1:2026-05-06",
        asset_id=output.asset_id,
        hypothesis_id=output.hypothesis_id,
        hypothesis_version=output.version,
        timestamp="2026-05-06T00:00:00+00:00",
        direction=output.direction,
        confidence=output.confidence,
        signals_snapshot_json=json.dumps(dict(sorted(output.signals_snapshot.items())), sort_keys=True),
        explanation_json=json.dumps(output.explanation, sort_keys=True),
        generated_trade_idea=False,
        validation_result_json=None,
        created_at="2026-05-06T00:00:00+00:00",
        research_run_id=research_run.research_run_id,
        dataset_snapshot_id=dataset_snapshot.dataset_snapshot_id,
    )
    repository.persist_hypothesis_evaluation(evaluation)
    evaluations = repository.get_hypothesis_evaluations(asset_id=asset.asset_id)
    assert len(evaluations) == 1
    retrieved = evaluations[0]
    assert retrieved.evaluation_id == evaluation.evaluation_id
    assert retrieved.asset_id == asset.asset_id
    assert retrieved.hypothesis_id == output.hypothesis_id
    assert retrieved.hypothesis_version == output.version
    assert retrieved.direction == "long"
    assert retrieved.confidence == 1.0
    assert not retrieved.generated_trade_idea
    assert retrieved.validation_result_json is None
    assert retrieved.research_run_id == research_run.research_run_id
    assert retrieved.dataset_snapshot_id == dataset_snapshot.dataset_snapshot_id

    signals_snapshot = json.loads(retrieved.signals_snapshot_json)
    explanation = json.loads(retrieved.explanation_json)
    assert "rsi_14" in signals_snapshot
    assert "hypothesis_id" in explanation
    assert repository.get_research_universes() == (
        ResearchUniverse(
            universe_id=universe.universe_id,
            name=universe.name,
            market=universe.market,
            description=universe.description,
            asset_ids=tuple(sorted(universe.asset_ids)),
        ),
    )
    assert repository.get_dataset_snapshots() == (
        DatasetSnapshot(
            dataset_snapshot_id=dataset_snapshot.dataset_snapshot_id,
            universe_id=dataset_snapshot.universe_id,
            captured_at=dataset_snapshot.captured_at,
            data_start=dataset_snapshot.data_start,
            data_end=dataset_snapshot.data_end,
            asset_ids=tuple(sorted(dataset_snapshot.asset_ids)),
        ),
    )
    assert repository.get_strategy_specs() == (strategy_spec,)
    assert repository.get_research_runs() == (research_run,)
    assert repository.get_strategy_evidence_summaries() == (evidence_summary,)
    assert db.fetch_all("select * from research_universes") == [
        (
            universe.universe_id,
            universe.name,
            universe.market,
            universe.description,
            json.dumps(sorted(universe.asset_ids)),
        )
    ]
    assert db.fetch_all("select * from dataset_snapshots") == [
        (
            dataset_snapshot.dataset_snapshot_id,
            dataset_snapshot.universe_id,
            dataset_snapshot.captured_at,
            dataset_snapshot.data_start,
            dataset_snapshot.data_end,
            json.dumps(sorted(dataset_snapshot.asset_ids)),
        )
    ]
    assert db.fetch_all("select * from strategy_specs") == [
        (
            strategy_spec.strategy_spec_id,
            strategy_spec.universe_id,
            strategy_spec.hypothesis_id,
            strategy_spec.hypothesis_version,
            strategy_spec.name,
            json.dumps(dict(strategy_spec.parameters), sort_keys=True),
        )
    ]
    assert db.fetch_all("select * from research_runs") == [
        (
            research_run.research_run_id,
            research_run.strategy_spec_id,
            research_run.dataset_snapshot_id,
            research_run.started_at,
            research_run.completed_at,
            research_run.status,
            research_run.notes,
        )
    ]
    assert db.fetch_all("select * from strategy_evidence_summaries") == [
        (
            evidence_summary.evidence_summary_id,
            evidence_summary.strategy_spec_id,
            evidence_summary.research_run_id,
            evidence_summary.dataset_snapshot_id,
            evidence_summary.summary,
            json.dumps(dict(evidence_summary.metrics), sort_keys=True),
            evidence_summary.created_at,
        )
    ]
    db.close()


def test_strategy_spec_record_rejects_duplicate_parameter_keys() -> None:
    spec = StrategySpec(
        strategy_spec_id="strategy_spec:dup",
        universe_id="research_universe:indian_indexes",
        hypothesis_id="hypothesis:rsi_mean_reversion",
        hypothesis_version=1,
        name="Duplicate Parameter Spec",
        parameters=(("lookback", 14), ("lookback", 21)),
    )

    with pytest.raises(ValueError, match="duplicate strategy parameter key: lookback"):
        StrategySpecRecord.from_artifact(spec)


def test_strategy_evidence_summary_record_rejects_duplicate_metric_keys() -> None:
    summary = StrategyEvidenceSummary(
        evidence_summary_id="strategy_evidence_summary:dup",
        strategy_spec_id="strategy_spec:rsi_mean_reversion:nse:v1",
        research_run_id="research_run:rsi_mean_reversion:2026-05-06",
        dataset_snapshot_id="dataset_snapshot:indian_indexes:2026-05-06",
        summary="Duplicate metric coverage",
        metrics=(("confidence", 1.0), ("confidence", 0.5)),
        created_at="2026-05-06T00:16:00+00:00",
    )

    with pytest.raises(ValueError, match="duplicate strategy metric key: confidence"):
        StrategyEvidenceSummaryRecord.from_artifact(summary)


def test_dataset_snapshot_provenance_is_deterministic() -> None:
    coverage_start = "2026-05-01T00:00:00+00:00"
    coverage_end = "2026-05-25T00:00:00+00:00"
    mapping = (
        ("asset:MIDCPNIFTY", "MIDCPNIFTY"),
        ("asset:BANKNIFTY", "BANKNIFTY"),
        ("asset:FINNIFTY", "FINNIFTY"),
        ("asset:NIFTY", "NIFTY"),
    )
    reversed_mapping = tuple(reversed(mapping))
    first = build_dataset_snapshot_identity(
        "fixture_csv",
        "1d",
        mapping,
        coverage_start,
        coverage_end,
    )
    second = build_dataset_snapshot_identity(
        "fixture_csv",
        "1d",
        reversed_mapping,
        coverage_start,
        coverage_end,
    )
    adapter = CsvSourceMetadataAdapter("fixture_csv", reversed_mapping, "1d")
    provenance = build_dataset_provenance(adapter, coverage_start, coverage_end)

    assert first == second
    assert provenance.snapshot_identity == first
    assert provenance.source_name == "fixture_csv"
    assert provenance.bar_timeframe == "1d"
    assert provenance.symbol_mapping == tuple(sorted(mapping))


def test_research_batch_persists_snapshot_evidence_and_dossier(tmp_path: Path) -> None:
    db = DuckDBAccess(tmp_path / "mft.duckdb")
    repository = DataRepository(db)
    repository.initialize()

    assets = (
        repository.add_asset("nifty", "NIFTY 50", "index", "NSE"),
        repository.add_asset("banknifty", "NIFTY BANK", "index", "NSE"),
        repository.add_asset("finnifty", "FINNIFTY", "index", "NSE"),
        repository.add_asset("midcpnifty", "NIFTY MIDCAP 50", "index", "NSE"),
    )
    base = datetime.now(UTC).replace(microsecond=0) - timedelta(days=24)
    price_map = {
        "NIFTY": [200.0 - float(index) for index in range(25)],
        "BANKNIFTY": [100.0 + float(index) for index in range(25)],
        "FINNIFTY": [100.0] * 20 + [300.0] * 5,
        "MIDCPNIFTY": [300.0] * 20 + [100.0] * 5,
    }
    for asset in assets:
        for index, close in enumerate(price_map[asset.symbol]):
            timestamp = base + timedelta(days=index)
            repository.ingest_raw(
                build_raw_price_point(
                    asset.asset_id,
                    timestamp.isoformat(),
                    close,
                    "fixture_csv",
                )
            )
            repository.ingest_market_data(
                asset.symbol,
                timestamp,
                close,
                close + 1.0,
                close - 1.0,
                close,
                1000.0,
            )

    result = run_research_batch(repository)
    payload = dict(cast(dict[str, Any], result))
    dossier = cast(
        dict[str, Any],
        build_strategy_dossier(repository, "hypothesis:rsi_mean_reversion"),
    )

    assert str(payload["dataset_snapshot_id"]).startswith("dataset_snapshot:fixture_csv:1d:")
    assert payload["evaluations"] == 8
    assert payload["evidence_summaries"] == 2
    assert payload["trade_ideas"] >= 2
    assert len(repository.get_dataset_snapshots()) == 1
    provenance = repository.get_dataset_provenance(
        repository.get_dataset_snapshots()[0],
        "1d",
    )
    assert provenance.snapshot_identity == payload["dataset_snapshot_id"]
    assert provenance.source_name == "fixture_csv"
    assert provenance.bar_timeframe == "1d"
    assert provenance.coverage_start == (base).isoformat()
    assert provenance.coverage_end == (base + timedelta(days=24)).isoformat()
    assert provenance.symbol_mapping == tuple(
        sorted((asset.asset_id, asset.symbol) for asset in assets)
    )
    assert len(repository.get_research_runs()) == 2
    assert len(repository.get_strategy_evidence_summaries()) == 2
    assert dossier["activation_status"] == "eligible"
    assert dossier["dataset_snapshot_id"] == payload["dataset_snapshot_id"]
    assert dossier["provenance"]["bar_timeframe"] == "1d"
    assert dossier["provenance"]["source_name"] == "fixture_csv"
    assert sorted(dossier["required_signals"]) == ["rsi_14"]
    assert repository.get_trade_ideas()
    db.close()
