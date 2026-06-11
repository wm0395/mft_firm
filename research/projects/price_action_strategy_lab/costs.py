from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class CostModel:
    name: str
    turnover_bps: float
    fixed_bps: float = 0.0


@dataclass(frozen=True)
class CostBreakdown:
    gross_return: pd.Series
    turnover: pd.Series
    cost_return: pd.Series
    net_return: pd.Series


def no_cost() -> CostModel:
    return CostModel(name="no_cost", turnover_bps=0.0, fixed_bps=0.0)


def turnover_cost(turnover_bps: float, fixed_bps: float = 0.0) -> CostModel:
    return CostModel(
        name=f"turnover_{turnover_bps:g}_fixed_{fixed_bps:g}",
        turnover_bps=float(turnover_bps),
        fixed_bps=float(fixed_bps),
    )


def apply_costs(
    gross_return: pd.Series,
    turnover: pd.Series,
    model: CostModel,
) -> CostBreakdown:
    aligned_turnover = turnover.reindex(gross_return.index).fillna(0.0)
    variable = aligned_turnover * (2.0 * model.turnover_bps / 10_000.0)
    fixed = gross_return.notna().astype(float) * (model.fixed_bps / 10_000.0)
    cost_return = variable + fixed
    net_return = gross_return - cost_return
    return CostBreakdown(
        gross_return=gross_return,
        turnover=aligned_turnover,
        cost_return=cost_return,
        net_return=net_return,
    )


def mean_bps(series: pd.Series) -> float:
    return float(series.mean() * 10_000.0)
