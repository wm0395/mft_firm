from __future__ import annotations

from dataclasses import asdict

from project.data.models import SignalEvaluation
from project.data.quality import build_data_quality_report
from project.data.repository import DataRepository
from project.learning.engine import (
    aggregate_signal_performance,
    analyze_hypothesis_performance,
)
from project.regimes.engine import RegimeEngine

from project.cli_support import (
    build_strategy_dossier,
    emit_error,
    emit_response,
    find_evaluation,
    load_json,
)


def show_validation_failures(repository: DataRepository) -> int:
    failures = []
    for evaluation in repository.get_hypothesis_evaluations():
        payload = load_json(evaluation.validation_result_json)
        if payload and not payload.get("is_valid", True):
            failures.append({"evaluation_id": evaluation.evaluation_id, **payload})
    emit_response("show-validation-failures", failures)
    return 0


def show_competition(
    repository: DataRepository, asset_id: str | None, direction: str | None
) -> int:
    rows = []
    for evaluation in repository.get_hypothesis_evaluations(asset_id=asset_id):
        if direction is not None and evaluation.direction != direction:
            continue
        rows.append(
            {
                "evaluation_id": evaluation.evaluation_id,
                "hypothesis_id": evaluation.hypothesis_id,
                "asset_id": evaluation.asset_id,
                "direction": evaluation.direction,
                "competition": load_json(evaluation.explanation_json).get(
                    "competition", {}
                ),
            }
        )
    emit_response("show-competition", rows)
    return 0


def show_explanation(repository: DataRepository, evaluation_id: str) -> int:
    evaluation = find_evaluation(repository, evaluation_id)
    if evaluation is None:
        emit_error("show-explanation", f"Evaluation {evaluation_id} not found")
        return 1
    emit_response("show-explanation", load_json(evaluation.explanation_json))
    return 0


def show_signal_lineage(repository: DataRepository, asset_id: str) -> int:
    emit_response(
        "show-signal-lineage",
        [
            {
                "evaluation_id": evaluation.evaluation_id,
                "timestamp": evaluation.timestamp,
                "hypothesis_id": evaluation.hypothesis_id,
                "signals": sorted(load_json(evaluation.signals_snapshot_json).keys()),
            }
            for evaluation in repository.get_hypothesis_evaluations(asset_id=asset_id)
        ],
    )
    return 0


def show_validation_path(repository: DataRepository, evaluation_id: str) -> int:
    evaluation = find_evaluation(repository, evaluation_id)
    if evaluation is None:
        emit_error("show-validation-path", f"Evaluation {evaluation_id} not found")
        return 1
    emit_response("show-validation-path", load_json(evaluation.validation_result_json))
    return 0


def list_rejected_hypotheses(repository: DataRepository) -> int:
    rejected = []
    for evaluation in repository.get_hypothesis_evaluations():
        payload = load_json(evaluation.validation_result_json)
        if payload and not payload.get("is_valid", True):
            rejected.append(
                {
                    "evaluation_id": evaluation.evaluation_id,
                    "hypothesis_id": evaluation.hypothesis_id,
                    "asset_id": evaluation.asset_id,
                    "reasons": payload.get("reasons", []),
                }
            )
    emit_response("list-rejected-hypotheses", rejected)
    return 0


def report_hypotheses(repository: DataRepository, horizon: int) -> int:
    horizon_index = {1: 0, 5: 1, 20: 2}[horizon]
    grouped: dict[str, list[SignalEvaluation]] = {}
    for evaluation in repository.get_signal_evaluations():
        grouped.setdefault(evaluation.hypothesis_id, []).append(evaluation)
    emit_response(
        "report-hypotheses",
        [
            {
                "hypothesis_id": hypothesis_id,
                "horizon": horizon,
                **aggregate_signal_performance(evaluations, horizon_index).__dict__,
            }
            for hypothesis_id, evaluations in sorted(grouped.items())
        ],
    )
    return 0


def backtest_results(repository: DataRepository) -> int:
    emit_response(
        "backtest-results",
        [result.__dict__ for result in repository.get_backtest_results()],
    )
    return 0


def hypothesis_performance(repository: DataRepository) -> int:
    grouped: dict[str, list[SignalEvaluation]] = {}
    for evaluation in repository.get_signal_evaluations():
        grouped.setdefault(evaluation.hypothesis_id, []).append(evaluation)
    emit_response(
        "hypothesis-performance",
        {
            "trade_outcomes": analyze_hypothesis_performance(
                repository.get_trade_outcomes()
            ),
            "signal_metrics": [
                {
                    "hypothesis_id": hypothesis_id,
                    "metrics_1": aggregate_signal_performance(evaluations, 0).__dict__,
                    "metrics_5": aggregate_signal_performance(evaluations, 1).__dict__,
                    "metrics_20": aggregate_signal_performance(evaluations, 2).__dict__,
                }
                for hypothesis_id, evaluations in sorted(grouped.items())
            ],
        },
    )
    return 0


def regime_analysis(repository: DataRepository, asset_symbol: str) -> int:
    market_data = repository.get_market_data(asset_symbol.upper(), None, None)
    if len(market_data) < 20:
        emit_error(
            "regime-analysis",
            f"Insufficient data for regime analysis: {len(market_data)} bars",
        )
        return 1
    snapshot = RegimeEngine().compute_regime(
        asset_id=f"asset:{asset_symbol.upper()}",
        timestamp=market_data[-1][0],
        market_data=market_data[-20:],
    )
    timestamp = (
        snapshot.timestamp.isoformat()
        if hasattr(snapshot.timestamp, "isoformat")
        else str(snapshot.timestamp)
    )
    emit_response(
        "regime-analysis",
        {
            "asset_id": snapshot.asset_id,
            "timestamp": timestamp,
            "volatility": snapshot.volatility.__dict__,
            "trend": snapshot.trend.__dict__,
            "liquidity": snapshot.liquidity.__dict__,
            "momentum": snapshot.momentum.__dict__,
        },
    )
    return 0


def lineage_trace(
    repository: DataRepository, signal_type: str | None, hypothesis_id: str | None
) -> int:
    rows = []
    for evaluation in repository.get_hypothesis_evaluations(
        hypothesis_id=hypothesis_id
    ):
        signals = load_json(evaluation.signals_snapshot_json)
        if signal_type is not None and signal_type not in signals:
            continue
        rows.append(
            {
                "evaluation_id": evaluation.evaluation_id,
                "hypothesis_id": evaluation.hypothesis_id,
                "asset_id": evaluation.asset_id,
                "timestamp": evaluation.timestamp,
                "signals": signals,
            }
        )
    emit_response("lineage-trace", rows)
    return 0


def position_management(
    repository: DataRepository,
    asset_id: str | None,
    hypothesis_id: str | None,
    status: str | None,
) -> int:
    emit_response(
        "position-management",
        [
            position.__dict__
            for position in repository.get_positions(
                asset_id=asset_id, hypothesis_id=hypothesis_id, status=status
            )
        ],
    )
    return 0


def advanced_report(
    repository: DataRepository, hypothesis_id: str, asset_id: str | None
) -> int:
    emit_response(
        "advanced-report",
        {
            "hypothesis_id": hypothesis_id,
            "asset_id": asset_id,
            "dossier": build_strategy_dossier(repository, hypothesis_id),
            "evaluations": [
                evaluation.__dict__
                for evaluation in repository.get_hypothesis_evaluations(
                    asset_id=asset_id, hypothesis_id=hypothesis_id
                )
            ],
            "backtests": [
                result.__dict__
                for result in repository.get_backtest_results()
                if result.hypothesis_id == hypothesis_id
            ],
            "trade_outcomes": [
                outcome.__dict__
                for outcome in repository.get_trade_outcomes()
                if outcome.hypothesis_id == hypothesis_id
            ],
            "signal_evaluations": [
                evaluation.__dict__
                for evaluation in repository.get_signal_evaluations()
                if evaluation.hypothesis_id == hypothesis_id
            ],
        },
    )
    return 0


def strategy_dossier(repository: DataRepository, hypothesis_id: str) -> int:
    dossier = build_strategy_dossier(repository, hypothesis_id)
    if dossier is None:
        emit_error(
            "strategy-dossier", f"Strategy dossier for {hypothesis_id} not found"
        )
        return 1
    emit_response("strategy-dossier", dossier)
    return 0


def data_quality_report(
    repository: DataRepository,
    symbols: list[str],
    resolution: str,
    max_staleness_days: int | None,
    strict: bool = False,
) -> int:
    try:
        report = build_data_quality_report(
            repository,
            tuple(symbols),
            resolution,
            max_staleness_days,
        )
    except ValueError as error:
        emit_error("data-quality-report", error)
        return 1
    emit_response("data-quality-report", asdict(report), status=report.status)
    return 1 if strict and report.status == "fail" else 0
