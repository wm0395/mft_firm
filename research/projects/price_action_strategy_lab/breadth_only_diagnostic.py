from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from research.projects.price_action_strategy_lab.run_activator_suite import _load_panel
from research.projects.price_action_strategy_lab.run_activator_suite import _read_config
from research.projects.price_action_strategy_lab.run_stress_confirmation import _config
from research.projects.price_action_strategy_lab.soft_throttle_walk_forward_reports import markdown_table
from research.projects.price_action_strategy_lab.stress_confirmation import StressConfirmationResult
from research.projects.price_action_strategy_lab.stress_confirmation import run_stress_confirmation
from research.projects.price_action_strategy_lab.activator_specs import default_activator_registry
from research.projects.price_action_strategy_lab.alpha_specs import default_alpha_registry
from research.projects.price_action_strategy_lab.universe_adapter import to_alpha101_panel


@dataclass(frozen=True)
class BreadthOnlyResult:
    report_dir: Path


def run_breadth_only_config(config_path: str | Path) -> BreadthOnlyResult:
    raw = _read_config(Path(config_path))
    panel = to_alpha101_panel(_load_panel(raw))
    result = run_stress_confirmation(panel, default_alpha_registry(), default_activator_registry(), _config(raw))
    write_breadth_only_artifacts(result)
    return BreadthOnlyResult(result.report_dir)


def write_breadth_only_artifacts(result: StressConfirmationResult) -> dict[str, Path]:
    paths = _paths(result.report_dir)
    result.fold_metrics.to_csv(paths["fold"], index=False)
    result.aggregate_metrics.to_csv(paths["aggregate"], index=False)
    result.tail_diagnostics.to_csv(paths["tail"], index=False)
    result.trade_diagnostics.to_csv(paths["trade"], index=False)
    result.event_split.to_csv(paths["event"], index=False)
    threshold_stability(result.fold_metrics).to_csv(paths["threshold"], index=False)
    concentration_diagnostics(result.fold_metrics).to_csv(paths["concentration"], index=False)
    result.cost_stress.to_csv(paths["cost"], index=False)
    paths["markdown"].write_text(_markdown(result), encoding="utf-8")
    return paths


def threshold_stability(folds: pd.DataFrame) -> pd.DataFrame:
    frame = folds.loc[~folds["variant"].eq("baseline")].copy()
    if frame.empty:
        return pd.DataFrame()
    rows = []
    for keys, group in frame.groupby(["variant", "cost_bps"], sort=False):
        rows.append(_threshold_row(str(keys[0]), float(keys[1]), group))
    return pd.DataFrame(rows)


def concentration_diagnostics(folds: pd.DataFrame) -> pd.DataFrame:
    frame = folds.loc[~folds["variant"].eq("baseline")].copy()
    if frame.empty:
        return pd.DataFrame()
    rows = []
    for keys, group in frame.groupby(["variant", "cost_bps"], sort=False):
        rows.append(fold_concentration_row(str(keys[0]), float(keys[1]), group))
    return pd.DataFrame(rows)


def fold_concentration_row(variant: str, cost: float, frame: pd.DataFrame) -> dict[str, float | int | str]:
    delta = frame["delta_return_pct"].sort_values(ascending=False)
    total = float(frame["delta_return_pct"].sum())
    return {
        "variant": variant,
        "cost_bps": cost,
        "fold_count": int(frame["fold"].nunique()),
        "helped_folds": int(frame["delta_return_pct"].gt(0.10).sum()),
        "hurt_folds": int(frame["delta_return_pct"].lt(-0.10).sum()),
        "top_1_fold_contribution": _share(float(delta.head(1).sum()), total),
        "top_3_fold_contribution": _share(float(delta.head(3).sum()), total),
        "excluding_best_fold_delta": float(frame["delta_return_pct"].drop(delta.index[0]).sum()),
        "excluding_worst_fold_delta": float(frame["delta_return_pct"].drop(delta.index[-1]).sum()),
    }


def _threshold_row(variant: str, cost: float, group: pd.DataFrame) -> dict[str, float | int | str]:
    return {
        "variant": variant,
        "cost_bps": cost,
        "fold_count": int(group["fold"].nunique()),
        "threshold_mean": float(group["selected_threshold"].mean()),
        "threshold_std": float(group["selected_threshold"].std(ddof=0)),
        "selected_quantile_mean": float(group["selected_quantile"].mean()),
        "selected_quantile_std": float(group["selected_quantile"].std(ddof=0)),
        "activation_rate": float(group["avg_exposure"].ne(1.0).mean()),
        "average_exposure": float(group["avg_exposure"].mean()),
    }


def _markdown(result: StressConfirmationResult) -> str:
    lines = ["# Support Trendline Breadth-Only Diagnostic", ""]
    lines.extend(["## Aggregate", "", markdown_table(result.aggregate_metrics, max_rows=20), ""])
    lines.extend(["## Tail", "", markdown_table(result.tail_diagnostics, max_rows=20), ""])
    lines.extend(["## Event Split", "", markdown_table(result.event_split, max_rows=20), ""])
    lines.extend(["## Threshold Stability", "", markdown_table(threshold_stability(result.fold_metrics), max_rows=20), ""])
    lines.extend(["## Fold Concentration", "", markdown_table(concentration_diagnostics(result.fold_metrics), max_rows=20), ""])
    lines.extend(["## Decision", "", _decision(result.tail_diagnostics, result.event_split, concentration_diagnostics(result.fold_metrics)), ""])
    return "\n".join(lines)


def _decision(tail: pd.DataFrame, events: pd.DataFrame, concentration: pd.DataFrame) -> str:
    cost = _target_cost(tail)
    target = tail.loc[tail["variant"].eq("breadth_risk_off_high") & tail["cost_bps"].eq(cost)]
    unmatched = events.loc[events["variant"].eq("breadth_risk_off_high") & events["cost_bps"].eq(cost) & events["split"].eq("unmatched")]
    conc = concentration.loc[concentration["variant"].eq("breadth_risk_off_high") & concentration["cost_bps"].eq(cost)]
    if target.empty or unmatched.empty or conc.empty:
        return "Reject: missing target diagnostic rows."
    if float(target.iloc[0]["right_tail_retention"]) < 0.95:
        return "Reject: right-tail retention below 95%."
    if float(unmatched.iloc[0]["mean_delta"]) < 0.0:
        return "Reject: unmatched delta is negative."
    if float(conc.iloc[0]["excluding_best_fold_delta"]) <= 0.0:
        return "Reject: edge disappears excluding best fold."
    return "Research lead: breadth_risk_off survives this focused diagnostic, still not deployable."


def _target_cost(tail: pd.DataFrame) -> float:
    costs = sorted(float(cost) for cost in tail["cost_bps"].dropna().unique())
    return costs[0] if costs else 10.0


def _paths(report_dir: Path) -> dict[str, Path]:
    prefix = "support_trendline_breadth_only"
    return {
        "fold": report_dir / f"{prefix}_fold_metrics.csv",
        "aggregate": report_dir / f"{prefix}_aggregate_metrics.csv",
        "tail": report_dir / f"{prefix}_tail_diagnostics.csv",
        "trade": report_dir / f"{prefix}_trade_diagnostics.csv",
        "event": report_dir / f"{prefix}_event_split.csv",
        "threshold": report_dir / f"{prefix}_threshold_stability.csv",
        "concentration": report_dir / f"{prefix}_fold_concentration.csv",
        "cost": report_dir / f"{prefix}_cost_stress.csv",
        "markdown": report_dir / f"{prefix}_report.md",
    }


def _share(part: float, total: float) -> float:
    return float(part / total) if total else 0.0
