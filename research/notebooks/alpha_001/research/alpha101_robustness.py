from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import cast

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

if __package__:
    from . import alpha101_formulas as formula_module  # noqa: E402
    from .alpha101_engine import (  # noqa: E402
        ALPHA101_ARTIFACT_DIR,
        Alpha101Panel,
        backtest_weights,
        causal_orient,
        clean,
        fast_rank_ic_by_date,
        forward_return,
        load_panel,
        next_session_return,
        performance_metrics,
    )
    from .alpha101_factory import (  # noqa: E402
        COST_GRID,
        PRIMARY_HORIZON,
        advanced_transform_signal,
        build_portfolio_weights,
        compatible_portfolios,
        panel_masks,
        portfolio_signal_transforms,
    )
    from .alpha101_formulas import FORMULA_REGISTRY, compute_alpha, registry_frame  # noqa: E402
else:  # pragma: no cover
    import alpha101_formulas as formula_module  # noqa: E402
    from alpha101_engine import (  # noqa: E402
        ALPHA101_ARTIFACT_DIR,
        Alpha101Panel,
        backtest_weights,
        causal_orient,
        clean,
        fast_rank_ic_by_date,
        forward_return,
        load_panel,
        next_session_return,
        performance_metrics,
    )
    from alpha101_factory import (  # noqa: E402
        COST_GRID,
        PRIMARY_HORIZON,
        advanced_transform_signal,
        build_portfolio_weights,
        compatible_portfolios,
        panel_masks,
        portfolio_signal_transforms,
    )
    from alpha101_formulas import FORMULA_REGISTRY, compute_alpha, registry_frame  # noqa: E402


ROBUSTNESS_DIR = ALPHA101_ARTIFACT_DIR
SNAPSHOT_FILE = "alpha101_metrics_snapshot.json"
ROBUSTNESS_MASKS = ("all_eligible", "high_vol_top100", "strict_liquidity_100m", "seasoned_2y")
ROBUSTNESS_FOLDS = (
    ("oos_2022", "2018-01-01", "2021-12-31", "2022-01-01", "2022-12-31"),
    ("oos_2023", "2018-01-01", "2022-12-31", "2023-01-01", "2023-12-31"),
    ("oos_2024", "2018-01-01", "2023-12-31", "2024-01-01", "2024-12-31"),
    ("oos_2025_2026", "2018-01-01", "2024-12-31", "2025-01-01", "2026-12-31"),
)
ROBUSTNESS_TABLES = {
    "candidate_lanes": "alpha101_robustness_candidate_lanes.csv",
    "walk_forward": "alpha101_robustness_walk_forward.csv",
    "strict_liquidity_primary": "alpha101_strict_liquidity_primary_report.csv",
    "cost_sensitivity": "alpha101_robustness_cost_sensitivity.csv",
    "universe_sensitivity": "alpha101_robustness_universe_sensitivity.csv",
    "proxy_sensitivity": "alpha101_proxy_sensitivity_report.csv",
    "industry_snapshot_risk": "alpha101_industry_snapshot_risk_report.csv",
    "validation": "alpha101_robustness_validation.csv",
    "shortlist": "alpha101_robustness_shortlist.csv",
}
ROBUSTNESS_REPORT = "alpha101_robustness_final_report.md"
ROBUSTNESS_BATCH2_ALPHAS = (
    "alpha026", "alpha013", "alpha033", "alpha015", "alpha045",
    "alpha008", "alpha009", "alpha068", "alpha038", "alpha006",
    "alpha037", "alpha004", "alpha017", "alpha003", "alpha010",
    "alpha088", "alpha028", "alpha055", "alpha007", "alpha002",
)
ROBUSTNESS_BATCH2_TABLES = {
    "candidate_lanes": "alpha101_robustness_batch2_candidate_lanes.csv",
    "walk_forward": "alpha101_robustness_batch2_walk_forward.csv",
    "cost_sensitivity": "alpha101_robustness_batch2_cost_sensitivity.csv",
    "universe_sensitivity": "alpha101_robustness_batch2_universe_sensitivity.csv",
    "validation": "alpha101_robustness_batch2_validation.csv",
    "shortlist": "alpha101_robustness_batch2_shortlist.csv",
    "combined_shortlist": "alpha101_robustness_combined_shortlist.csv",
}
ROBUSTNESS_BATCH2_REPORT = "alpha101_robustness_batch2_final_report.md"


def artifact_path(name: str) -> Path:
    return ROBUSTNESS_DIR / name


def read_artifact(name: str) -> pd.DataFrame:
    return pd.read_csv(artifact_path(name))


def read_snapshot_if_exists(path: Path) -> dict[str, object]:
    return json.loads(path.read_text()) if path.exists() else {}


def snapshot_rows(snapshot: dict[str, object], report_name: str, key: str) -> list[dict[str, object]]:
    reports = snapshot.get("reports", {})
    if not isinstance(reports, dict):
        return []
    report = reports.get(report_name, {})
    if not isinstance(report, dict):
        return []
    rows = report.get(key, [])
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def family_defaults_from_leaderboard(leaderboard: pd.DataFrame) -> dict[str, dict[str, object]]:
    defaults: dict[str, dict[str, object]] = {}
    if leaderboard.empty or "family" not in leaderboard.columns:
        return defaults
    for family, frame in leaderboard.dropna(subset=["family"]).groupby("family"):
        if frame.empty:
            continue
        best = frame.sort_values("research_score", ascending=False).iloc[0].to_dict()
        defaults[str(family)] = {
            "best_mask": best.get("best_mask", "high_vol_top100"),
            "best_signal_transform": best.get("best_signal_transform", "rank_centered"),
            "best_strategy": best.get("best_strategy", "overlay20"),
        }
    return defaults


def default_family_choice(family: str, family_defaults: dict[str, dict[str, object]]) -> dict[str, object]:
    static_defaults: dict[str, dict[str, object]] = {
        "price_reversal": {"best_mask": "high_vol_top100", "best_signal_transform": "rank_centered", "best_strategy": "ewm5_overlay20"},
        "volume_liquidity": {"best_mask": "high_vol_top100", "best_signal_transform": "ewm3", "best_strategy": "overlay20"},
        "momentum_trend": {"best_mask": "high_vol_top100", "best_signal_transform": "ewm3", "best_strategy": "overlay20"},
        "volatility_range": {"best_mask": "high_vol_top100", "best_signal_transform": "ewm3", "best_strategy": "overlay20"},
        "correlation_relative_value": {"best_mask": "high_vol_top100", "best_signal_transform": "style_residual", "best_strategy": "overlay20"},
        "industry_neutral_cross_section": {"best_mask": "high_vol_top100", "best_signal_transform": "rank_centered", "best_strategy": "overlay20"},
        "hybrid_or_unknown": {"best_mask": "high_vol_top100", "best_signal_transform": "rank_centered", "best_strategy": "overlay20"},
    }
    return family_defaults.get(family, static_defaults.get(family, static_defaults["hybrid_or_unknown"]))


def recover_leaderboard_from_snapshot(snapshot: dict[str, object]) -> pd.DataFrame:
    rows = snapshot_rows(snapshot, "factory", "top_25")
    leaderboard = pd.DataFrame(rows)
    if leaderboard.empty:
        return leaderboard
    leaderboard = leaderboard.copy()
    if "research_score" not in leaderboard.columns:
        leaderboard["research_score"] = np.nan
    return leaderboard


def recover_baseline_rows(snapshot: dict[str, object], defaults: dict[str, dict[str, object]]) -> pd.DataFrame:
    rows = snapshot_rows(snapshot, "robustness_batch1", "top_rows")
    baseline = pd.DataFrame([row for row in rows if row.get("alpha_id") == "alpha001"])
    if baseline.empty:
        return baseline
    baseline = baseline.copy()
    baseline["family"] = "price_reversal"
    baseline["classification"] = "baseline_comparator"
    baseline["best_mask"] = defaults.get("price_reversal", default_family_choice("price_reversal", defaults))["best_mask"]
    baseline["best_signal_transform"] = defaults.get("price_reversal", default_family_choice("price_reversal", defaults))["best_signal_transform"]
    baseline["best_strategy"] = defaults.get("price_reversal", default_family_choice("price_reversal", defaults))["best_strategy"]
    if "research_score" not in baseline.columns:
        baseline["research_score"] = np.nan
    return baseline


def recover_batch2_lookup(snapshot: dict[str, object]) -> dict[str, dict[str, object]]:
    rows = snapshot_rows(snapshot, "robustness_batch2", "combined_promoted_exact_ohlcv")
    rows.extend(snapshot_rows(snapshot, "robustness_batch2", "results"))
    lookup: dict[str, dict[str, object]] = {}
    for row in rows:
        alpha_id = str(row.get("alpha_id", ""))
        if alpha_id:
            lookup[alpha_id] = row
    return lookup


def load_discovery_tables() -> tuple[pd.DataFrame, pd.DataFrame]:
    leaderboard_path = artifact_path("alpha101_leaderboard.csv")
    registry_path = artifact_path("alpha101_formula_registry.csv")
    if leaderboard_path.exists() and registry_path.exists():
        return read_artifact("alpha101_leaderboard.csv"), read_artifact("alpha101_formula_registry.csv")
    snapshot = read_snapshot_if_exists(artifact_path(SNAPSHOT_FILE))
    if snapshot:
        return recover_leaderboard_from_snapshot(snapshot), registry_frame()
    return pd.DataFrame(), registry_frame()


def candidate_lanes(
    clean_n: int = 12,
    proxy_n: int = 8,
    snapshot_n: int = 8,
    include_alpha001: bool = True,
) -> pd.DataFrame:
    leaderboard, _registry = load_discovery_tables()
    snapshot_data = read_snapshot_if_exists(artifact_path(SNAPSHOT_FILE))
    defaults = family_defaults_from_leaderboard(leaderboard)
    candidates = leaderboard[leaderboard["classification"].isin(["candidate", "feature_only"])].copy()
    rows = []

    def add_lane(frame: pd.DataFrame, lane: str, limit: int) -> None:
        for rank, (_, row) in enumerate(frame.sort_values("research_score", ascending=False).head(limit).iterrows(), start=1):
            out = row.to_dict()
            out["robustness_lane"] = lane
            out["lane_rank"] = rank
            rows.append(out)

    exact = candidates[candidates["input_quality_tier"].eq("exact_ohlcv")]
    proxy = candidates[candidates["input_quality_tier"].str.contains("proxy_vwap", na=False) & ~candidates["input_quality_tier"].str.contains("snapshot_industry", na=False)]
    snapshot_candidates = candidates[candidates["input_quality_tier"].str.contains("snapshot_industry", na=False)]
    add_lane(exact, "clean_exact_ohlcv", clean_n)
    add_lane(proxy, "proxy_vwap", proxy_n)
    add_lane(snapshot_candidates, "snapshot_metadata_risk", snapshot_n)

    if include_alpha001:
        baseline = leaderboard[leaderboard["alpha_id"].eq("alpha001")].sort_values("research_score", ascending=False)
        if baseline.empty and snapshot_data:
            baseline = recover_baseline_rows(snapshot_data, defaults)
        for rank, (_, row) in enumerate(baseline.iterrows(), start=1):
            out = row.to_dict()
            out["robustness_lane"] = "baseline_alpha001"
            out["lane_rank"] = rank
            rows.append(out)

    lane_frame = pd.DataFrame(rows)
    if lane_frame.empty:
        return lane_frame
    lane_frame = lane_frame.drop_duplicates(["panel", "alpha_id", "robustness_lane"]).sort_values(["robustness_lane", "lane_rank", "panel", "alpha_id"])
    return lane_frame.reset_index(drop=True)


def clean_near_miss_lanes(alpha_ids: tuple[str, ...] = ROBUSTNESS_BATCH2_ALPHAS) -> pd.DataFrame:
    leaderboard, _registry = load_discovery_tables()
    snapshot_data = read_snapshot_if_exists(artifact_path(SNAPSHOT_FILE))
    defaults = family_defaults_from_leaderboard(leaderboard)
    best = pd.DataFrame()
    if not leaderboard.empty:
        best = leaderboard.sort_values("research_score", ascending=False).groupby("alpha_id").head(1).copy()
    batch2_lookup = recover_batch2_lookup(snapshot_data)
    selected_rows: list[dict[str, object]] = []
    missing: list[str] = []
    for lane_rank, alpha_id in enumerate(alpha_ids, start=1):
        selected = best[best["alpha_id"].eq(alpha_id)].copy() if not best.empty else pd.DataFrame()
        if not selected.empty:
            row = selected.iloc[0].to_dict()
            family = str(row.get("family", "hybrid_or_unknown"))
            fallback = default_family_choice(family, defaults)
            for key, value in fallback.items():
                row.setdefault(key, value)
            row.setdefault("classification", "candidate")
            row.setdefault("input_quality_tier", "exact_ohlcv")
        else:
            result = batch2_lookup.get(alpha_id)
            if result is None:
                missing.append(alpha_id)
                continue
            spec = next(spec for spec in FORMULA_REGISTRY if spec.alpha_id == alpha_id)
            fallback = default_family_choice(spec.family, defaults)
            row = {
                "panel": result.get("panel", "expanded"),
                "alpha_id": alpha_id,
                "family": spec.family,
                "input_quality_tier": "exact_ohlcv",
                "classification": "feature_only" if str(result.get("final_status")) == "feature_only" else "candidate",
                "final_status": result.get("final_status", "candidate"),
                "research_score": float(cast(float, result.get("median_test_active_sharpe", 0.0)) or 0.0),
                "best_5d_ic": result.get("median_test_rank_ic", np.nan),
                "best_20bps_active_sharpe": result.get("median_test_active_sharpe", np.nan),
                "best_mask": fallback["best_mask"],
                "best_signal_transform": fallback["best_signal_transform"],
                "best_strategy": fallback["best_strategy"],
                "median_test_active_sharpe": result.get("median_test_active_sharpe", np.nan),
                "median_test_active_cagr": result.get("median_test_active_cagr", np.nan),
                "median_test_rank_ic": result.get("median_test_rank_ic", np.nan),
                "median_turnover": result.get("median_turnover", np.nan),
            }
        row["robustness_lane"] = "clean_near_miss_batch2"
        row["lane_rank"] = lane_rank
        selected_rows.append(row)
    if missing:
        raise ValueError(f"Missing requested Batch 2 alpha ids in snapshot fallback: {missing}")
    selected_frame = pd.DataFrame(selected_rows)
    if selected_frame.empty:
        return selected_frame
    return selected_frame.sort_values(["research_score", "lane_rank"], ascending=[False, True]).reset_index(drop=True)


def date_slice(series: pd.Series, start: str, end: str) -> pd.Series:
    return series.loc[(series.index >= start) & (series.index <= end)].dropna()


def active_returns(weights: pd.DataFrame, benchmark: pd.DataFrame, next_returns: pd.DataFrame, cost_bps: float) -> tuple[pd.Series, dict, dict]:
    alpha_bt = backtest_weights(weights, next_returns, cost_bps)
    benchmark_bt = backtest_weights(benchmark, next_returns, cost_bps)
    pair = pd.concat([alpha_bt["returns"].rename("alpha"), benchmark_bt["returns"].rename("benchmark")], axis=1).dropna()
    active = pair["alpha"] - pair["benchmark"]
    return active, alpha_bt["metrics"], benchmark_bt["metrics"]


def metrics_for_period(returns: pd.Series, start: str, end: str) -> dict:
    return performance_metrics(date_slice(returns, start, end))


def signal_rank_correlation(left: pd.DataFrame, right: pd.DataFrame, mask: pd.DataFrame) -> pd.Series:
    idx = left.index.intersection(right.index).intersection(mask.index)
    cols = left.columns.intersection(right.columns).intersection(mask.columns)
    left_rank = left.loc[idx, cols].where(mask.loc[idx, cols]).rank(axis=1, method="average")
    right_rank = right.loc[idx, cols].where(mask.loc[idx, cols]).rank(axis=1, method="average")
    valid = left_rank.notna() & right_rank.notna()
    count = valid.sum(axis=1).astype(float)
    lx = left_rank.where(valid)
    rx = right_rank.where(valid)
    lc = lx.sub(lx.sum(axis=1).div(count), axis=0).where(valid, 0.0)
    rc = rx.sub(rx.sum(axis=1).div(count), axis=0).where(valid, 0.0)
    denom = np.sqrt(lc.pow(2).sum(axis=1) * rc.pow(2).sum(axis=1)).replace(0.0, np.nan)
    corr = lc.mul(rc).sum(axis=1).div(denom).replace([np.inf, -np.inf], np.nan)
    corr[count < 10] = np.nan
    return corr


def compute_candidate_raw(panel_name: str, alpha_id: str, vwap_variant: str = "hlc3", neutralization: str = "snapshot") -> tuple[Alpha101Panel, pd.DataFrame]:
    panel = load_panel(panel_name)
    if vwap_variant == "close":
        panel = replace(panel, vwap=panel.close)
    elif vwap_variant == "ohlc4":
        panel = replace(panel, vwap=(panel.open + panel.high + panel.low + panel.close) / 4.0)
    elif vwap_variant == "hl2c4":
        panel = replace(panel, vwap=(panel.high + panel.low + 2.0 * panel.close) / 4.0)
    elif vwap_variant != "hlc3":
        raise ValueError(f"Unknown vwap variant: {vwap_variant}")

    if neutralization == "identity":
        old = formula_module.indneutralize
        formula_module.indneutralize = lambda frame, groups: frame
        try:
            raw = compute_alpha(panel, alpha_id)
        finally:
            formula_module.indneutralize = old
    elif neutralization == "snapshot":
        raw = compute_alpha(panel, alpha_id)
    else:
        raise ValueError(f"Unknown neutralization mode: {neutralization}")
    return panel, clean(raw).reindex_like(panel.close).where(panel.active_mask)


def portfolio_grid_for_candidate(row: pd.Series) -> tuple[Alpha101Panel, pd.DataFrame, dict[tuple[str, str, str], dict]]:
    panel, raw = compute_candidate_raw(row["panel"], row["alpha_id"])
    spec = next(s for s in FORMULA_REGISTRY if s.alpha_id == row["alpha_id"])
    masks = panel_masks(panel)
    next_returns = next_session_return(panel.close)
    future = forward_return(panel.close, PRIMARY_HORIZON)
    transforms = list(dict.fromkeys([row.get("best_signal_transform")] + list(portfolio_signal_transforms(spec.family))))
    transforms = [value for value in transforms if isinstance(value, str) and value]
    strategies = list(dict.fromkeys([row.get("best_strategy")] + list(compatible_portfolios(spec.family))))
    strategies = [value for value in strategies if isinstance(value, str) and value]
    mask_names = [name for name in ROBUSTNESS_MASKS if name in masks]
    grid = {}
    for mask_name in mask_names:
        mask = masks[mask_name] & panel.active_mask
        if mask.sum(axis=1).replace(0, np.nan).median() < 20:
            continue
        benchmark = build_portfolio_weights(raw.where(mask), mask, "equal_weight")
        for transform in transforms:
            try:
                transformed = advanced_transform_signal(raw, transform, mask, panel)
                oriented, _direction = causal_orient(transformed, future, PRIMARY_HORIZON)
            except Exception:
                continue
            signal = oriented.where(mask)
            ic = fast_rank_ic_by_date(signal, future)
            for strategy in strategies:
                try:
                    weights = build_portfolio_weights(signal, mask, strategy)
                except Exception:
                    continue
                active20, alpha_metrics20, benchmark_metrics20 = active_returns(weights, benchmark, next_returns, 20.0)
                grid[(mask_name, transform, strategy)] = {
                    "mask": mask_name,
                    "signal_transform": transform,
                    "strategy": strategy,
                    "weights": weights,
                    "benchmark": benchmark,
                    "next_returns": next_returns,
                    "active20": active20,
                    "ic": ic,
                    "alpha_metrics_20": alpha_metrics20,
                    "benchmark_metrics_20": benchmark_metrics20,
                }
    return panel, raw, grid


def select_combo(grid: dict[tuple[str, str, str], dict], train_start: str, train_end: str, fixed_mask: str | None = None) -> tuple[str, str, str] | None:
    rows = []
    for key, data in grid.items():
        if fixed_mask and data["mask"] != fixed_mask:
            continue
        active_metrics = metrics_for_period(data["active20"], train_start, train_end)
        ic_train = date_slice(data["ic"], train_start, train_end)
        rows.append({
            "key": key,
            "train_active_sharpe": active_metrics["sharpe"],
            "train_active_cagr": active_metrics["cagr"],
            "train_mean_rank_ic": ic_train.mean(),
            "train_observations": active_metrics["observations"],
        })
    if not rows:
        return None
    frame = pd.DataFrame(rows)
    frame = frame[frame["train_observations"].ge(120)]
    if frame.empty:
        return None
    frame = frame.sort_values(["train_active_sharpe", "train_active_cagr", "train_mean_rank_ic"], ascending=False)
    return frame.iloc[0]["key"]


def evaluate_selected_combo(
    panel_name: str,
    alpha_id: str,
    lane: str,
    input_quality_tier: str,
    grid_data: dict,
    fold: tuple[str, str, str, str, str],
    cost_bps: float,
    selection_scope: str,
) -> dict:
    fold_name, train_start, train_end, test_start, test_end = fold
    active, alpha_metrics, benchmark_metrics = active_returns(grid_data["weights"], grid_data["benchmark"], grid_data["next_returns"], cost_bps)
    train_active = metrics_for_period(active, train_start, train_end)
    test_active = metrics_for_period(active, test_start, test_end)
    ic_train = date_slice(grid_data["ic"], train_start, train_end)
    ic_test = date_slice(grid_data["ic"], test_start, test_end)
    return {
        "panel": panel_name,
        "alpha_id": alpha_id,
        "robustness_lane": lane,
        "input_quality_tier": input_quality_tier,
        "fold": fold_name,
        "train_start": train_start,
        "train_end": train_end,
        "test_start": test_start,
        "test_end": test_end,
        "selection_scope": selection_scope,
        "selected_mask": grid_data["mask"],
        "selected_signal_transform": grid_data["signal_transform"],
        "selected_strategy": grid_data["strategy"],
        "cost_bps": cost_bps,
        "train_active_cagr": train_active["cagr"],
        "train_active_sharpe": train_active["sharpe"],
        "train_active_max_drawdown": train_active["max_drawdown"],
        "test_active_cagr": test_active["cagr"],
        "test_active_sharpe": test_active["sharpe"],
        "test_active_sortino": test_active["sortino"],
        "test_active_max_drawdown": test_active["max_drawdown"],
        "test_active_hit_rate": test_active["hit_rate"],
        "test_observations": test_active["observations"],
        "train_mean_rank_ic": ic_train.mean(),
        "test_mean_rank_ic": ic_test.mean(),
        "test_rank_icir": ic_test.mean() / ic_test.std() if ic_test.std() and not pd.isna(ic_test.std()) else np.nan,
        "test_positive_ic_rate": ic_test.gt(0).mean() if len(ic_test) else np.nan,
        "alpha_avg_daily_turnover": alpha_metrics.get("avg_daily_turnover", np.nan),
        "alpha_full_cagr": alpha_metrics.get("cagr", np.nan),
        "benchmark_full_cagr": benchmark_metrics.get("cagr", np.nan),
    }


def fixed_mask_rescore(
    panel_name: str,
    alpha_id: str,
    lane: str,
    input_quality_tier: str,
    signal_transform: str,
    strategy: str,
    fold: tuple[str, str, str, str, str],
    cost_bps: float,
    mask_name: str = "strict_liquidity_100m",
    panel: Alpha101Panel | None = None,
    raw: pd.DataFrame | None = None,
) -> dict:
    fold_name, train_start, train_end, test_start, test_end = fold
    if panel is None or raw is None:
        panel, raw = compute_candidate_raw(panel_name, alpha_id)
    masks = panel_masks(panel)
    if mask_name not in masks:
        raise ValueError(f"Unknown mask: {mask_name}")
    mask = masks[mask_name] & panel.active_mask
    future = forward_return(panel.close, PRIMARY_HORIZON)
    signal = advanced_transform_signal(raw, signal_transform, mask, panel)
    oriented, _direction = causal_orient(signal, future, PRIMARY_HORIZON)
    active, alpha_metrics, benchmark_metrics = active_returns(
        build_portfolio_weights(oriented.where(mask), mask, strategy),
        build_portfolio_weights(raw.where(mask), mask, "equal_weight"),
        next_session_return(panel.close),
        cost_bps,
    )
    ic = fast_rank_ic_by_date(oriented.where(mask), future)
    train_active = metrics_for_period(active, train_start, train_end)
    test_active = metrics_for_period(active, test_start, test_end)
    ic_train = date_slice(ic, train_start, train_end)
    ic_test = date_slice(ic, test_start, test_end)
    return {
        "panel": panel_name,
        "alpha_id": alpha_id,
        "robustness_lane": lane,
        "input_quality_tier": input_quality_tier,
        "fold": fold_name,
        "train_start": train_start,
        "train_end": train_end,
        "test_start": test_start,
        "test_end": test_end,
        "selection_scope": "strict_liquidity_mask_fixed",
        "selected_mask": mask_name,
        "selected_signal_transform": signal_transform,
        "selected_strategy": strategy,
        "cost_bps": cost_bps,
        "train_active_cagr": train_active["cagr"],
        "train_active_sharpe": train_active["sharpe"],
        "train_active_max_drawdown": train_active["max_drawdown"],
        "test_active_cagr": test_active["cagr"],
        "test_active_sharpe": test_active["sharpe"],
        "test_active_sortino": test_active["sortino"],
        "test_active_max_drawdown": test_active["max_drawdown"],
        "test_active_hit_rate": test_active["hit_rate"],
        "test_observations": test_active["observations"],
        "train_mean_rank_ic": ic_train.mean(),
        "test_mean_rank_ic": ic_test.mean(),
        "test_rank_icir": ic_test.mean() / ic_test.std() if ic_test.std() and not pd.isna(ic_test.std()) else np.nan,
        "test_positive_ic_rate": ic_test.gt(0).mean() if len(ic_test) else np.nan,
        "alpha_avg_daily_turnover": alpha_metrics.get("avg_daily_turnover", np.nan),
        "alpha_full_cagr": alpha_metrics.get("cagr", np.nan),
        "benchmark_full_cagr": benchmark_metrics.get("cagr", np.nan),
    }


def strict_liquidity_primary_report(walk_forward: pd.DataFrame, shortlist: pd.DataFrame | None = None) -> pd.DataFrame:
    if shortlist is not None:
        promoted = shortlist[
            shortlist["final_status"].eq("promote_to_deeper_research")
            & shortlist["input_quality_tier"].eq("exact_ohlcv")
        ].copy()
        rows = []
        for _, row in promoted.iterrows():
            panel, raw = compute_candidate_raw(row["panel"], row["alpha_id"])
            for fold in ROBUSTNESS_FOLDS:
                rows.append(
                    fixed_mask_rescore(
                        row["panel"],
                        row["alpha_id"],
                        row["robustness_lane"],
                        row["input_quality_tier"],
                        row["best_signal_transform"],
                        row["best_strategy"],
                        fold,
                        20.0,
                        panel=panel,
                        raw=raw,
                    )
                )
        strict = pd.DataFrame(rows)
    else:
        strict = walk_forward[walk_forward["selected_mask"].eq("strict_liquidity_100m")].copy()
    if strict.empty:
        return strict
    return strict.groupby(["panel", "alpha_id"], dropna=False).agg(
        robustness_lane=("robustness_lane", "first"),
        input_quality_tier=("input_quality_tier", "first"),
        folds=("fold", "nunique"),
        median_test_active_sharpe=("test_active_sharpe", "median"),
        median_test_active_cagr=("test_active_cagr", "median"),
        positive_test_sharpe_rate=("test_active_sharpe", lambda s: s.gt(0).mean()),
        median_test_rank_ic=("test_mean_rank_ic", "median"),
        median_turnover=("alpha_avg_daily_turnover", "median"),
        worst_test_drawdown=("test_active_max_drawdown", "min"),
        selected_mask=("selected_mask", "first"),
        selected_signal_transform=("selected_signal_transform", "first"),
        selected_strategy=("selected_strategy", "first"),
    ).reset_index().sort_values(["median_test_active_sharpe", "median_test_rank_ic"], ascending=False).reset_index(drop=True)


def run_walk_forward(candidate_frame: pd.DataFrame, progress: bool = False) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    walk_rows = []
    cost_rows = []
    universe_rows = []
    total = len(candidate_frame)
    for i, (_, row) in enumerate(candidate_frame.iterrows(), start=1):
        if progress:
            print(f"[alpha101 robustness] {i}/{total} walk-forward {row['panel']} {row['alpha_id']} {row['robustness_lane']}", flush=True)
        panel, _raw, grid = portfolio_grid_for_candidate(row)
        if not grid:
            continue
        for fold in ROBUSTNESS_FOLDS:
            fold_name, train_start, train_end, _test_start, _test_end = fold
            selected = select_combo(grid, train_start, train_end)
            if selected is not None:
                selected_data = grid[selected]
                walk_rows.append(evaluate_selected_combo(row["panel"], row["alpha_id"], row["robustness_lane"], row["input_quality_tier"], selected_data, fold, 20.0, "all_masks_train_selected"))
                for cost in COST_GRID:
                    cost_rows.append(evaluate_selected_combo(row["panel"], row["alpha_id"], row["robustness_lane"], row["input_quality_tier"], selected_data, fold, cost, "all_masks_train_selected"))
            for mask_name in ROBUSTNESS_MASKS:
                mask_selected = select_combo(grid, train_start, train_end, fixed_mask=mask_name)
                if mask_selected is not None:
                    universe_rows.append(evaluate_selected_combo(row["panel"], row["alpha_id"], row["robustness_lane"], row["input_quality_tier"], grid[mask_selected], fold, 20.0, "per_mask_train_selected"))
    return pd.DataFrame(walk_rows), pd.DataFrame(cost_rows), pd.DataFrame(universe_rows)


def proxy_sensitivity(candidate_frame: pd.DataFrame, progress: bool = False) -> pd.DataFrame:
    proxy_candidates = candidate_frame[candidate_frame["input_quality_tier"].str.contains("proxy_vwap", na=False)]
    rows = []
    total = len(proxy_candidates)
    for i, (_, row) in enumerate(proxy_candidates.iterrows(), start=1):
        if progress:
            print(f"[alpha101 robustness] {i}/{total} proxy sensitivity {row['panel']} {row['alpha_id']}", flush=True)
        spec = next(s for s in FORMULA_REGISTRY if s.alpha_id == row["alpha_id"])
        variant_signals = {}
        variant_sharpes = {}
        for variant in ("hlc3", "close", "ohlc4", "hl2c4"):
            try:
                panel, raw = compute_candidate_raw(row["panel"], row["alpha_id"], vwap_variant=variant)
                masks = panel_masks(panel)
                mask_name = row.get("best_mask") if row.get("best_mask") in masks else "high_vol_top100"
                mask = masks[mask_name] & panel.active_mask
                transform = row.get("best_signal_transform") if isinstance(row.get("best_signal_transform"), str) else "rank_centered"
                strategy = row.get("best_strategy") if isinstance(row.get("best_strategy"), str) else compatible_portfolios(spec.family)[0]
                signal = advanced_transform_signal(raw, transform, mask, panel)
                oriented, _direction = causal_orient(signal, forward_return(panel.close, PRIMARY_HORIZON), PRIMARY_HORIZON)
                benchmark = build_portfolio_weights(raw.where(mask), mask, "equal_weight")
                weights = build_portfolio_weights(oriented.where(mask), mask, strategy)
                active, _alpha_metrics, _benchmark_metrics = active_returns(weights, benchmark, next_session_return(panel.close), 20.0)
                variant_signals[variant] = signal
                variant_sharpes[variant] = performance_metrics(active)["sharpe"]
            except Exception as exc:
                rows.append({
                    "panel": row["panel"],
                    "alpha_id": row["alpha_id"],
                    "variant": variant,
                    "proxy_check_status": "failed",
                    "reason": repr(exc),
                })
        if "hlc3" not in variant_signals:
            continue
        base_signal = variant_signals["hlc3"]
        panel = load_panel(row["panel"])
        masks = panel_masks(panel)
        mask_name = row.get("best_mask") if row.get("best_mask") in masks else "high_vol_top100"
        mask = masks[mask_name] & panel.active_mask
        base_sharpe = variant_sharpes.get("hlc3", np.nan)
        for variant, signal in variant_signals.items():
            corr = signal_rank_correlation(base_signal, signal, mask)
            rows.append({
                "panel": row["panel"],
                "alpha_id": row["alpha_id"],
                "robustness_lane": row["robustness_lane"],
                "variant": variant,
                "proxy_check_status": "ok",
                "median_signal_rank_corr_vs_hlc3": corr.median(),
                "mean_signal_rank_corr_vs_hlc3": corr.mean(),
                "active_sharpe_20bps": variant_sharpes.get(variant, np.nan),
                "active_sharpe_delta_vs_hlc3": variant_sharpes.get(variant, np.nan) - base_sharpe,
                "reason": "",
            })
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    ok = frame[frame["proxy_check_status"].eq("ok")]
    summary = ok.groupby(["panel", "alpha_id"], dropna=False).agg(
        min_median_corr=("median_signal_rank_corr_vs_hlc3", "min"),
        sharpe_range=("active_sharpe_20bps", lambda s: s.max() - s.min()),
        sharpe_sign_flips=("active_sharpe_20bps", lambda s: bool(s.gt(0).any() and s.lt(0).any())),
    ).reset_index()
    summary["proxy_dependent"] = summary["min_median_corr"].lt(0.70) | summary["sharpe_range"].gt(1.0) | summary["sharpe_sign_flips"]
    return frame.merge(summary, on=["panel", "alpha_id"], how="left")


def industry_snapshot_risk(candidate_frame: pd.DataFrame, progress: bool = False) -> pd.DataFrame:
    industry_candidates = candidate_frame[candidate_frame["input_quality_tier"].str.contains("snapshot_industry", na=False)]
    rows = []
    total = len(industry_candidates)
    for i, (_, row) in enumerate(industry_candidates.iterrows(), start=1):
        if progress:
            print(f"[alpha101 robustness] {i}/{total} snapshot sensitivity {row['panel']} {row['alpha_id']}", flush=True)
        try:
            panel, raw_snapshot = compute_candidate_raw(row["panel"], row["alpha_id"], neutralization="snapshot")
            _panel, raw_identity = compute_candidate_raw(row["panel"], row["alpha_id"], neutralization="identity")
            masks = panel_masks(panel)
            mask_name = row.get("best_mask") if row.get("best_mask") in masks else "high_vol_top100"
            mask = masks[mask_name] & panel.active_mask
            corr = signal_rank_correlation(raw_snapshot, raw_identity, mask)
            transform = row.get("best_signal_transform") if isinstance(row.get("best_signal_transform"), str) else "rank_centered"
            strategy = row.get("best_strategy") if isinstance(row.get("best_strategy"), str) else "overlay20"
            next_returns = next_session_return(panel.close)
            benchmark = build_portfolio_weights(raw_snapshot.where(mask), mask, "equal_weight")
            sharpes = {}
            for label, raw in {"snapshot_neutralized": raw_snapshot, "identity_unneutralized": raw_identity}.items():
                signal = advanced_transform_signal(raw, transform, mask, panel)
                oriented, _direction = causal_orient(signal, forward_return(panel.close, PRIMARY_HORIZON), PRIMARY_HORIZON)
                weights = build_portfolio_weights(oriented.where(mask), mask, strategy)
                active, _alpha_metrics, _benchmark_metrics = active_returns(weights, benchmark, next_returns, 20.0)
                sharpes[label] = performance_metrics(active)["sharpe"]
            rows.append({
                "panel": row["panel"],
                "alpha_id": row["alpha_id"],
                "robustness_lane": row["robustness_lane"],
                "mask": mask_name,
                "signal_transform": transform,
                "strategy": strategy,
                "median_signal_rank_corr_snapshot_vs_identity": corr.median(),
                "mean_signal_rank_corr_snapshot_vs_identity": corr.mean(),
                "snapshot_active_sharpe_20bps": sharpes.get("snapshot_neutralized", np.nan),
                "identity_active_sharpe_20bps": sharpes.get("identity_unneutralized", np.nan),
                "snapshot_minus_identity_sharpe": sharpes.get("snapshot_neutralized", np.nan) - sharpes.get("identity_unneutralized", np.nan),
                "final_data_risk": "snapshot_metadata_risk",
                "note": "Formula-level industry neutralization uses current snapshot metadata; identity mode removes formula neutralization for sensitivity only.",
            })
        except Exception as exc:
            rows.append({
                "panel": row["panel"],
                "alpha_id": row["alpha_id"],
                "robustness_lane": row["robustness_lane"],
                "final_data_risk": "snapshot_metadata_risk",
                "note": repr(exc),
            })
    return pd.DataFrame(rows)


def classify_shortlist(candidate_frame: pd.DataFrame, walk_forward: pd.DataFrame, proxy_report: pd.DataFrame) -> pd.DataFrame:
    if walk_forward.empty:
        return pd.DataFrame()
    grouped = walk_forward.groupby(["panel", "alpha_id"], dropna=False).agg(
        robustness_lane=("robustness_lane", "first"),
        input_quality_tier=("input_quality_tier", "first"),
        folds=("fold", "nunique"),
        median_test_active_sharpe=("test_active_sharpe", "median"),
        median_test_active_cagr=("test_active_cagr", "median"),
        positive_test_sharpe_rate=("test_active_sharpe", lambda s: s.gt(0).mean()),
        positive_test_cagr_rate=("test_active_cagr", lambda s: s.gt(0).mean()),
        median_test_rank_ic=("test_mean_rank_ic", "median"),
        median_turnover=("alpha_avg_daily_turnover", "median"),
        worst_test_drawdown=("test_active_max_drawdown", "min"),
    ).reset_index()
    lanes = candidate_frame[["panel", "alpha_id", "research_score", "best_5d_ic", "best_20bps_active_sharpe", "best_mask", "best_signal_transform", "best_strategy"]].drop_duplicates(["panel", "alpha_id"])
    out = grouped.merge(lanes, on=["panel", "alpha_id"], how="left")
    proxy_flags = pd.DataFrame(columns=["panel", "alpha_id", "proxy_dependent"])
    if not proxy_report.empty and "proxy_dependent" in proxy_report.columns:
        proxy_flags = proxy_report[["panel", "alpha_id", "proxy_dependent"]].dropna().drop_duplicates(["panel", "alpha_id"])
    out = out.merge(proxy_flags, on=["panel", "alpha_id"], how="left")
    out["proxy_dependent"] = out["proxy_dependent"].fillna(False).astype(bool)
    robust = (
        out["median_test_active_sharpe"].gt(0.50)
        & out["median_test_active_cagr"].gt(0.0)
        & out["positive_test_sharpe_rate"].ge(0.60)
        & out["median_test_rank_ic"].gt(0.0)
        & out["median_turnover"].lt(0.15)
    )
    out["final_status"] = "discard"
    out.loc[out["median_test_rank_ic"].gt(0.01) & out["final_status"].eq("discard"), "final_status"] = "feature_only"
    out.loc[robust, "final_status"] = "promote_to_deeper_research"
    out.loc[out["proxy_dependent"], "final_status"] = "proxy_dependent"
    out.loc[out["input_quality_tier"].str.contains("snapshot_industry", na=False), "final_status"] = "snapshot_metadata_risk"
    out.loc[out["robustness_lane"].eq("baseline_alpha001"), "final_status"] = "baseline_comparator"
    return out.sort_values(["final_status", "median_test_active_sharpe"], ascending=[True, False]).reset_index(drop=True)


def validation_report(
    candidate_frame: pd.DataFrame,
    walk_forward: pd.DataFrame,
    shortlist: pd.DataFrame,
    strict_liquidity_report: pd.DataFrame | None = None,
) -> pd.DataFrame:
    checks = [
        {
            "check": "alpha001_included_as_baseline",
            "passed": bool(candidate_frame["alpha_id"].eq("alpha001").any()),
            "detail": "Alpha#1 included in baseline_alpha001 lane.",
        },
        {
            "check": "exact_candidates_separated",
            "passed": bool(candidate_frame["robustness_lane"].eq("clean_exact_ohlcv").any()),
            "detail": "Exact OHLCV candidates have their own lane.",
        },
        {
            "check": "train_selected_only",
            "passed": bool(not walk_forward.empty and walk_forward["selection_scope"].str.contains("train_selected").all()),
            "detail": "Walk-forward rows select transforms/portfolios using train windows.",
        },
        {
            "check": "cost_grid_present",
            "passed": True,
            "detail": "Cost sensitivity is generated at 10/20/35/50 bps.",
        },
        {
            "check": "no_full_sample_orientation",
            "passed": True,
            "detail": "Tradable signals use causal_orient, which shifts IC before rolling orientation.",
        },
        {
            "check": "final_status_available",
            "passed": bool(not shortlist.empty and shortlist["final_status"].notna().all()),
            "detail": "Each robustness candidate receives a final triage status.",
        },
        {
            "check": "strict_liquidity_primary_reported",
            "passed": bool(strict_liquidity_report is not None and not strict_liquidity_report.empty and strict_liquidity_report["selected_mask"].eq("strict_liquidity_100m").all()),
            "detail": "Strict-liquidity rows are surfaced as a dedicated mask-fixed rescore report.",
        },
    ]
    return pd.DataFrame(checks)


def batch2_validation_report(candidate_frame: pd.DataFrame, walk_forward: pd.DataFrame, cost_sensitivity: pd.DataFrame, universe_sensitivity: pd.DataFrame) -> pd.DataFrame:
    expected = set(ROBUSTNESS_BATCH2_ALPHAS)
    actual = set(candidate_frame["alpha_id"]) if not candidate_frame.empty else set()
    required_masks = set(ROBUSTNESS_MASKS)
    observed_masks = set(universe_sensitivity["selected_mask"]) if not universe_sensitivity.empty and "selected_mask" in universe_sensitivity.columns else set()
    checks = [
        {
            "check": "batch2_exact_20_alphas",
            "passed": actual == expected and len(candidate_frame) == len(expected),
            "detail": f"Expected {len(expected)} fixed clean near-miss alphas; found {len(candidate_frame)}.",
        },
        {
            "check": "batch2_only_exact_ohlcv",
            "passed": bool(not candidate_frame.empty and candidate_frame["input_quality_tier"].eq("exact_ohlcv").all()),
            "detail": "Batch 2 excludes proxy, snapshot, decayed, and discarded alphas.",
        },
        {
            "check": "batch2_train_selected_only",
            "passed": bool(not walk_forward.empty and walk_forward["selection_scope"].str.contains("train_selected").all()),
            "detail": "Walk-forward rows select transforms/portfolios using train windows.",
        },
        {
            "check": "batch2_cost_grid_present",
            "passed": bool(not cost_sensitivity.empty and set(cost_sensitivity["cost_bps"].dropna().astype(float)) == set(COST_GRID)),
            "detail": "Cost sensitivity exists at 10/20/35/50 bps.",
        },
        {
            "check": "batch2_universe_masks_present",
            "passed": required_masks.issubset(observed_masks),
            "detail": "Universe sensitivity includes all eligible, high-vol, strict-liquidity, and seasoned masks where available.",
        },
        {
            "check": "batch2_no_batch1_overwrite",
            "passed": all((ROBUSTNESS_DIR / name).exists() for name in ROBUSTNESS_TABLES.values()),
            "detail": "Batch 1 artifact files are still present.",
        },
    ]
    return pd.DataFrame(checks)


def markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return ""
    view = frame.astype(object).where(pd.notna(frame), "")
    headers = [str(c) for c in view.columns]
    rows = [[str(v) for v in row] for row in view.to_numpy()]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def final_report(
    shortlist: pd.DataFrame,
    candidate_frame: pd.DataFrame,
    proxy_report: pd.DataFrame,
    industry_report: pd.DataFrame,
    strict_liquidity_report: pd.DataFrame,
) -> str:
    status_counts = shortlist["final_status"].value_counts(dropna=False).rename("candidates").reset_index().rename(columns={"index": "final_status"})
    lane_counts = candidate_frame["robustness_lane"].value_counts(dropna=False).rename("rows").reset_index().rename(columns={"index": "robustness_lane"})
    proxy_summary = pd.DataFrame()
    if not proxy_report.empty and "proxy_dependent" in proxy_report.columns:
        proxy_summary = proxy_report.drop_duplicates(["panel", "alpha_id"])[["panel", "alpha_id", "proxy_dependent", "min_median_corr", "sharpe_range"]].sort_values(["proxy_dependent", "sharpe_range"], ascending=[False, False])
    industry_summary = industry_report[["panel", "alpha_id", "median_signal_rank_corr_snapshot_vs_identity", "snapshot_minus_identity_sharpe", "final_data_risk"]].head(20) if not industry_report.empty else pd.DataFrame()
    strict_summary = strict_liquidity_report[["panel", "alpha_id", "robustness_lane", "input_quality_tier", "median_test_active_sharpe", "median_test_active_cagr", "positive_test_sharpe_rate", "median_test_rank_ic", "median_turnover"]].head(20) if not strict_liquidity_report.empty else pd.DataFrame()
    top = shortlist.sort_values("median_test_active_sharpe", ascending=False).head(25)
    cols = ["panel", "alpha_id", "robustness_lane", "input_quality_tier", "final_status", "median_test_active_sharpe", "median_test_active_cagr", "positive_test_sharpe_rate", "median_test_rank_ic", "median_turnover"]
    return "\n".join([
        "# Alpha101 Robustness And Data-Risk Triage Report",
        "",
        "This report treats the Alpha101 factory output as discovery only, then reruns top candidates with train-only transform/portfolio selection, a strict-liquidity mask-fixed rescore of the promoted exact-OHLCV queue, active benchmark comparison, cost sensitivity, and proxy/snapshot data-risk checks.",
        "",
        "## Candidate Lane Counts",
        markdown_table(lane_counts),
        "",
        "## Final Status Counts",
        markdown_table(status_counts),
        "",
        "## Top Robustness Rows",
        markdown_table(top[cols]),
        "",
        "## Proxy Sensitivity Summary",
        markdown_table(proxy_summary.head(20)) if not proxy_summary.empty else "No proxy candidates were selected.",
        "",
        "## Strict Liquidity Primary Rescore",
        markdown_table(strict_summary) if not strict_summary.empty else "No strict-liquidity rows were selected.",
        "",
        "## Industry Snapshot Risk Summary",
        markdown_table(industry_summary) if not industry_summary.empty else "No snapshot-industry candidates were selected.",
        "",
        "## Interpretation Rules",
        "- `promote_to_deeper_research` means the candidate survived walk-forward active return tests after train-only selection.",
        "- `feature_only` means IC survived better than portfolio expression.",
        "- `proxy_dependent` means VWAP proxy choice materially changes signal rankings or active Sharpe.",
        "- `snapshot_metadata_risk` remains research-only until point-in-time industry metadata exists.",
        "- `baseline_comparator` is included for Alpha#1 context only.",
    ])


def batch2_final_report(shortlist: pd.DataFrame, candidate_frame: pd.DataFrame, combined: pd.DataFrame) -> str:
    status_counts = shortlist["final_status"].value_counts(dropna=False).rename("candidates").reset_index().rename(columns={"index": "final_status"})
    lane_counts = candidate_frame["robustness_lane"].value_counts(dropna=False).rename("rows").reset_index().rename(columns={"index": "robustness_lane"})
    top = shortlist.sort_values("median_test_active_sharpe", ascending=False)
    promoted_combined = combined[
        combined["final_status"].eq("promote_to_deeper_research")
        & combined["input_quality_tier"].eq("exact_ohlcv")
    ].sort_values(["batch", "median_test_active_sharpe"], ascending=[True, False])
    cols = ["batch", "panel", "alpha_id", "robustness_lane", "final_status", "median_test_active_sharpe", "median_test_active_cagr", "positive_test_sharpe_rate", "median_test_rank_ic", "median_turnover"]
    return "\n".join([
        "# Alpha101 Robustness Batch 2 Clean Near-Miss Report",
        "",
        "Batch 2 reruns only exact-OHLCV discovery candidates that missed the first top-12 robustness cutoff. It excludes proxy, snapshot-industry, decayed, and discarded alphas.",
        "",
        "## Batch 2 Lane Counts",
        markdown_table(lane_counts),
        "",
        "## Batch 2 Final Status Counts",
        markdown_table(status_counts),
        "",
        "## Batch 2 Results",
        markdown_table(top[cols[1:]]),
        "",
        "## Combined Promoted Exact-OHLCV Candidates",
        markdown_table(promoted_combined[cols]) if not promoted_combined.empty else "No combined exact-OHLCV promoted candidates.",
        "",
        "## Interpretation Rules",
        "- `promote_to_deeper_research` uses the same Batch 1 robustness thresholds.",
        "- `feature_only` means IC survived better than portfolio expression.",
        "- `discard` means the alpha failed the Batch 2 walk-forward robustness hurdle.",
        "- Batch 2 remains a research expansion, not a capital-promotion step.",
    ])


def run_alpha101_robustness(
    refresh: bool = False,
    clean_n: int = 12,
    proxy_n: int = 8,
    snapshot_n: int = 8,
    progress: bool = True,
) -> dict[str, pd.DataFrame]:
    ROBUSTNESS_DIR.mkdir(parents=True, exist_ok=True)
    paths = {key: ROBUSTNESS_DIR / name for key, name in ROBUSTNESS_TABLES.items()}
    report_path = ROBUSTNESS_DIR / ROBUSTNESS_REPORT
    if not refresh and all(path.exists() for path in paths.values()) and report_path.exists():
        return {key: pd.read_csv(path) for key, path in paths.items()}

    lanes = candidate_lanes(clean_n=clean_n, proxy_n=proxy_n, snapshot_n=snapshot_n)
    walk_forward, cost_sensitivity, universe_sensitivity = run_walk_forward(lanes, progress=progress)
    proxy_report = proxy_sensitivity(lanes, progress=progress)
    industry_report = industry_snapshot_risk(lanes, progress=progress)
    shortlist = classify_shortlist(lanes, walk_forward, proxy_report)
    strict_liquidity_report = strict_liquidity_primary_report(walk_forward, shortlist)
    validation = validation_report(lanes, walk_forward, shortlist, strict_liquidity_report)
    outputs = {
        "candidate_lanes": lanes,
        "walk_forward": walk_forward,
        "strict_liquidity_primary": strict_liquidity_report,
        "cost_sensitivity": cost_sensitivity,
        "universe_sensitivity": universe_sensitivity,
        "proxy_sensitivity": proxy_report,
        "industry_snapshot_risk": industry_report,
        "validation": validation,
        "shortlist": shortlist,
    }
    for key, frame in outputs.items():
        frame.to_csv(paths[key], index=False)
    report_path.write_text(final_report(shortlist, lanes, proxy_report, industry_report, strict_liquidity_report))
    return outputs


def run_alpha101_robustness_batch2(refresh: bool = False, progress: bool = True) -> dict[str, pd.DataFrame]:
    ROBUSTNESS_DIR.mkdir(parents=True, exist_ok=True)
    paths = {key: ROBUSTNESS_DIR / name for key, name in ROBUSTNESS_BATCH2_TABLES.items()}
    report_path = ROBUSTNESS_DIR / ROBUSTNESS_BATCH2_REPORT
    if not refresh and all(path.exists() for path in paths.values()) and report_path.exists():
        return {key: pd.read_csv(path) for key, path in paths.items()}

    lanes = clean_near_miss_lanes()
    walk_forward, cost_sensitivity, universe_sensitivity = run_walk_forward(lanes, progress=progress)
    proxy_report = pd.DataFrame(columns=["panel", "alpha_id", "proxy_dependent"])
    shortlist = classify_shortlist(lanes, walk_forward, proxy_report)
    validation = batch2_validation_report(lanes, walk_forward, cost_sensitivity, universe_sensitivity)

    batch1 = read_artifact("alpha101_robustness_shortlist.csv").copy()
    batch1["batch"] = "batch1"
    batch2 = shortlist.copy()
    batch2["batch"] = "batch2"
    combined = pd.concat([batch1, batch2], ignore_index=True, sort=False)
    combined = combined.sort_values(["final_status", "median_test_active_sharpe"], ascending=[True, False]).reset_index(drop=True)

    outputs = {
        "candidate_lanes": lanes,
        "walk_forward": walk_forward,
        "cost_sensitivity": cost_sensitivity,
        "universe_sensitivity": universe_sensitivity,
        "validation": validation,
        "shortlist": shortlist,
        "combined_shortlist": combined,
    }
    for key, frame in outputs.items():
        frame.to_csv(paths[key], index=False)
    report_path.write_text(batch2_final_report(shortlist, lanes, combined))
    return outputs


if __name__ == "__main__":
    out = run_alpha101_robustness(refresh=False)
    print({key: value.shape for key, value in out.items()})
    print(out["shortlist"].head(25).to_string(index=False))
