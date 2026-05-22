from __future__ import annotations

import concurrent.futures as futures
from pathlib import Path

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from research.alpha101_engine import (
    ALPHA101_ARTIFACT_DIR,
    backtest_weights,
    causal_orient,
    centered_rank,
    clean,
    equal_weight_targets,
    fast_rank_ic_by_date,
    forward_return,
    indneutralize,
    load_panel,
    next_session_return,
    operator_validation,
    overlay_weights,
    performance_metrics,
    row_zscore,
    score_tilt_weights,
    top_bucket_weights,
    long_short_weights,
    weekly_rebalance_mask,
    carry_on_rebalance,
    winsorized_zscore,
)
from research.alpha101_formulas import FORMULA_REGISTRY, compute_alpha, registry_frame


PANELS = ("nifty500", "expanded")
HORIZONS = (1, 3, 5, 10)
PRIMARY_HORIZON = 5
COST_GRID = (10.0, 20.0, 35.0, 50.0)
TASK_TABLES = ("formula_validation", "metric_panel", "decay_report", "portfolio_report")
ERA_SPLITS = (
    ("2018_2020", "2018-01-01", "2020-12-31"),
    ("2021_2023", "2021-01-01", "2023-12-31"),
    ("2024_2026", "2024-01-01", "2026-12-31"),
)


def strict_liquidity_mask(panel, min_adv_rupees: float = 100_000_000.0, min_shares: float = 100_000.0) -> pd.DataFrame:
    adv60 = panel.close.mul(panel.volume).rolling(60, min_periods=60).median().shift(1)
    shares60 = panel.volume.rolling(60, min_periods=60).median().shift(1)
    return panel.active_mask & adv60.ge(min_adv_rupees) & shares60.ge(min_shares)


def ex_microcap_mask(panel) -> pd.DataFrame:
    if "source_slugs" not in panel.constituents.columns:
        return panel.active_mask.copy()
    slugs = panel.constituents.drop_duplicates("Symbol").set_index("Symbol")["source_slugs"].astype(str).reindex(panel.active_mask.columns).fillna("")
    keep = ~slugs.str.contains("nifty_microcap_250", case=False, regex=False)
    keep_frame = pd.DataFrame(np.tile(keep.to_numpy(bool), (len(panel.active_mask), 1)), index=panel.active_mask.index, columns=panel.active_mask.columns)
    return panel.active_mask & keep_frame


def seasoned_mask(panel, sessions: int = 504) -> pd.DataFrame:
    first_valid = panel.adj_close.apply(lambda col: col.first_valid_index())
    seasoned = pd.DataFrame(False, index=panel.active_mask.index, columns=panel.active_mask.columns)
    for symbol, first_date in pd.to_datetime(first_valid).items():
        if pd.notna(first_date):
            seasoned[symbol] = panel.active_mask.index >= (first_date + pd.tseries.offsets.BDay(sessions))
    return panel.active_mask & seasoned


def panel_masks(panel) -> dict[str, pd.DataFrame]:
    masks = {
        "all_eligible": panel.active_mask,
        "high_vol_top100": panel.high_vol_mask & panel.active_mask,
        "strict_liquidity_100m": strict_liquidity_mask(panel),
        "seasoned_2y": seasoned_mask(panel),
    }
    if panel.name == "expanded":
        masks["ex_microcap"] = ex_microcap_mask(panel)
        masks["ex_microcap_strict_liquidity_100m"] = ex_microcap_mask(panel) & strict_liquidity_mask(panel)
    return masks


def transform_signal(raw_signal: pd.DataFrame, transform: str, mask: pd.DataFrame) -> pd.DataFrame:
    masked = clean(raw_signal).where(mask)
    if transform == "raw":
        return masked
    if transform == "rank_centered":
        return centered_rank(masked).where(mask)
    if transform == "zscore":
        return row_zscore(masked).where(mask)
    if transform == "winsor_zscore":
        return winsorized_zscore(masked).where(mask)
    raise ValueError(f"Unknown transform: {transform}")


def smoothed_threshold_top_bottom(frame: pd.DataFrame, span: int, min_periods: int) -> pd.DataFrame:
    smoothed = frame.ewm(span=span, min_periods=min_periods, adjust=False).mean()
    rank_pct = smoothed.rank(axis=1, pct=True)
    return smoothed.where(rank_pct.ge(0.80) | rank_pct.le(0.20))


def residualize_against(signal: pd.DataFrame, factors: dict[str, pd.DataFrame], mask: pd.DataFrame) -> pd.DataFrame:
    signal = clean(signal).where(mask)
    factor_names = list(factors)
    aligned_factors = [clean(factors[name]).reindex_like(signal) for name in factor_names]
    out = pd.DataFrame(np.nan, index=signal.index, columns=signal.columns)
    for date in signal.index:
        y = signal.loc[date]
        xs = [factor.loc[date] for factor in aligned_factors]
        valid = y.notna()
        for x in xs:
            valid &= x.notna()
        if valid.sum() <= len(xs) + 10:
            continue
        xmat = np.column_stack([np.ones(int(valid.sum()))] + [x.loc[valid].to_numpy(dtype=float) for x in xs])
        yvec = y.loc[valid].to_numpy(dtype=float)
        try:
            beta, *_ = np.linalg.lstsq(xmat, yvec, rcond=None)
        except np.linalg.LinAlgError:
            continue
        fitted = xmat @ beta
        out.loc[date, valid] = yvec - fitted
    return out.where(mask)


def advanced_transform_signal(raw_signal: pd.DataFrame, transform: str, mask: pd.DataFrame, panel) -> pd.DataFrame:
    base = transform_signal(raw_signal, "rank_centered", mask)
    if transform in {"raw", "rank_centered", "zscore", "winsor_zscore"}:
        return transform_signal(raw_signal, transform, mask)
    if transform == "ewm3":
        return base.ewm(span=3, min_periods=2, adjust=False).mean().where(mask)
    if transform == "ewm5":
        return base.ewm(span=5, min_periods=3, adjust=False).mean().where(mask)
    if transform == "ewm10":
        return base.ewm(span=10, min_periods=5, adjust=False).mean().where(mask)
    if transform == "rolling5":
        return base.rolling(5, min_periods=3).mean().where(mask)
    if transform == "rank_normal":
        return row_zscore(base).where(mask)
    if transform == "clipped_zscore":
        return row_zscore(base).clip(-3.0, 3.0).where(mask)
    if transform == "signed_sqrt":
        return np.sign(base) * np.sqrt(base.abs()).where(mask)
    if transform == "signed_square":
        return (np.sign(base) * base.pow(2)).where(mask)
    if transform == "tanh_z":
        return np.tanh(row_zscore(base)).where(mask)
    if transform == "threshold_top_bottom":
        rank_pct = base.rank(axis=1, pct=True)
        return base.where(rank_pct.ge(0.80) | rank_pct.le(0.20)).where(mask)
    if transform == "ewm3_threshold_top_bottom":
        return smoothed_threshold_top_bottom(base, 3, 2).where(mask)
    if transform == "ewm5_threshold_top_bottom":
        return smoothed_threshold_top_bottom(base, 5, 3).where(mask)
    if transform == "ewm10_threshold_top_bottom":
        return smoothed_threshold_top_bottom(base, 10, 5).where(mask)
    if transform == "decay_ensemble":
        return pd.concat(
            [base.stack(), base.rolling(3, min_periods=2).mean().stack(), base.rolling(5, min_periods=3).mean().stack()],
            axis=1,
        ).mean(axis=1).unstack().reindex_like(base).where(mask)
    if transform == "vol_scaled":
        vol20 = panel.returns.rolling(20, min_periods=20).std().shift(1).reindex_like(base)
        denom = vol20.where(mask).replace(0.0, np.nan)
        return row_zscore(base.div(denom)).where(mask)
    if transform == "liquidity_scaled":
        adv20_rupees = panel.close.mul(panel.volume).rolling(20, min_periods=20).median().shift(1)
        liq_rank = adv20_rupees.rank(axis=1, pct=True).reindex_like(base)
        return row_zscore(base.mul(liq_rank)).where(mask)
    if transform == "industry_residual":
        return indneutralize(base, panel.industry).where(mask)
    if transform == "style_residual":
        factors = {
            "volatility": panel.returns.rolling(20, min_periods=20).std().shift(1),
            "momentum": panel.close.pct_change(63, fill_method=None).shift(1),
            "reversal": panel.close.pct_change(5, fill_method=None).shift(1),
            "liquidity": panel.close.mul(panel.volume).rolling(20, min_periods=20).median().shift(1),
        }
        factors = {name: row_zscore(value) for name, value in factors.items()}
        return residualize_against(base, factors, mask)
    raise ValueError(f"Unknown transform: {transform}")


def family_transforms(family: str) -> tuple[str, ...]:
    base = ("raw", "rank_centered", "zscore", "winsor_zscore", "rank_normal", "clipped_zscore", "tanh_z")
    if family == "price_reversal":
        return base + ("ewm3", "ewm5", "rolling5", "threshold_top_bottom", "ewm3_threshold_top_bottom", "ewm5_threshold_top_bottom", "ewm10_threshold_top_bottom", "decay_ensemble", "signed_sqrt")
    if family == "momentum_trend":
        return base + ("ewm5", "ewm10", "rolling5", "ewm3_threshold_top_bottom", "ewm5_threshold_top_bottom", "ewm10_threshold_top_bottom", "decay_ensemble", "signed_square")
    if family == "volume_liquidity":
        return base + ("liquidity_scaled", "ewm3", "threshold_top_bottom", "ewm3_threshold_top_bottom", "ewm5_threshold_top_bottom", "ewm10_threshold_top_bottom")
    if family == "volatility_range":
        return base + ("vol_scaled", "ewm3", "threshold_top_bottom", "ewm3_threshold_top_bottom", "ewm5_threshold_top_bottom", "ewm10_threshold_top_bottom")
    if family in {"correlation_relative_value", "industry_neutral_cross_section"}:
        return base + ("industry_residual", "style_residual", "ewm3", "threshold_top_bottom", "ewm3_threshold_top_bottom", "ewm5_threshold_top_bottom", "ewm10_threshold_top_bottom")
    return base + ("ewm3", "style_residual")


def portfolio_signal_transforms(family: str) -> tuple[str, ...]:
    if family == "price_reversal":
        return ("rank_centered", "winsor_zscore", "ewm3", "threshold_top_bottom", "ewm3_threshold_top_bottom", "ewm5_threshold_top_bottom", "ewm10_threshold_top_bottom")
    if family == "momentum_trend":
        return ("rank_centered", "winsor_zscore", "ewm5", "ewm3_threshold_top_bottom", "ewm5_threshold_top_bottom", "ewm10_threshold_top_bottom", "decay_ensemble")
    if family == "volume_liquidity":
        return ("rank_centered", "winsor_zscore", "liquidity_scaled", "ewm3", "ewm3_threshold_top_bottom", "ewm5_threshold_top_bottom", "ewm10_threshold_top_bottom")
    if family == "volatility_range":
        return ("rank_centered", "winsor_zscore", "vol_scaled", "ewm3", "ewm3_threshold_top_bottom", "ewm5_threshold_top_bottom", "ewm10_threshold_top_bottom")
    if family in {"correlation_relative_value", "industry_neutral_cross_section"}:
        return ("rank_centered", "winsor_zscore", "industry_residual", "style_residual", "ewm3_threshold_top_bottom", "ewm5_threshold_top_bottom", "ewm10_threshold_top_bottom")
    return ("rank_centered", "winsor_zscore", "ewm3")


def build_portfolio_weights(signal: pd.DataFrame, mask: pd.DataFrame, strategy: str) -> pd.DataFrame:
    rebalance = weekly_rebalance_mask(signal.index)
    if strategy == "equal_weight":
        return carry_on_rebalance(equal_weight_targets(mask), rebalance)
    if strategy == "top10":
        return carry_on_rebalance(top_bucket_weights(signal, mask, 10), rebalance)
    if strategy == "long_short_10":
        return carry_on_rebalance(long_short_weights(signal, mask, 10), rebalance)
    if strategy == "score_tilt":
        return carry_on_rebalance(score_tilt_weights(signal, mask, 0.25), rebalance)
    if strategy == "overlay20":
        return carry_on_rebalance(overlay_weights(signal, mask, 0.20), rebalance, partial=0.50)
    if strategy == "ewm3_overlay20":
        return carry_on_rebalance(overlay_weights(signal.ewm(span=3, min_periods=2, adjust=False).mean(), mask, 0.20), rebalance, partial=0.50)
    if strategy == "ewm5_overlay20":
        return carry_on_rebalance(overlay_weights(signal.ewm(span=5, min_periods=3, adjust=False).mean(), mask, 0.20), rebalance, partial=0.50)
    if strategy == "ewm10_overlay20":
        return carry_on_rebalance(overlay_weights(signal.ewm(span=10, min_periods=5, adjust=False).mean(), mask, 0.20), rebalance, partial=0.50)
    raise ValueError(f"Unknown portfolio strategy: {strategy}")


def compatible_portfolios(family: str) -> tuple[str, ...]:
    if family == "price_reversal":
        return ("top10", "long_short_10", "score_tilt", "overlay20", "ewm3_overlay20", "ewm5_overlay20")
    if family == "momentum_trend":
        return ("top10", "score_tilt", "overlay20", "ewm5_overlay20", "ewm10_overlay20")
    if family in {"correlation_relative_value", "industry_neutral_cross_section"}:
        return ("long_short_10", "score_tilt", "overlay20", "ewm3_overlay20")
    return ("top10", "long_short_10", "score_tilt", "overlay20", "ewm3_overlay20")


def metric_row(panel_name: str, alpha_id: str, family: str, transform: str, horizon: int, signal: pd.DataFrame, future: pd.DataFrame) -> dict:
    ic = fast_rank_ic_by_date(signal, future)
    vol = ic.std()
    return {
        "panel": panel_name,
        "alpha_id": alpha_id,
        "family": family,
        "transform": transform,
        "horizon_days": horizon,
        "mean_rank_ic": ic.mean(),
        "median_rank_ic": ic.median(),
        "rank_ic_vol": vol,
        "rank_icir": ic.mean() / vol if vol and not pd.isna(vol) else np.nan,
        "positive_ic_rate": ic.dropna().gt(0).mean(),
        "observations": ic.notna().sum(),
    }


def decay_rows(panel_name: str, alpha_id: str, family: str, signal: pd.DataFrame, futures_by_horizon: dict[int, pd.DataFrame]) -> list[dict]:
    rows = []
    future = futures_by_horizon[PRIMARY_HORIZON]
    ic = fast_rank_ic_by_date(signal, future)
    for era, start, end in ERA_SPLITS:
        part = ic.loc[(ic.index >= start) & (ic.index <= end)].dropna()
        rows.append({
            "panel": panel_name,
            "alpha_id": alpha_id,
            "family": family,
            "era": era,
            "mean_rank_ic": part.mean(),
            "positive_ic_rate": part.gt(0).mean() if len(part) else np.nan,
            "observations": len(part),
        })
    old = ic.loc[ic.index < "2024-01-01"].mean()
    recent = ic.loc[ic.index >= "2024-01-01"].mean()
    rows.append({
        "panel": panel_name,
        "alpha_id": alpha_id,
        "family": family,
        "era": "recent_minus_old",
        "mean_rank_ic": recent - old,
        "positive_ic_rate": np.nan,
        "observations": ic.notna().sum(),
    })
    return rows


def portfolio_row(
    panel_name: str,
    alpha_id: str,
    family: str,
    signal_transform: str,
    mask_name: str,
    strategy: str,
    cost_bps: float,
    weights: pd.DataFrame,
    benchmark: pd.DataFrame,
    next_returns: pd.DataFrame,
) -> dict:
    bt = backtest_weights(weights, next_returns, cost_bps)
    bm = backtest_weights(benchmark, next_returns, cost_bps)
    pair = pd.concat([bt["returns"].rename("alpha"), bm["returns"].rename("benchmark")], axis=1).dropna()
    excess = pair["alpha"] - pair["benchmark"]
    row = {
        "panel": panel_name,
        "alpha_id": alpha_id,
        "family": family,
        "signal_transform": signal_transform,
        "mask": mask_name,
        "strategy": strategy,
        "cost_bps": cost_bps,
        "avg_names": weights.abs().gt(1e-12).sum(axis=1).replace(0, np.nan).mean(),
    }
    row.update({f"alpha_{k}": v for k, v in bt["metrics"].items()})
    row.update({f"benchmark_{k}": v for k, v in bm["metrics"].items()})
    row.update({f"active_{k}": v for k, v in performance_metrics(excess).items()})
    return row


def evaluate_alpha_panel(args: tuple[str, str]) -> dict[str, pd.DataFrame]:
    alpha_id, panel_name = args
    spec = next(s for s in FORMULA_REGISTRY if s.alpha_id == alpha_id)
    panel = load_panel(panel_name)
    formula_rows: list[dict[str, object]] = []
    metric_rows: list[dict[str, object]] = []
    decay_report_rows: list[dict[str, object]] = []
    portfolio_rows: list[dict[str, object]] = []
    if spec.callable_name is None:
        formula_rows.append({
            "panel": panel_name,
            "alpha_id": alpha_id,
            "computed": False,
            "reason": spec.notes,
            "non_null_scores": 0,
        })
        return {
            "formula_validation": pd.DataFrame(formula_rows),
            "metric_panel": pd.DataFrame(metric_rows),
            "decay_report": pd.DataFrame(decay_report_rows),
            "portfolio_report": pd.DataFrame(portfolio_rows),
        }
    try:
        raw = compute_alpha(panel, alpha_id)
    except Exception as exc:
        formula_rows.append({
            "panel": panel_name,
            "alpha_id": alpha_id,
            "computed": False,
            "reason": repr(exc),
            "non_null_scores": 0,
        })
        return {
            "formula_validation": pd.DataFrame(formula_rows),
            "metric_panel": pd.DataFrame(metric_rows),
            "decay_report": pd.DataFrame(decay_report_rows),
            "portfolio_report": pd.DataFrame(portfolio_rows),
        }

    raw = clean(raw).reindex_like(panel.adj_close)
    masks = panel_masks(panel)
    primary_mask = masks["high_vol_top100"]
    raw = raw.where(panel.active_mask)
    non_null = int(raw.notna().sum().sum())
    formula_rows.append({
        "panel": panel_name,
        "alpha_id": alpha_id,
        "computed": non_null > 0,
        "reason": "" if non_null > 0 else "all_nan",
        "non_null_scores": non_null,
        "median_daily_coverage": raw.notna().sum(axis=1).median(),
        "min_score": raw.min().min(),
        "max_score": raw.max().max(),
    })
    futures_by_horizon = {h: forward_return(panel.adj_close, h) for h in HORIZONS}
    transformed = {
        name: advanced_transform_signal(raw, name, primary_mask, panel)
        for name in dict.fromkeys(family_transforms(spec.family))
    }
    for transform_name, signal in transformed.items():
        for horizon, future in futures_by_horizon.items():
            metric_rows.append(metric_row(panel_name, alpha_id, spec.family, transform_name, horizon, signal, future))

    oriented_by_transform = {}
    for transform_name in portfolio_signal_transforms(spec.family):
        if transform_name in transformed:
            oriented_by_transform[transform_name] = causal_orient(transformed[transform_name], futures_by_horizon[PRIMARY_HORIZON], PRIMARY_HORIZON)[0]
    decay_report_rows.extend(decay_rows(panel_name, alpha_id, spec.family, oriented_by_transform["rank_centered"], futures_by_horizon))
    next_returns = next_session_return(panel.adj_close)
    for mask_name, mask in masks.items():
        if mask.sum(axis=1).replace(0, np.nan).median() < 20:
            continue
        benchmark = build_portfolio_weights(raw.where(mask), mask, "equal_weight")
        for transform_name, oriented in oriented_by_transform.items():
            signal = oriented.where(mask)
            for strategy in compatible_portfolios(spec.family):
                weights = build_portfolio_weights(signal, mask, strategy)
                for cost_bps in COST_GRID:
                    portfolio_rows.append(portfolio_row(panel_name, alpha_id, spec.family, transform_name, mask_name, strategy, cost_bps, weights, benchmark, next_returns))
    return {
        "formula_validation": pd.DataFrame(formula_rows),
        "metric_panel": pd.DataFrame(metric_rows),
        "decay_report": pd.DataFrame(decay_report_rows),
        "portfolio_report": pd.DataFrame(portfolio_rows),
    }


def task_cache_paths(alpha_id: str, panel_name: str) -> dict[str, Path]:
    base = ALPHA101_ARTIFACT_DIR / "_task_cache"
    return {name: base / f"{alpha_id}_{panel_name}_{name}.csv" for name in TASK_TABLES}


def read_cached_frame(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def evaluate_alpha_panel_cached(args: tuple[str, str], refresh: bool = False) -> dict[str, pd.DataFrame]:
    alpha_id, panel_name = args
    paths = task_cache_paths(alpha_id, panel_name)
    if not refresh and all(path.exists() for path in paths.values()):
        return {name: read_cached_frame(path) for name, path in paths.items()}
    result = evaluate_alpha_panel(args)
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    for name, frame in result.items():
        frame.to_csv(paths[name], index=False)
    return result


def transform_compatibility_frame() -> pd.DataFrame:
    rows = []
    families = sorted({s.family for s in FORMULA_REGISTRY})
    for family in families:
        rows.append({
            "family": family,
            "signal_transforms": ",".join(family_transforms(family)),
            "portfolio_templates": ",".join(compatible_portfolios(family)),
            "note": "Transforms are family-compatible candidates, not forced rescue methods.",
        })
    return pd.DataFrame(rows)


def classify_alpha(row: pd.Series) -> str:
    if row.get("input_quality_tier") == "missing_cap":
        return "untestable"
    sharpe = row.get("best_20bps_active_sharpe", np.nan)
    ic = row.get("best_5d_ic", np.nan)
    recent_delta = row.get("recent_minus_old_ic", np.nan)
    if pd.notna(sharpe) and sharpe > 0.50 and pd.notna(ic) and ic > 0.02:
        return "candidate"
    if pd.notna(ic) and ic > 0.01 and (pd.isna(sharpe) or sharpe <= 0.50):
        return "feature_only"
    if pd.notna(recent_delta) and recent_delta < -0.02:
        return "decayed"
    return "discard"


def build_leaderboard(metric_panel: pd.DataFrame, portfolio_report: pd.DataFrame, decay_report: pd.DataFrame, registry: pd.DataFrame) -> pd.DataFrame:
    best_ic = (
        metric_panel.query("horizon_days == @PRIMARY_HORIZON")
        .sort_values("mean_rank_ic", ascending=False)
        .groupby(["panel", "alpha_id"])
        .head(1)
        [["panel", "alpha_id", "mean_rank_ic", "rank_icir", "positive_ic_rate", "transform"]]
        .rename(columns={"mean_rank_ic": "best_5d_ic", "transform": "best_ic_transform"})
    )
    best_port = (
        portfolio_report.query("cost_bps == 20.0")
        .sort_values("active_sharpe", ascending=False)
        .groupby(["panel", "alpha_id"])
        .head(1)
        [["panel", "alpha_id", "active_sharpe", "active_cagr", "alpha_avg_daily_turnover", "signal_transform", "mask", "strategy"]]
        .rename(columns={"active_sharpe": "best_20bps_active_sharpe", "active_cagr": "best_20bps_active_cagr", "signal_transform": "best_signal_transform", "mask": "best_mask", "strategy": "best_strategy"})
    )
    recent = (
        decay_report.query("era == 'recent_minus_old'")
        [["panel", "alpha_id", "mean_rank_ic"]]
        .rename(columns={"mean_rank_ic": "recent_minus_old_ic"})
    )
    board = registry[["alpha_id", "family", "input_quality_tier", "required_inputs"]].merge(best_ic, on="alpha_id", how="left").merge(best_port, on=["panel", "alpha_id"], how="left").merge(recent, on=["panel", "alpha_id"], how="left")
    board["classification"] = board.apply(classify_alpha, axis=1)
    board["research_score"] = (
        board["best_20bps_active_sharpe"].fillna(-2.0)
        + 5.0 * board["best_5d_ic"].fillna(0.0)
        + 0.25 * board["positive_ic_rate"].fillna(0.0)
        - 0.25 * board["alpha_avg_daily_turnover"].fillna(0.5)
    )
    return board.sort_values(["classification", "research_score"], ascending=[True, False])


def markdown_table(frame: pd.DataFrame, index: bool = False) -> str:
    if frame.empty:
        return ""
    view = frame.reset_index() if index else frame.copy()
    view = view.astype(object).where(pd.notna(view), "")
    headers = [str(col) for col in view.columns]
    rows = [[str(value) for value in row] for row in view.to_numpy()]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def final_report_markdown(leaderboard: pd.DataFrame, registry: pd.DataFrame, formula_validation: pd.DataFrame) -> str:
    counts = leaderboard["classification"].value_counts(dropna=False)
    input_counts = registry["input_quality_tier"].value_counts(dropna=False)
    failed = formula_validation[~formula_validation["computed"].fillna(False)]
    top = leaderboard.sort_values("research_score", ascending=False).head(25)
    return "\n".join([
        "# Alpha101 Research Factory Report",
        "",
        "This report evaluates the Kakushadze 101 Formulaic Alphas on the cached NIFTY500 and expanded India equity universes.",
        "",
        "## Classification Counts",
        markdown_table(counts.to_frame("alpha_panel_rows"), index=True),
        "",
        "## Input Quality Counts",
        markdown_table(input_counts.to_frame("alphas"), index=True),
        "",
        "## Formula Failures / Untestable",
        markdown_table(failed[["panel", "alpha_id", "reason"]]) if not failed.empty else "All formula computations produced outputs.",
        "",
        "## Top 25 Research Scores",
        markdown_table(top[["panel", "alpha_id", "family", "input_quality_tier", "classification", "best_5d_ic", "best_20bps_active_sharpe", "best_signal_transform", "best_strategy", "best_mask", "research_score"]]),
        "",
        "## Limitations",
        "- VWAP is proxied by typical price `(high + low + close) / 3`.",
        "- Industry neutralization uses current snapshot industry metadata.",
        "- Parent constituent histories are current snapshots, so expanded-universe results carry PIT/survivorship risk.",
        "- Transform winners are research candidates; transform selection is reported separately to control data-mining risk.",
    ])


def run_alpha101_factory(max_workers: int | None = None, refresh: bool = False, progress: bool = True, reaggregate: bool = False) -> dict[str, pd.DataFrame]:
    ALPHA101_ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    paths = {
        "registry": ALPHA101_ARTIFACT_DIR / "alpha101_formula_registry.csv",
        "input_quality": ALPHA101_ARTIFACT_DIR / "alpha101_input_quality_report.csv",
        "operator_validation": ALPHA101_ARTIFACT_DIR / "alpha101_operator_validation.csv",
        "formula_validation": ALPHA101_ARTIFACT_DIR / "alpha101_formula_validation.csv",
        "family_classification": ALPHA101_ARTIFACT_DIR / "alpha101_family_classification.csv",
        "transform_compatibility": ALPHA101_ARTIFACT_DIR / "alpha101_transform_compatibility.csv",
        "metric_panel": ALPHA101_ARTIFACT_DIR / "alpha101_metric_panel.csv",
        "transform_grid": ALPHA101_ARTIFACT_DIR / "alpha101_transform_grid.csv",
        "decay_report": ALPHA101_ARTIFACT_DIR / "alpha101_decay_report.csv",
        "portfolio_report": ALPHA101_ARTIFACT_DIR / "alpha101_portfolio_report.csv",
        "leaderboard": ALPHA101_ARTIFACT_DIR / "alpha101_leaderboard.csv",
        "shortlist": ALPHA101_ARTIFACT_DIR / "alpha101_candidate_shortlist.csv",
        "final_report": ALPHA101_ARTIFACT_DIR / "alpha101_final_report.md",
    }
    if not refresh and not reaggregate and all(path.exists() for key, path in paths.items() if key != "final_report"):
        return {key: pd.read_csv(path) for key, path in paths.items() if key != "final_report"}

    registry = registry_frame()
    input_quality = registry[["alpha_id", "required_inputs", "input_quality_tier", "notes"]].copy()
    op_validation = operator_validation()
    family = registry[["alpha_id", "family"]].copy()
    compatibility = transform_compatibility_frame()
    tasks = [(spec.alpha_id, panel_name) for spec in FORMULA_REGISTRY for panel_name in PANELS]
    workers = max_workers if max_workers is not None else min(4, len(tasks))
    results = []
    if workers <= 1:
        for i, task in enumerate(tasks, start=1):
            results.append(evaluate_alpha_panel_cached(task, refresh=refresh and not reaggregate))
            if progress:
                print(f"[alpha101] {i}/{len(tasks)} completed {task[0]} {task[1]}", flush=True)
    else:
        with futures.ProcessPoolExecutor(max_workers=workers) as pool:
            future_map = {pool.submit(evaluate_alpha_panel_cached, task, refresh and not reaggregate): task for task in tasks}
            for i, future in enumerate(futures.as_completed(future_map), start=1):
                task = future_map[future]
                result = future.result()
                results.append(result)
                if progress:
                    formula = result["formula_validation"]
                    status = "computed"
                    if not formula.empty and not bool(formula["computed"].fillna(False).iloc[0]):
                        status = str(formula["reason"].fillna("failed").iloc[0])[:80]
                    print(f"[alpha101] {i}/{len(tasks)} completed {task[0]} {task[1]}: {status}", flush=True)

    formula_validation = pd.concat([r["formula_validation"] for r in results], ignore_index=True)
    metric_panel = pd.concat([r["metric_panel"] for r in results if not r["metric_panel"].empty], ignore_index=True)
    decay_report = pd.concat([r["decay_report"] for r in results if not r["decay_report"].empty], ignore_index=True)
    portfolio_report = pd.concat([r["portfolio_report"] for r in results if not r["portfolio_report"].empty], ignore_index=True)
    leaderboard = build_leaderboard(metric_panel, portfolio_report, decay_report, registry)
    shortlist = leaderboard[leaderboard["classification"].isin(["candidate", "feature_only"])].sort_values("research_score", ascending=False).head(50)
    transform_grid = portfolio_report.groupby(["panel", "family", "signal_transform", "mask", "strategy", "cost_bps"], dropna=False).agg(
        mean_active_sharpe=("active_sharpe", "mean"),
        median_active_sharpe=("active_sharpe", "median"),
        positive_active_rate=("active_sharpe", lambda s: s.gt(0).mean()),
        alphas=("alpha_id", "nunique"),
    ).reset_index()

    outputs = {
        "registry": registry,
        "input_quality": input_quality,
        "operator_validation": op_validation,
        "formula_validation": formula_validation,
        "family_classification": family,
        "transform_compatibility": compatibility,
        "metric_panel": metric_panel,
        "transform_grid": transform_grid,
        "decay_report": decay_report,
        "portfolio_report": portfolio_report,
        "leaderboard": leaderboard,
        "shortlist": shortlist,
    }
    for key, frame in outputs.items():
        frame.to_csv(paths[key], index=False)
    paths["final_report"].write_text(final_report_markdown(leaderboard, registry, formula_validation))
    return outputs


if __name__ == "__main__":
    out = run_alpha101_factory(max_workers=1, refresh=False)
    print(out["leaderboard"].head(25).to_string(index=False))
