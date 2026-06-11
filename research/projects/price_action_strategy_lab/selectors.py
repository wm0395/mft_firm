from __future__ import annotations

import pandas as pd

from research.projects.price_action_strategy_lab.backtest_modes import (
    BacktestResult,
    summarize_backtest,
)
from research.projects.price_action_strategy_lab.selector_registry import (
    SelectorDecision,
    selector_spec,
)


@selector_spec(
    name="best_mean_net_bps",
    description="Choose the candidate with the highest observed mean net return.",
)
def best_mean_net_bps(results: tuple[BacktestResult, ...]) -> SelectorDecision:
    summary = selector_summary(results)
    if summary.empty:
        return _abstain("no_candidates")
    row = summary.sort_values("net_mean_bps", ascending=False).iloc[0]
    if int(row["obs"]) == 0:
        return _abstain("no_observations")
    confidence = max(float(row["net_mean_bps"]), 0.0) / 100.0
    return SelectorDecision(
        selector="best_mean_net_bps",
        chosen_name=str(row["name"]),
        confidence=float(confidence),
        abstain=False,
        reason_code="highest_mean_net_bps",
    )


@selector_spec(
    name="positive_mean_abstain",
    description="Choose the best positive candidate and abstain if none are positive.",
)
def positive_mean_abstain(results: tuple[BacktestResult, ...]) -> SelectorDecision:
    summary = selector_summary(results)
    positive = summary.loc[summary["net_mean_bps"].gt(0.0)]
    if positive.empty:
        return _abstain("no_positive_candidate")
    row = positive.sort_values("net_mean_bps", ascending=False).iloc[0]
    return SelectorDecision(
        selector="positive_mean_abstain",
        chosen_name=str(row["name"]),
        confidence=float(row["net_mean_bps"]) / 100.0,
        abstain=False,
        reason_code="positive_mean_net_bps",
    )


@selector_spec(
    name="lower_bound_net_bps_abstain",
    description="Choose the best lower-bound candidate and abstain if the bound is non-positive.",
)
def lower_bound_net_bps_abstain(results: tuple[BacktestResult, ...]) -> SelectorDecision:
    summary = selector_summary(results)
    if summary.empty:
        return _abstain("no_candidates")
    ranked = summary.assign(lower_bound_bps=summary.apply(_lower_bound_bps, axis=1))
    row = ranked.sort_values(["lower_bound_bps", "net_mean_bps"], ascending=False).iloc[0]
    if float(row["lower_bound_bps"]) <= 0.0:
        return _abstain("no_positive_lower_bound")
    return SelectorDecision(
        selector="lower_bound_net_bps_abstain",
        chosen_name=str(row["name"]),
        confidence=float(row["lower_bound_bps"]) / 100.0,
        abstain=False,
        reason_code="highest_lower_bound_net_bps",
    )


def selector_summary(results: tuple[BacktestResult, ...]) -> pd.DataFrame:
    rows = [summarize_backtest(result) for result in results]
    return pd.DataFrame(rows)


def _abstain(reason: str) -> SelectorDecision:
    return SelectorDecision(
        selector="abstain",
        chosen_name="",
        confidence=0.0,
        abstain=True,
        reason_code=reason,
    )


def _lower_bound_bps(row: pd.Series) -> float:
    obs = float(row.get("obs", 0.0))
    mean = float(row.get("net_mean_bps", 0.0))
    std = float(row.get("net_std_bps", float("nan")))
    if obs <= 1.0 or pd.isna(std) or std <= 0.0:
        return float("-inf")
    return mean - 1.96 * std / obs**0.5


SELECTORS = (best_mean_net_bps, positive_mean_abstain, lower_bound_net_bps_abstain)
