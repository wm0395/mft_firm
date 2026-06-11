from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
from importlib import import_module
from pathlib import Path

import numpy as np
import pandas as pd

from research.notebooks.alpha_001.research.alpha101_engine import Alpha101Panel
from research.notebooks.alpha_001.research.alpha101_engine import forward_return
from research.projects.price_action_strategy_lab.activator_registry import ActivatorRegistry
from research.projects.price_action_strategy_lab.activator_suite import build_activator_masks
from research.projects.price_action_strategy_lab.alpha_registry import AlphaRegistry
from research.projects.price_action_strategy_lab.alpha_runner import load_signal_bundles
from research.projects.price_action_strategy_lab.compute_backend import GpuConfig
from research.projects.price_action_strategy_lab.narrow_falsification import NarrowFalsificationConfig
from research.projects.price_action_strategy_lab.narrow_falsification import NarrowHypothesis
from research.projects.price_action_strategy_lab.narrow_falsification import _baseline_result
from research.projects.price_action_strategy_lab.narrow_falsification import _daily
from research.projects.price_action_strategy_lab.narrow_falsification import _folds
from research.projects.price_action_strategy_lab.narrow_falsification import _multiplier
from research.projects.price_action_strategy_lab.narrow_falsification import _threshold
from research.projects.price_action_strategy_lab.soft_throttle_analysis import _annual_sharpe
from research.projects.price_action_strategy_lab.soft_throttle_analysis import _annual_vol_pct
from research.projects.price_action_strategy_lab.soft_throttle_analysis import _cagr_pct
from research.projects.price_action_strategy_lab.soft_throttle_analysis import _max_drawdown_pct
from research.projects.price_action_strategy_lab.soft_throttle_analysis import _total_return_pct
from research.projects.price_action_strategy_lab.soft_throttle_walk_forward_reports import markdown_table
from research.projects.price_action_strategy_lab.survivor_diagnostic import _event_labels
from research.projects.price_action_strategy_lab.survivor_diagnostic import _fold_label
from research.projects.price_action_strategy_lab.survivor_features import blocker_value_row
from research.projects.price_action_strategy_lab.survivor_features import build_survivor_features
from research.projects.price_action_strategy_lab.survivor_features import trade_feature_rows


@dataclass(frozen=True)
class StressVariant:
    variant_id: str
    indicators: tuple[str, ...]
    combine: str
    hypothesis: NarrowHypothesis


@dataclass(frozen=True)
class StressConfirmationConfig:
    variants: tuple[StressVariant, ...]
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
class StressConfirmationResult:
    report_dir: Path
    fold_metrics: pd.DataFrame
    aggregate_metrics: pd.DataFrame
    tail_diagnostics: pd.DataFrame
    trade_diagnostics: pd.DataFrame
    event_split: pd.DataFrame
    cost_stress: pd.DataFrame


def run_stress_confirmation(
    panel: Alpha101Panel,
    alpha_registry: AlphaRegistry,
    activator_registry: ActivatorRegistry,
    config: StressConfirmationConfig,
) -> StressConfirmationResult:
    bundle = load_signal_bundles(panel, alpha_registry, _alpha_names(config), config.cache_dir, config.gpu, config.max_workers)[0]
    masks = build_activator_masks(panel, activator_registry, config.max_workers)
    future = forward_return(panel.close, config.horizon)
    features = build_survivor_features(panel, bundle.signal, masks["volatility_expansion"].mean(axis=1))
    fold_rows, trade_rows, daily_rows = _run_jobs(panel, bundle, masks, future, features, config)
    fold_frame = pd.DataFrame(fold_rows)
    result = StressConfirmationResult(
        _report_dir(config.report_root),
        fold_frame,
        _aggregate(pd.DataFrame(daily_rows), fold_frame),
        _tail(fold_frame),
        pd.DataFrame(trade_rows),
        _event_split(fold_frame),
        _cost_stress(fold_frame),
    )
    write_stress_confirmation_reports(result)
    return result


def write_stress_confirmation_reports(result: StressConfirmationResult) -> dict[str, Path]:
    result.report_dir.mkdir(parents=True, exist_ok=True)
    paths = _paths(result.report_dir)
    result.fold_metrics.to_csv(paths["fold"], index=False)
    result.aggregate_metrics.to_csv(paths["aggregate"], index=False)
    result.tail_diagnostics.to_csv(paths["tail"], index=False)
    result.trade_diagnostics.to_csv(paths["trade"], index=False)
    result.event_split.to_csv(paths["event"], index=False)
    result.cost_stress.to_csv(paths["cost"], index=False)
    paths["markdown"].write_text(_markdown(result), encoding="utf-8")
    return paths


def stress_variant_ids(config: StressConfirmationConfig) -> tuple[str, ...]:
    return tuple(variant.variant_id for variant in config.variants)


def _alpha_names(config: StressConfirmationConfig) -> tuple[str, ...]:
    names = tuple({alpha for variant in config.variants for alpha in variant.hypothesis.alphas})
    if len(names) != 1:
        raise ValueError("stress confirmation expects exactly one alpha per run")
    return names


def and_intensity(left: pd.DataFrame, right: pd.DataFrame) -> pd.Series:
    return (left.fillna(False) & right.fillna(False)).mean(axis=1)


def _run_jobs(panel, bundle, masks, future, features, config):
    fold_rows: list[dict[str, object]] = []
    trade_rows: list[dict[str, object]] = []
    daily_rows: list[dict[str, object]] = []
    events = _event_labels(config.source_report_dir)
    cache: dict[tuple[str, float, str, str, int], object] = {}
    for cost in config.cost_bps:
        for fold in _folds(panel.close.index, _narrow_config(config)):
            result = _baseline_result(panel, bundle, future, fold.test_index, cost, config, cache)
            base = _daily(result.net_return, config.horizon)
            for variant in config.variants:
                selected = _select(panel, bundle, masks, future, fold, cost, variant, config, cache)
                multiplier = _variant_multiplier(masks, fold.test_index, variant, selected)
                returns = base if variant.variant_id == "baseline" else base.mul(multiplier, fill_value=0.0)
                fold_rows.append(_fold_row(fold, cost, variant, selected, base, returns, multiplier, events))
                trade_rows.append(_trade_row(result.positions, future, multiplier, features, fold, cost, variant, config, events))
                daily_rows.extend(_daily_rows(fold, cost, variant.variant_id, base, returns, result.turnover, multiplier))
    return fold_rows, trade_rows, daily_rows


def _select(panel, bundle, masks, future, fold, cost, variant, config, cache) -> dict[str, float]:
    if variant.variant_id == "baseline":
        return {"threshold": 0.0, "quantile": 0.0, "down": 1.0, "up": 1.0}
    intensity = _intensity(masks, variant).reindex(fold.train_index)
    best, score = None, -float("inf")
    for quantile in variant.hypothesis.threshold_quantiles:
        threshold = _threshold(intensity, quantile, "high")
        for params in variant.hypothesis.multiplier_grid:
            row_score = _score(panel, bundle, masks, future, fold, cost, variant, threshold, params, config, cache)
            if row_score > score:
                best, score = {"threshold": threshold, "quantile": quantile, **params}, row_score
    return best or {"threshold": 0.0, "quantile": 0.0, "down": 1.0, "up": 1.0}


def _score(panel, bundle, masks, future, fold, cost, variant, threshold, params, config, cache) -> float:
    result = _baseline_result(panel, bundle, future, fold.train_index, cost, config, cache)
    base = _daily(result.net_return, config.horizon)
    mult = _variant_multiplier(masks, fold.train_index, variant, {"threshold": threshold, **params})
    returns = base.mul(mult, fill_value=0.0)
    left = (returns - base).loc[base.le(base.quantile(0.25))].mean() * 100.0
    return float(_total_return_pct(returns) - _total_return_pct(base) + max(0.0, left))


def _variant_multiplier(masks, index, variant, selected) -> pd.Series:
    if variant.variant_id == "baseline":
        return pd.Series(1.0, index=index)
    intensity = _intensity(masks, variant).reindex(index)
    return _multiplier(intensity, variant.hypothesis, selected["threshold"], selected)


def _intensity(masks: dict[str, pd.DataFrame], variant: StressVariant) -> pd.Series:
    if variant.combine == "and":
        return and_intensity(masks[variant.indicators[0]], masks[variant.indicators[1]])
    return masks[variant.indicators[0]].mean(axis=1)


def _fold_row(fold, cost, variant, selected, base, returns, multiplier, events) -> dict[str, object]:
    return {
        "fold": fold.fold,
        "variant": variant.variant_id,
        "cost_bps": float(cost),
        "test_start": str(fold.test_index[0].date()),
        "test_end": str(fold.test_index[-1].date()),
        "event_label": events.get(fold.fold, "unmatched"),
        "baseline_return_pct": _total_return_pct(base),
        "variant_return_pct": _total_return_pct(returns),
        "delta_return_pct": _total_return_pct(returns) - _total_return_pct(base),
        "variant_ann_sharpe": _annual_sharpe(returns),
        "variant_max_drawdown_pct": _max_drawdown_pct(returns),
        "avg_exposure": float(multiplier.mean()),
        "selected_quantile": float(selected["quantile"]),
        "selected_threshold": float(selected["threshold"]),
        "helped_hurt_neutral": _fold_label(_total_return_pct(returns) - _total_return_pct(base)),
    }


def _trade_row(positions, future, multiplier, features, fold, cost, variant, config, events) -> dict[str, object]:
    trades = trade_feature_rows(positions, future.reindex(fold.test_index), multiplier, features, config.horizon)
    return {"fold": fold.fold, "variant": variant.variant_id, "cost_bps": float(cost), "event_label": events.get(fold.fold, "unmatched"), **blocker_value_row(trades)}


def _daily_rows(fold, cost, variant_id, base, returns, turnover, multiplier) -> list[dict[str, object]]:
    scaled_turnover = turnover.reindex(base.index).fillna(0.0).mul(multiplier.reindex(base.index).fillna(1.0))
    return [
        {
            "date": date,
            "fold": fold.fold,
            "cost_bps": float(cost),
            "variant": variant_id,
            "baseline": base.loc[date],
            "returns": value,
            "turnover": scaled_turnover.loc[date],
        }
        for date, value in returns.items()
    ]


def _aggregate(daily: pd.DataFrame, folds: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for keys, frame in daily.groupby(["variant", "cost_bps"], sort=False):
        variant, cost = str(keys[0]), float(keys[1])
        ordered = frame.sort_values("date")
        returns = ordered["returns"]
        fold_frame = folds.loc[folds["variant"].eq(variant) & folds["cost_bps"].eq(cost)]
        rows.append(_aggregate_row(variant, cost, returns, ordered["turnover"], fold_frame))
    return pd.DataFrame(rows)


def _aggregate_row(variant: str, cost: float, returns: pd.Series, turnover: pd.Series, folds: pd.DataFrame) -> dict[str, object]:
    return {
        "variant": variant,
        "cost_bps": cost,
        "return_pct": _total_return_pct(returns),
        "cagr_pct": _cagr_pct(returns),
        "ann_vol_pct": _annual_vol_pct(returns),
        "ann_sharpe": _annual_sharpe(returns),
        "max_drawdown_pct": _max_drawdown_pct(returns),
        "negative_fold_rate": float(folds["variant_return_pct"].lt(0.0).mean()),
        "worst_fold_sharpe": float(folds["variant_ann_sharpe"].min()),
        "latest_fold_sharpe": float(folds.sort_values("fold").iloc[-1]["variant_ann_sharpe"]),
        "average_exposure": float(folds["avg_exposure"].mean()),
        "turnover": float(turnover.mean()) if not turnover.empty else 0.0,
    }


def _tail(folds: pd.DataFrame) -> pd.DataFrame:
    rows = [_tail_row(str(k[0]), float(k[1]), f) for k, f in folds.groupby(["variant", "cost_bps"], sort=False)]
    frame = pd.DataFrame(rows)
    frame["bh_p_value"] = _bh(frame["paired_p_value"])
    return frame


def _tail_row(variant: str, cost: float, frame: pd.DataFrame) -> dict[str, object]:
    base, delta = frame["baseline_return_pct"], frame["delta_return_pct"]
    right = frame.loc[base.ge(base.quantile(0.75))]
    top = frame.loc[base.ge(base.quantile(0.90))]
    bottom = frame.loc[base.le(base.quantile(0.10)), "delta_return_pct"]
    ci_low, ci_high = _bootstrap(delta)
    t_stat, p_value = _paired_t(delta)
    return {
        "variant": variant,
        "cost_bps": cost,
        "mean_delta_vs_baseline": float(delta.mean()),
        "left_tail_delta": float(delta.loc[base.le(base.quantile(0.25))].mean()),
        "right_tail_retention": _ratio(right["variant_return_pct"].mean(), right["baseline_return_pct"].mean()),
        "top_decile_retention": _ratio(top["variant_return_pct"].mean(), top["baseline_return_pct"].mean()),
        "bottom_decile_improvement": float(bottom.mean()),
        "best_fold_damage": float(delta.loc[base.idxmax()]),
        "worst_fold_improvement": float(delta.loc[base.idxmin()]),
        "ci_low": ci_low,
        "ci_high": ci_high,
        "paired_t_stat": t_stat,
        "paired_p_value": p_value,
    }


def _event_split(folds: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for keys, frame in folds.groupby(["variant", "cost_bps"], sort=False):
        rows.extend(_event_rows(str(keys[0]), float(keys[1]), frame))
    return pd.DataFrame(rows)


def _event_rows(variant: str, cost: float, frame: pd.DataFrame) -> list[dict[str, object]]:
    stress = frame.loc[~frame["event_label"].eq("unmatched")]
    ordinary = frame.loc[frame["event_label"].eq("unmatched")]
    return [_event_row(variant, cost, "known_stress", stress), _event_row(variant, cost, "unmatched", ordinary), _event_row(variant, cost, "all", frame)]


def _event_row(variant: str, cost: float, label: str, frame: pd.DataFrame) -> dict[str, object]:
    return {
        "variant": variant,
        "cost_bps": cost,
        "split": label,
        "fold_count": int(frame["fold"].nunique()),
        "mean_delta": float(frame["delta_return_pct"].mean()) if not frame.empty else 0.0,
        "net_delta": float(frame["delta_return_pct"].sum()) if not frame.empty else 0.0,
        "average_exposure": float(frame["avg_exposure"].mean()) if not frame.empty else 0.0,
    }


def _cost_stress(folds: pd.DataFrame) -> pd.DataFrame:
    return _tail(folds)[["variant", "cost_bps", "mean_delta_vs_baseline", "left_tail_delta", "right_tail_retention", "ci_low"]]


def _narrow_config(config: StressConfirmationConfig) -> NarrowFalsificationConfig:
    return NarrowFalsificationConfig(
        hypotheses=tuple(variant.hypothesis for variant in config.variants),
        cache_dir=config.cache_dir,
        report_root=config.report_root,
        source_report_dir=config.source_report_dir,
        train_size_days=config.train_size_days,
        test_size_days=config.test_size_days,
        step_size_days=config.step_size_days,
        lookahead_days=config.lookahead_days,
        max_folds=config.max_folds,
    )


def _paths(report_dir: Path) -> dict[str, Path]:
    prefix = "support_trendline_stress_confirmation"
    return {
        "fold": report_dir / f"{prefix}_fold_metrics.csv",
        "aggregate": report_dir / f"{prefix}_aggregate_metrics.csv",
        "tail": report_dir / f"{prefix}_tail_diagnostics.csv",
        "trade": report_dir / f"{prefix}_trade_diagnostics.csv",
        "event": report_dir / f"{prefix}_event_split.csv",
        "cost": report_dir / f"{prefix}_cost_stress.csv",
        "markdown": report_dir / f"{prefix}_report.md",
    }


def _markdown(result: StressConfirmationResult) -> str:
    lines = ["# Support Trendline Stress Confirmation", ""]
    lines.extend(["## Aggregate", "", markdown_table(result.aggregate_metrics, max_rows=40), ""])
    lines.extend(["## Tail", "", markdown_table(result.tail_diagnostics, max_rows=40), ""])
    lines.extend(["## Event Split", "", markdown_table(result.event_split, max_rows=60), ""])
    lines.extend(["## Trade Diagnostics", "", markdown_table(result.trade_diagnostics, max_rows=60), ""])
    lines.extend(["## Decision", "", _decision(result.tail_diagnostics, result.event_split), ""])
    return "\n".join(lines)


def _decision(tail: pd.DataFrame, events: pd.DataFrame) -> str:
    row = tail.loc[tail["variant"].eq("vol_and_breadth") & tail["cost_bps"].eq(25.0)]
    ordinary = events.loc[events["variant"].eq("vol_and_breadth") & events["cost_bps"].eq(25.0) & events["split"].eq("unmatched")]
    if row.empty or ordinary.empty:
        return "Reject: missing target diagnostic rows."
    if float(row.iloc[0]["right_tail_retention"]) < 0.95:
        return "Reject: AND condition fails right-tail retention."
    if float(ordinary.iloc[0]["mean_delta"]) < -0.10:
        return "Reject: unmatched-fold damage remains material."
    return "Research-only lead: AND condition passes first stress-overlay screen."


def _bootstrap(values: pd.Series) -> tuple[float, float]:
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


def _bh(values: pd.Series) -> pd.Series:
    pvals = values.fillna(1.0).to_numpy(dtype=float)
    order, adjusted, running = np.argsort(pvals), np.empty_like(pvals), 1.0
    for rank, idx in enumerate(order[::-1], start=1):
        running = min(running, pvals[idx] * len(pvals) / (len(pvals) - rank + 1))
        adjusted[idx] = running
    return pd.Series(adjusted, index=values.index)


def _ratio(numerator: float, denominator: float) -> float:
    return float(numerator / denominator) if denominator else 0.0


def _report_dir(root: Path) -> Path:
    return root / datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
