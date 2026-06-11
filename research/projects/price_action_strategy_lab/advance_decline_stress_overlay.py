from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from research.notebooks.alpha_001.research.alpha101_engine import Alpha101Panel, forward_return
from research.projects.price_action_strategy_lab.alpha_specs import default_alpha_registry
from research.projects.price_action_strategy_lab.alpha_runner import load_signal_bundles
from research.projects.price_action_strategy_lab.backtest_modes import BacktestConfig, run_backtest
from research.projects.price_action_strategy_lab.breadth_only_diagnostic import fold_concentration_row
from research.projects.price_action_strategy_lab.compute_backend import GpuConfig
from research.projects.price_action_strategy_lab.costs import turnover_cost
from research.projects.price_action_strategy_lab.external_stress_diagnostics import _raw_features
from research.projects.price_action_strategy_lab.narrow_falsification import FoldSpec, _daily, _folds
from research.projects.price_action_strategy_lab.narrow_falsification_stats import metric_row
from research.projects.price_action_strategy_lab.run_activator_suite import _load_panel, _read_config
from research.projects.price_action_strategy_lab.soft_throttle_walk_forward_reports import markdown_table
from research.projects.price_action_strategy_lab.stress_confirmation import _bh, _bootstrap, _event_labels, _paired_t, _ratio
from research.projects.price_action_strategy_lab.universe_adapter import to_alpha101_panel


@dataclass(frozen=True)
class StressHypothesis:
    signal: str
    scope: str
    variant: str
    alphas: tuple[str, ...]
    multipliers: tuple[dict[str, float], ...]


@dataclass(frozen=True)
class AdvanceDeclineStressConfig:
    alphas: tuple[str, ...]
    hypotheses: tuple[StressHypothesis, ...]
    threshold_quantiles: tuple[float, ...]
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
    top_quantile: float = 0.8
    min_names: int = 20
    max_workers: int = 1
    gpu: GpuConfig = GpuConfig()


@dataclass(frozen=True)
class AdvanceDeclineStressResult:
    report_dir: Path
    metrics: pd.DataFrame
    tail: pd.DataFrame
    targeting: pd.DataFrame
    trade: pd.DataFrame
    event: pd.DataFrame
    concentration: pd.DataFrame
    stability: pd.DataFrame
    cost: pd.DataFrame


def run_advance_decline_stress_config(path: str | Path) -> AdvanceDeclineStressResult:
    raw = _read_config(Path(path))
    panel = to_alpha101_panel(_load_panel(raw))
    result = run_advance_decline_stress(panel, _config(raw))
    write_advance_decline_stress_reports(result, Path(path))
    return result


def run_advance_decline_stress(panel: Alpha101Panel, config: AdvanceDeclineStressConfig) -> AdvanceDeclineStressResult:
    bundles = {b.alpha: b for b in load_signal_bundles(panel, default_alpha_registry(), config.alphas, config.cache_dir, config.gpu, config.max_workers)}
    features = _stress_features(panel)
    future = forward_return(panel.close, config.horizon)
    folds, trades = _run_folds(panel, bundles, features, future, config)
    fold = pd.DataFrame(folds)
    result = AdvanceDeclineStressResult(
        _report_dir(config.report_root),
        _metrics(fold),
        _tail(fold),
        _targeting(fold),
        pd.DataFrame(trades),
        _events(fold, config.source_report_dir),
        _concentration(fold),
        _stability(fold),
        _cost(_tail(fold)),
    )
    return result


def write_advance_decline_stress_reports(result: AdvanceDeclineStressResult, config_path: Path) -> dict[str, Path]:
    result.report_dir.mkdir(parents=True, exist_ok=True)
    paths = _paths(result.report_dir)
    paths["hypothesis"].write_text(config_path.read_text(encoding="utf-8"), encoding="utf-8")
    result.metrics.to_csv(paths["metrics"], index=False)
    result.tail.to_csv(paths["tail"], index=False)
    result.targeting.to_csv(paths["targeting"], index=False)
    result.trade.to_csv(paths["trade"], index=False)
    result.event.to_csv(paths["event"], index=False)
    result.concentration.to_csv(paths["concentration"], index=False)
    result.stability.to_csv(paths["stability"], index=False)
    result.cost.to_csv(paths["cost"], index=False)
    paths["report"].write_text(_markdown(result), encoding="utf-8")
    return paths


def _run_folds(panel, bundles, features, future, config):
    folds, trades = [], []
    cache: dict[tuple[str, float, str, str, int], object] = {}
    for cost in config.cost_bps:
        for fold in _folds(panel.close.index, _narrow(config)):
            data = _baseline_data(panel, bundles, future, fold, cost, config, cache)
            folds.extend(_baseline_rows(fold, cost, data, config))
            for hyp in config.hypotheses:
                selected = _select(data, features[hyp.signal], fold, hyp, config)
                rows, trade = _hypothesis_rows(data, features[hyp.signal], fold, cost, hyp, selected, config)
                folds.append(rows)
                trades.append(trade)
    return folds, trades


def _baseline_data(panel, bundles, future, fold, cost, config, cache):
    out = {}
    for alpha, bundle in bundles.items():
        result = _baseline_result(panel, bundle, future, fold, cost, config, cache)
        out[alpha] = {"returns": _daily(result.net_return, config.horizon), "positions": result.positions, "turnover": result.turnover, "future": future.reindex(fold.test_index)}
    return out


def _baseline_rows(fold, cost, data, config) -> list[dict[str, object]]:
    rows = []
    for scope, alphas in _scopes(config).items():
        returns = _combine([data[a]["returns"] for a in alphas])
        selected = {"threshold": 0.0, "quantile": 0.0, "down": 1.0, "up": 1.0}
        rows.append(_fold_row(fold, cost, f"{scope}:baseline", scope, "baseline", "none", returns, returns, pd.Series(1.0, index=returns.index), _combine([data[a]["turnover"].reindex(returns.index).fillna(0.0) for a in alphas]), selected))
    return rows


def _hypothesis_rows(data, intensity, fold, cost, hyp, selected, config):
    base = _combine([data[a]["returns"] for a in hyp.alphas])
    mult = _multiplier(intensity.reindex(fold.test_index), float(selected["threshold"]), selected)
    variant = base.mul(mult.reindex(base.index).fillna(1.0), fill_value=0.0)
    turnover = _combine([data[a]["turnover"].reindex(base.index).fillna(0.0) for a in hyp.alphas]).mul(mult.reindex(base.index).fillna(1.0), fill_value=0.0)
    row = _fold_row(fold, cost, _hyp_id(hyp), hyp.scope, hyp.variant, hyp.signal, variant, base, mult, turnover, selected)
    return row, _trade_row(data, intensity, fold, cost, hyp, mult, config)


def _select(data, intensity, fold, hyp, config) -> dict[str, float]:
    del data
    best, score = {"threshold": 0.0, "quantile": 0.0, **hyp.multipliers[0]}, float("inf")
    train = intensity.reindex(fold.train_index).dropna()
    for quantile in config.threshold_quantiles:
        threshold = float(train.quantile(quantile)) if not train.empty else 0.0
        for params in hyp.multipliers:
            activation_error = abs(float(intensity.reindex(fold.train_index).ge(threshold).mean()) - 0.20)
            if activation_error < score:
                best, score = {"threshold": threshold, "quantile": quantile, **params}, activation_error
    return best


def _fold_row(fold, cost, hypothesis, scope, variant, signal, returns, base, mult, turnover, selected) -> dict[str, object]:
    row = {"hypothesis_id": hypothesis, "scope": scope, "variant": variant, "signal": signal, "fold": fold.fold, "cost_bps": float(cost), "test_start": str(fold.test_index[0].date()), "test_end": str(fold.test_index[-1].date()), "selected_threshold": float(selected["threshold"]), "selected_quantile": float(selected["quantile"]), "multiplier_down": float(selected["down"]), "multiplier_up": float(selected["up"]), "activation_rate": float(mult.lt(1.0).mean()), "avg_exposure_multiplier": float(mult.mean()), "turnover": float(turnover.mean()) if not turnover.empty else 0.0}
    row.update(metric_row(base, "baseline"))
    row.update(metric_row(returns, "variant"))
    row["delta_return_pct"] = float(row["variant_return_pct"] - row["baseline_return_pct"])
    row["max_drawdown_delta_pct"] = float(row["variant_max_drawdown_pct"] - row["baseline_max_drawdown_pct"])
    return row


def _trade_row(data, intensity, fold, cost, hyp, mult, config) -> dict[str, object]:
    del intensity
    positions = _combine_frames([data[alpha]["positions"] for alpha in hyp.alphas])
    future = next(iter(data.values()))["future"]
    total = _fast_trade_diagnostics(positions, future, mult, config.horizon)
    return {"hypothesis_id": _hyp_id(hyp), "fold": fold.fold, "cost_bps": float(cost), **total}


def _metrics(fold: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for keys, frame in fold.groupby(["hypothesis_id", "cost_bps"], sort=False):
        rows.append({"hypothesis_id": str(keys[0]), "cost_bps": float(keys[1]), "return_pct": float(frame["variant_return_pct"].sum()), "baseline_return_pct": float(frame["baseline_return_pct"].sum()), "delta_return_pct": float(frame["delta_return_pct"].sum()), "ann_sharpe": float(frame["variant_ann_sharpe"].mean()), "baseline_ann_sharpe": float(frame["baseline_ann_sharpe"].mean()), "max_drawdown_pct": float(frame["variant_max_drawdown_pct"].min()), "baseline_max_drawdown_pct": float(frame["baseline_max_drawdown_pct"].min()), "negative_fold_rate": float(frame["variant_return_pct"].lt(0.0).mean()), "worst_fold_sharpe": float(frame["variant_ann_sharpe"].min()), "latest_fold_sharpe": float(frame.sort_values("fold").iloc[-1]["variant_ann_sharpe"]), "turnover": float(frame["turnover"].mean()), "average_exposure": float(frame["avg_exposure_multiplier"].mean())})
    return pd.DataFrame(rows)


def _tail(fold: pd.DataFrame) -> pd.DataFrame:
    rows = [_tail_row(str(k[0]), float(k[1]), f) for k, f in fold.groupby(["hypothesis_id", "cost_bps"], sort=False)]
    out = pd.DataFrame(rows)
    out["bh_p_value"] = _bh(out["paired_p_value"]) if not out.empty else pd.Series(dtype=float)
    return out


def _tail_row(hypothesis: str, cost: float, frame: pd.DataFrame) -> dict[str, object]:
    base, delta = frame["baseline_return_pct"], frame["delta_return_pct"]
    right, top = frame.loc[base.ge(base.quantile(0.75))], frame.loc[base.ge(base.quantile(0.90))]
    ci_low, ci_high = _bootstrap(delta)
    t_stat, p_value = _paired_t(delta)
    return {"hypothesis_id": hypothesis, "cost_bps": cost, "mean_delta_vs_baseline": float(delta.mean()), "left_tail_delta": float(delta.loc[base.le(base.quantile(0.25))].mean()), "right_tail_retention": _ratio(right["variant_return_pct"].mean(), right["baseline_return_pct"].mean()), "top_decile_retention": _ratio(top["variant_return_pct"].mean(), top["baseline_return_pct"].mean()), "bottom_decile_improvement": float(delta.loc[base.le(base.quantile(0.10))].mean()), "best_fold_damage": float(delta.loc[base.idxmax()]), "worst_fold_improvement": float(delta.loc[base.idxmin()]), "ci_low": ci_low, "ci_high": ci_high, "paired_t_stat": t_stat, "paired_p_value": p_value}


def _targeting(fold: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for keys, frame in fold.groupby(["hypothesis_id", "cost_bps"], sort=False):
        base = frame["baseline_return_pct"]
        weak = base.le(base.quantile(0.25))
        normal = ~weak
        rows.append({"hypothesis_id": str(keys[0]), "cost_bps": float(keys[1]), "weak_folds_correctly_reduced": int((frame["avg_exposure_multiplier"].lt(1.0) & weak).sum()), "normal_folds_incorrectly_reduced": int((frame["avg_exposure_multiplier"].lt(1.0) & normal).sum()), "false_positive_fold_cost": float(frame.loc[frame["avg_exposure_multiplier"].lt(1.0) & normal, "delta_return_pct"].sum()), "false_negative_weak_fold_cost": float(frame.loc[frame["avg_exposure_multiplier"].ge(1.0) & weak, "delta_return_pct"].sum()), "stress_activation_rate": float(frame["activation_rate"].mean()), "avg_exposure_weak_folds": float(frame.loc[weak, "avg_exposure_multiplier"].mean()), "avg_exposure_normal_folds": float(frame.loc[normal, "avg_exposure_multiplier"].mean())})
    return pd.DataFrame(rows)


def _events(fold: pd.DataFrame, source: Path) -> pd.DataFrame:
    labels = _event_labels(source)
    frame = fold.assign(event_label=fold["fold"].map(labels).fillna("unmatched"))
    rows = []
    for keys, group in frame.groupby(["hypothesis_id", "cost_bps", "event_label"], sort=False):
        rows.append({"hypothesis_id": str(keys[0]), "cost_bps": float(keys[1]), "event_label": str(keys[2]), "fold_count": int(group["fold"].nunique()), "mean_delta": float(group["delta_return_pct"].mean()), "mean_baseline_return": float(group["baseline_return_pct"].mean()), "mean_variant_return": float(group["variant_return_pct"].mean())})
    return pd.DataFrame(rows)


def _concentration(fold: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame([fold_concentration_row(str(k[0]), float(k[1]), f.rename(columns={"delta_return_pct": "delta_return_pct"})) for k, f in fold.groupby(["hypothesis_id", "cost_bps"], sort=False)])


def _stability(fold: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for keys, frame in fold.groupby(["hypothesis_id", "cost_bps"], sort=False):
        rows.append({"hypothesis_id": str(keys[0]), "cost_bps": float(keys[1]), "fold_count": int(frame["fold"].nunique()), "selected_threshold_mean": float(frame["selected_threshold"].mean()), "selected_threshold_std": float(frame["selected_threshold"].std(ddof=0)), "selected_quantile_mean": float(frame["selected_quantile"].mean()), "multiplier_down_mean": float(frame["multiplier_down"].mean()), "multiplier_up_mean": float(frame["multiplier_up"].mean()), "activation_rate": float(frame["activation_rate"].mean()), "avg_exposure_multiplier": float(frame["avg_exposure_multiplier"].mean())})
    return pd.DataFrame(rows)


def _cost(tail: pd.DataFrame) -> pd.DataFrame:
    return tail[["hypothesis_id", "cost_bps", "mean_delta_vs_baseline", "left_tail_delta", "right_tail_retention", "ci_low"]]


def _stress_features(panel: Alpha101Panel) -> dict[str, pd.Series]:
    raw = _raw_features(panel)
    ad1 = -raw["advance_decline_ratio_lag1"].shift(1)
    n5 = -raw["nifty_return_5d_lag1"].shift(1)
    ad5 = -raw["advance_decline_ratio_5d_lag1"].shift(1)
    breadth = raw["breadth_risk_off_lag1"].shift(1)
    composite = pd.concat([ad1, n5], axis=1)
    return {"advance_decline_ratio_lag1_low": ad1, "nifty_return_5d_lag1_low": n5, "advance_decline_ratio_5d_lag1_low": ad5, "composite_ad1d_low_and_nifty5d_low": composite.min(axis=1), "composite_ad1d_low_or_nifty5d_low": composite.max(axis=1), "breadth_risk_off_lag1_high": breadth}


def _multiplier(intensity: pd.Series, threshold: float, params: dict[str, float]) -> pd.Series:
    stress = intensity.ge(threshold).fillna(False)
    return pd.Series(np.where(stress, float(params["down"]), float(params["up"])), index=intensity.index)


def _baseline_result(panel, bundle, future, fold: FoldSpec, cost, config, cache):
    key = (bundle.alpha, float(cost), str(fold.test_index[0]), str(fold.test_index[-1]), len(fold.test_index))
    if key not in cache:
        active = panel.active_mask.reindex(fold.test_index).fillna(False).astype(bool)
        bt = BacktestConfig(bundle.alpha, "ranked_long_only", config.horizon, turnover_cost(float(cost)), top_quantile=config.top_quantile, min_names=config.min_names)
        cache[key] = run_backtest(bundle.signal.reindex(fold.test_index), future.reindex(fold.test_index), bt, active, bundle.rank_pct.reindex(fold.test_index))
    return cache[key]


def _config(raw: dict[str, Any]) -> AdvanceDeclineStressConfig:
    compute, backtests, walk, gpu = dict(raw["compute"]), dict(raw["backtests"]), dict(raw["walk_forward_validation"]), dict(raw["gpu"])
    overlay, groups = dict(raw["stress_overlay"]), {str(g["group_id"]): tuple(str(a) for a in g["alphas"]) for g in raw["overlay_groups"]}
    hypotheses = tuple(StressHypothesis(signal, scope, variant, groups[scope], tuple(dict(x) for x in grid)) for signal in overlay["signals"] for scope in groups for variant, grid in dict(overlay["variants"]).items())
    return AdvanceDeclineStressConfig(tuple(raw["alphas"]), hypotheses, tuple(float(x) for x in overlay["threshold_quantiles"]), Path(str(compute["cache_dir"])), Path(str(compute["report_root"])), Path(str(compute["source_report_dir"])), tuple(float(x) for x in backtests["cost_bps"]), int(backtests["horizon"]), int(walk["train_size_days"]), int(walk["test_size_days"]), int(walk["step_size_days"]), int(walk["lookahead_days"]), int(walk["max_folds"]), float(backtests["top_quantile"]), int(backtests["min_active_names"]), int(compute.get("max_workers", 1)), GpuConfig(bool(gpu.get("enabled", False)), str(gpu.get("backend", "auto"))))


def _narrow(config: AdvanceDeclineStressConfig):
    from research.projects.price_action_strategy_lab.narrow_falsification import NarrowFalsificationConfig, NarrowHypothesis

    hyp = NarrowHypothesis("folds", ("support_trendline_position_20",), "advance_decline_ratio_lag1", "high", "reduce_only", config.threshold_quantiles, ({"down": 0.5, "up": 1.0},))
    return NarrowFalsificationConfig((hyp,), config.cache_dir, config.report_root, config.source_report_dir, horizon=config.horizon, cost_bps=config.cost_bps, train_size_days=config.train_size_days, test_size_days=config.test_size_days, step_size_days=config.step_size_days, lookahead_days=config.lookahead_days, max_folds=config.max_folds, top_quantile=config.top_quantile, min_names=config.min_names, max_workers=config.max_workers, gpu=config.gpu)


def _scopes(config: AdvanceDeclineStressConfig) -> dict[str, tuple[str, ...]]:
    return {hyp.scope: hyp.alphas for hyp in config.hypotheses}


def _paths(report_dir: Path) -> dict[str, Path]:
    p = "advance_decline_stress_overlay"
    return {"hypothesis": report_dir / f"{p}_hypothesis.yaml", "metrics": report_dir / f"{p}_metrics.csv", "tail": report_dir / f"{p}_tail_diagnostics.csv", "targeting": report_dir / f"{p}_targeting_diagnostics.csv", "trade": report_dir / f"{p}_trade_diagnostics.csv", "event": report_dir / f"{p}_event_split.csv", "concentration": report_dir / f"{p}_fold_concentration.csv", "stability": report_dir / f"{p}_threshold_stability.csv", "cost": report_dir / f"{p}_cost_stress.csv", "report": report_dir / f"{p}_report.md"}


def _markdown(result: AdvanceDeclineStressResult) -> str:
    return "\n".join(["# Advance-Decline Stress Overlay Report", "", "Status: research-only falsification sprint.", "", "## Metrics", "", markdown_table(result.metrics, max_rows=30), "", "## Tail Diagnostics", "", markdown_table(result.tail, max_rows=30), "", "## Targeting", "", markdown_table(result.targeting, max_rows=30)])


def _report_dir(root: Path) -> Path:
    return root / datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _hyp_id(hyp: StressHypothesis) -> str:
    return f"{hyp.scope}:{hyp.signal}:{hyp.variant}"


def _combine(series: list[pd.Series]) -> pd.Series:
    return pd.concat(series, axis=1).mean(axis=1).fillna(0.0) if series else pd.Series(dtype=float)


def _combine_frames(frames: list[pd.DataFrame]) -> pd.DataFrame:
    return pd.concat(frames).groupby(level=0).mean() if frames else pd.DataFrame()


def _fast_trade_diagnostics(positions: pd.DataFrame, future: pd.DataFrame, multiplier: pd.Series, horizon: int) -> dict[str, float | int]:
    base = positions.mul(future.reindex_like(positions).fillna(0.0)).div(float(horizon))
    base_arr = np.nan_to_num(base.to_numpy(dtype=float), nan=0.0)
    mult_arr = np.nan_to_num(multiplier.reindex(base.index).to_numpy(dtype=float), nan=1.0)
    scaled = base_arr * mult_arr[:, None]
    active = (positions.to_numpy(dtype=float) != 0.0) & (base_arr != 0.0)
    mult = np.broadcast_to(mult_arr[:, None], base_arr.shape)
    winner, loser = base_arr > 0.0, base_arr < 0.0
    blocked, reduced = mult == 0.0, (mult > 0.0) & (mult < 1.0)
    increased, accepted = mult > 1.0, mult == 1.0
    fields = _fast_trade_value_fields(base_arr, scaled, active, blocked, reduced, increased, winner, loser)
    return {"accepted_winner": _n(accepted & winner & active), "accepted_loser": _n(accepted & loser & active), "blocked_winner": _n(blocked & winner & active), "blocked_loser": _n(blocked & loser & active), "reduced_winner": _n(reduced & winner & active), "reduced_loser": _n(reduced & loser & active), "increased_winner": _n(increased & winner & active), "increased_loser": _n(increased & loser & active), **fields}


def _fast_trade_value_fields(base, scaled, active, blocked, reduced, increased, winner, loser) -> dict[str, float]:
    values = {
        "loss_saved_from_blocked_losers": _v(-base, active & blocked & loser),
        "profit_lost_from_blocked_winners": _v(base, active & blocked & winner),
        "loss_reduced_from_sized_down_losers": _v(scaled - base, active & reduced & loser),
        "profit_reduced_from_sized_down_winners": _v(base - scaled, active & reduced & winner),
        "profit_added_from_sized_up_winners": _v(scaled - base, active & increased & winner),
        "loss_added_from_sized_up_losers": _v(base - scaled, active & increased & loser),
    }
    values["net_blocker_value"] = values["loss_saved_from_blocked_losers"] - values["profit_lost_from_blocked_winners"] + values["loss_reduced_from_sized_down_losers"] - values["profit_reduced_from_sized_down_winners"] + values["profit_added_from_sized_up_winners"] - values["loss_added_from_sized_up_losers"]
    return {key: float(value * 100.0) for key, value in values.items()}


def _n(mask: np.ndarray) -> int:
    return int(mask.sum())


def _v(values: np.ndarray, mask: np.ndarray) -> float:
    return float(values[mask].sum())
