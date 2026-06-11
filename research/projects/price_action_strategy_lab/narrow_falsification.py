from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from project.alpha_math.validation import purged_time_split
from research.notebooks.alpha_001.research.alpha101_engine import Alpha101Panel
from research.notebooks.alpha_001.research.alpha101_engine import forward_return
from research.projects.price_action_strategy_lab.activator_registry import ActivatorRegistry
from research.projects.price_action_strategy_lab.activator_suite import build_activator_masks
from research.projects.price_action_strategy_lab.alpha_registry import AlphaRegistry
from research.projects.price_action_strategy_lab.alpha_runner import SignalBundle
from research.projects.price_action_strategy_lab.alpha_runner import load_signal_bundles
from research.projects.price_action_strategy_lab.backtest_modes import BacktestConfig
from research.projects.price_action_strategy_lab.backtest_modes import run_backtest
from research.projects.price_action_strategy_lab.compute_backend import GpuConfig
from research.projects.price_action_strategy_lab.costs import turnover_cost
from research.projects.price_action_strategy_lab.narrow_falsification_stats import aggregate_metrics
from research.projects.price_action_strategy_lab.narrow_falsification_stats import event_cluster_metrics
from research.projects.price_action_strategy_lab.narrow_falsification_stats import gate_stability
from research.projects.price_action_strategy_lab.narrow_falsification_stats import metric_row
from research.projects.price_action_strategy_lab.narrow_falsification_stats import tail_diagnostics
from research.projects.price_action_strategy_lab.narrow_falsification_stats import trade_diagnostics
from research.projects.price_action_strategy_lab.soft_throttle_analysis import _total_return_pct
from research.projects.price_action_strategy_lab.soft_throttle_walk_forward_reports import markdown_table


@dataclass(frozen=True)
class NarrowHypothesis:
    hypothesis_id: str
    alphas: tuple[str, ...]
    indicator: str
    side: str
    throttle_variant: str
    threshold_quantiles: tuple[float, ...]
    multiplier_grid: tuple[dict[str, float], ...]


@dataclass(frozen=True)
class NarrowFalsificationConfig:
    hypotheses: tuple[NarrowHypothesis, ...]
    cache_dir: Path
    report_root: Path
    source_report_dir: Path
    mode: str = "ranked_long_only"
    horizon: int = 10
    cost_bps: tuple[float, ...] = (10.0, 25.0, 50.0)
    train_size_days: int = 126
    test_size_days: int = 21
    step_size_days: int = 21
    lookahead_days: int = 10
    max_folds: int = 24
    fold_selection: str = "latest"
    top_quantile: float = 0.8
    min_names: int = 20
    max_workers: int = 1
    gpu: GpuConfig = GpuConfig()


@dataclass(frozen=True)
class NarrowFalsificationResult:
    report_dir: Path
    fold_metrics: pd.DataFrame
    aggregate_metrics: pd.DataFrame
    tail_diagnostics: pd.DataFrame
    trade_diagnostics: pd.DataFrame
    gate_stability: pd.DataFrame
    event_clusters: pd.DataFrame


@dataclass(frozen=True)
class FoldSpec:
    fold: int
    train_index: pd.Index
    test_index: pd.Index


def run_narrow_falsification(
    panel: Alpha101Panel,
    alpha_registry: AlphaRegistry,
    activator_registry: ActivatorRegistry,
    config: NarrowFalsificationConfig,
) -> NarrowFalsificationResult:
    bundles = _bundle_map(panel, alpha_registry, config)
    intensities = _indicator_intensities(panel, activator_registry, config)
    future = forward_return(panel.close, config.horizon)
    folds = _folds(panel.close.index, config)
    fold_rows, trade_rows = _run_folds(panel, bundles, intensities, future, folds, config)
    fold_frame = pd.DataFrame(fold_rows)
    trade_frame = pd.DataFrame(trade_rows)
    result = NarrowFalsificationResult(
        _timestamped_report_dir(config.report_root),
        fold_frame,
        aggregate_metrics(fold_frame),
        tail_diagnostics(fold_frame),
        trade_frame,
        gate_stability(fold_frame),
        event_cluster_metrics(fold_frame, _event_labels(config.source_report_dir)),
    )
    write_narrow_falsification_reports(result)
    return result


def write_narrow_falsification_reports(result: NarrowFalsificationResult) -> dict[str, Path]:
    result.report_dir.mkdir(parents=True, exist_ok=True)
    paths = _report_paths(result.report_dir)
    result.fold_metrics.to_csv(paths["fold"], index=False)
    result.aggregate_metrics.to_csv(paths["aggregate"], index=False)
    result.tail_diagnostics.to_csv(paths["tail"], index=False)
    result.trade_diagnostics.to_csv(paths["trade"], index=False)
    result.gate_stability.to_csv(paths["stability"], index=False)
    result.event_clusters.to_csv(paths["events"], index=False)
    paths["markdown"].write_text(_report_markdown(result), encoding="utf-8")
    return paths


def _run_folds(panel, bundles, intensities, future, folds, config):
    fold_rows: list[dict[str, object]] = []
    trade_rows: list[dict[str, object]] = []
    baseline_cache: dict[tuple[str, float, str, str, int], object] = {}
    for cost_bps in config.cost_bps:
        for fold in folds:
            for hypothesis in config.hypotheses:
                fold_row, trade_row = _evaluate_hypothesis(
                    panel, bundles, intensities, future, fold, hypothesis, cost_bps, config, baseline_cache
                )
                fold_rows.append(fold_row)
                trade_rows.append(trade_row)
    return fold_rows, trade_rows


def _evaluate_hypothesis(panel, bundles, intensities, future, fold, hypothesis, cost_bps, config, baseline_cache):
    selected = _select_params(panel, bundles, intensities, future, fold, hypothesis, cost_bps, config, baseline_cache)
    base_returns, variant_returns, trade_values, multiplier = _test_streams(
        panel, bundles, intensities, future, fold, hypothesis, cost_bps, config, selected, baseline_cache
    )
    fold_row = _fold_row(fold, hypothesis, cost_bps, selected, base_returns, variant_returns, multiplier)
    trade_row = {"hypothesis_id": hypothesis.hypothesis_id, "fold": fold.fold, "cost_bps": cost_bps, **trade_values}
    return fold_row, trade_row


def _select_params(panel, bundles, intensities, future, fold, hypothesis, cost_bps, config, baseline_cache) -> dict[str, float]:
    best: dict[str, float] | None = None
    best_score = -float("inf")
    for quantile in hypothesis.threshold_quantiles:
        threshold = _threshold(intensities[hypothesis.indicator].reindex(fold.train_index), quantile, hypothesis.side)
        for params in hypothesis.multiplier_grid:
            score = _train_score(panel, bundles, intensities, future, fold, hypothesis, cost_bps, config, threshold, params, baseline_cache)
            if score > best_score:
                best_score = score
                best = {"threshold": threshold, "quantile": quantile, **params}
    return best or {"threshold": 0.0, "quantile": 0.0, "down": 1.0, "up": 1.0}


def _train_score(panel, bundles, intensities, future, fold, hypothesis, cost_bps, config, threshold, params, baseline_cache) -> float:
    base, variant, _, _ = _streams_for_index(
        panel,
        bundles,
        intensities,
        future,
        fold.train_index,
        hypothesis,
        cost_bps,
        config,
        threshold,
        params,
        baseline_cache,
        False,
    )
    delta = _total_return_pct(variant) - _total_return_pct(base)
    left = (variant - base).loc[base.le(base.quantile(0.25))].mean() * 100.0
    return float(delta + max(0.0, left))


def _test_streams(panel, bundles, intensities, future, fold, hypothesis, cost_bps, config, selected, baseline_cache):
    return _streams_for_index(
        panel,
        bundles,
        intensities,
        future,
        fold.test_index,
        hypothesis,
        cost_bps,
        config,
        selected["threshold"],
        selected,
        baseline_cache,
        True,
    )


def _streams_for_index(panel, bundles, intensities, future, index, hypothesis, cost_bps, config, threshold, params, baseline_cache, include_trade):
    base_series: list[pd.Series] = []
    variant_series: list[pd.Series] = []
    trade_rows: list[dict[str, float | int]] = []
    multiplier = _multiplier(intensities[hypothesis.indicator].reindex(index), hypothesis, threshold, params)
    for alpha in hypothesis.alphas:
        result = _baseline_result(panel, bundles[alpha], future, index, cost_bps, config, baseline_cache)
        base = _daily(result.net_return, config.horizon)
        base_series.append(base.rename(alpha))
        variant_series.append(base.mul(multiplier, fill_value=0.0).rename(alpha))
        if include_trade:
            trade_rows.append(trade_diagnostics(result.positions, future.reindex(index), multiplier, config.horizon))
    return _combine(base_series), _combine(variant_series), _sum_trade_rows(trade_rows), multiplier


def _baseline_result(panel, bundle: SignalBundle, future, index, cost_bps, config, baseline_cache):
    key = _baseline_key(bundle.alpha, cost_bps, index)
    if key in baseline_cache:
        return baseline_cache[key]
    bt_config = BacktestConfig(
        name=f"{bundle.alpha}:{cost_bps:g}",
        mode=config.mode,
        horizon=config.horizon,
        cost_model=turnover_cost(float(cost_bps)),
        top_quantile=config.top_quantile,
        min_names=config.min_names,
    )
    active = panel.active_mask.reindex(index).fillna(False).astype(bool)
    result = run_backtest(bundle.signal.reindex(index), future.reindex(index), bt_config, active, bundle.rank_pct.reindex(index))
    baseline_cache[key] = result
    return result


def _baseline_key(alpha: str, cost_bps: float, index: pd.Index) -> tuple[str, float, str, str, int]:
    return (alpha, float(cost_bps), str(index[0]), str(index[-1]), int(len(index)))


def _fold_row(fold, hypothesis, cost_bps, selected, baseline, variant, multiplier) -> dict[str, object]:
    row = {
        "hypothesis_id": hypothesis.hypothesis_id,
        "fold": fold.fold,
        "cost_bps": float(cost_bps),
        "train_start": str(fold.train_index[0].date()),
        "train_end": str(fold.train_index[-1].date()),
        "test_start": str(fold.test_index[0].date()),
        "test_end": str(fold.test_index[-1].date()),
        "indicator": hypothesis.indicator,
        "side": hypothesis.side,
        "throttle_variant": hypothesis.throttle_variant,
        "selected_threshold": float(selected["threshold"]),
        "selected_quantile": float(selected["quantile"]),
        "multiplier_down": float(selected.get("down", 1.0)),
        "multiplier_up": float(selected.get("up", 1.0)),
        "activation_rate": float(multiplier.ne(1.0).mean()),
        "avg_exposure_multiplier": float(multiplier.mean()),
    }
    row.update(metric_row(baseline, "baseline"))
    row.update(metric_row(variant, "variant"))
    row["delta_return_pct"] = float(row["variant_return_pct"] - row["baseline_return_pct"])
    row["max_drawdown_delta_pct"] = float(row["variant_max_drawdown_pct"] - row["baseline_max_drawdown_pct"])
    return row


def _multiplier(intensity: pd.Series, hypothesis: NarrowHypothesis, threshold: float, params: dict[str, float]) -> pd.Series:
    good = _good(intensity, hypothesis.side, threshold)
    adverse = ~good
    if hypothesis.throttle_variant == "drawdown_only_throttle":
        return pd.Series(np.where(adverse, params.get("down", 0.5), 1.0), index=intensity.index)
    return pd.Series(np.select([good, adverse], [params.get("up", 1.25), params.get("down", 0.25)], 1.0), index=intensity.index)


def _good(intensity: pd.Series, side: str, threshold: float) -> pd.Series:
    return intensity.ge(threshold) if side == "high" else intensity.le(threshold)


def _threshold(intensity: pd.Series, quantile: float, side: str) -> float:
    target = quantile if side == "high" else 1.0 - quantile
    return float(intensity.dropna().quantile(target)) if not intensity.dropna().empty else 0.0


def _folds(index: pd.Index, config: NarrowFalsificationConfig) -> tuple[FoldSpec, ...]:
    all_folds = tuple(
        FoldSpec(i, train, test)
        for i, (train, test) in enumerate(
            purged_time_split(index, config.train_size_days, config.test_size_days, config.lookahead_days, config.step_size_days)
        )
    )
    if config.max_folds <= 0:
        return all_folds
    return all_folds[-config.max_folds :] if config.fold_selection == "latest" else all_folds[: config.max_folds]


def _bundle_map(panel, alpha_registry, config) -> dict[str, SignalBundle]:
    alpha_names = tuple(sorted({alpha for hyp in config.hypotheses for alpha in hyp.alphas}))
    bundles = load_signal_bundles(panel, alpha_registry, alpha_names, config.cache_dir, config.gpu, config.max_workers)
    return {bundle.alpha: bundle for bundle in bundles}


def _indicator_intensities(panel, activator_registry, config) -> dict[str, pd.Series]:
    masks = build_activator_masks(panel, activator_registry, config.max_workers)
    indicators = {hyp.indicator for hyp in config.hypotheses}
    return {name: masks[name].mean(axis=1).fillna(0.0) for name in indicators}


def _event_labels(source_report_dir: Path) -> pd.DataFrame:
    path = source_report_dir / "weak_fold_event_attribution.csv"
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def _report_paths(report_dir: Path) -> dict[str, Path]:
    return {
        "fold": report_dir / "narrow_falsification_fold_metrics.csv",
        "aggregate": report_dir / "narrow_falsification_aggregate_metrics.csv",
        "tail": report_dir / "narrow_falsification_tail_diagnostics.csv",
        "trade": report_dir / "narrow_falsification_trade_diagnostics.csv",
        "stability": report_dir / "narrow_falsification_gate_stability.csv",
        "events": report_dir / "narrow_falsification_event_cluster_report.csv",
        "markdown": report_dir / "narrow_falsification_report.md",
    }


def _report_markdown(result: NarrowFalsificationResult) -> str:
    lines = ["# Narrow Falsification Report", ""]
    lines.extend(["## Tail Diagnostics", "", markdown_table(result.tail_diagnostics, max_rows=30), ""])
    lines.extend(["## Aggregate Metrics", "", markdown_table(result.aggregate_metrics, max_rows=30), ""])
    lines.extend(["## Gate Stability", "", markdown_table(result.gate_stability, max_rows=30), ""])
    lines.append("White Reality Check / Hansen SPA are not implemented in this sprint.")
    return "\n".join(lines)


def _timestamped_report_dir(root: Path) -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return root / stamp


def _daily(series: pd.Series, horizon: int) -> pd.Series:
    return series.fillna(0.0).div(float(horizon))


def _combine(series: list[pd.Series]) -> pd.Series:
    return pd.concat(series, axis=1).mean(axis=1).fillna(0.0) if series else pd.Series(dtype=float)


def _sum_trade_rows(rows: list[dict[str, float | int]]) -> dict[str, float | int]:
    keys = {key for row in rows for key in row}
    return {key: sum(row.get(key, 0) for row in rows) for key in keys}
