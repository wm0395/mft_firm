from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
import json
import math
from statistics import mean, median, pstdev
from typing import Any, cast

from project.backtesting.engine import BacktestEngine
from project.backtesting.models import BacktestConfig, BacktestResult
from project.common.models import (
    Asset,
    DatasetSnapshot,
    DecisionAction,
    DecisionReason,
    HypothesisDefinition,
    HypothesisOutput,
    ResearchRun,
    ResearchUniverse,
    StrategyEvidenceSummary,
    StrategySpec,
    strategy_spec_parameters,
    utc_now_iso,
)
from project.data.ingestion import build_dataset_snapshot_identity
from project.data.models import DatasetProvenance, HypothesisEvaluation
from project.data.repository import DataRepository
from project.hypotheses.engine import evaluate_hypotheses
from project.hypotheses.ma_crossover import MACrossoverHypothesis
from project.hypotheses.registry import HypothesisRegistry
from project.hypotheses.rsi_mean_reversion import RSIMeanReversionHypothesis
from project.replay.engine import ReplayEngine
from project.signals.pipeline import compute_latest_price_signals
from project.signals.registry import default_signal_registry
from project.trade_engine.generator import generate_trade_ideas
from project.validation.engine import ValidationEngine
from project.validation.models import ValidationResult


RESEARCH_UNIVERSE_ID = "research_universe:indian_indexes:daily"
RESEARCH_UNIVERSE_SYMBOLS = ("NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY")
RESEARCH_BAR_TIMEFRAME = "1d"


def emit(payload: object) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def parse_datetime(value: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


def load_json(payload: str | None) -> dict:
    if not payload:
        return {}
    return json.loads(payload)


def find_asset(repository: DataRepository, asset_ref: str) -> Asset | None:
    for asset in repository.list_assets():
        if asset.asset_id == asset_ref or asset.symbol == asset_ref.upper():
            return asset
    return None


def find_evaluation(repository: DataRepository, evaluation_id: str) -> HypothesisEvaluation | None:
    for evaluation in repository.get_hypothesis_evaluations():
        if evaluation.evaluation_id == evaluation_id:
            return evaluation
    return None


def hypotheses() -> tuple[RSIMeanReversionHypothesis, MACrossoverHypothesis]:
    return (RSIMeanReversionHypothesis(), MACrossoverHypothesis())


def research_assets(repository: DataRepository) -> tuple[Asset, ...]:
    allowed = set(RESEARCH_UNIVERSE_SYMBOLS)
    assets = [
        asset
        for asset in repository.list_assets()
        if asset.symbol in allowed and asset.market == "NSE"
    ]
    return tuple(sorted(assets, key=lambda item: item.symbol))


def ensure_research_universe(repository: DataRepository) -> ResearchUniverse:
    assets = research_assets(repository)
    if not assets:
        raise ValueError("research run requires NSE index assets for the configured universe")
    universe = ResearchUniverse(
        universe_id=RESEARCH_UNIVERSE_ID,
        name="Indian Daily Index Basket",
        market="NSE",
        description="Deterministic daily research universe for NIFTY family indexes.",
        asset_ids=tuple(asset.asset_id for asset in assets),
    )
    repository.persist_research_artifact(universe)
    return universe


def ensure_strategy_specs(repository: DataRepository, universe: ResearchUniverse) -> tuple[StrategySpec, ...]:
    specs = (
        RSIMeanReversionHypothesis.strategy_spec(universe.universe_id),
        MACrossoverHypothesis.strategy_spec(universe.universe_id),
    )
    for spec in specs:
        repository.persist_research_artifact(spec)
    return specs


def build_dataset_snapshot(
    repository: DataRepository,
    universe: ResearchUniverse,
) -> DatasetSnapshot:
    symbol_mapping = tuple(
        (asset.asset_id, asset.symbol)
        for asset in research_assets(repository)
        if asset.asset_id in universe.asset_ids
    )
    asset_points = {
        asset_id: repository.read_raw_values(asset_id, "price") for asset_id in universe.asset_ids
    }
    if not all(asset_points.values()):
        raise ValueError("dataset snapshot requires persisted daily price data for every research asset")
    data_start = min(points[0].timestamp for points in asset_points.values())
    data_end = max(points[-1].timestamp for points in asset_points.values())
    source_names = sorted(
        {point.source for points in asset_points.values() for point in points}
    )
    snapshot = DatasetSnapshot(
        dataset_snapshot_id=build_dataset_snapshot_identity(
            ",".join(source_names),
            RESEARCH_BAR_TIMEFRAME,
            symbol_mapping,
            data_start,
            data_end,
        ),
        universe_id=universe.universe_id,
        captured_at=data_end,
        data_start=data_start,
        data_end=data_end,
        asset_ids=tuple(sorted(universe.asset_ids)),
    )
    repository.persist_research_artifact(snapshot)
    return snapshot


def build_dataset_provenance(
    repository: DataRepository,
    snapshot: DatasetSnapshot,
) -> DatasetProvenance:
    sources = sorted(
        {
            point.source
            for asset_id in snapshot.asset_ids
            for point in repository.read_raw_values(asset_id, "price")
            if snapshot.data_start <= point.timestamp <= snapshot.data_end
        }
    )
    symbol_mapping = tuple(
        sorted(
            (asset.asset_id, asset.symbol)
            for asset in repository.list_assets()
            if asset.asset_id in snapshot.asset_ids
        )
    )
    return DatasetProvenance(
        snapshot_identity=snapshot.dataset_snapshot_id,
        source_name=",".join(sources),
        bar_timeframe=RESEARCH_BAR_TIMEFRAME,
        symbol_mapping=symbol_mapping,
        coverage_start=snapshot.data_start,
        coverage_end=snapshot.data_end,
    )


def validate_outputs(
    repository: DataRepository,
    outputs: tuple[HypothesisOutput, ...],
) -> list[tuple[HypothesisOutput, ValidationResult]]:
    validation_engine = ValidationEngine()
    registry = HypothesisRegistry()
    _register_strategy(registry, repository, RSIMeanReversionHypothesis.definition, ("rsi_14",))
    _register_strategy(registry, repository, MACrossoverHypothesis.definition, ("ma_5", "ma_20"))
    results: list[tuple[HypothesisOutput, ValidationResult]] = []
    for output in outputs:
        evaluation = evaluation_from_output(
            output,
            False,
            None,
            timestamp=_latest_price_timestamp(repository, output.asset_id),
        )
        result = validation_engine.validate(
            evaluation=evaluation,
            repository=repository,
            hypothesis_registry=registry,
            max_signal_age_hours=24,
        )
        results.append((output, _apply_research_gate(repository, output, result)))
    return results


def run_research_batch(repository: DataRepository) -> dict[str, object]:
    universe = ensure_research_universe(repository)
    strategy_specs = ensure_strategy_specs(repository, universe)
    snapshot = build_dataset_snapshot(repository, universe)
    provenance = build_dataset_provenance(repository, snapshot)
    outputs = _evaluate_research_outputs(repository, universe)
    runs = _persist_research_runs(repository, snapshot, strategy_specs)
    _persist_preliminary_evaluations(repository, outputs, runs, snapshot)
    _persist_strategy_evidence(repository, snapshot, strategy_specs, runs)
    validations = validate_outputs(repository, outputs)
    ideas = generate_trade_ideas(tuple(output for output, result in validations if result.is_valid))
    _persist_validated_evaluations(repository, validations, ideas, runs, snapshot)
    for idea in ideas:
        repository.persist_trade_idea(idea)
    return {
        "universe_id": universe.universe_id,
        "dataset_snapshot_id": snapshot.dataset_snapshot_id,
        "provenance": provenance.__dict__,
        "research_runs": [run.research_run_id for run in runs.values()],
        "evidence_summaries": len(repository.get_strategy_evidence_summaries()),
        "evaluations": len(outputs),
        "valid_hypotheses": sum(result.is_valid for _, result in validations),
        "trade_ideas": len(ideas),
    }


def evaluation_from_output(
    output: HypothesisOutput,
    generated_trade_idea: bool,
    validation_payload: dict | None,
    timestamp: str | None = None,
    research_run_id: str | None = None,
    dataset_snapshot_id: str | None = None,
) -> HypothesisEvaluation:
    timestamp_value = timestamp or utc_now_iso()
    return HypothesisEvaluation(
        evaluation_id=f"eval:{output.asset_id}:{output.hypothesis_id}:{output.version}:{timestamp_value}",
        asset_id=output.asset_id,
        hypothesis_id=output.hypothesis_id,
        hypothesis_version=output.version,
        timestamp=timestamp_value,
        direction=output.direction,
        confidence=output.confidence,
        signals_snapshot_json=json.dumps(dict(sorted(output.signals_snapshot.items())), sort_keys=True),
        explanation_json=json.dumps(output.explanation, sort_keys=True),
        generated_trade_idea=generated_trade_idea,
        validation_result_json=json.dumps(validation_payload, sort_keys=True) if validation_payload else None,
        created_at=timestamp_value,
        research_run_id=research_run_id,
        dataset_snapshot_id=dataset_snapshot_id,
    )


def validation_payload(result: ValidationResult) -> dict:
    return {
        "is_valid": result.is_valid,
        "reasons": result.reasons,
        "metrics": result.metrics,
        "validated_at": result.validated_at,
    }


def decision_action(value: str) -> DecisionAction:
    return cast(DecisionAction, {"approve": "approve", "reject": "reject", "watchlist": "watch"}[value])


def decision_reason(value: str | None) -> DecisionReason:
    return cast(DecisionReason, value or "market_conditions")


def build_strategy_dossier(
    repository: DataRepository,
    hypothesis_id: str,
) -> dict[str, object] | None:
    strategy_spec = next(
        (spec for spec in repository.get_strategy_specs() if spec.hypothesis_id == hypothesis_id),
        None,
    )
    if strategy_spec is None:
        return None
    snapshots = [
        snapshot
        for snapshot in repository.get_dataset_snapshots()
        if snapshot.universe_id == strategy_spec.universe_id
    ]
    latest_snapshot = snapshots[-1] if snapshots else None
    latest_evidence = _latest_evidence_summary(
        repository,
        strategy_spec.strategy_spec_id,
        latest_snapshot.dataset_snapshot_id if latest_snapshot else None,
    )
    latest_run = _latest_research_run(repository, strategy_spec.strategy_spec_id)
    provenance = (
        build_dataset_provenance(repository, latest_snapshot).__dict__
        if latest_snapshot is not None
        else None
    )
    parameters = strategy_spec_parameters(strategy_spec)
    return {
        "hypothesis_id": hypothesis_id,
        "strategy_spec_id": strategy_spec.strategy_spec_id,
        "strategy_name": strategy_spec.name,
        "activation_status": "eligible" if latest_evidence is not None else "research_only",
        "thesis": parameters.get("thesis"),
        "bar_timeframe": parameters.get("bar_timeframe"),
        "holding_horizon": parameters.get("holding_horizon"),
        "required_signals": list(parameters.get("required_signals", ())),
        "expected_failure_modes": list(parameters.get("expected_failure_modes", ())),
        "dataset_snapshot_id": latest_snapshot.dataset_snapshot_id if latest_snapshot else None,
        "provenance": provenance,
        "research_run_id": latest_run.research_run_id if latest_run else None,
        "evidence_summary": (
            {
                "summary": latest_evidence.summary,
                "metrics": dict(latest_evidence.metrics),
                "created_at": latest_evidence.created_at,
            }
            if latest_evidence is not None
            else None
        ),
    }


def _register_strategy(
    registry: HypothesisRegistry,
    repository: DataRepository,
    definition: HypothesisDefinition,
    signal_types: tuple[str, ...],
) -> None:
    strategy_spec = repository.get_strategy_spec(definition.hypothesis_id, definition.version)
    if strategy_spec is None:
        registry.register(replace(definition, status="draft"), signal_types)
        return
    try:
        registry.activate(definition, signal_types, strategy_spec)
    except ValueError:
        registry.register(replace(definition, status="draft"), signal_types)


def _evaluate_research_outputs(
    repository: DataRepository,
    universe: ResearchUniverse,
) -> tuple[HypothesisOutput, ...]:
    outputs: list[HypothesisOutput] = []
    for asset_id in universe.asset_ids:
        signals = compute_latest_price_signals(repository, default_signal_registry(), asset_id)
        outputs.extend(evaluate_hypotheses(asset_id, signals, hypotheses()))
    return tuple(outputs)


def _persist_research_runs(
    repository: DataRepository,
    snapshot: DatasetSnapshot,
    strategy_specs: tuple[StrategySpec, ...],
) -> dict[str, ResearchRun]:
    runs: dict[str, ResearchRun] = {}
    for strategy_spec in strategy_specs:
        run = ResearchRun(
            research_run_id=(
                "research_run:"
                f"{strategy_spec.hypothesis_id}:{snapshot.dataset_snapshot_id}"
            ),
            strategy_spec_id=strategy_spec.strategy_spec_id,
            dataset_snapshot_id=snapshot.dataset_snapshot_id,
            started_at=snapshot.captured_at,
            completed_at=snapshot.captured_at,
            status="completed",
            notes="Deterministic daily research run.",
        )
        repository.persist_research_artifact(run)
        runs[strategy_spec.hypothesis_id] = run
    return runs


def _persist_preliminary_evaluations(
    repository: DataRepository,
    outputs: tuple[HypothesisOutput, ...],
    runs: dict[str, ResearchRun],
    snapshot: DatasetSnapshot,
) -> None:
    for output in outputs:
        timestamp = _latest_price_timestamp(repository, output.asset_id)
        run = runs[output.hypothesis_id]
        repository.persist_hypothesis_evaluation(
            evaluation_from_output(
                output,
                False,
                None,
                timestamp=timestamp,
                research_run_id=run.research_run_id,
                dataset_snapshot_id=snapshot.dataset_snapshot_id,
            )
        )
        if output.direction == "flat":
            continue
        asset = _asset_by_id(repository, output.asset_id)
        if asset is None:
            continue
        replay_evaluation = ReplayEngine(repository).evaluate_signal(
            asset.symbol,
            parse_datetime(timestamp),
            output.direction,
            output.hypothesis_id,
        )
        repository.persist_signal_evaluation(replay_evaluation)


def _persist_validated_evaluations(
    repository: DataRepository,
    validations: list[tuple[HypothesisOutput, ValidationResult]],
    ideas: tuple[object, ...],
    runs: dict[str, ResearchRun],
    snapshot: DatasetSnapshot,
) -> None:
    idea_ids = {getattr(idea, "trade_id") for idea in ideas}
    for output, result in validations:
        timestamp = _latest_price_timestamp(repository, output.asset_id)
        trade_id = _trade_id_for_output(output)
        repository.persist_hypothesis_evaluation(
            evaluation_from_output(
                output,
                trade_id in idea_ids,
                validation_payload(result),
                timestamp=timestamp,
                research_run_id=runs[output.hypothesis_id].research_run_id,
                dataset_snapshot_id=snapshot.dataset_snapshot_id,
            )
        )


def _persist_strategy_evidence(
    repository: DataRepository,
    snapshot: DatasetSnapshot,
    strategy_specs: tuple[StrategySpec, ...],
    runs: dict[str, ResearchRun],
) -> None:
    for strategy_spec in strategy_specs:
        evaluations = tuple(
            evaluation
            for evaluation in repository.get_signal_evaluations()
            if evaluation.hypothesis_id == strategy_spec.hypothesis_id
        )
        if not evaluations:
            continue
        backtests = _persist_backtests_for_strategy(repository, snapshot, strategy_spec)
        metrics = _evidence_metrics(evaluations, backtests)
        summary = StrategyEvidenceSummary(
            evidence_summary_id=(
                "strategy_evidence_summary:"
                f"{strategy_spec.hypothesis_id}:{snapshot.dataset_snapshot_id}"
            ),
            strategy_spec_id=strategy_spec.strategy_spec_id,
            research_run_id=runs[strategy_spec.hypothesis_id].research_run_id,
            dataset_snapshot_id=snapshot.dataset_snapshot_id,
            summary=(
                f"{strategy_spec.name} produced {len(evaluations)} replay evaluations "
                f"across the deterministic daily Indian index basket."
            ),
            metrics=tuple(sorted(metrics.items())),
            created_at=snapshot.captured_at,
        )
        repository.persist_research_artifact(summary)


def _persist_backtests_for_strategy(
    repository: DataRepository,
    snapshot: DatasetSnapshot,
    strategy_spec: StrategySpec,
) -> tuple[BacktestResult, ...]:
    parameters = strategy_spec_parameters(strategy_spec)
    horizon_days = _horizon_days(str(parameters["holding_horizon"]))
    engine = BacktestEngine(repository)
    results: list[BacktestResult] = []
    for asset_id in snapshot.asset_ids:
        asset = _asset_by_id(repository, asset_id)
        if asset is None:
            continue
        result = engine.run(
            strategy_spec.hypothesis_id,
            asset.symbol,
            parse_datetime(snapshot.data_start),
            parse_datetime(snapshot.data_end),
            BacktestConfig(exit_horizon=horizon_days),
        )
        repository.persist_backtest_result(result)
        results.append(result)
    return tuple(results)


def _evidence_metrics(
    evaluations,
    backtests: tuple[BacktestResult, ...],
) -> dict[str, float]:
    forward_1 = _non_nan_values(evaluation.forward_return_1 for evaluation in evaluations)
    forward_5 = _non_nan_values(evaluation.forward_return_5 for evaluation in evaluations)
    forward_20 = _non_nan_values(evaluation.forward_return_20 for evaluation in evaluations)
    total_returns = forward_20 or forward_5 or forward_1
    hit_rate = (
        sum(value > 0 for value in total_returns) / len(total_returns)
        if total_returns
        else 0.0
    )
    return {
        "hit_rate": hit_rate,
        "mean_return": mean(total_returns) if total_returns else 0.0,
        "median_return": median(total_returns) if total_returns else 0.0,
        "volatility": pstdev(total_returns) if len(total_returns) > 1 else 0.0,
        "max_drawdown": max((result.max_drawdown for result in backtests), default=0.0),
        "horizon_return_1": mean(forward_1) if forward_1 else 0.0,
        "horizon_return_5": mean(forward_5) if forward_5 else 0.0,
        "horizon_return_20": mean(forward_20) if forward_20 else 0.0,
    }


def _apply_research_gate(
    repository: DataRepository,
    output: HypothesisOutput,
    result: ValidationResult,
) -> ValidationResult:
    reasons = list(result.reasons)
    metrics: dict[str, Any] = dict(result.metrics)
    strategy_spec = repository.get_strategy_spec(output.hypothesis_id, output.version)
    if strategy_spec is None:
        return result
    parameters = strategy_spec_parameters(strategy_spec)
    snapshot = _latest_snapshot_for_universe(repository, strategy_spec.universe_id)
    if snapshot is None:
        reasons.append("missing_dataset_snapshot")
    elif output.asset_id not in snapshot.asset_ids:
        reasons.append("unsupported_universe")
        metrics["research_gate.dataset_snapshot_id"] = snapshot.dataset_snapshot_id
    else:
        evidence = _latest_evidence_summary(
            repository,
            strategy_spec.strategy_spec_id,
            snapshot.dataset_snapshot_id,
        )
        if evidence is None:
            reasons.append("missing_strategy_evidence")
        metrics["research_gate.dataset_snapshot_id"] = snapshot.dataset_snapshot_id
    if output.horizon != parameters.get("holding_horizon"):
        reasons.append("unsupported_horizon")
    if not reasons:
        return result
    metrics["research_gate.strategy_spec_id"] = strategy_spec.strategy_spec_id
    metrics["research_gate.expected_horizon"] = parameters.get("holding_horizon")
    metrics["research_gate.output_horizon"] = output.horizon
    deduped_reasons = tuple(dict.fromkeys(reasons))
    return ValidationResult(
        is_valid=False,
        reasons=list(deduped_reasons),
        metrics=metrics,
        validated_at=result.validated_at,
    )


def _asset_by_id(repository: DataRepository, asset_id: str) -> Asset | None:
    for asset in repository.list_assets():
        if asset.asset_id == asset_id:
            return asset
    return None


def _latest_price_timestamp(repository: DataRepository, asset_id: str) -> str:
    if not hasattr(repository, "read_raw_values"):
        return utc_now_iso()
    points = repository.read_raw_values(asset_id, "price")
    if not points:
        return utc_now_iso()
    return points[-1].timestamp


def _latest_snapshot_for_universe(
    repository: DataRepository,
    universe_id: str,
) -> DatasetSnapshot | None:
    snapshots = [
        snapshot
        for snapshot in repository.get_dataset_snapshots()
        if snapshot.universe_id == universe_id
    ]
    return snapshots[-1] if snapshots else None


def _latest_evidence_summary(
    repository: DataRepository,
    strategy_spec_id: str,
    dataset_snapshot_id: str | None,
) -> StrategyEvidenceSummary | None:
    matches = [
        summary
        for summary in repository.get_strategy_evidence_summaries()
        if summary.strategy_spec_id == strategy_spec_id
        and (dataset_snapshot_id is None or summary.dataset_snapshot_id == dataset_snapshot_id)
    ]
    return matches[-1] if matches else None


def _latest_research_run(
    repository: DataRepository,
    strategy_spec_id: str,
) -> ResearchRun | None:
    matches = [
        run
        for run in repository.get_research_runs()
        if run.strategy_spec_id == strategy_spec_id
    ]
    return matches[-1] if matches else None


def _trade_id_for_output(output: HypothesisOutput) -> str:
    return f"trade:{output.asset_id}:{output.hypothesis_id}:{output.version}"


def _horizon_days(value: str) -> int:
    digits = "".join(character for character in value if character.isdigit())
    return int(digits or "1")


def _non_nan_values(values) -> list[float]:
    return [float(value) for value in values if not math.isnan(float(value))]
