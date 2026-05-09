from __future__ import annotations
import statistics
import math
from datetime import UTC, datetime
from typing import List, Dict

from project.common.models import TradeOutcome
from project.data.models import SignalEvaluation, HypothesisMetrics

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
    evaluations: List[SignalEvaluation], 
    horizon_idx: int = 2  # Default to forward_return_20
) -> HypothesisMetrics:
    """
    Aggregates signal evaluations into measurable research metrics.
    horizon_idx mapping: 0 -> return_1, 1 -> return_5, 2 -> return_20
    """
    if not evaluations:
        return HypothesisMetrics(0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    horizons = [1, 5, 20]
    attr_name = f"forward_return_{horizons[horizon_idx]}"
    
    returns = []
    for e in evaluations:
        val = getattr(e, attr_name)
        if not math.isnan(val):
            returns.append(val)

    if not returns:
        return HypothesisMetrics(len(evaluations), 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    n_signals = len(returns)
    hits = sum(1 for r in returns if r > 0)
    hit_rate = hits / n_signals
    mean_ret = statistics.mean(returns)
    median_ret = statistics.median(returns)
    
    # Volatility (Std Dev)
    vol = statistics.stdev(returns) if n_signals > 1 else 0.0
    
    # Sharpe-like score: mean / vol
    sharpe = mean_ret / vol if vol > 0 else 0.0
    
    # Max Drawdown on cumulative returns
    cum_ret = 0.0
    peak = -float('inf')
    max_dd = 0.0
    for r in returns:
        cum_ret += r
        if cum_ret > peak:
            peak = cum_ret
        dd = peak - cum_ret
        if dd > max_dd:
            max_dd = dd
            
    return HypothesisMetrics(
        n_signals=n_signals,
        hit_rate=hit_rate,
        mean_return=mean_ret,
        median_return=median_ret,
        volatility=vol,
        sharpe_like_score=sharpe,
        max_drawdown=max_dd
    )
