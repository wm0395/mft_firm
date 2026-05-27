from __future__ import annotations

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from research.alpha101_engine import backtest_weights, performance_metrics


def backtests_by_cost(weights: pd.DataFrame, next_returns: pd.DataFrame, costs: tuple[float, ...]) -> dict[float, dict]:
    gross = backtest_weights(weights, next_returns, 0.0)["gross_returns"]
    turnover = weights.diff().abs().sum(axis=1, min_count=1).fillna(weights.abs().sum(axis=1))
    rows = {}
    for cost_bps in costs:
        net = gross - turnover * (cost_bps / 10000.0)
        valid = net.dropna().index
        returns = net.reindex(valid)
        cost_turnover = turnover.reindex(valid).fillna(0.0)
        rows[cost_bps] = {"returns": returns, "metrics": performance_metrics(returns, cost_turnover)}
    return rows


def portfolio_row_from_backtests(
    labels: dict[str, object],
    cost_bps: float,
    alpha_bt: dict,
    benchmark_bt: dict,
    avg_names: float,
) -> dict:
    pair = pd.concat([alpha_bt["returns"].rename("alpha"), benchmark_bt["returns"].rename("benchmark")], axis=1).dropna()
    excess = pair["alpha"] - pair["benchmark"]
    row = dict(labels)
    row.update({"cost_bps": cost_bps, "avg_names": avg_names})
    row.update({f"alpha_{key}": value for key, value in alpha_bt["metrics"].items()})
    row.update({f"benchmark_{key}": value for key, value in benchmark_bt["metrics"].items()})
    row.update({f"active_{key}": value for key, value in performance_metrics(excess).items()})
    return row


def average_names(weights: pd.DataFrame) -> float:
    return weights.abs().gt(1e-12).sum(axis=1).replace(0, np.nan).mean()
