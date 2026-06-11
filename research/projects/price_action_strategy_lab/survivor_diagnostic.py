from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
from pathlib import Path
from typing import cast

import pandas as pd

from research.notebooks.alpha_001.research.alpha101_engine import Alpha101Panel
from research.notebooks.alpha_001.research.alpha101_engine import forward_return
from research.projects.price_action_strategy_lab.activator_registry import ActivatorRegistry
from research.projects.price_action_strategy_lab.activator_suite import build_activator_masks
from research.projects.price_action_strategy_lab.alpha_registry import AlphaRegistry
from research.projects.price_action_strategy_lab.alpha_runner import load_signal_bundles
from research.projects.price_action_strategy_lab.compute_backend import GpuConfig
from research.projects.price_action_strategy_lab.narrow_falsification import FoldSpec
from research.projects.price_action_strategy_lab.narrow_falsification import NarrowFalsificationConfig
from research.projects.price_action_strategy_lab.narrow_falsification import NarrowHypothesis
from research.projects.price_action_strategy_lab.narrow_falsification import _baseline_result
from research.projects.price_action_strategy_lab.narrow_falsification import _daily
from research.projects.price_action_strategy_lab.narrow_falsification import _folds
from research.projects.price_action_strategy_lab.narrow_falsification import _multiplier
from research.projects.price_action_strategy_lab.narrow_falsification import _threshold
from research.projects.price_action_strategy_lab.narrow_falsification_stats import metric_row
from research.projects.price_action_strategy_lab.soft_throttle_analysis import _total_return_pct
from research.projects.price_action_strategy_lab.soft_throttle_walk_forward_reports import markdown_table
from research.projects.price_action_strategy_lab.survivor_features import blocker_value_row
from research.projects.price_action_strategy_lab.survivor_features import build_survivor_features
from research.projects.price_action_strategy_lab.survivor_features import saved_loser_lost_winner_summary
from research.projects.price_action_strategy_lab.survivor_features import trade_feature_rows


@dataclass(frozen=True)
class SurvivorDiagnosticConfig:
    hypothesis: NarrowHypothesis
    cache_dir: Path
    report_root: Path
    source_report_dir: Path
    mode: str = "ranked_long_only"
    horizon: int = 10
    cost_bps: tuple[float, ...] = (10.0, 25.0, 50.0, 75.0)
    train_size_days: int = 126
    test_size_days: int = 21
    step_size_days: int = 21
    lookahead_days: int = 10
    max_folds: int = 24
    top_quantile: float = 0.8
    min_names: int = 20
    max_workers: int = 1
    gpu: GpuConfig = GpuConfig()


@dataclass(frozen=True)
class SurvivorDiagnosticResult:
    report_dir: Path
    trade_diagnostics: pd.DataFrame
    blocker_value: pd.DataFrame
    saved_loser_vs_lost_winner: pd.DataFrame
    fold_anatomy: pd.DataFrame
    threshold_sensitivity: pd.DataFrame
    cost_stress: pd.DataFrame


def run_survivor_diagnostic(
    panel: Alpha101Panel,
    alpha_registry: AlphaRegistry,
    activator_registry: ActivatorRegistry,
    config: SurvivorDiagnosticConfig,
) -> SurvivorDiagnosticResult:
    bundle = load_signal_bundles(
        panel,
        alpha_registry,
        config.hypothesis.alphas,
        config.cache_dir,
        config.gpu,
        config.max_workers,
    )[0]
    intensity = build_activator_masks(panel, activator_registry, config.max_workers)[config.hypothesis.indicator].mean(axis=1)
    future = forward_return(panel.close, config.horizon)
    features = build_survivor_features(panel, bundle.signal, intensity)
    rows = _run_folds(panel, bundle, intensity, future, features, config)
    result = SurvivorDiagnosticResult(_timestamped_report_dir(config.report_root), *rows)
    write_survivor_diagnostic_reports(result)
    return result


def write_survivor_diagnostic_reports(result: SurvivorDiagnosticResult) -> dict[str, Path]:
    result.report_dir.mkdir(parents=True, exist_ok=True)
    paths = _report_paths(result.report_dir)
    result.trade_diagnostics.to_csv(paths["trade"], index=False)
    result.blocker_value.to_csv(paths["blocker"], index=False)
    result.saved_loser_vs_lost_winner.to_csv(paths["saved_lost"], index=False)
    result.fold_anatomy.to_csv(paths["fold"], index=False)
    result.threshold_sensitivity.to_csv(paths["threshold"], index=False)
    result.cost_stress.to_csv(paths["cost"], index=False)
    paths["markdown"].write_text(_report_markdown(result), encoding="utf-8")
    return paths


def perturbed_quantiles(selected: float) -> tuple[float, ...]:
    return tuple(round(max(0.01, min(0.99, selected + delta)), 4) for delta in (-0.10, -0.05, 0.0, 0.05, 0.10))


def _run_folds(panel, bundle, intensity, future, features, config):
    fold_rows: list[dict[str, object]] = []
    trade_frames: list[pd.DataFrame] = []
    sensitivity_rows: list[dict[str, object]] = []
    value_rows: list[dict[str, object]] = []
    event_labels = _event_labels(config.source_report_dir)
    baseline_cache: dict[tuple[str, float, str, str, int], object] = {}
    for cost in config.cost_bps:
        for fold in _folds(panel.close.index, _narrow_config(config)):
            selected = _select_params(panel, bundle, intensity, future, fold, cost, config, baseline_cache)
            data = _evaluate(panel, bundle, intensity, future, features, fold, cost, selected, config, baseline_cache)
            event_label = event_labels.get(fold.fold, "unmatched")
            fold_rows.append(_fold_row(fold, cost, selected, data, event_label))
            sensitivity_rows.extend(_threshold_rows(panel, bundle, intensity, future, fold, cost, selected, config, baseline_cache))
            value_rows.append(_value_row(fold, cost, data.trade_rows, event_label))
            trade_frames.append(_annotate(data.trade_rows, fold, cost, selected, event_label))
    trade = pd.concat(trade_frames, ignore_index=True) if trade_frames else pd.DataFrame()
    fold_frame = pd.DataFrame(fold_rows)
    return (
        trade,
        pd.DataFrame(value_rows),
        _saved_lost_frame(trade),
        fold_frame,
        pd.DataFrame(sensitivity_rows),
        _cost_stress(fold_frame),
    )


@dataclass(frozen=True)
class _EvalData:
    baseline: pd.Series
    throttle: pd.Series
    multiplier: pd.Series
    base_drawdown: float
    throttle_drawdown: float
    trade_rows: pd.DataFrame


def _evaluate(panel, bundle, intensity, future, features, fold, cost, selected, config, cache) -> _EvalData:
    result = _baseline_result(panel, bundle, future, fold.test_index, cost, config, cache)
    base = _daily(result.net_return, config.horizon)
    multiplier = _multiplier(intensity.reindex(fold.test_index), config.hypothesis, selected["threshold"], selected)
    throttle = base.mul(multiplier, fill_value=0.0)
    trades = trade_feature_rows(result.positions, future.reindex(fold.test_index), multiplier, features, config.horizon)
    return _EvalData(base, throttle, multiplier, _max_drawdown(base), _max_drawdown(throttle), trades)


def _select_params(panel, bundle, intensity, future, fold, cost, config, cache) -> dict[str, float]:
    best, best_score = None, -float("inf")
    for quantile in config.hypothesis.threshold_quantiles:
        threshold = _threshold(intensity.reindex(fold.train_index), quantile, config.hypothesis.side)
        for params in config.hypothesis.multiplier_grid:
            score = _train_score(panel, bundle, intensity, future, fold, cost, threshold, params, config, cache)
            if score > best_score:
                best, best_score = {"threshold": threshold, "quantile": quantile, **params}, score
    return best or {"threshold": 0.0, "quantile": 0.0, "down": 1.0, "up": 1.0}


def _train_score(panel, bundle, intensity, future, fold, cost, threshold, params, config, cache) -> float:
    result = _baseline_result(panel, bundle, future, fold.train_index, cost, config, cache)
    base = _daily(result.net_return, config.horizon)
    mult = _multiplier(intensity.reindex(fold.train_index), config.hypothesis, threshold, params)
    variant = base.mul(mult, fill_value=0.0)
    left = (variant - base).loc[base.le(base.quantile(0.25))].mean() * 100.0
    return float(_total_return_pct(variant) - _total_return_pct(base) + max(0.0, left))


def _threshold_rows(panel, bundle, intensity, future, fold, cost, selected, config, cache) -> list[dict[str, object]]:
    rows = []
    for quantile in perturbed_quantiles(float(selected["quantile"])):
        threshold = _threshold(intensity.reindex(fold.train_index), quantile, config.hypothesis.side)
        params = {**selected, "threshold": threshold, "quantile": quantile}
        base, throttle = _return_streams(panel, bundle, intensity, future, fold, cost, params, config, cache)
        rows.append(_sensitivity_row(fold, cost, quantile, threshold, selected, base, throttle))
    return rows


def _return_streams(panel, bundle, intensity, future, fold, cost, selected, config, cache) -> tuple[pd.Series, pd.Series]:
    result = _baseline_result(panel, bundle, future, fold.test_index, cost, config, cache)
    base = _daily(result.net_return, config.horizon)
    mult = _multiplier(intensity.reindex(fold.test_index), config.hypothesis, selected["threshold"], selected)
    return base, base.mul(mult, fill_value=0.0)


def _fold_row(fold: FoldSpec, cost: float, selected: dict[str, float], data: _EvalData, event_label: str) -> dict[str, object]:
    row = _base_fold_fields(fold, cost, selected, data, event_label)
    row.update(metric_row(data.baseline, "baseline"))
    row.update(metric_row(data.throttle, "throttle"))
    throttle_return = cast(float, row["throttle_return_pct"])
    baseline_return = cast(float, row["baseline_return_pct"])
    delta = throttle_return - baseline_return
    row["delta_vs_baseline_pct"] = delta
    row["helped_hurt_neutral"] = _fold_label(delta)
    return row


def _base_fold_fields(fold, cost, selected, data, event_label) -> dict[str, object]:
    return {
        "fold": fold.fold,
        "test_start": str(fold.test_index[0].date()),
        "test_end": str(fold.test_index[-1].date()),
        "cost_bps": float(cost),
        "selected_quantile": float(selected["quantile"]),
        "selected_threshold": float(selected["threshold"]),
        "multiplier_down": float(selected.get("down", 1.0)),
        "multiplier_up": float(selected.get("up", 1.0)),
        "average_exposure": float(data.multiplier.mean()),
        "baseline_max_drawdown": data.base_drawdown,
        "throttle_max_drawdown": data.throttle_drawdown,
        "net_blocker_value": float(data.trade_rows.get("blocker_value", pd.Series(dtype=float)).sum() * 100.0),
        "event_label": event_label,
    }


def _value_row(fold: FoldSpec, cost: float, trades: pd.DataFrame, event_label: str) -> dict[str, object]:
    return {"fold": fold.fold, "cost_bps": float(cost), "event_label": event_label, **blocker_value_row(trades)}


def _sensitivity_row(fold, cost, quantile, threshold, selected, base, throttle) -> dict[str, object]:
    return {
        "fold": fold.fold,
        "cost_bps": float(cost),
        "selected_quantile": float(selected["quantile"]),
        "perturbed_quantile": float(quantile),
        "threshold": float(threshold),
        "baseline_return_pct": _total_return_pct(base),
        "throttle_return_pct": _total_return_pct(throttle),
        "delta_vs_baseline_pct": _total_return_pct(throttle) - _total_return_pct(base),
    }


def _annotate(frame: pd.DataFrame, fold: FoldSpec, cost: float, selected: dict[str, float], event_label: str) -> pd.DataFrame:
    out = frame.copy()
    out.insert(0, "fold", fold.fold)
    out.insert(1, "cost_bps", float(cost))
    out["selected_quantile"] = float(selected["quantile"])
    out["selected_threshold"] = float(selected["threshold"])
    out["event_label"] = event_label
    return out


def _saved_lost_frame(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()
    rows = []
    for keys, frame in trades.groupby(["cost_bps", "event_label"], sort=False):
        summary = saved_loser_lost_winner_summary(frame)
        summary.insert(0, "event_label", str(keys[1]))
        summary.insert(0, "cost_bps", float(keys[0]))
        rows.append(summary)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def _cost_stress(folds: pd.DataFrame) -> pd.DataFrame:
    if folds.empty:
        return pd.DataFrame()
    rows = []
    for cost, frame in folds.groupby("cost_bps", sort=False):
        rows.append(_cost_row(float(cost), frame))
    return pd.DataFrame(rows)


def _cost_row(cost: float, frame: pd.DataFrame) -> dict[str, float | int | str]:
    base = frame["baseline_return_pct"]
    right = frame.loc[base.ge(base.quantile(0.75))]
    left = frame.loc[base.le(base.quantile(0.25)), "delta_vs_baseline_pct"]
    return {
        "cost_bps": cost,
        "fold_count": int(frame["fold"].nunique()),
        "mean_delta_pct": float(frame["delta_vs_baseline_pct"].mean()),
        "left_tail_delta_pct": float(left.mean()),
        "right_tail_retention": _ratio(right["throttle_return_pct"].mean(), right["baseline_return_pct"].mean()),
        "net_blocker_value": float(frame["net_blocker_value"].sum()),
        "helped_folds": int(frame["helped_hurt_neutral"].eq("helped").sum()),
        "hurt_folds": int(frame["helped_hurt_neutral"].eq("hurt").sum()),
    }


def _narrow_config(config: SurvivorDiagnosticConfig) -> NarrowFalsificationConfig:
    return NarrowFalsificationConfig(
        hypotheses=(config.hypothesis,),
        cache_dir=config.cache_dir,
        report_root=config.report_root,
        source_report_dir=config.source_report_dir,
        train_size_days=config.train_size_days,
        test_size_days=config.test_size_days,
        step_size_days=config.step_size_days,
        lookahead_days=config.lookahead_days,
        max_folds=config.max_folds,
    )


def _event_labels(source_dir: Path) -> dict[int, str]:
    path = source_dir / "weak_fold_event_attribution.csv"
    if not path.exists():
        return {}
    frame = pd.read_csv(path)
    return {int(fold): str(labels.value_counts().index[0]) for fold, labels in frame.groupby("fold")["event_label"]}


def _report_paths(report_dir: Path) -> dict[str, Path]:
    prefix = "support_trendline_survivor"
    return {
        "trade": report_dir / f"{prefix}_trade_diagnostics.csv",
        "blocker": report_dir / f"{prefix}_blocker_value.csv",
        "saved_lost": report_dir / f"{prefix}_saved_loser_vs_lost_winner.csv",
        "fold": report_dir / f"{prefix}_fold_anatomy.csv",
        "threshold": report_dir / f"{prefix}_threshold_sensitivity.csv",
        "cost": report_dir / f"{prefix}_cost_stress.csv",
        "markdown": report_dir / f"{prefix}_report.md",
    }


def _report_markdown(result: SurvivorDiagnosticResult) -> str:
    lines = ["# Support Trendline Survivor Diagnostic", ""]
    lines.extend(["## Cost Stress", "", markdown_table(result.cost_stress, max_rows=20), ""])
    lines.extend(["## Blocker Value", "", markdown_table(result.blocker_value, max_rows=40), ""])
    lines.extend(["## Fold Anatomy", "", markdown_table(result.fold_anatomy, max_rows=40), ""])
    lines.extend(["## Saved Loser vs Lost Winner", "", markdown_table(result.saved_loser_vs_lost_winner, max_rows=40), ""])
    lines.extend(["## Threshold Sensitivity", "", markdown_table(result.threshold_sensitivity, max_rows=40), ""])
    lines.extend(["## Decision", "", _decision_text(result.cost_stress), ""])
    return "\n".join(lines)


def _decision_text(costs: pd.DataFrame) -> str:
    if costs.empty:
        return "Reject: no diagnostic data produced."
    row = costs.loc[costs["cost_bps"].eq(25.0)]
    target = row.iloc[0] if not row.empty else costs.iloc[0]
    if float(target["right_tail_retention"]) < 0.95:
        return "Reject: right-tail retention fell below 95%."
    if float(target["net_blocker_value"]) <= 0.0:
        return "Reject: net blocker value is not positive OOS."
    return "Research lead only: blocker value is positive, but significance still requires separate validation."


def _fold_label(delta: float) -> str:
    if delta > 0.10:
        return "helped"
    if delta < -0.10:
        return "hurt"
    return "neutral"


def _max_drawdown(returns: pd.Series) -> float:
    equity = (1.0 + returns.fillna(0.0)).cumprod()
    return float((equity / equity.cummax() - 1.0).min() * 100.0) if not equity.empty else 0.0


def _ratio(numerator: float, denominator: float) -> float:
    return float(numerator / denominator) if denominator else 0.0


def _timestamped_report_dir(root: Path) -> Path:
    return root / datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
