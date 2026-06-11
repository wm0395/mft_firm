from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from research.notebooks.alpha_001.research.alpha101_engine import Alpha101Panel, forward_return
from research.projects.price_action_strategy_lab.activator_specs import default_activator_registry
from research.projects.price_action_strategy_lab.activator_suite import build_activator_masks
from research.projects.price_action_strategy_lab.alpha_specs import default_alpha_registry
from research.projects.price_action_strategy_lab.alpha_runner import load_signal_bundles
from research.projects.price_action_strategy_lab.backtest_modes import BacktestConfig, run_backtest
from research.projects.price_action_strategy_lab.breadth_only_diagnostic import fold_concentration_row
from research.projects.price_action_strategy_lab.compute_backend import GpuConfig
from research.projects.price_action_strategy_lab.costs import turnover_cost
from research.projects.price_action_strategy_lab.narrow_falsification import NarrowFalsificationConfig, NarrowHypothesis
from research.projects.price_action_strategy_lab.narrow_falsification import _daily, _folds, _multiplier, _threshold
from research.projects.price_action_strategy_lab.run_activator_suite import _load_panel, _read_config
from research.projects.price_action_strategy_lab.soft_throttle_analysis import _annual_sharpe, _annual_vol_pct, _cagr_pct
from research.projects.price_action_strategy_lab.soft_throttle_analysis import _max_drawdown_pct, _total_return_pct
from research.projects.price_action_strategy_lab.soft_throttle_walk_forward_reports import markdown_table
from research.projects.price_action_strategy_lab.stress_confirmation import _bh, _bootstrap, _event_labels, _paired_t, _ratio
from research.projects.price_action_strategy_lab.survivor_features import blocker_value_row, trade_feature_rows, build_survivor_features
from research.projects.price_action_strategy_lab.universe_adapter import to_alpha101_panel


@dataclass(frozen=True)
class PortfolioIntegrationConfig:
    alphas: tuple[str, ...]
    structure: tuple[str, ...]
    core: tuple[str, ...]
    reversal: tuple[str, ...]
    cache_dir: Path
    report_root: Path
    source_report_dir: Path
    cost_bps: tuple[float, ...]
    horizon: int = 10
    train_size_days: int = 126
    test_size_days: int = 21
    step_size_days: int = 21
    lookahead_days: int = 10
    max_folds: int = 24
    max_workers: int = 1
    gpu: GpuConfig = GpuConfig()


@dataclass(frozen=True)
class PortfolioIntegrationResult:
    report_dir: Path
    metrics: pd.DataFrame
    tail: pd.DataFrame
    attribution: pd.DataFrame
    trade: pd.DataFrame
    event: pd.DataFrame
    concentration: pd.DataFrame
    cost: pd.DataFrame


def run_portfolio_integration_config(config_path: str | Path) -> PortfolioIntegrationResult:
    raw = _read_config(Path(config_path))
    panel = to_alpha101_panel(_load_panel(raw))
    result = run_portfolio_integration(panel, _config(raw))
    return result


def run_portfolio_integration(panel: Alpha101Panel, config: PortfolioIntegrationConfig) -> PortfolioIntegrationResult:
    bundles = {b.alpha: b for b in load_signal_bundles(panel, default_alpha_registry(), config.alphas, config.cache_dir, config.gpu, config.max_workers)}
    mask = build_activator_masks(panel, default_activator_registry(), config.max_workers)["breadth_risk_off"]
    future = forward_return(panel.close, config.horizon)
    rows, trades = _run_folds(panel, bundles, mask.mean(axis=1), future, config)
    fold = pd.DataFrame(rows)
    result = PortfolioIntegrationResult(_report_dir(config.report_root), _metrics(fold), _tail(fold), _attribution(fold), pd.DataFrame(trades), _events(fold, config.source_report_dir), _concentration(fold), _cost(_tail(fold)))
    return result


def write_portfolio_integration(result: PortfolioIntegrationResult) -> dict[str, Path]:
    result.report_dir.mkdir(parents=True, exist_ok=True)
    paths = _paths(result.report_dir)
    result.metrics.to_csv(paths["metrics"], index=False)
    result.tail.to_csv(paths["tail"], index=False)
    result.attribution.to_csv(paths["attribution"], index=False)
    result.trade.to_csv(paths["trade"], index=False)
    result.event.to_csv(paths["event"], index=False)
    result.concentration.to_csv(paths["concentration"], index=False)
    result.cost.to_csv(paths["cost"], index=False)
    paths["markdown"].write_text(_markdown(result), encoding="utf-8")
    return paths


def _run_folds(panel, bundles, intensity, future, config):
    rows: list[dict[str, object]] = []
    trade_rows: list[dict[str, object]] = []
    hyp = NarrowHypothesis("breadth", ("alpha",), "breadth_risk_off", "high", "soft_aggressive", (0.5, 0.6, 0.7, 0.8), _grid())
    folds = _folds(panel.close.index, _narrow(config, hyp))
    for cost in config.cost_bps:
        for fold in folds:
            streams, turnovers, trade = _alpha_streams(panel, bundles, intensity, future, fold, cost, config, hyp)
            rows.extend(_portfolio_rows(fold, cost, streams, turnovers, config))
            trade_rows.extend(trade)
    return rows, trade_rows


def _alpha_streams(panel, bundles, intensity, future, fold, cost, config, hyp):
    streams, turnovers, trade_rows = {}, {}, []
    for alpha, bundle in bundles.items():
        base_result = _backtest(panel, bundle, future, fold.test_index, cost, config)
        base = _daily(base_result.net_return, config.horizon)
        streams[(alpha, "baseline")] = base
        turnovers[(alpha, "baseline")] = base_result.turnover.reindex(base.index).fillna(0.0)
        if alpha in set(config.structure) | set(config.reversal):
            selected = _select(panel, bundle, intensity, future, fold, cost, config, hyp)
            mult = _multiplier(intensity.reindex(fold.test_index), hyp, selected["threshold"], selected)
            streams[(alpha, "overlay")] = base.mul(mult, fill_value=0.0)
            turnovers[(alpha, "overlay")] = base_result.turnover.reindex(base.index).fillna(0.0).mul(mult, fill_value=0.0)
            trade_rows.append(_trade_row(panel, bundle, future, fold, cost, config, alpha, mult, base_result.positions, intensity))
    return streams, turnovers, trade_rows


def _portfolio_rows(fold, cost, streams, turnovers, config) -> list[dict[str, object]]:
    specs = _portfolio_specs(config)
    base_full = _combine([streams[(a, "baseline")] for a in config.alphas])
    rows = []
    for variant, alphas, overlay in specs:
        series = [_stream_for(streams, alpha, overlay) for alpha in alphas]
        turn = [_stream_for(turnovers, alpha, overlay) for alpha in alphas]
        returns = _combine(series)
        baseline = base_full if variant.startswith("full_") else _combine([streams[(a, "baseline")] for a in alphas])
        rows.append(_fold_row(fold, cost, variant, returns, baseline, _combine(turn)))
    return rows


def _portfolio_specs(config) -> tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...]:
    return (
        ("full_baseline", config.alphas, ()),
        ("full_stack_structure_overlay", config.alphas, config.structure),
        ("full_stack_core_structure_overlay", config.alphas, config.core),
        ("structure_family_only_baseline", config.structure, ()),
        ("structure_family_only_overlay", config.structure, config.structure),
        ("reversal_family_only_baseline", config.reversal, ()),
        ("reversal_family_only_overlay_negative_control", config.reversal, config.reversal),
    )


def _fold_row(fold, cost, variant, returns, baseline, turnover) -> dict[str, object]:
    return {
        "fold": fold.fold, "variant": variant, "cost_bps": float(cost),
        "test_start": str(fold.test_index[0].date()), "test_end": str(fold.test_index[-1].date()),
        "return_pct": _total_return_pct(returns), "cagr_pct": _cagr_pct(returns),
        "ann_vol_pct": _annual_vol_pct(returns), "ann_sharpe": _annual_sharpe(returns),
        "max_drawdown_pct": _max_drawdown_pct(returns), "baseline_return_pct": _total_return_pct(baseline),
        "variant_return_pct": _total_return_pct(returns), "delta_return_pct": _total_return_pct(returns) - _total_return_pct(baseline),
        "turnover": float(turnover.mean()) if not turnover.empty else 0.0,
    }


def _metrics(fold: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for keys, frame in fold.groupby(["variant", "cost_bps"], sort=False):
        rows.append(_metric_row(str(keys[0]), float(keys[1]), frame))
    return pd.DataFrame(rows)


def _metric_row(variant: str, cost: float, frame: pd.DataFrame) -> dict[str, object]:
    return {
        "variant": variant, "cost_bps": cost, "return_pct": float(frame["return_pct"].sum()),
        "ann_sharpe": float(frame["ann_sharpe"].mean()), "max_drawdown_pct": float(frame["max_drawdown_pct"].min()),
        "negative_fold_rate": float(frame["return_pct"].lt(0.0).mean()), "worst_fold_sharpe": float(frame["ann_sharpe"].min()),
        "latest_fold_sharpe": float(frame.sort_values("fold").iloc[-1]["ann_sharpe"]), "turnover": float(frame["turnover"].mean()),
    }


def _tail(fold: pd.DataFrame) -> pd.DataFrame:
    rows = [_tail_row(str(k[0]), float(k[1]), f) for k, f in fold.groupby(["variant", "cost_bps"], sort=False)]
    frame = pd.DataFrame(rows)
    frame["bh_p_value"] = _bh(frame["paired_p_value"])
    return frame


def _tail_row(variant: str, cost: float, frame: pd.DataFrame) -> dict[str, object]:
    base, delta = frame["baseline_return_pct"], frame["delta_return_pct"]
    right, top = frame.loc[base.ge(base.quantile(0.75))], frame.loc[base.ge(base.quantile(0.90))]
    ci_low, ci_high = _bootstrap(delta)
    t_stat, p_value = _paired_t(delta)
    return {
        "variant": variant, "cost_bps": cost, "mean_delta": float(delta.mean()),
        "left_tail_delta": float(delta.loc[base.le(base.quantile(0.25))].mean()),
        "right_tail_retention": _ratio(right["variant_return_pct"].mean(), right["baseline_return_pct"].mean()),
        "top_decile_retention": _ratio(top["variant_return_pct"].mean(), top["baseline_return_pct"].mean()),
        "bottom_decile_improvement": float(delta.loc[base.le(base.quantile(0.10))].mean()),
        "best_fold_damage": float(delta.loc[base.idxmax()]), "worst_fold_improvement": float(delta.loc[base.idxmin()]),
        "ci_low": ci_low, "ci_high": ci_high, "paired_t_stat": t_stat, "paired_p_value": p_value,
    }


def _events(fold: pd.DataFrame, source: Path) -> pd.DataFrame:
    labels = _event_labels(source)
    frame = fold.assign(event_label=fold["fold"].map(labels).fillna("unmatched"))
    rows = []
    for keys, group in frame.groupby(["variant", "cost_bps"], sort=False):
        rows.extend(_event_rows(str(keys[0]), float(keys[1]), group))
    return pd.DataFrame(rows)


def _event_rows(variant: str, cost: float, frame: pd.DataFrame) -> list[dict[str, object]]:
    stress, ordinary = frame.loc[~frame["event_label"].eq("unmatched")], frame.loc[frame["event_label"].eq("unmatched")]
    return [_event_row(variant, cost, "known_stress", stress), _event_row(variant, cost, "unmatched", ordinary), _event_row(variant, cost, "all", frame)]


def _event_row(variant, cost, split, frame) -> dict[str, object]:
    return {"variant": variant, "cost_bps": cost, "split": split, "fold_count": int(frame["fold"].nunique()), "mean_delta": float(frame["delta_return_pct"].mean()) if not frame.empty else 0.0}


def _concentration(fold: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame([fold_concentration_row(str(k[0]), float(k[1]), f) for k, f in fold.groupby(["variant", "cost_bps"], sort=False)])


def _attribution(fold: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for keys, frame in fold.groupby(["variant", "cost_bps"], sort=False):
        rows.append({"variant": str(keys[0]), "cost_bps": float(keys[1]), "portfolio_net_delta": float(frame["delta_return_pct"].sum())})
    return pd.DataFrame(rows)


def _cost(tail: pd.DataFrame) -> pd.DataFrame:
    return tail[["variant", "cost_bps", "mean_delta", "left_tail_delta", "right_tail_retention", "ci_low"]]


def _trade_row(panel, bundle, future, fold, cost, config, alpha, multiplier, positions, intensity) -> dict[str, object]:
    features = build_survivor_features(panel, bundle.signal, intensity)
    trades = trade_feature_rows(positions, future.reindex(fold.test_index), multiplier, features, config.horizon)
    return {"alpha": alpha, "fold": fold.fold, "cost_bps": float(cost), **blocker_value_row(trades)}


def _select(panel, bundle, intensity, future, fold, cost, config, hyp) -> dict[str, float]:
    best, best_score = None, -float("inf")
    for quantile in hyp.threshold_quantiles:
        threshold = _threshold(intensity.reindex(fold.train_index), quantile, "high")
        for params in hyp.multiplier_grid:
            result = _backtest(panel, bundle, future, fold.train_index, cost, config)
            base = _daily(result.net_return, config.horizon)
            returns = base.mul(_multiplier(intensity.reindex(fold.train_index), hyp, threshold, params), fill_value=0.0)
            score = _total_return_pct(returns) - _total_return_pct(base)
            if score > best_score:
                best, best_score = {"threshold": threshold, "quantile": quantile, **params}, score
    return best or {"threshold": 0.0, "quantile": 0.0, "down": 1.0, "up": 1.0}


def _backtest(panel, bundle, future, index, cost, config):
    bt = BacktestConfig(bundle.alpha, "ranked_long_only", config.horizon, turnover_cost(float(cost)), top_quantile=0.8, min_names=20)
    active = panel.active_mask.reindex(index).fillna(False).astype(bool)
    return run_backtest(bundle.signal.reindex(index), future.reindex(index), bt, active, bundle.rank_pct.reindex(index))


def _config(raw: dict[str, Any]) -> PortfolioIntegrationConfig:
    compute, backtests, walk, gpu = dict(raw["compute"]), dict(raw["backtests"]), dict(raw["walk_forward_validation"]), dict(raw["gpu"])
    groups = {str(g["group_id"]): tuple(str(a) for a in g["alphas"]) for g in raw["overlay_groups"]}
    return PortfolioIntegrationConfig(tuple(raw["alphas"]), groups["structure_level"], groups["core_structure"], groups["reversal_exhaustion"], Path(str(compute["cache_dir"])), Path(str(compute["report_root"])), Path(str(compute["source_report_dir"])), tuple(float(c) for c in backtests["cost_bps"]), int(backtests["horizon"]), int(walk["train_size_days"]), int(walk["test_size_days"]), int(walk["step_size_days"]), int(walk["lookahead_days"]), int(walk["max_folds"]), int(compute.get("max_workers", 1)), GpuConfig(bool(gpu.get("enabled", False)), str(gpu.get("backend", "auto"))))


def _paths(report_dir: Path) -> dict[str, Path]:
    p = "breadth_risk_off_portfolio_integration"
    return {k: report_dir / f"{p}_{name}.csv" for k, name in {"metrics": "metrics", "tail": "tail_diagnostics", "attribution": "overlay_attribution", "trade": "trade_diagnostics", "event": "event_split", "concentration": "fold_concentration", "cost": "cost_stress"}.items()} | {"markdown": report_dir / f"{p}_report.md"}


def _markdown(result: PortfolioIntegrationResult) -> str:
    return "\n".join(["# Breadth Risk-Off Portfolio Integration", "", "## Metrics", "", markdown_table(result.metrics, max_rows=30), "", "## Tail", "", markdown_table(result.tail, max_rows=30), ""])


def _narrow(config, hyp) -> NarrowFalsificationConfig:
    return NarrowFalsificationConfig((hyp,), config.cache_dir, config.report_root, config.source_report_dir, train_size_days=config.train_size_days, test_size_days=config.test_size_days, step_size_days=config.step_size_days, lookahead_days=config.lookahead_days, max_folds=config.max_folds)


def _stream_for(streams, alpha: str, overlay: tuple[str, ...]) -> pd.Series:
    return streams[(alpha, "overlay")] if alpha in overlay and (alpha, "overlay") in streams else streams[(alpha, "baseline")]


def _combine(series: list[pd.Series]) -> pd.Series:
    return pd.concat(series, axis=1).mean(axis=1).fillna(0.0) if series else pd.Series(dtype=float)


def _grid() -> tuple[dict[str, float], ...]:
    return ({"down": 0.25, "up": 1.10}, {"down": 0.25, "up": 1.25}, {"down": 0.50, "up": 1.10}, {"down": 0.50, "up": 1.25})


def _report_dir(root: Path) -> Path:
    return root / datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
