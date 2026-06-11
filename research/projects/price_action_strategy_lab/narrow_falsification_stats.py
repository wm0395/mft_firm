from __future__ import annotations

from importlib import import_module

import numpy as np
import pandas as pd

from research.projects.price_action_strategy_lab.soft_throttle_analysis import _annual_sharpe
from research.projects.price_action_strategy_lab.soft_throttle_analysis import _max_drawdown_pct
from research.projects.price_action_strategy_lab.soft_throttle_analysis import _total_return_pct


def metric_row(returns: pd.Series, prefix: str) -> dict[str, float]:
    clean = returns.dropna().fillna(0.0)
    return {
        f"{prefix}_return_pct": _total_return_pct(clean),
        f"{prefix}_ann_sharpe": _annual_sharpe(clean),
        f"{prefix}_max_drawdown_pct": _max_drawdown_pct(clean),
        f"{prefix}_negative_day_rate": float(clean.lt(0.0).mean()) if not clean.empty else 0.0,
        f"{prefix}_worst_day_pct": float(clean.min() * 100.0) if not clean.empty else 0.0,
    }


def trade_diagnostics(
    positions: pd.DataFrame,
    future: pd.DataFrame,
    multiplier: pd.Series,
    horizon: int,
) -> dict[str, float | int]:
    base = positions.mul(future.reindex_like(positions).fillna(0.0)).div(float(horizon))
    scaled = base.mul(multiplier.reindex(base.index).fillna(1.0), axis=0)
    active = positions.ne(0.0) & base.ne(0.0)
    mult = pd.DataFrame({col: multiplier.reindex(base.index).fillna(1.0) for col in base.columns})
    return _trade_values(base.where(active), scaled.where(active), mult.where(active))


def tail_diagnostics(folds: pd.DataFrame) -> pd.DataFrame:
    if folds.empty:
        return pd.DataFrame()
    rows = [_tail_row(keys, frame) for keys, frame in folds.groupby(["hypothesis_id", "cost_bps"], sort=False)]
    result = pd.DataFrame(rows)
    result["bh_p_value"] = _bh_pvalues(result["paired_p_value"])
    result["decision"] = result.apply(_decision, axis=1)
    return result


def aggregate_metrics(folds: pd.DataFrame) -> pd.DataFrame:
    if folds.empty:
        return pd.DataFrame()
    rows = []
    for keys, frame in folds.groupby(["hypothesis_id", "cost_bps"], sort=False):
        hypothesis_id, cost_bps = keys
        rows.append(_aggregate_row(str(hypothesis_id), float(cost_bps), frame))
    return pd.DataFrame(rows)


def gate_stability(folds: pd.DataFrame) -> pd.DataFrame:
    if folds.empty:
        return pd.DataFrame()
    rows = []
    for keys, frame in folds.groupby(["hypothesis_id", "cost_bps"], sort=False):
        rows.append(_stability_row(str(keys[0]), float(keys[1]), frame))
    return pd.DataFrame(rows)


def event_cluster_metrics(folds: pd.DataFrame, event_labels: pd.DataFrame) -> pd.DataFrame:
    if folds.empty or event_labels.empty:
        return pd.DataFrame()
    labels = event_labels.groupby("fold")["event_label"].agg(lambda x: x.value_counts().index[0])
    merged = folds.assign(event_label=folds["fold"].map(labels).fillna("unmatched"))
    grouped = merged.groupby(["hypothesis_id", "cost_bps", "event_label"], sort=False)
    return pd.DataFrame([_event_row(keys, frame) for keys, frame in grouped])


def _trade_values(base: pd.DataFrame, scaled: pd.DataFrame, mult: pd.DataFrame) -> dict[str, float | int]:
    winner = base.gt(0.0)
    loser = base.lt(0.0)
    blocked = mult.eq(0.0)
    reduced = mult.gt(0.0) & mult.lt(1.0)
    increased = mult.gt(1.0)
    accepted = mult.eq(1.0)
    return {
        "accepted_winner": _count(accepted & winner),
        "accepted_loser": _count(accepted & loser),
        "blocked_winner": _count(blocked & winner),
        "blocked_loser": _count(blocked & loser),
        "reduced_winner": _count(reduced & winner),
        "reduced_loser": _count(reduced & loser),
        "increased_winner": _count(increased & winner),
        "increased_loser": _count(increased & loser),
        **_trade_value_fields(base, scaled, blocked, reduced, increased, winner, loser),
    }


def _trade_value_fields(base, scaled, blocked, reduced, increased, winner, loser) -> dict[str, float]:
    values = {
        "loss_saved_from_blocked_losers": _sum(-base.where(blocked & loser)),
        "profit_lost_from_blocked_winners": _sum(base.where(blocked & winner)),
        "loss_reduced_from_sized_down_losers": _sum((scaled - base).where(reduced & loser)),
        "profit_reduced_from_sized_down_winners": _sum((base - scaled).where(reduced & winner)),
        "profit_added_from_sized_up_winners": _sum((scaled - base).where(increased & winner)),
        "loss_added_from_sized_up_losers": _sum((base - scaled).where(increased & loser)),
    }
    values["net_blocker_value"] = (
        values["loss_saved_from_blocked_losers"]
        - values["profit_lost_from_blocked_winners"]
        + values["loss_reduced_from_sized_down_losers"]
        - values["profit_reduced_from_sized_down_winners"]
        + values["profit_added_from_sized_up_winners"]
        - values["loss_added_from_sized_up_losers"]
    )
    return {key: float(value * 100.0) for key, value in values.items()}


def _tail_row(keys: tuple[object, object], frame: pd.DataFrame) -> dict[str, float | str]:
    hypothesis_id, cost_bps = keys
    base = frame["baseline_return_pct"]
    delta = frame["delta_return_pct"]
    left = frame.loc[base.le(base.quantile(0.25)), "delta_return_pct"]
    right = frame.loc[base.ge(base.quantile(0.75))]
    ci_low, ci_high = _bootstrap_ci(delta)
    t_stat, p_value = _paired_t(delta)
    return {
        "hypothesis_id": str(hypothesis_id),
        "cost_bps": float(str(cost_bps)),
        "fold_count": int(frame["fold"].nunique()),
        "mean_delta_vs_baseline_pct": float(delta.mean()),
        "delta_ci_low_pct": ci_low,
        "delta_ci_high_pct": ci_high,
        "paired_t_stat": t_stat,
        "paired_p_value": p_value,
        "left_tail_delta_pct": float(left.mean()),
        "right_tail_retention": _ratio(right["variant_return_pct"].mean(), right["baseline_return_pct"].mean()),
        "worst_fold_improvement_pct": float(delta.loc[base.idxmin()]),
        "best_fold_damage_pct": float(delta.loc[base.idxmax()]),
    }


def _aggregate_row(hypothesis_id: str, cost_bps: float, frame: pd.DataFrame) -> dict[str, float | str]:
    return {
        "hypothesis_id": hypothesis_id,
        "cost_bps": cost_bps,
        "fold_count": int(frame["fold"].nunique()),
        "baseline_return_pct": float(frame["baseline_return_pct"].sum()),
        "variant_return_pct": float(frame["variant_return_pct"].sum()),
        "delta_return_pct": float(frame["delta_return_pct"].sum()),
        "negative_fold_rate": float(frame["variant_return_pct"].lt(0.0).mean()),
        "worst_fold_sharpe": float(frame["variant_ann_sharpe"].min()),
        "latest_fold_sharpe": float(frame.sort_values("fold").iloc[-1]["variant_ann_sharpe"]),
        "avg_exposure_multiplier": float(frame["avg_exposure_multiplier"].mean()),
    }


def _stability_row(hypothesis_id: str, cost_bps: float, frame: pd.DataFrame) -> dict[str, float | str]:
    return {
        "hypothesis_id": hypothesis_id,
        "cost_bps": cost_bps,
        "fold_count": int(frame["fold"].nunique()),
        "threshold_mean": float(frame["selected_threshold"].mean()),
        "threshold_std": float(frame["selected_threshold"].std(ddof=0)),
        "multiplier_down_mean": float(frame["multiplier_down"].mean()),
        "multiplier_up_mean": float(frame["multiplier_up"].mean()),
        "activation_rate": float(frame["activation_rate"].mean()),
        "avg_exposure_multiplier": float(frame["avg_exposure_multiplier"].mean()),
    }


def _event_row(keys: tuple[object, object, object], frame: pd.DataFrame) -> dict[str, float | str]:
    return {
        "hypothesis_id": str(keys[0]),
        "cost_bps": float(str(keys[1])),
        "event_label": str(keys[2]),
        "fold_count": int(frame["fold"].nunique()),
        "mean_delta_pct": float(frame["delta_return_pct"].mean()),
        "mean_baseline_return_pct": float(frame["baseline_return_pct"].mean()),
        "mean_variant_return_pct": float(frame["variant_return_pct"].mean()),
    }


def _bootstrap_ci(values: pd.Series) -> tuple[float, float]:
    clean = values.dropna().to_numpy(dtype=float)
    if clean.size == 0:
        return 0.0, 0.0
    rng = np.random.default_rng(17)
    draws = rng.choice(clean, size=(2000, clean.size), replace=True).mean(axis=1)
    return float(np.quantile(draws, 0.05)), float(np.quantile(draws, 0.95))


def _paired_t(values: pd.Series) -> tuple[float, float]:
    clean = values.dropna().to_numpy(dtype=float)
    if clean.size < 2 or float(np.std(clean, ddof=1)) == 0.0:
        return 0.0, 1.0
    result = import_module("scipy.stats").ttest_1samp(clean, 0.0)
    return float(result.statistic), float(result.pvalue)


def _bh_pvalues(values: pd.Series) -> pd.Series:
    pvals = values.fillna(1.0).to_numpy(dtype=float)
    order = np.argsort(pvals)
    adjusted = np.empty_like(pvals)
    running = 1.0
    for rank, idx in enumerate(order[::-1], start=1):
        running = min(running, pvals[idx] * len(pvals) / (len(pvals) - rank + 1))
        adjusted[idx] = running
    return pd.Series(adjusted, index=values.index)


def _decision(row: pd.Series) -> str:
    if float(row["right_tail_retention"]) < 0.95:
        return "reject_right_tail_loss"
    if float(row["left_tail_delta_pct"]) <= 0.0:
        return "reject_no_left_tail_help"
    if float(row["delta_ci_low_pct"]) <= 0.0 or float(row["bh_p_value"]) >= 0.05:
        return "research_only_not_significant"
    return "passes_initial_falsification"


def _count(frame: pd.DataFrame) -> int:
    return int(frame.fillna(False).to_numpy(dtype=bool).sum())


def _sum(frame: pd.DataFrame) -> float:
    return float(frame.fillna(0.0).to_numpy(dtype=float).sum())


def _ratio(numerator: float, denominator: float) -> float:
    return float(numerator / denominator) if denominator else 0.0
