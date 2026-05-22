from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from project.common.models import (
    DatasetSnapshot,
    ResearchRun,
    ResearchUniverse,
    StrategyEvidenceSummary,
    StrategySpec,
)
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
from project.hypotheses.engine import evaluate_hypotheses
from project.hypotheses.rsi_mean_reversion import RSIMeanReversionHypothesis
from project.signals.pipeline import compute_latest_price_signals
from project.signals.registry import default_signal_registry


def _build_hypothesis_persistence_fixture(
    tmp_path: Path,
) -> tuple[
    DuckDBAccess,
    DataRepository,
    Any,
    Any,
    RSIMeanReversionHypothesis,
    ResearchUniverse,
    DatasetSnapshot,
    StrategySpec,
    ResearchRun,
    StrategyEvidenceSummary,
]:
    db = DuckDBAccess(tmp_path / "mft.duckdb")
    repository = DataRepository(db)
    repository.initialize()
    asset = repository.add_asset("nifty", "NIFTY 50", "index", "NSE")
    banknifty = repository.add_asset("banknifty", "NIFTY BANK", "index", "NSE")
    hypothesis = RSIMeanReversionHypothesis()
    universe = _build_pipeline_universe(asset.asset_id, banknifty.asset_id)
    dataset_snapshot, strategy_spec, research_run, evidence_summary = _build_pipeline_records(
        hypothesis, universe, asset.asset_id, banknifty.asset_id
    )
    for artifact in (universe, dataset_snapshot, strategy_spec, research_run, evidence_summary):
        repository.persist_research_artifact(artifact)
    return (
        db,
        repository,
        asset,
        banknifty,
        hypothesis,
        universe,
        dataset_snapshot,
        strategy_spec,
        research_run,
        evidence_summary,
    )


def _build_pipeline_universe(asset_id: str, banknifty_id: str) -> ResearchUniverse:
    return ResearchUniverse(
        universe_id="research_universe:indian_indexes",
        name="Indian Index Universe",
        market="NSE",
        description="Canonical NSE index research universe",
        asset_ids=(asset_id, banknifty_id),
    )


def _build_pipeline_records(
    hypothesis: RSIMeanReversionHypothesis,
    universe: ResearchUniverse,
    asset_id: str,
    banknifty_id: str,
) -> tuple[DatasetSnapshot, StrategySpec, ResearchRun, StrategyEvidenceSummary]:
    dataset_snapshot, strategy_spec, research_run, evidence_summary = (
        _build_pipeline_records_payload(hypothesis, universe, asset_id, banknifty_id)
    )
    return dataset_snapshot, strategy_spec, research_run, evidence_summary


def _build_pipeline_records_payload(
    hypothesis: RSIMeanReversionHypothesis,
    universe: ResearchUniverse,
    asset_id: str,
    banknifty_id: str,
) -> tuple[DatasetSnapshot, StrategySpec, ResearchRun, StrategyEvidenceSummary]:
    dataset_snapshot = _build_pipeline_dataset_snapshot(universe, asset_id, banknifty_id)
    strategy_spec = _build_pipeline_strategy_spec(hypothesis, universe)
    research_run = _build_pipeline_research_run(strategy_spec, dataset_snapshot)
    evidence_summary = _build_pipeline_evidence_summary(
        strategy_spec,
        research_run,
        dataset_snapshot,
    )
    return dataset_snapshot, strategy_spec, research_run, evidence_summary


def _build_pipeline_dataset_snapshot(
    universe: ResearchUniverse, asset_id: str, banknifty_id: str
) -> DatasetSnapshot:
    return DatasetSnapshot(
        dataset_snapshot_id="dataset_snapshot:indian_indexes:2026-05-06",
        universe_id=universe.universe_id,
        captured_at="2026-05-06T00:00:00+00:00",
        data_start="2026-05-01T00:00:00+00:00",
        data_end="2026-05-06T00:00:00+00:00",
        asset_ids=(banknifty_id, asset_id),
    )


def _build_pipeline_strategy_spec(
    hypothesis: RSIMeanReversionHypothesis, universe: ResearchUniverse
) -> StrategySpec:
    return StrategySpec(
        strategy_spec_id="strategy_spec:rsi_mean_reversion:nse:v1",
        universe_id=universe.universe_id,
        hypothesis_id=hypothesis.definition.hypothesis_id,
        hypothesis_version=hypothesis.definition.version,
        name="NSE RSI Mean Reversion",
        parameters=(("lookback", 14), ("risk_bucket", "index")),
    )


def _build_pipeline_research_run(
    strategy_spec: StrategySpec, dataset_snapshot: DatasetSnapshot
) -> ResearchRun:
    return ResearchRun(
        research_run_id="research_run:rsi_mean_reversion:2026-05-06",
        strategy_spec_id=strategy_spec.strategy_spec_id,
        dataset_snapshot_id=dataset_snapshot.dataset_snapshot_id,
        started_at="2026-05-06T00:00:00+00:00",
        completed_at="2026-05-06T00:15:00+00:00",
        status="completed",
        notes="Deterministic regression run",
    )


def _build_pipeline_evidence_summary(
    strategy_spec: StrategySpec,
    research_run: ResearchRun,
    dataset_snapshot: DatasetSnapshot,
) -> StrategyEvidenceSummary:
    return StrategyEvidenceSummary(
        evidence_summary_id="strategy_evidence_summary:rsi_mean_reversion:2026-05-06",
        strategy_spec_id=strategy_spec.strategy_spec_id,
        research_run_id=research_run.research_run_id,
        dataset_snapshot_id=dataset_snapshot.dataset_snapshot_id,
        summary="RSI oversold setup produces a single long idea on the test fixture.",
        metrics=(("confidence", 1.0), ("trade_ideas", 1)),
        created_at="2026-05-06T00:16:00+00:00",
    )


def _seed_hypothesis_prices(repository: DataRepository, asset_id: str) -> None:
    for index, close in enumerate(
        [100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 90, 89, 88, 87, 86, 85, 84, 83, 82, 81, 80],
        start=1,
    ):
        repository.ingest_raw(
            build_raw_price_point(asset_id, f"2026-05-{index:02d}T00:00:00+00:00", close, "test")
        )


def _make_hypothesis_evaluation(
    output: Any, research_run_id: str, dataset_snapshot_id: str
) -> HypothesisEvaluation:
    return HypothesisEvaluation(
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
        research_run_id=research_run_id,
        dataset_snapshot_id=dataset_snapshot_id,
    )


def _assert_retrieved_hypothesis_evaluation(
    retrieved: HypothesisEvaluation,
    evaluation: HypothesisEvaluation,
    output: Any,
    research_run_id: str,
    dataset_snapshot_id: str,
) -> None:
    assert retrieved.evaluation_id == evaluation.evaluation_id
    assert retrieved.asset_id == output.asset_id
    assert retrieved.hypothesis_id == output.hypothesis_id
    assert retrieved.hypothesis_version == output.version
    assert retrieved.direction == "long"
    assert retrieved.confidence == 1.0
    assert not retrieved.generated_trade_idea
    assert retrieved.validation_result_json is None
    assert retrieved.research_run_id == research_run_id
    assert retrieved.dataset_snapshot_id == dataset_snapshot_id


def _assert_pipeline_runtime_state(
    repository: DataRepository,
    asset_id: str,
    hypothesis: RSIMeanReversionHypothesis,
    research_run: ResearchRun,
    dataset_snapshot: DatasetSnapshot,
) -> None:
    signals = compute_latest_price_signals(repository, default_signal_registry(), asset_id)
    assert len(signals) == 6
    outputs = evaluate_hypotheses(asset_id, signals, (hypothesis,))
    assert len(outputs) == 1
    output = outputs[0]
    assert output.direction == "long"
    assert output.confidence == 1.0
    evaluation = _make_hypothesis_evaluation(
        output, research_run.research_run_id, dataset_snapshot.dataset_snapshot_id
    )
    repository.persist_hypothesis_evaluation(evaluation)
    evaluations = repository.get_hypothesis_evaluations(asset_id=asset_id)
    assert len(evaluations) == 1
    _assert_retrieved_hypothesis_evaluation(
        evaluations[0],
        evaluation,
        output,
        research_run.research_run_id,
        dataset_snapshot.dataset_snapshot_id,
    )
    signals_snapshot = json.loads(evaluations[0].signals_snapshot_json)
    explanation = json.loads(evaluations[0].explanation_json)
    assert "rsi_14" in signals_snapshot
    assert "hypothesis_id" in explanation


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
