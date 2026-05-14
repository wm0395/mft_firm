from __future__ import annotations

from statistics import mean, median, pstdev
import math

from project.backtesting.engine import BacktestEngine
from project.backtesting.models import BacktestConfig, BacktestResult
from project.cli_utils import hypotheses, parse_datetime, research_assets
from project.common.models import (
    Asset,
    DatasetSnapshot,
    HypothesisOutput,
    ResearchRun,
    ResearchUniverse,
    StrategyEvidenceSummary,
    StrategySpec,
    strategy_spec_parameters,
    utc_now_iso,
)
from project.data.ingestion import build_dataset_snapshot_identity
from project.data.repository import DataRepository
from project.hypotheses.engine import evaluate_hypotheses
from project.hypotheses.ma_crossover import MACrossoverHypothesis
from project.hypotheses.rsi_mean_reversion import RSIMeanReversionHypothesis
from project.research_validation import evaluation_from_output, validate_outputs, validation_payload
from project.replay.engine import ReplayEngine
from project.signals.pipeline import compute_latest_price_signals
from project.signals.registry import default_signal_registry
from project.trade_engine.generator import generate_trade_ideas


RESEARCH_UNIVERSE_ID = "research_universe:indian_indexes:daily"
RESEARCH_BAR_TIMEFRAME = "1d"


def run_research_batch(repository: DataRepository) -> dict[str, object]:
    with repository.transaction():
        universe = ensure_research_universe(repository)
        strategy_specs = ensure_strategy_specs(repository, universe)
        snapshot = build_dataset_snapshot(repository, universe)
        provenance = repository.get_dataset_provenance(snapshot, RESEARCH_BAR_TIMEFRAME)
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
    source_names = sorted({point.source for points in asset_points.values() for point in points})
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
    outputs,
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
    validations,
    ideas,
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


def _asset_by_id(repository: DataRepository, asset_id: str) -> Asset | None:
    for asset in repository.list_assets():
        if asset.asset_id == asset_id:
            return asset
    return None


def _latest_price_timestamp(repository: DataRepository, asset_id: str) -> str:
    points = repository.read_raw_values(asset_id, "price")
    if not points:
        return utc_now_iso()
    return points[-1].timestamp


def _trade_id_for_output(output) -> str:
    return f"trade:{output.asset_id}:{output.hypothesis_id}:{output.version}"


def _horizon_days(value: str) -> int:
    digits = "".join(character for character in value if character.isdigit())
    return int(digits or "1")


def _non_nan_values(values) -> list[float]:
    return [float(value) for value in values if not math.isnan(float(value))]
