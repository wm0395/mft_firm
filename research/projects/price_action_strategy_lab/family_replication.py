from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from research.projects.price_action_strategy_lab.activator_specs import default_activator_registry
from research.projects.price_action_strategy_lab.alpha_specs import default_alpha_registry
from research.projects.price_action_strategy_lab.breadth_only_diagnostic import concentration_diagnostics
from research.projects.price_action_strategy_lab.breadth_only_diagnostic import threshold_stability
from research.projects.price_action_strategy_lab.narrow_falsification import NarrowHypothesis
from research.projects.price_action_strategy_lab.run_activator_suite import _load_panel
from research.projects.price_action_strategy_lab.run_activator_suite import _read_config
from research.projects.price_action_strategy_lab.soft_throttle_walk_forward_reports import markdown_table
from research.projects.price_action_strategy_lab.stress_confirmation import StressConfirmationConfig
from research.projects.price_action_strategy_lab.stress_confirmation import StressVariant
from research.projects.price_action_strategy_lab.stress_confirmation import _tail
from research.projects.price_action_strategy_lab.stress_confirmation import run_stress_confirmation
from research.projects.price_action_strategy_lab.universe_adapter import to_alpha101_panel


@dataclass(frozen=True)
class FamilyReplicationResult:
    report_dir: Path


def run_family_replication_config(config_path: str | Path) -> FamilyReplicationResult:
    raw = _read_config(Path(config_path))
    panel = to_alpha101_panel(_load_panel(raw))
    config = _base_config(raw)
    frames = [_alpha_result(panel, alpha, group, config) for group, alphas in _groups(raw).items() for alpha in alphas]
    report_dir = frames[0]["report_dir"] if frames else Path("research/projects/price_action_strategy_lab/reports/empty")
    _write(report_dir, _combined(frames))
    return FamilyReplicationResult(report_dir)


def _alpha_result(panel, alpha: str, group: str, config: StressConfirmationConfig) -> dict[str, pd.DataFrame | Path]:
    variants = tuple(_variant(alpha, item.variant_id, item.hypothesis.throttle_variant) for item in config.variants)
    result = run_stress_confirmation(panel, default_alpha_registry(), default_activator_registry(), _replace_variants(config, variants))
    return {
        "report_dir": result.report_dir,
        "fold": _tag(result.fold_metrics, alpha, group),
        "aggregate": _tag(result.aggregate_metrics, alpha, group),
        "tail": _tag(result.tail_diagnostics, alpha, group),
        "trade": _tag(result.trade_diagnostics, alpha, group),
        "event": _tag(result.event_split, alpha, group),
    }


def _combined(frames: list[dict[str, pd.DataFrame | Path]]) -> dict[str, pd.DataFrame]:
    fold = _concat(frames, "fold")
    tail = _concat(frames, "tail")
    event = _concat(frames, "event")
    trade = _concat(frames, "trade")
    return {
        "per_alpha": _per_alpha(fold, tail, event, trade),
        "group": _group_metrics(fold, event, trade),
        "tail": tail,
        "trade": trade,
        "event": event,
        "concentration": concentration_diagnostics(fold),
        "cost": _cost_stress(tail),
        "threshold": threshold_stability(fold),
    }


def _per_alpha(fold: pd.DataFrame, tail: pd.DataFrame, event: pd.DataFrame, trade: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for keys, frame in fold.groupby(["group", "alpha", "variant", "cost_bps"], sort=False):
        group, alpha, variant, cost = str(keys[0]), str(keys[1]), str(keys[2]), float(keys[3])
        row = _base_metric_row(group, alpha, variant, cost, frame)
        row.update(_tail_fields(tail, group, alpha, variant, cost))
        row.update(_event_fields(event, group, alpha, variant, cost))
        row["net_blocker_value"] = _trade_value(trade, group, alpha, variant, cost)
        rows.append(row)
    return pd.DataFrame(rows)


def _group_metrics(fold: pd.DataFrame, event: pd.DataFrame, trade: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for keys, frame in fold.groupby(["group", "variant", "cost_bps"], sort=False):
        group, variant, cost = str(keys[0]), str(keys[1]), float(keys[2])
        by_fold = frame.groupby("fold", as_index=False).mean(numeric_only=True)
        row = _base_metric_row(group, "GROUP", variant, cost, by_fold)
        row.update(_group_tail(by_fold))
        row.update(_group_event(event, group, variant, cost))
        row["net_blocker_value"] = _group_trade_value(trade, group, variant, cost)
        row["alpha_improve_rate"] = _alpha_improve_rate(fold, group, variant, cost)
        rows.append(row)
    return pd.DataFrame(rows)


def _base_metric_row(group: str, alpha: str, variant: str, cost: float, frame: pd.DataFrame) -> dict[str, object]:
    delta = frame["delta_return_pct"]
    return {
        "group": group,
        "alpha": alpha,
        "variant": variant,
        "cost_bps": cost,
        "mean_delta": float(delta.mean()),
        "helped_folds": int(delta.gt(0.10).sum()),
        "hurt_folds": int(delta.lt(-0.10).sum()),
        "avg_exposure": float(frame["avg_exposure"].mean()),
    }


def _tail_fields(tail: pd.DataFrame, group: str, alpha: str, variant: str, cost: float) -> dict[str, float]:
    row = tail.loc[_mask(tail, group, alpha, variant, cost)]
    if row.empty:
        return {}
    item = row.iloc[0]
    return {
        "left_tail_delta": float(item["left_tail_delta"]),
        "right_tail_retention": float(item["right_tail_retention"]),
        "ci_low": float(item["ci_low"]),
        "ci_high": float(item["ci_high"]),
        "paired_p_value": float(item["paired_p_value"]),
    }


def _event_fields(event: pd.DataFrame, group: str, alpha: str, variant: str, cost: float) -> dict[str, float]:
    rows = event.loc[_mask(event, group, alpha, variant, cost)]
    return {
        "unmatched_delta": _split_delta(rows, "unmatched"),
        "stress_delta": _split_delta(rows, "known_stress"),
    }


def _group_tail(frame: pd.DataFrame) -> dict[str, float]:
    tail = _tail(frame.assign(variant="group", cost_bps=float(frame["cost_bps"].iloc[0])))
    row = tail.iloc[0]
    return {
        "left_tail_delta": float(row["left_tail_delta"]),
        "right_tail_retention": float(row["right_tail_retention"]),
        "ci_low": float(row["ci_low"]),
        "ci_high": float(row["ci_high"]),
        "paired_p_value": float(row["paired_p_value"]),
    }


def _group_event(event: pd.DataFrame, group: str, variant: str, cost: float) -> dict[str, float]:
    rows = event.loc[event["group"].eq(group) & event["variant"].eq(variant) & event["cost_bps"].eq(cost)]
    return {"unmatched_delta": _split_delta(rows, "unmatched"), "stress_delta": _split_delta(rows, "known_stress")}


def _write(report_dir: Path, frames: dict[str, pd.DataFrame]) -> None:
    paths = _paths(report_dir)
    for key, frame in frames.items():
        frame.to_csv(paths[key], index=False)
    paths["markdown"].write_text(_markdown(frames), encoding="utf-8")


def _paths(report_dir: Path) -> dict[str, Path]:
    prefix = "breadth_risk_off_family"
    return {
        "per_alpha": report_dir / f"{prefix}_per_alpha_metrics.csv",
        "group": report_dir / f"{prefix}_group_metrics.csv",
        "tail": report_dir / f"{prefix}_tail_diagnostics.csv",
        "trade": report_dir / f"{prefix}_trade_diagnostics.csv",
        "event": report_dir / f"{prefix}_event_split.csv",
        "concentration": report_dir / f"{prefix}_fold_concentration.csv",
        "cost": report_dir / f"{prefix}_cost_stress.csv",
        "threshold": report_dir / f"{prefix}_threshold_stability.csv",
        "markdown": report_dir / f"{prefix}_replication_report.md",
    }


def _markdown(frames: dict[str, pd.DataFrame]) -> str:
    lines = ["# Breadth Risk-Off Family Replication", ""]
    lines.extend(["## Group Metrics", "", markdown_table(frames["group"], max_rows=40), ""])
    lines.extend(["## Per-Alpha Metrics", "", markdown_table(frames["per_alpha"], max_rows=80), ""])
    lines.extend(["## Decision", "", _decision(frames["group"]), ""])
    return "\n".join(lines)


def _decision(group: pd.DataFrame) -> str:
    rows = group.loc[group["variant"].ne("baseline") & group["cost_bps"].eq(10.0)]
    passed = rows.loc[rows["mean_delta"].gt(0.0) & rows["right_tail_retention"].ge(0.95) & rows["unmatched_delta"].ge(0.0)]
    return "Retain research overlay candidate." if not passed.empty else "Reject family overlay."


def _base_config(raw: dict[str, Any]) -> StressConfirmationConfig:
    from research.projects.price_action_strategy_lab.run_stress_confirmation import _config

    return _config(raw)


def _variant(alpha: str, variant_id: str, throttle: str) -> StressVariant:
    hypothesis = NarrowHypothesis(variant_id, (alpha,), "breadth_risk_off", "high", throttle, (0.5, 0.6, 0.7, 0.8), _grid(throttle))
    return StressVariant(variant_id, () if variant_id == "baseline" else ("breadth_risk_off",), "baseline" if variant_id == "baseline" else "single", hypothesis)


def _grid(throttle: str) -> tuple[dict[str, float], ...]:
    if throttle == "drawdown_only_throttle":
        return ({"down": 0.25, "up": 1.0}, {"down": 0.5, "up": 1.0}, {"down": 0.75, "up": 1.0})
    return ({"down": 0.25, "up": 1.10}, {"down": 0.25, "up": 1.25}, {"down": 0.50, "up": 1.10}, {"down": 0.50, "up": 1.25})


def _replace_variants(config: StressConfirmationConfig, variants: tuple[StressVariant, ...]) -> StressConfirmationConfig:
    return StressConfirmationConfig(variants, config.cache_dir, config.report_root, config.source_report_dir, config.mode, config.horizon, config.cost_bps, config.train_size_days, config.test_size_days, config.step_size_days, config.lookahead_days, config.max_folds, config.top_quantile, config.min_names, config.max_workers, config.gpu)


def _groups(raw: dict[str, Any]) -> dict[str, tuple[str, ...]]:
    return {str(group["group_id"]): tuple(str(alpha) for alpha in group["alphas"]) for group in raw.get("alpha_groups", ())}


def _tag(frame: pd.DataFrame, alpha: str, group: str) -> pd.DataFrame:
    out = frame.copy()
    out.insert(0, "alpha", alpha)
    out.insert(0, "group", group)
    return out


def _concat(frames: list[dict[str, pd.DataFrame | Path]], key: str) -> pd.DataFrame:
    return pd.concat([item[key] for item in frames if isinstance(item[key], pd.DataFrame)], ignore_index=True)


def _mask(frame: pd.DataFrame, group: str, alpha: str, variant: str, cost: float) -> pd.Series:
    return frame["group"].eq(group) & frame["alpha"].eq(alpha) & frame["variant"].eq(variant) & frame["cost_bps"].eq(cost)


def _split_delta(rows: pd.DataFrame, split: str) -> float:
    match = rows.loc[rows["split"].eq(split)]
    return float(match.iloc[0]["mean_delta"]) if not match.empty else 0.0


def _trade_value(trade: pd.DataFrame, group: str, alpha: str, variant: str, cost: float) -> float:
    return float(trade.loc[_mask(trade, group, alpha, variant, cost), "net_blocker_value"].sum())


def _group_trade_value(trade: pd.DataFrame, group: str, variant: str, cost: float) -> float:
    rows = trade.loc[trade["group"].eq(group) & trade["variant"].eq(variant) & trade["cost_bps"].eq(cost)]
    return float(rows.groupby("alpha")["net_blocker_value"].sum().mean()) if not rows.empty else 0.0


def _alpha_improve_rate(fold: pd.DataFrame, group: str, variant: str, cost: float) -> float:
    rows = fold.loc[fold["group"].eq(group) & fold["variant"].eq(variant) & fold["cost_bps"].eq(cost)]
    improved = rows.groupby("alpha")["delta_return_pct"].mean().gt(0.0)
    return float(improved.mean()) if not improved.empty else 0.0


def _cost_stress(tail: pd.DataFrame) -> pd.DataFrame:
    return tail[["group", "alpha", "variant", "cost_bps", "mean_delta_vs_baseline", "left_tail_delta", "right_tail_retention", "ci_low"]]
