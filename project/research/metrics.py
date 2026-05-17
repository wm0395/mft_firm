from __future__ import annotations

from statistics import mean, median, pstdev
from typing import Sequence

from project.research.models import ResearchMetrics


def compute_metrics(
    trade_returns_pct: Sequence[float],
    equity_curve_pct: Sequence[float] | None = None,
) -> ResearchMetrics:
    returns = tuple(float(value) for value in trade_returns_pct)
    equity_curve = tuple(float(value) for value in equity_curve_pct) if equity_curve_pct else _equity_curve(returns)
    winning_trades = sum(1 for value in returns if value > 0)
    volatility = pstdev(returns) if len(returns) > 1 else 0.0
    return ResearchMetrics(
        trade_count=len(returns),
        winning_trades=winning_trades,
        win_rate=(winning_trades / len(returns)) if returns else 0.0,
        total_return_pct=sum(returns),
        mean_return_pct=mean(returns) if returns else 0.0,
        median_return_pct=median(returns) if returns else 0.0,
        volatility_pct=volatility,
        max_drawdown_pct=_max_drawdown(equity_curve),
        sharpe_like_score=(mean(returns) / volatility) if returns and volatility > 0 else 0.0,
    )


def _equity_curve(returns: tuple[float, ...]) -> tuple[float, ...]:
    total = 0.0
    curve: list[float] = []
    for value in returns:
        total += value
        curve.append(total)
    return tuple(curve)


def _max_drawdown(equity_curve_pct: tuple[float, ...]) -> float:
    peak = 0.0
    max_drawdown = 0.0
    for value in equity_curve_pct:
        peak = max(peak, value)
        max_drawdown = max(max_drawdown, peak - value)
    return max_drawdown
