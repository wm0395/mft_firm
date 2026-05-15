from __future__ import annotations

import math
import statistics

from project.common.models import TradeOutcome
from project.data.models import HypothesisMetrics, SignalEvaluation


def analyze_hypothesis_performance(outcomes: tuple[TradeOutcome, ...]) -> dict[str, dict[str, float | int]]:
    grouped: dict[str, list[TradeOutcome]] = {}
    for outcome in outcomes:
        grouped.setdefault(outcome.hypothesis_id, []).append(outcome)
    return {
        hypothesis_id: {
            "trades": len(items),
            "total_pnl": round(sum(item.pnl for item in items), 6),
            "average_pnl": round(sum(item.pnl for item in items) / len(items), 6),
        }
        for hypothesis_id, items in sorted(grouped.items())
    }


def aggregate_signal_performance(
    evaluations: list[SignalEvaluation],
    horizon_idx: int = 2,
) -> HypothesisMetrics:
    returns = _signal_returns(evaluations, horizon_idx)
    if not returns:
        return HypothesisMetrics(len(evaluations), 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    return _metrics_from_returns(len(returns), returns)


def _signal_returns(evaluations: list[SignalEvaluation], horizon_idx: int) -> list[float]:
    attr_name = _horizon_attribute(horizon_idx)
    return [
        value
        for value in (_signal_return(evaluation, attr_name) for evaluation in evaluations)
        if not math.isnan(value)
    ]


def _horizon_attribute(horizon_idx: int) -> str:
    horizons = (1, 5, 20)
    return f"forward_return_{horizons[horizon_idx]}"


def _signal_return(evaluation: SignalEvaluation, attr_name: str) -> float:
    return float(getattr(evaluation, attr_name))


def _metrics_from_returns(n_signals: int, returns: list[float]) -> HypothesisMetrics:
    hit_rate = sum(1 for value in returns if value > 0) / n_signals
    volatility = statistics.stdev(returns) if n_signals > 1 else 0.0
    return HypothesisMetrics(
        n_signals=n_signals,
        hit_rate=hit_rate,
        mean_return=statistics.mean(returns),
        median_return=statistics.median(returns),
        volatility=volatility,
        sharpe_like_score=statistics.mean(returns) / volatility if volatility > 0 else 0.0,
        max_drawdown=_max_drawdown(returns),
    )


def _max_drawdown(returns: list[float]) -> float:
    equity = 0.0
    peak = 0.0
    max_drawdown = 0.0
    for value in returns:
        equity += value
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, peak - equity)
    return max_drawdown
