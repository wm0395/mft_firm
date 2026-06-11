from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from research.notebooks.alpha_001.research.alpha101_engine import Alpha101Panel, forward_return
from research.projects.price_action_strategy_lab.activator_specs import default_activator_registry
from research.projects.price_action_strategy_lab.activator_suite import build_activator_masks
from research.projects.price_action_strategy_lab.alpha_specs import default_alpha_registry
from research.projects.price_action_strategy_lab.alpha_runner import load_signal_bundles
from research.projects.price_action_strategy_lab.breadth_only_diagnostic import fold_concentration_row
from research.projects.price_action_strategy_lab.compute_backend import GpuConfig
from research.projects.price_action_strategy_lab.narrow_falsification import _baseline_result, _daily, _folds, _multiplier, _threshold
from research.projects.price_action_strategy_lab.run_activator_suite import _load_panel, _read_config
from research.projects.price_action_strategy_lab.soft_throttle_analysis import _annual_sharpe, _annual_vol_pct, _cagr_pct, _max_drawdown_pct, _total_return_pct
from research.projects.price_action_strategy_lab.soft_throttle_walk_forward_reports import markdown_table
from research.projects.price_action_strategy_lab.survivor_diagnostic import _event_labels
from research.projects.price_action_strategy_lab.survivor_features import blocker_value_row, build_survivor_features, trade_feature_rows
from research.projects.price_action_strategy_lab.universe_adapter import to_alpha101_panel


@dataclass(frozen=True)
class SleeveVariantSpec:
    variant_id: str
    kind: str
    sleeve_group: str
    weight: float


@dataclass(frozen=True)
class StructureSleeveAllocationConfig:
    alphas: tuple[str, ...]
    structure: tuple[str, ...]
    core: tuple[str, ...]
    cache_dir: Path
    report_root: Path
    source_report_dir: Path
    cost_bps: tuple[float, ...]
    core_weights: tuple[float, ...]
    full_structure_weights: tuple[float, ...]
    mode: str = "ranked_long_only"
    horizon: int = 10
    train_size_days: int = 126
    test_size_days: int = 21
    step_size_days: int = 21
    lookahead_days: int = 10
    max_folds: int = 24
    top_quantile: float = 0.8
    min_names: int = 20
    threshold_quantiles: tuple[float, ...] = (0.5, 0.6, 0.7, 0.8)
    multiplier_grid: tuple[dict[str, float], ...] = (
        {"down": 0.25, "up": 1.10},
        {"down": 0.25, "up": 1.25},
        {"down": 0.50, "up": 1.10},
        {"down": 0.50, "up": 1.25},
    )
    max_workers: int = 1
    gpu: GpuConfig = field(default_factory=GpuConfig)


@dataclass(frozen=True)
class StructureSleeveAllocationResult:
    report_dir: Path
    metrics: pd.DataFrame
    tail: pd.DataFrame
    attribution: pd.DataFrame
    event: pd.DataFrame
    concentration: pd.DataFrame
    cost: pd.DataFrame


@dataclass(frozen=True)
class StructureSleeveAllocationRunResult:
    report_dir: Path


def run_structure_sleeve_allocation_config(config_path: str | Path) -> StructureSleeveAllocationRunResult:
    raw = _read_config(Path(config_path))
    panel = to_alpha101_panel(_load_panel(raw))
    result = run_structure_sleeve_allocation(panel, _config(raw))
    write_structure_sleeve_allocation_reports(result)
    return StructureSleeveAllocationRunResult(result.report_dir)


def run_structure_sleeve_allocation(panel: Alpha101Panel, config: StructureSleeveAllocationConfig) -> StructureSleeveAllocationResult:
    bundles = {bundle.alpha: bundle for bundle in load_signal_bundles(panel, default_alpha_registry(), config.alphas, config.cache_dir, config.gpu, config.max_workers)}
    intensity = build_activator_masks(panel, default_activator_registry(), config.max_workers)["breadth_risk_off"].mean(axis=1).fillna(0.0)
    future = forward_return(panel.close, config.horizon)
    fold_rows, daily_rows, attribution_rows = _run_folds(panel, bundles, intensity, future, config)
    fold_frame = pd.DataFrame(fold_rows)
    daily_frame = pd.DataFrame(daily_rows)
    attr_frame = _aggregate_attribution(pd.DataFrame(attribution_rows))
    tail = _tail(fold_frame)
    return StructureSleeveAllocationResult(
        report_dir=_report_dir(config.report_root),
        metrics=_metrics(daily_frame, fold_frame),
        tail=tail,
        attribution=attr_frame,
        event=_event_split(fold_frame, config.source_report_dir),
        concentration=_concentration(fold_frame),
        cost=_cost(tail),
    )


def write_structure_sleeve_allocation_reports(result: StructureSleeveAllocationResult) -> dict[str, Path]:
    result.report_dir.mkdir(parents=True, exist_ok=True)
    paths = _paths(result.report_dir)
    result.metrics.to_csv(paths["metrics"], index=False)
    result.tail.to_csv(paths["tail"], index=False)
    result.attribution.to_csv(paths["attribution"], index=False)
    result.event.to_csv(paths["event"], index=False)
    result.concentration.to_csv(paths["concentration"], index=False)
    result.cost.to_csv(paths["cost"], index=False)
    paths["markdown"].write_text(_markdown(result), encoding="utf-8")
    return paths


def _run_folds(panel, bundles, intensity, future, config):
    fold_rows: list[dict[str, object]] = []
    daily_rows: list[dict[str, object]] = []
    attribution_rows: list[dict[str, object]] = []
    cache: dict[tuple[str, float, str, str, int], object] = {}
    selected_alphas = set(config.structure)
    for cost in config.cost_bps:
        for fold in _folds(panel.close.index, _narrow(config)):
            alpha_data, alpha_blockers = _alpha_streams(panel, bundles, intensity, future, fold, cost, config, cache, selected_alphas)
            fold_rows.extend(_fold_rows(fold, cost, alpha_data, alpha_blockers, config))
            daily_rows.extend(_daily_rows(fold, cost, alpha_data, config))
            attribution_rows.extend(_attribution_rows(fold, cost, alpha_data, alpha_blockers, config))
    return fold_rows, daily_rows, attribution_rows


def _alpha_streams(panel, bundles, intensity, future, fold, cost, config, cache, selected_alphas):
    data: dict[str, dict[str, pd.Series]] = {}
    blockers: dict[str, dict[str, float | int]] = {}
    for alpha, bundle in bundles.items():
        result = _baseline_result(panel, bundle, future, fold.test_index, cost, config, cache)
        base = _daily(result.net_return, config.horizon)
        turn = result.turnover.reindex(base.index).fillna(0.0)
        data[alpha] = {"baseline": base, "baseline_turnover": turn}
        if alpha in selected_alphas:
            selected = _select(panel, bundle, intensity, future, fold, cost, config, cache)
            mult = _multiplier(intensity.reindex(fold.test_index), _hypothesis(alpha), selected["threshold"], selected)
            overlay = base.mul(mult, fill_value=0.0)
            data[alpha]["overlay"] = overlay
            data[alpha]["overlay_turnover"] = turn.mul(mult, fill_value=0.0)
            blockers[alpha] = blocker_value_row(trade_feature_rows(result.positions, future.reindex(fold.test_index), mult, build_survivor_features(panel, bundle.signal, intensity), config.horizon))
    return data, blockers


def _fold_rows(fold, cost, alpha_data, alpha_blockers, config):
    rows = []
    components = _component_series(alpha_data, config)
    base_full, base_turn = components[0], components[1]
    base_wo, turn_wo = components[2], components[3]
    core_base, core_turn, core_overlay, core_overlay_turn = components[4], components[5], components[6], components[7]
    struct_base, struct_turn, struct_overlay, struct_overlay_turn = components[8], components[9], components[10], components[11]
    for spec in _variant_specs(config):
        series, turnover, sleeve_base, sleeve_overlay = _variant_stream(
            spec,
            base_full,
            base_turn,
            base_wo,
            turn_wo,
            core_base,
            core_turn,
            core_overlay,
            core_overlay_turn,
            struct_base,
            struct_turn,
            struct_overlay,
            struct_overlay_turn,
        )
        sleeve_blocker = _group_blocker(alpha_blockers, config.core if spec.sleeve_group == "core_structure" else config.structure if spec.sleeve_group == "structure_level" else ())
        rows.append(_fold_row(fold, cost, spec, series, turnover, base_full, base_turn, sleeve_base, sleeve_overlay, sleeve_blocker))
    return rows


def _variant_outputs(alpha_data: dict[str, dict[str, pd.Series]], config: StructureSleeveAllocationConfig):
    components = _component_series(alpha_data, config)
    base_full, base_turn = components[0], components[1]
    base_wo, turn_wo = components[2], components[3]
    core_base, core_turn, core_overlay, core_overlay_turn = components[4], components[5], components[6], components[7]
    struct_base, struct_turn, struct_overlay, struct_overlay_turn = components[8], components[9], components[10], components[11]
    outputs = []
    for spec in _variant_specs(config):
        outputs.append(_variant_stream(spec, base_full, base_turn, base_wo, turn_wo, core_base, core_turn, core_overlay, core_overlay_turn, struct_base, struct_turn, struct_overlay, struct_overlay_turn))
    return tuple(outputs), components


def _variant_stream(
    spec: SleeveVariantSpec,
    base_full: pd.Series,
    base_turn: pd.Series,
    base_wo: pd.Series,
    turn_wo: pd.Series,
    core_base: pd.Series,
    core_turn: pd.Series,
    core_overlay: pd.Series,
    core_overlay_turn: pd.Series,
    struct_base: pd.Series,
    struct_turn: pd.Series,
    struct_overlay: pd.Series,
    struct_overlay_turn: pd.Series,
) -> tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
    if spec.kind == "full_baseline":
        return base_full, base_turn, pd.Series(dtype=float), pd.Series(dtype=float)
    if spec.kind == "subset_baseline":
        return base_wo, turn_wo, pd.Series(dtype=float), pd.Series(dtype=float)
    if spec.kind == "group_baseline":
        return (core_base, core_turn, core_base, core_base) if spec.sleeve_group == "core_structure" else (struct_base, struct_turn, struct_base, struct_base)
    if spec.kind == "group_overlay":
        return (core_overlay, core_overlay_turn, core_base, core_overlay) if spec.sleeve_group == "core_structure" else (struct_overlay, struct_overlay_turn, struct_base, struct_overlay)
    if spec.sleeve_group == "core_structure":
        delta = core_overlay.sub(core_base, fill_value=0.0)
        turn = core_overlay_turn.sub(core_turn, fill_value=0.0)
        return _blend_series(base_full, delta, spec.weight), _blend_series(base_turn, turn, spec.weight), core_base, core_overlay
    delta = struct_overlay.sub(struct_base, fill_value=0.0)
    turn = struct_overlay_turn.sub(struct_turn, fill_value=0.0)
    return _blend_series(base_full, delta, spec.weight), _blend_series(base_turn, turn, spec.weight), struct_base, struct_overlay


def _fold_row(fold, cost, spec, series, turnover, base_full, base_turn, sleeve_base, sleeve_overlay, sleeve_blocker):
    base = base_full
    base_return = _total_return_pct(base)
    variant_return = _total_return_pct(series)
    sleeve_delta = _total_return_pct(sleeve_overlay) - _total_return_pct(sleeve_base) if not sleeve_base.empty and not sleeve_overlay.empty else 0.0
    weighted_sleeve_delta = sleeve_delta * float(spec.weight)
    corr = float(base.corr(sleeve_overlay.sub(sleeve_base, fill_value=0.0))) if len(base) > 1 and not sleeve_base.empty and not sleeve_overlay.empty else 0.0
    if pd.isna(corr):
        corr = 0.0
    return {
        "variant": spec.variant_id,
        "variant_kind": spec.kind,
        "sleeve_group": spec.sleeve_group,
        "sleeve_weight": float(spec.weight),
        "fold": fold.fold,
        "cost_bps": float(cost),
        "train_start": str(fold.train_index[0].date()),
        "train_end": str(fold.train_index[-1].date()),
        "test_start": str(fold.test_index[0].date()),
        "test_end": str(fold.test_index[-1].date()),
        "baseline_return_pct": base_return,
        "variant_return_pct": variant_return,
        "delta_return_pct": variant_return - base_return,
        "sleeve_baseline_return_pct": _total_return_pct(sleeve_base) if not sleeve_base.empty else 0.0,
        "sleeve_overlay_return_pct": _total_return_pct(sleeve_overlay) if not sleeve_overlay.empty else 0.0,
        "sleeve_delta_return_pct": sleeve_delta,
        "weighted_sleeve_delta_return_pct": weighted_sleeve_delta,
        "weighted_sleeve_net_blocker_value": float(sleeve_blocker.get("net_blocker_value", 0.0)) * float(spec.weight),
        "base_sleeve_corr": corr,
        "blend_residual_pct": variant_return - (base_return + weighted_sleeve_delta),
        "average_exposure": 1.0 if spec.kind in {"group_baseline", "group_overlay"} else float(spec.weight),
        "turnover": float(turnover.mean()) if not turnover.empty else 0.0,
        "return_pct": variant_return,
        "cagr_pct": _cagr_pct(series),
        "ann_vol_pct": _annual_vol_pct(series),
        "ann_sharpe": _annual_sharpe(series),
        "max_drawdown_pct": _max_drawdown_pct(series),
        "sleeve_net_blocker_value": float(sleeve_blocker.get("net_blocker_value", 0.0)),
    }

def _daily_rows(fold, cost, alpha_data, config):
    rows = []
    outputs, _ = _variant_outputs(alpha_data, config)
    for spec, (series, turnover, _, _) in zip(_variant_specs(config), outputs, strict=False):
        for date, value in series.items():
            rows.append({"variant": spec.variant_id, "cost_bps": float(cost), "fold": fold.fold, "date": date, "returns": float(value), "turnover": float(turnover.reindex(series.index).fillna(0.0).get(date, 0.0)), "average_exposure": 1.0 if spec.kind in {"group_baseline", "group_overlay"} else float(spec.weight)})
    return rows


def _attribution_rows(fold, cost, alpha_data, alpha_blockers, config):
    outputs, _ = _variant_outputs(alpha_data, config)
    rows = []
    base_full = outputs[0][0] if outputs else pd.Series(dtype=float)
    for spec, (series, turnover, sleeve_base, sleeve_overlay) in zip(_variant_specs(config), outputs, strict=False):
        blocker = _group_blocker(alpha_blockers, config.core if spec.sleeve_group == "core_structure" else config.structure if spec.sleeve_group == "structure_level" else ())
        sleeve_delta = _total_return_pct(sleeve_overlay) - _total_return_pct(sleeve_base) if not sleeve_base.empty and not sleeve_overlay.empty else 0.0
        weighted_sleeve_delta = sleeve_delta * float(spec.weight)
        corr = float(base_full.corr(sleeve_overlay.sub(sleeve_base, fill_value=0.0))) if len(base_full) > 1 and not sleeve_base.empty and not sleeve_overlay.empty else 0.0
        if pd.isna(corr):
            corr = 0.0
        rows.append({
            "variant": spec.variant_id,
            "cost_bps": float(cost),
            "fold": fold.fold,
            "variant_return_pct": _total_return_pct(series),
            "baseline_return_pct": _total_return_pct(base_full) if not base_full.empty else 0.0,
            "sleeve_baseline_return_pct": _total_return_pct(sleeve_base) if not sleeve_base.empty else 0.0,
            "sleeve_overlay_return_pct": _total_return_pct(sleeve_overlay) if not sleeve_overlay.empty else 0.0,
            "sleeve_delta_return_pct": sleeve_delta,
            "weighted_sleeve_delta_return_pct": weighted_sleeve_delta,
            "weighted_sleeve_net_blocker_value": float(blocker.get("net_blocker_value", 0.0)) * float(spec.weight),
            "base_sleeve_corr": corr,
            "blend_residual_pct": _total_return_pct(series) - (_total_return_pct(base_full) + weighted_sleeve_delta) if not base_full.empty else 0.0,
            "sleeve_net_blocker_value": float(blocker.get("net_blocker_value", 0.0)),
        })
    return rows


def _component_series(alpha_data, config):
    base_full, base_turn = _group_series(alpha_data, config.alphas, overlay=False)
    base_wo, turn_wo = _group_series(alpha_data, tuple(a for a in config.alphas if a not in set(config.structure)), overlay=False)
    core_base, core_turn = _group_series(alpha_data, config.core, overlay=False)
    core_overlay, core_overlay_turn = _group_series(alpha_data, config.core, overlay=True)
    struct_base, struct_turn = _group_series(alpha_data, config.structure, overlay=False)
    struct_overlay, struct_overlay_turn = _group_series(alpha_data, config.structure, overlay=True)
    return base_full, base_turn, base_wo, turn_wo, core_base, core_turn, core_overlay, core_overlay_turn, struct_base, struct_turn, struct_overlay, struct_overlay_turn


def _aggregate_attribution(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    grouped = frame.groupby(["variant", "cost_bps"], sort=False)
    rows = []
    for keys, group in grouped:
        rows.append(
            {
                "variant": str(keys[0]),
                "cost_bps": float(keys[1]),
                "fold_count": int(group["fold"].nunique()),
                "mean_base_return_pct": float(group["baseline_return_pct"].mean()),
                "mean_variant_return_pct": float(group["variant_return_pct"].mean()),
                "mean_sleeve_baseline_return_pct": float(group["sleeve_baseline_return_pct"].mean()),
                "mean_sleeve_overlay_return_pct": float(group["sleeve_overlay_return_pct"].mean()),
                "mean_sleeve_delta_return_pct": float(group["sleeve_delta_return_pct"].mean()),
                "mean_weighted_sleeve_delta_return_pct": float(group["weighted_sleeve_delta_return_pct"].mean()),
                "mean_base_sleeve_corr": float(group["base_sleeve_corr"].mean()),
                "mean_blend_residual_pct": float(group["blend_residual_pct"].mean()),
                "net_blocker_value": float(group["weighted_sleeve_net_blocker_value"].sum()),
                "sleeve_net_blocker_value": float(group["sleeve_net_blocker_value"].mean()),
            }
        )
    return pd.DataFrame(rows)


def _metrics(daily: pd.DataFrame, folds: pd.DataFrame) -> pd.DataFrame:
    if daily.empty:
        return pd.DataFrame()
    rows = []
    baseline_map = {
        float(cost): _total_return_pct(frame.sort_values("date")["returns"])
        for cost, frame in daily.loc[daily["variant"].eq("full_baseline")].groupby("cost_bps", sort=False)
    }
    for keys, frame in daily.groupby(["variant", "cost_bps"], sort=False):
        variant, cost = str(keys[0]), float(keys[1])
        ordered = frame.sort_values("date")
        fold_frame = folds.loc[folds["variant"].eq(variant) & folds["cost_bps"].eq(cost)]
        baseline = baseline_map.get(cost, 0.0)
        rows.append(
            {
                "variant": variant,
                "cost_bps": cost,
                "baseline_return_pct": float(baseline),
                "return_pct": _total_return_pct(ordered["returns"]),
                "delta_return_pct": _total_return_pct(ordered["returns"]) - float(baseline),
                "cagr_pct": _cagr_pct(ordered["returns"]),
                "ann_vol_pct": _annual_vol_pct(ordered["returns"]),
                "ann_sharpe": _annual_sharpe(ordered["returns"]),
                "max_drawdown_pct": _max_drawdown_pct(ordered["returns"]),
                "negative_fold_rate": float(fold_frame["variant_return_pct"].lt(0.0).mean()) if not fold_frame.empty else 0.0,
                "worst_fold_sharpe": float(fold_frame["ann_sharpe"].min()) if not fold_frame.empty else 0.0,
                "latest_fold_sharpe": float(fold_frame.sort_values("fold").iloc[-1]["ann_sharpe"]) if not fold_frame.empty else 0.0,
                "average_exposure": float(fold_frame["average_exposure"].mean()) if not fold_frame.empty else 0.0,
                "turnover": float(ordered["turnover"].mean()) if not ordered.empty else 0.0,
            }
        )
    return pd.DataFrame(rows)


def _tail(folds: pd.DataFrame) -> pd.DataFrame:
    if folds.empty:
        return pd.DataFrame()
    frame = pd.DataFrame([_tail_row(str(keys[0]), float(keys[1]), group) for keys, group in folds.groupby(["variant", "cost_bps"], sort=False)])
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
        "fold_count": int(frame["fold"].nunique()),
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


def _event_split(folds: pd.DataFrame, source_dir: Path) -> pd.DataFrame:
    labels = _event_labels(source_dir)
    merged = folds.assign(event_label=folds["fold"].map(labels).fillna("unmatched"))
    rows = []
    for keys, frame in merged.groupby(["variant", "cost_bps"], sort=False):
        variant, cost = str(keys[0]), float(keys[1])
        stress = frame.loc[~frame["event_label"].eq("unmatched")]
        ordinary = frame.loc[frame["event_label"].eq("unmatched")]
        for split, group in (("known_stress", stress), ("unmatched", ordinary), ("all", frame)):
            rows.append({"variant": variant, "cost_bps": cost, "split": split, "fold_count": int(group["fold"].nunique()), "mean_delta": float(group["delta_return_pct"].mean()) if not group.empty else 0.0, "net_delta": float(group["delta_return_pct"].sum()) if not group.empty else 0.0, "average_exposure": float(group["average_exposure"].mean()) if not group.empty else 0.0})
    return pd.DataFrame(rows)


def _concentration(folds: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame([fold_concentration_row(str(keys[0]), float(keys[1]), group) for keys, group in folds.groupby(["variant", "cost_bps"], sort=False)])


def _cost(tail: pd.DataFrame) -> pd.DataFrame:
    return tail[["variant", "cost_bps", "mean_delta_vs_baseline", "left_tail_delta", "right_tail_retention", "ci_low"]].copy()


def _variant_specs(config: StructureSleeveAllocationConfig) -> tuple[SleeveVariantSpec, ...]:
    return (
        SleeveVariantSpec("full_baseline", "full_baseline", "none", 0.0),
        SleeveVariantSpec("full_baseline_without_structure", "subset_baseline", "non_structure", 0.0),
        SleeveVariantSpec("core_structure_baseline_sleeve", "group_baseline", "core_structure", 1.0),
        SleeveVariantSpec("core_structure_overlay_sleeve", "group_overlay", "core_structure", 1.0),
        SleeveVariantSpec("full_structure_baseline_sleeve", "group_baseline", "structure_level", 1.0),
        SleeveVariantSpec("full_structure_overlay_sleeve", "group_overlay", "structure_level", 1.0),
        *tuple(SleeveVariantSpec(f"full_baseline_plus_{int(weight * 100)}pct_core_overlay_sleeve", "blend", "core_structure", weight) for weight in config.core_weights),
        *tuple(SleeveVariantSpec(f"full_baseline_plus_{int(weight * 100)}pct_full_structure_overlay_sleeve", "blend", "structure_level", weight) for weight in config.full_structure_weights),
    )


def _select(panel, bundle, intensity, future, fold, cost, config, cache) -> dict[str, float]:
    best: dict[str, float] | None = None
    best_score = -float("inf")
    for quantile in config.threshold_quantiles:
        threshold = _threshold(intensity.reindex(fold.train_index), quantile, "high")
        for params in config.multiplier_grid:
            score = _score(panel, bundle, intensity, future, fold, cost, config, threshold, params, cache)
            if score > best_score:
                best, best_score = {"threshold": threshold, "quantile": quantile, **params}, score
    return best or {"threshold": 0.0, "quantile": 0.0, "down": 1.0, "up": 1.0}


def _score(panel, bundle, intensity, future, fold, cost, config, threshold, params, cache) -> float:
    result = _baseline_result(panel, bundle, future, fold.train_index, cost, config, cache)
    base = _daily(result.net_return, config.horizon)
    mult = _multiplier(intensity.reindex(fold.train_index), _hypothesis(bundle.alpha), threshold, params)
    variant = base.mul(mult, fill_value=0.0)
    left = (variant - base).loc[base.le(base.quantile(0.25))].mean() * 100.0
    return float(_total_return_pct(variant) - _total_return_pct(base) + max(0.0, left))


def _hypothesis(alpha: str):
    from research.projects.price_action_strategy_lab.narrow_falsification import NarrowHypothesis

    return NarrowHypothesis(alpha, (alpha,), "breadth_risk_off", "high", "soft_aggressive", (0.5, 0.6, 0.7, 0.8), (
        {"down": 0.25, "up": 1.10},
        {"down": 0.25, "up": 1.25},
        {"down": 0.50, "up": 1.10},
        {"down": 0.50, "up": 1.25},
    ))


def _group_series(alpha_data: dict[str, dict[str, pd.Series]], alphas: tuple[str, ...], overlay: bool) -> tuple[pd.Series, pd.Series]:
    if not alphas:
        empty = pd.Series(dtype=float)
        return empty, empty
    series = [alpha_data[a]["overlay" if overlay and "overlay" in alpha_data[a] else "baseline"] for a in alphas]
    turns = [alpha_data[a]["overlay_turnover" if overlay and "overlay_turnover" in alpha_data[a] else "baseline_turnover"] for a in alphas]
    return _combine(series), _combine(turns)


def _group_blocker(blockers: dict[str, dict[str, float | int]], alphas: tuple[str, ...]) -> dict[str, float]:
    rows = [blockers[a] for a in alphas if a in blockers]
    if not rows:
        return {"net_blocker_value": 0.0}
    keys = rows[0].keys()
    return {str(key): float(sum(float(row.get(key, 0.0)) for row in rows)) for key in keys}


def _combine(series: list[pd.Series]) -> pd.Series:
    return pd.concat(series, axis=1).mean(axis=1).fillna(0.0) if series else pd.Series(dtype=float)


def _blend_series(base: pd.Series, delta: pd.Series, weight: float) -> pd.Series:
    return base.add(delta.mul(weight, fill_value=0.0), fill_value=0.0)


def _bootstrap(values: pd.Series) -> tuple[float, float]:
    clean = values.dropna().to_numpy(dtype=float)
    if clean.size == 0:
        return 0.0, 0.0
    rng = np.random.default_rng(17)
    draws = rng.choice(clean, size=(2000, clean.size), replace=True).mean(axis=1)
    return float(np.quantile(draws, 0.05)), float(np.quantile(draws, 0.95))


def _paired_t(values: pd.Series) -> tuple[float, float]:
    clean = values.dropna().to_numpy(dtype=float)
    if clean.size < 2 or float(pd.Series(clean).std(ddof=1)) == 0.0:
        return 0.0, 1.0
    from scipy.stats import ttest_1samp  # type: ignore[import-untyped]

    result = ttest_1samp(clean, 0.0)
    return float(result.statistic), float(result.pvalue)


def _bh(values: pd.Series) -> pd.Series:
    pvals = values.fillna(1.0).to_numpy(dtype=float)
    order, adjusted, running = pvals.argsort(), pd.Series(index=values.index, dtype=float), 1.0
    for rank, idx in enumerate(order[::-1], start=1):
        running = min(running, pvals[idx] * len(pvals) / (len(pvals) - rank + 1))
        adjusted.iloc[idx] = running
    return adjusted


def _narrow(config: StructureSleeveAllocationConfig):
    from research.projects.price_action_strategy_lab.narrow_falsification import NarrowFalsificationConfig, NarrowHypothesis

    hypothesis = NarrowHypothesis("sleeve", ("support_trendline_position_20",), "breadth_risk_off", "high", "soft_aggressive", config.threshold_quantiles, config.multiplier_grid)
    return NarrowFalsificationConfig((hypothesis,), config.cache_dir, config.report_root, config.source_report_dir, mode=config.mode, horizon=config.horizon, cost_bps=config.cost_bps, train_size_days=config.train_size_days, test_size_days=config.test_size_days, step_size_days=config.step_size_days, lookahead_days=config.lookahead_days, max_folds=config.max_folds, top_quantile=config.top_quantile, min_names=config.min_names, max_workers=config.max_workers, gpu=config.gpu)


def _config(raw: dict[str, Any]) -> StructureSleeveAllocationConfig:
    compute = dict(raw.get("compute", {}))
    backtests = dict(raw.get("backtests", {}))
    walk = dict(raw.get("walk_forward_validation", {}))
    gpu = dict(raw.get("gpu", {}))
    groups = {str(item["group_id"]): tuple(str(alpha) for alpha in item.get("alphas", ())) for item in raw.get("overlay_groups", ())}
    sleeve = dict(raw.get("sleeve_allocation", {}))
    return StructureSleeveAllocationConfig(
        alphas=tuple(str(alpha) for alpha in raw.get("alphas", ())),
        structure=groups.get("structure_level", ()),
        core=groups.get("core_structure", ()),
        cache_dir=Path(str(compute.get("cache_dir"))),
        report_root=Path(str(compute.get("report_root"))),
        source_report_dir=Path(str(compute.get("source_report_dir"))),
        cost_bps=tuple(float(item) for item in backtests.get("cost_bps", (10.0, 25.0, 50.0))),
        core_weights=tuple(float(item) for item in sleeve.get("core_weights", (0.05, 0.10, 0.15, 0.20))),
        full_structure_weights=tuple(float(item) for item in sleeve.get("full_structure_weights", (0.10, 0.20))),
        mode=str(backtests.get("mode", "ranked_long_only")),
        horizon=int(backtests.get("horizon", 10)),
        train_size_days=int(walk.get("train_size_days", 126)),
        test_size_days=int(walk.get("test_size_days", 21)),
        step_size_days=int(walk.get("step_size_days", 21)),
        lookahead_days=int(walk.get("lookahead_days", 10)),
        max_folds=int(walk.get("max_folds", 24)),
        top_quantile=float(backtests.get("top_quantile", 0.8)),
        min_names=int(backtests.get("min_active_names", 20)),
        threshold_quantiles=tuple(float(item) for item in sleeve.get("threshold_quantiles", (0.5, 0.6, 0.7, 0.8))),
        multiplier_grid=tuple(dict(item) for item in sleeve.get("multiplier_grid", ({"down": 0.25, "up": 1.10}, {"down": 0.25, "up": 1.25}, {"down": 0.50, "up": 1.10}, {"down": 0.50, "up": 1.25}))),
        max_workers=int(compute.get("max_workers") or 1),
        gpu=GpuConfig(enabled=bool(gpu.get("enabled", False)), backend=str(gpu.get("backend") or "auto")),
    )


def _paths(report_dir: Path) -> dict[str, Path]:
    prefix = "breadth_risk_off_structure_sleeve"
    return {"metrics": report_dir / f"{prefix}_metrics.csv", "tail": report_dir / f"{prefix}_tail_diagnostics.csv", "attribution": report_dir / f"{prefix}_attribution.csv", "event": report_dir / f"{prefix}_event_split.csv", "concentration": report_dir / f"{prefix}_fold_concentration.csv", "cost": report_dir / f"{prefix}_cost_stress.csv", "markdown": report_dir / f"{prefix}_report.md"}


def _markdown(result: StructureSleeveAllocationResult) -> str:
    lines = ["# Breadth Risk-Off Structure Sleeve Allocation", "", "## Metrics", "", markdown_table(result.metrics, max_rows=40), "", "## Tail", "", markdown_table(result.tail, max_rows=40), "", "## Attribution", "", markdown_table(result.attribution, max_rows=40), "", "## Event Split", "", markdown_table(result.event, max_rows=40), "", "## Fold Concentration", "", markdown_table(result.concentration, max_rows=40), "", "## Decision", "", _decision(result.metrics, result.tail), ""]
    return "\n".join(lines)


def _decision(metrics: pd.DataFrame, tail: pd.DataFrame) -> str:
    if metrics.empty or tail.empty:
        return "Reject: missing sleeve allocation diagnostics."
    target_pool = metrics.loc[metrics["variant"].str.startswith("full_baseline_plus_") & metrics["cost_bps"].eq(10.0)]
    if target_pool.empty:
        return "Reject: missing weighted sleeve candidate rows."
    target = target_pool.sort_values(["ann_sharpe", "return_pct"], ascending=[False, False]).iloc[0]
    variant = str(target["variant"])
    baseline_10 = metrics.loc[metrics["variant"].eq("full_baseline") & metrics["cost_bps"].eq(10.0)]
    baseline_25 = metrics.loc[metrics["variant"].eq("full_baseline") & metrics["cost_bps"].eq(25.0)]
    target_25 = metrics.loc[metrics["variant"].eq(variant) & metrics["cost_bps"].eq(25.0)]
    tail_10 = tail.loc[tail["variant"].eq(variant) & tail["cost_bps"].eq(10.0)]
    tail_25 = tail.loc[tail["variant"].eq(variant) & tail["cost_bps"].eq(25.0)]
    if baseline_10.empty or baseline_25.empty or target_25.empty or tail_10.empty or tail_25.empty:
        return "Reject: missing robustness rows for the sleeve candidate."
    t10, b10, t25, b25 = target, baseline_10.iloc[0], target_25.iloc[0], baseline_25.iloc[0]
    tail10, tail25 = tail_10.iloc[0], tail_25.iloc[0]
    if (
        float(t10["ann_sharpe"]) > float(b10["ann_sharpe"]) and
        float(t10["max_drawdown_pct"]) >= float(b10["max_drawdown_pct"]) and
        float(tail10["right_tail_retention"]) >= 0.95 and
        float(tail10["mean_delta_vs_baseline"]) > 0.0 and
        float(t25["ann_sharpe"]) > float(b25["ann_sharpe"]) and
        float(t25["max_drawdown_pct"]) >= float(b25["max_drawdown_pct"]) and
        float(tail25["right_tail_retention"]) >= 0.95 and
        float(tail25["mean_delta_vs_baseline"]) > 0.0
    ):
        return "Shadow-candidate research stage: the sleeve improves the portfolio at 10bps and survives 25bps."
    return "Research-only: sleeve allocation is informative, but full-portfolio improvement is not strong enough yet."


def _report_dir(root: Path) -> Path:
    return root / datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _ratio(numerator: float, denominator: float) -> float:
    return float(numerator / denominator) if denominator else 0.0
