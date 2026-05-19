from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


ANNUALIZATION = 252
ARTIFACT_SUBDIR = Path("research/artifacts/alpha001_research_to_alpha")
NIFTY500_DATA_SUBDIR = Path("research/data/nifty500_high_vol")
EXPANDED_DATA_SUBDIR = Path("research/data/expanded_high_vol_parent")


@dataclass(frozen=True)
class PanelData:
    name: str
    adj_close: pd.DataFrame
    raw_close: pd.DataFrame
    volume: pd.DataFrame
    active_mask: pd.DataFrame
    constituents: pd.DataFrame


def read_frame(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, index_col=0, parse_dates=True)
    frame.index = pd.to_datetime(frame.index).tz_localize(None)
    return frame.sort_index()


def read_bool_frame(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, index_col=0, parse_dates=True)
    frame.index = pd.to_datetime(frame.index).tz_localize(None)
    if frame.dtypes.astype(str).str.contains("bool").all():
        return frame.sort_index().astype(bool)
    return frame.sort_index().astype(str).apply(lambda col: col.str.lower().isin({"true", "1", "yes"}))


def forward_return(price: pd.DataFrame, horizon: int) -> pd.DataFrame:
    return price.shift(-horizon).div(price).sub(1.0)


def next_session_returns(price: pd.DataFrame) -> pd.DataFrame:
    return price.pct_change(fill_method=None).shift(-1)


def row_zscore(frame: pd.DataFrame) -> pd.DataFrame:
    mean = frame.mean(axis=1)
    std = frame.std(axis=1, ddof=0).replace(0.0, np.nan)
    return frame.sub(mean, axis=0).div(std, axis=0)


def centered_rank(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.rank(axis=1, pct=True) - 0.5


def fast_rank_ic_by_date(signal: pd.DataFrame, future: pd.DataFrame, min_names: int = 10) -> pd.Series:
    common_index = signal.index.intersection(future.index)
    common_columns = signal.columns.intersection(future.columns)
    s = signal.loc[common_index, common_columns].astype(float)
    f = future.loc[common_index, common_columns].astype(float)
    valid = s.notna() & f.notna()
    count = valid.sum(axis=1).astype(float)

    x = s.rank(axis=1, method="average").where(valid)
    y = f.rank(axis=1, method="average").where(valid)
    x_mean = x.sum(axis=1).div(count)
    y_mean = y.sum(axis=1).div(count)
    x_centered = x.sub(x_mean, axis=0).where(valid, 0.0)
    y_centered = y.sub(y_mean, axis=0).where(valid, 0.0)
    numerator = x_centered.mul(y_centered).sum(axis=1)
    denominator = np.sqrt(x_centered.pow(2).sum(axis=1).mul(y_centered.pow(2).sum(axis=1)))
    ic = numerator.div(denominator).replace([np.inf, -np.inf], np.nan)
    ic[count < min_names] = np.nan
    return ic.rename("rank_ic")


def fast_ts_argmax_position(frame: pd.DataFrame, window: int) -> pd.DataFrame:
    values = frame.to_numpy(dtype=float, copy=False)
    out = np.full(values.shape, np.nan, dtype=float)
    if len(frame) < window:
        return pd.DataFrame(out, index=frame.index, columns=frame.columns)

    windows = np.lib.stride_tricks.sliding_window_view(values, window_shape=window, axis=0)
    all_nan = np.isnan(windows).all(axis=-1)
    filled = np.where(np.isnan(windows), -np.inf, windows)
    positions = np.argmax(filled, axis=-1).astype(float) + 1.0
    positions[all_nan] = np.nan
    out[window - 1 :] = positions
    return pd.DataFrame(out, index=frame.index, columns=frame.columns)


def fast_alpha001(
    close: pd.DataFrame,
    returns: pd.DataFrame,
    active_mask: pd.DataFrame,
    argmax_window: int = 5,
    vol_lookback: int = 20,
    power: float = 2.0,
    negative_return_threshold_sigma: float = 0.0,
) -> pd.DataFrame:
    rolling_vol = returns.rolling(vol_lookback, min_periods=vol_lookback).std()
    if negative_return_threshold_sigma == 0.0:
        use_vol = returns.lt(0)
    else:
        use_vol = returns.lt(-negative_return_threshold_sigma * rolling_vol)
    condition_value = close.where(~use_vol, rolling_vol)
    transformed = np.sign(condition_value) * np.power(condition_value.abs(), power)
    argmax = fast_ts_argmax_position(transformed, argmax_window)
    active_argmax = argmax.where(active_mask.reindex_like(argmax).fillna(False))
    return centered_rank(active_argmax)


def causal_orient_signal(
    signal: pd.DataFrame,
    future: pd.DataFrame,
    horizon: int,
    train_window: int = 504,
    min_ic_observations: int = 126,
) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    raw_ic = fast_rank_ic_by_date(signal, future, min_names=10)
    train_mean_ic = raw_ic.shift(horizon).rolling(train_window, min_periods=min_ic_observations).mean()
    direction = pd.Series(np.where(train_mean_ic >= 0, 1.0, -1.0), index=signal.index, name="causal_direction")
    direction[train_mean_ic.isna()] = np.nan
    oriented = signal.mul(direction, axis=0)
    return oriented, direction, train_mean_ic


def smooth_signal(signal: pd.DataFrame, method: str) -> pd.DataFrame:
    if method == "raw":
        return signal
    if method == "ewm3":
        return signal.ewm(span=3, min_periods=2, adjust=False).mean()
    if method == "ewm5":
        return signal.ewm(span=5, min_periods=3, adjust=False).mean()
    raise ValueError(f"Unknown smoothing method: {method}")


def weekly_rebalance_mask(index: pd.DatetimeIndex) -> pd.Series:
    weeks = pd.Series(index.to_period("W-FRI"), index=index)
    mask = weeks.ne(weeks.shift(1))
    if len(mask):
        mask.iloc[0] = True
    return mask.astype(bool)


def equal_weight_targets(active_mask: pd.DataFrame) -> pd.DataFrame:
    mask = active_mask.fillna(False).astype(bool)
    counts = mask.sum(axis=1).replace(0, np.nan)
    return mask.astype(float).div(counts, axis=0).fillna(0.0)


def normalized_positive(raw: pd.DataFrame) -> pd.DataFrame:
    clipped = raw.clip(lower=0.0).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    row_sum = clipped.sum(axis=1).replace(0.0, np.nan)
    return clipped.div(row_sum, axis=0).fillna(0.0)


def overlay_targets(signal: pd.DataFrame, active_mask: pd.DataFrame, active_budget: float) -> pd.DataFrame:
    mask = active_mask.reindex_like(signal).fillna(False).astype(bool)
    base = equal_weight_targets(mask)
    z = row_zscore(signal.where(mask)).where(mask, 0.0)
    active = z.div(z.abs().sum(axis=1).replace(0.0, np.nan), axis=0).fillna(0.0) * active_budget
    return normalized_positive(base + active).where(mask, 0.0)


def score_tilt_targets(signal: pd.DataFrame, active_mask: pd.DataFrame, intensity: float) -> pd.DataFrame:
    mask = active_mask.reindex_like(signal).fillna(False).astype(bool)
    z = row_zscore(signal.where(mask)).where(mask)
    raw = (1.0 + intensity * z).clip(lower=0.05).where(mask)
    return normalized_positive(raw).where(mask, 0.0)


def rank_weight_targets(signal: pd.DataFrame, active_mask: pd.DataFrame) -> pd.DataFrame:
    mask = active_mask.reindex_like(signal).fillna(False).astype(bool)
    raw = (signal.where(mask) + 0.5).clip(lower=0.0)
    return normalized_positive(raw).where(mask, 0.0)


def positive_score_targets(signal: pd.DataFrame, active_mask: pd.DataFrame) -> pd.DataFrame:
    mask = active_mask.reindex_like(signal).fillna(False).astype(bool)
    raw = signal.where(mask).clip(lower=0.0)
    fallback = equal_weight_targets(mask)
    targets = normalized_positive(raw).where(mask, 0.0)
    empty = targets.sum(axis=1).eq(0) & mask.any(axis=1)
    targets.loc[empty] = fallback.loc[empty]
    return targets


def carry_targets_on_rebalance(
    targets: pd.DataFrame,
    rebalance_mask: pd.Series,
    partial_adjustment: float = 1.0,
    no_trade_band: float = 0.0,
) -> pd.DataFrame:
    rebalance_mask = rebalance_mask.reindex(targets.index).fillna(False).astype(bool)
    weights = pd.DataFrame(0.0, index=targets.index, columns=targets.columns)
    last = pd.Series(0.0, index=targets.columns)
    for i, date in enumerate(targets.index):
        if i == 0 or bool(rebalance_mask.loc[date]):
            target = targets.loc[date].fillna(0.0).astype(float)
            if no_trade_band > 0.0:
                diff = target - last
                target = last + diff.where(diff.abs() >= no_trade_band, 0.0)
            if partial_adjustment < 1.0:
                target = last + partial_adjustment * (target - last)
            gross = target.abs().sum()
            if gross > 0:
                target = target / target.sum() if target.sum() > 0 else target / gross
            last = target.reindex(targets.columns).fillna(0.0)
        weights.loc[date] = last
    return weights


def buffered_top_weights(
    signal: pd.DataFrame,
    top_n: int,
    exit_rank: int,
    rebalance_mask: pd.Series,
) -> pd.DataFrame:
    weights = pd.DataFrame(0.0, index=signal.index, columns=signal.columns)
    holdings: list[str] = []
    for i, date in enumerate(signal.index):
        if i == 0 or bool(rebalance_mask.reindex(signal.index).fillna(False).loc[date]):
            scores = signal.loc[date].dropna().sort_values(ascending=False)
            rank_map = pd.Series(np.arange(1, len(scores) + 1), index=scores.index)
            holdings = [name for name in holdings if name in rank_map.index and rank_map.loc[name] <= exit_rank]
            for name in scores.index:
                if len(holdings) >= top_n:
                    break
                if name not in holdings:
                    holdings.append(name)
            holdings = holdings[:top_n]
        if holdings:
            weights.loc[date, holdings] = 1.0 / len(holdings)
    return weights


def portfolio_gross_returns(weights: pd.DataFrame, returns: pd.DataFrame) -> pd.Series:
    aligned = returns.reindex(index=weights.index, columns=weights.columns)
    valid_weighted = weights.abs().gt(0) & aligned.notna()
    no_exposure = weights.abs().sum(axis=1).eq(0)
    gross = weights.mul(aligned).sum(axis=1, min_count=1)
    return gross.where(valid_weighted.any(axis=1) | no_exposure, np.nan)


def backtest_weights(weights: pd.DataFrame, returns: pd.DataFrame, cost_bps: float) -> dict[str, pd.Series | dict]:
    gross = portfolio_gross_returns(weights, returns)
    turnover = weights.diff().abs().sum(axis=1, min_count=1).fillna(weights.abs().sum(axis=1))
    costs = turnover * (cost_bps / 10000.0)
    net = gross - costs
    valid_index = net.dropna().index
    return {
        "returns": net.reindex(valid_index),
        "gross_returns": gross.reindex(valid_index),
        "turnover": turnover.reindex(valid_index).fillna(0.0),
        "costs": costs.reindex(valid_index).fillna(0.0),
        "metrics": performance_metrics(net, turnover),
    }


def performance_metrics(returns: pd.Series, turnover: pd.Series | None = None, periods_per_year: int = ANNUALIZATION) -> dict:
    r = returns.dropna().astype(float)
    if r.empty:
        return {
            "cagr": np.nan,
            "ann_return": np.nan,
            "ann_vol": np.nan,
            "sharpe": np.nan,
            "sortino": np.nan,
            "max_drawdown": np.nan,
            "hit_rate": np.nan,
            "avg_daily_turnover": np.nan,
            "observations": 0,
        }
    equity = (1.0 + r).cumprod()
    years = len(r) / periods_per_year
    cagr = equity.iloc[-1] ** (1.0 / years) - 1.0 if years > 0 and equity.iloc[-1] > 0 else np.nan
    ann_return = r.mean() * periods_per_year
    ann_vol = r.std(ddof=0) * math.sqrt(periods_per_year)
    downside = r.where(r < 0).dropna()
    downside_vol = downside.std(ddof=0) * math.sqrt(periods_per_year) if len(downside) > 1 else np.nan
    drawdown = equity.div(equity.cummax()).sub(1.0)
    return {
        "cagr": cagr,
        "ann_return": ann_return,
        "ann_vol": ann_vol,
        "sharpe": ann_return / ann_vol if ann_vol and not pd.isna(ann_vol) else np.nan,
        "sortino": ann_return / downside_vol if downside_vol and not pd.isna(downside_vol) else np.nan,
        "max_drawdown": drawdown.min(),
        "hit_rate": r.gt(0).mean(),
        "avg_daily_turnover": turnover.reindex(r.index).mean() if turnover is not None else np.nan,
        "observations": len(r),
    }


def active_report_row(
    panel: str,
    strategy: str,
    horizon: int,
    smoothing: str,
    cost_bps: float,
    weights: pd.DataFrame,
    benchmark_weights: pd.DataFrame,
    returns: pd.DataFrame,
    extra: dict | None = None,
) -> dict:
    alpha_bt = backtest_weights(weights, returns, cost_bps)
    benchmark_bt = backtest_weights(benchmark_weights, returns, cost_bps)
    pair = pd.concat(
        [
            alpha_bt["returns"].rename("alpha"),
            benchmark_bt["returns"].rename("benchmark"),
        ],
        axis=1,
    ).dropna()
    excess = pair["alpha"] - pair["benchmark"]
    row = {
        "panel": panel,
        "strategy": strategy,
        "horizon_days": horizon,
        "smoothing": smoothing,
        "cost_bps": cost_bps,
        "avg_names": weights.abs().gt(1e-12).sum(axis=1).replace(0, np.nan).mean(),
        "avg_gross_exposure": weights.abs().sum(axis=1).replace(0, np.nan).mean(),
    }
    row.update({f"alpha_{k}": v for k, v in alpha_bt["metrics"].items()})
    row.update({f"benchmark_{k}": v for k, v in benchmark_bt["metrics"].items()})
    row.update({f"active_{k}": v for k, v in performance_metrics(excess).items()})
    row["cost_drag_ann"] = alpha_bt["costs"].mean() * ANNUALIZATION if len(alpha_bt["costs"]) else np.nan
    if extra:
        row.update(extra)
    return row


def style_factor_frames(panel: PanelData) -> dict[str, pd.DataFrame]:
    returns = panel.adj_close.pct_change(fill_method=None)
    adv20 = panel.raw_close.mul(panel.volume).rolling(20, min_periods=20).mean()
    factors = {
        "stock_vol_20d": returns.rolling(20, min_periods=20).std() * math.sqrt(ANNUALIZATION),
        "stock_mom_20d": panel.adj_close.pct_change(20, fill_method=None),
        "stock_mom_63d": panel.adj_close.pct_change(63, fill_method=None),
        "stock_reversal_5d": -panel.adj_close.pct_change(5, fill_method=None),
        "stock_volume_intensity": panel.volume.div(panel.volume.rolling(20, min_periods=20).mean()),
        "stock_adv20_rupees": adv20,
    }
    return {name: frame.reindex_like(panel.adj_close) for name, frame in factors.items()}


def interaction_report(panel_name: str, alpha_by_horizon: dict[int, pd.DataFrame], factors: dict[str, pd.DataFrame], mask: pd.DataFrame, forward_by_horizon: dict[int, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for horizon, alpha in alpha_by_horizon.items():
        future = forward_by_horizon[horizon]
        candidates = {"alpha001": alpha}
        for factor_name, factor in factors.items():
            factor_rank = centered_rank(factor.where(mask)).where(mask)
            candidates[f"alpha_x_{factor_name}"] = alpha * factor_rank
            candidates[f"alpha_only_{factor_name}_high"] = alpha.where(factor_rank >= 1.0 / 6.0)
            candidates[f"alpha_only_{factor_name}_low"] = alpha.where(factor_rank <= -1.0 / 6.0)
        for feature_name, feature_signal in candidates.items():
            ic = fast_rank_ic_by_date(feature_signal, future)
            vol = ic.std()
            rows.append(
                {
                    "panel": panel_name,
                    "feature": feature_name,
                    "horizon_days": horizon,
                    "mean_rank_ic": ic.mean(),
                    "rank_ic_vol": vol,
                    "rank_icir": ic.mean() / vol if vol and not pd.isna(vol) else np.nan,
                    "positive_ic_rate": ic.dropna().gt(0).mean(),
                    "observations": ic.notna().sum(),
                }
            )
    return pd.DataFrame(rows)


def industry_dummy_frame(constituents: pd.DataFrame, columns: pd.Index) -> pd.DataFrame:
    if "Industry" in constituents.columns:
        industry_col = "Industry"
        symbol_col = "Symbol"
    elif "industry" in constituents.columns:
        industry_col = "industry"
        symbol_col = "Symbol"
    else:
        return pd.DataFrame(index=columns)
    industry = constituents.drop_duplicates(symbol_col).set_index(symbol_col)[industry_col].reindex(columns).fillna("unknown")
    return pd.get_dummies(industry, prefix="industry", dtype=float)


def residualize_signal(
    signal: pd.DataFrame,
    factors: dict[str, pd.DataFrame],
    active_mask: pd.DataFrame,
    industry_dummies: pd.DataFrame | None = None,
    min_names: int = 30,
) -> pd.DataFrame:
    style_ranks = {name: centered_rank(frame.where(active_mask)).where(active_mask) for name, frame in factors.items()}
    residual = pd.DataFrame(np.nan, index=signal.index, columns=signal.columns)
    static_industry = industry_dummies.reindex(signal.columns).fillna(0.0) if industry_dummies is not None and not industry_dummies.empty else None
    for date in signal.index:
        y = signal.loc[date]
        valid = y.notna() & active_mask.reindex_like(signal).loc[date].fillna(False)
        for frame in style_ranks.values():
            valid &= frame.loc[date].notna()
        if valid.sum() < min_names:
            continue
        x_parts = [np.ones((int(valid.sum()), 1))]
        for frame in style_ranks.values():
            x_parts.append(frame.loc[date, valid].to_numpy(dtype=float).reshape(-1, 1))
        if static_industry is not None:
            x_parts.append(static_industry.loc[valid].to_numpy(dtype=float))
        x = np.concatenate(x_parts, axis=1)
        yv = y.loc[valid].to_numpy(dtype=float)
        beta, *_ = np.linalg.lstsq(x, yv, rcond=None)
        residual.loc[date, valid] = yv - x @ beta
    return centered_rank(residual.where(active_mask))


def neutralized_ic_report(panel_name: str, alpha_by_horizon: dict[int, pd.DataFrame], factors: dict[str, pd.DataFrame], mask: pd.DataFrame, constituents: pd.DataFrame, forward_by_horizon: dict[int, pd.DataFrame]) -> pd.DataFrame:
    style_subset = {k: factors[k] for k in ["stock_vol_20d", "stock_mom_20d", "stock_mom_63d", "stock_reversal_5d", "stock_adv20_rupees"]}
    industry_dummies = industry_dummy_frame(constituents, mask.columns)
    rows = []
    for horizon, alpha in alpha_by_horizon.items():
        variants = {
            "raw_oriented": alpha,
            "style_residual": residualize_signal(alpha, style_subset, mask, industry_dummies=None),
            "style_industry_residual": residualize_signal(alpha, style_subset, mask, industry_dummies=industry_dummies),
        }
        for variant, signal in variants.items():
            ic = fast_rank_ic_by_date(signal, forward_by_horizon[horizon])
            vol = ic.std()
            rows.append(
                {
                    "panel": panel_name,
                    "variant": variant,
                    "horizon_days": horizon,
                    "mean_rank_ic": ic.mean(),
                    "rank_ic_vol": vol,
                    "rank_icir": ic.mean() / vol if vol and not pd.isna(vol) else np.nan,
                    "positive_ic_rate": ic.dropna().gt(0).mean(),
                    "observations": ic.notna().sum(),
                }
            )
    return pd.DataFrame(rows)


def build_gate_frame(base_dir: Path, index: pd.DatetimeIndex) -> pd.DataFrame:
    artifact_dir = base_dir / ARTIFACT_SUBDIR
    gates = pd.DataFrame(index=index)
    gates["all"] = True

    high_vol_features_path = artifact_dir / "high_vol_causal_regime_features.csv"
    if high_vol_features_path.exists():
        hv = read_frame(high_vol_features_path).reindex(index).ffill()
        gates["breadth_weak"] = hv.get("breadth_level", pd.Series(index=index, dtype=object)).eq("weak")
        gates["dispersion_high"] = hv.get("dispersion_level", pd.Series(index=index, dtype=object)).eq("high")
        gates["vol_change_rising"] = hv.get("market_vol_change", pd.Series(index=index, dtype=object)).eq("rising")
        gates["breadth_weak_or_vol_rising"] = gates["breadth_weak"] | gates["vol_change_rising"]
        gates["transition_stress_2of3"] = (
            gates[["breadth_weak", "dispersion_high", "vol_change_rising"]].sum(axis=1) >= 2
        )

    volatile_features_path = artifact_dir / "volatile_index_regime_features.csv"
    if volatile_features_path.exists():
        vi = read_frame(volatile_features_path).reindex(index).ffill()
        for col in [
            "nifty_midcap_150_breadth",
            "nifty_smallcap_250_breadth",
            "nifty_midcap_150_mom20",
            "nifty_smallcap_250_mom20",
            "india_vix_change",
        ]:
            if col in vi.columns:
                if col.endswith("_breadth"):
                    gates[f"{col}_weak"] = vi[col].eq("weak")
                elif col.endswith("_mom20"):
                    gates[f"{col}_weak"] = vi[col].eq("weak")
                elif col == "india_vix_change":
                    gates["india_vix_rising"] = vi[col].eq("rising")
        breadth_cols = [c for c in gates.columns if c.endswith("_breadth_weak")]
        if breadth_cols:
            gates["any_index_breadth_weak"] = gates[breadth_cols].any(axis=1)
    return gates.fillna(False).astype(bool)


def walk_forward_gate_selection(
    panel_name: str,
    candidate_weights: dict[str, pd.DataFrame],
    benchmark_weights: pd.DataFrame,
    returns: pd.DataFrame,
    gates: pd.DataFrame,
    cost_bps: float = 20.0,
    train_days: int = 504,
    test_days: int = 126,
    step_days: int = 126,
) -> pd.DataFrame:
    index = benchmark_weights.index.intersection(returns.index).intersection(gates.index)
    rows = []
    for start in range(0, max(0, len(index) - train_days - test_days + 1), step_days):
        train_idx = index[start : start + train_days]
        test_idx = index[start + train_days : start + train_days + test_days]
        if len(test_idx) < 60:
            continue
        train_scores = []
        for strategy, weights in candidate_weights.items():
            for gate_name, gate in gates.items():
                if gate.loc[train_idx].mean() < 0.15:
                    continue
                gated_weights = weights.where(gate.reindex(weights.index), 0.0)
                gated_benchmark = benchmark_weights.where(gate.reindex(benchmark_weights.index), 0.0)
                train_row = active_report_row(
                    panel_name,
                    strategy,
                    -1,
                    "wf_candidate",
                    cost_bps,
                    gated_weights.loc[train_idx],
                    gated_benchmark.loc[train_idx],
                    returns.loc[train_idx],
                    {"gate": gate_name},
                )
                train_scores.append(train_row)
        if not train_scores:
            continue
        train_table = pd.DataFrame(train_scores)
        train_table["selection_score"] = (
            train_table["active_sharpe"].fillna(-10.0)
            - 0.50 * train_table["alpha_avg_daily_turnover"].fillna(1.0)
            + 0.10 * train_table["active_hit_rate"].fillna(0.0)
        )
        best = train_table.sort_values("selection_score", ascending=False).iloc[0]
        best_weights = candidate_weights[str(best["strategy"])]
        best_gate = gates[str(best["gate"])]
        gated_weights = best_weights.where(best_gate.reindex(best_weights.index), 0.0)
        gated_benchmark = benchmark_weights.where(best_gate.reindex(benchmark_weights.index), 0.0)
        test_row = active_report_row(
            panel_name,
            str(best["strategy"]),
            -1,
            "wf_selected",
            cost_bps,
            gated_weights.loc[test_idx],
            gated_benchmark.loc[test_idx],
            returns.loc[test_idx],
            {"gate": str(best["gate"])},
        )
        rows.append(
            {
                "panel": panel_name,
                "fold_start": test_idx.min(),
                "fold_end": test_idx.max(),
                "chosen_strategy": str(best["strategy"]),
                "chosen_gate": str(best["gate"]),
                "candidate_family": "predeclared_review_thesis",
                "candidate_count": len(candidate_weights),
                "train_selection_score": best["selection_score"],
                "train_active_sharpe": best["active_sharpe"],
                "train_alpha_turnover": best["alpha_avg_daily_turnover"],
                "test_active_cagr": test_row["active_cagr"],
                "test_active_sharpe": test_row["active_sharpe"],
                "test_active_hit_rate": test_row["active_hit_rate"],
                "test_alpha_cagr": test_row["alpha_cagr"],
                "test_benchmark_cagr": test_row["benchmark_cagr"],
                "test_alpha_turnover": test_row["alpha_avg_daily_turnover"],
                "test_cost_drag_ann": test_row["cost_drag_ann"],
                "test_observations": test_row["active_observations"],
            }
        )
    return pd.DataFrame(rows)


def load_panel(base_dir: Path, name: str) -> PanelData:
    artifact_dir = base_dir / ARTIFACT_SUBDIR
    if name == "nifty500_high_vol_top100":
        data_dir = base_dir / NIFTY500_DATA_SUBDIR
        mask_path = artifact_dir / "dynamic_high_vol_universe_mask_top100.csv"
        constituents_path = data_dir / "nifty500_constituents.csv"
    elif name == "expanded_high_vol_top100":
        data_dir = base_dir / EXPANDED_DATA_SUBDIR
        mask_path = artifact_dir / "expanded_high_vol_universe_mask_top100.csv"
        constituents_path = data_dir / "expanded_parent_constituents.csv"
    else:
        raise ValueError(f"Unknown panel: {name}")
    adj_close = read_frame(data_dir / "adj_close.csv")
    raw_close = read_frame(data_dir / "close.csv")
    volume = read_frame(data_dir / "volume.csv")
    mask = read_bool_frame(mask_path)
    common_columns = adj_close.columns.intersection(mask.columns)
    constituents = pd.read_csv(constituents_path)
    return PanelData(
        name=name,
        adj_close=adj_close.loc[:, common_columns],
        raw_close=raw_close.loc[:, common_columns],
        volume=volume.loc[:, common_columns],
        active_mask=mask.reindex(index=adj_close.index, columns=common_columns).fillna(False).astype(bool),
        constituents=constituents,
    )


def candidate_weight_grid(signal_by_key: dict[tuple[int, str], pd.DataFrame], active_mask: pd.DataFrame) -> dict[str, pd.DataFrame]:
    rebalance = weekly_rebalance_mask(active_mask.index)
    weights = {}
    benchmark_targets = equal_weight_targets(active_mask)
    weights["equal_weight_active"] = carry_targets_on_rebalance(benchmark_targets, rebalance)
    for (horizon, smoothing), signal in signal_by_key.items():
        for budget in [0.20, 0.35]:
            targets = overlay_targets(signal, active_mask, active_budget=budget)
            for partial in [1.0, 0.50]:
                for band in [0.0, 0.0025]:
                    key = f"h{horizon}_{smoothing}_overlay{int(budget*100)}_partial{int(partial*100)}_band{int(band*10000)}"
                    weights[key] = carry_targets_on_rebalance(targets, rebalance, partial_adjustment=partial, no_trade_band=band)
        for intensity in [0.25, 0.50]:
            targets = score_tilt_targets(signal, active_mask, intensity=intensity)
            key = f"h{horizon}_{smoothing}_scoretilt{int(intensity*100)}_partial50_band25"
            weights[key] = carry_targets_on_rebalance(targets, rebalance, partial_adjustment=0.50, no_trade_band=0.0025)
        weights[f"h{horizon}_{smoothing}_rank_weight_partial50"] = carry_targets_on_rebalance(
            rank_weight_targets(signal, active_mask),
            rebalance,
            partial_adjustment=0.50,
            no_trade_band=0.0025,
        )
        weights[f"h{horizon}_{smoothing}_positive_score_partial50"] = carry_targets_on_rebalance(
            positive_score_targets(signal, active_mask),
            rebalance,
            partial_adjustment=0.50,
            no_trade_band=0.0025,
        )
        weights[f"h{horizon}_{smoothing}_top10_buffer35"] = buffered_top_weights(signal, top_n=10, exit_rank=35, rebalance_mask=rebalance)
    return weights


def predeclared_walk_forward_candidate_names() -> list[str]:
    """Thesis-driven candidate family for walk-forward selection.

    This avoids selecting candidates from the full-sample leaderboard before
    fold scoring. The set is intentionally small and centered on the review
    thesis: causal overlays, smoothing, modest active budget, and partial
    adjustment.
    """
    names = []
    for horizon in [3, 5]:
        for smoothing in ["raw", "ewm3", "ewm5"]:
            names.append(f"h{horizon}_{smoothing}_overlay20_partial50_band0")
        names.extend(
            [
                f"h{horizon}_ewm3_overlay20_partial50_band25",
                f"h{horizon}_ewm3_overlay35_partial50_band0",
                f"h{horizon}_ewm3_scoretilt25_partial50_band25",
                f"h{horizon}_ewm3_rank_weight_partial50",
            ]
        )
    return names


def run_panel_experiments(panel: PanelData, horizons: tuple[int, ...] = (3, 5)) -> dict[str, pd.DataFrame | dict[str, pd.DataFrame]]:
    returns = panel.adj_close.pct_change(fill_method=None)
    next_returns = next_session_returns(panel.adj_close)
    forward_by_horizon = {h: forward_return(panel.adj_close, h) for h in horizons}
    raw_alpha = fast_alpha001(panel.adj_close, returns, panel.active_mask)

    alpha_by_horizon = {}
    signal_by_key = {}
    orientation_rows = []
    for horizon in horizons:
        oriented, direction, train_mean_ic = causal_orient_signal(raw_alpha, forward_by_horizon[horizon], horizon=horizon)
        alpha_by_horizon[horizon] = oriented
        raw_ic = fast_rank_ic_by_date(raw_alpha, forward_by_horizon[horizon])
        oriented_ic = fast_rank_ic_by_date(oriented, forward_by_horizon[horizon])
        orientation_rows.append(
            {
                "panel": panel.name,
                "horizon_days": horizon,
                "raw_mean_rank_ic": raw_ic.mean(),
                "oriented_mean_rank_ic": oriented_ic.mean(),
                "oriented_positive_ic_rate": oriented_ic.dropna().gt(0).mean(),
                "orientation_available_fraction": direction.notna().mean(),
                "inverted_fraction_when_available": direction.dropna().eq(-1).mean() if direction.notna().any() else np.nan,
                "latest_train_mean_ic": train_mean_ic.dropna().iloc[-1] if train_mean_ic.notna().any() else np.nan,
            }
        )
        for smoothing in ["raw", "ewm3", "ewm5"]:
            signal_by_key[(horizon, smoothing)] = smooth_signal(oriented, smoothing).where(panel.active_mask)

    weights_by_strategy = candidate_weight_grid(signal_by_key, panel.active_mask)
    benchmark_weights = weights_by_strategy["equal_weight_active"]
    grid_rows = []
    for strategy, weights in weights_by_strategy.items():
        if strategy == "equal_weight_active":
            continue
        parts = strategy.split("_")
        horizon = int(parts[0][1:]) if parts and parts[0].startswith("h") else -1
        smoothing = parts[1] if len(parts) > 1 else "unknown"
        for cost_bps in [10.0, 20.0, 35.0, 50.0]:
            grid_rows.append(
                active_report_row(
                    panel.name,
                    strategy,
                    horizon,
                    smoothing,
                    cost_bps,
                    weights,
                    benchmark_weights,
                    next_returns,
                )
            )
    factors = style_factor_frames(panel)
    return {
        "orientation": pd.DataFrame(orientation_rows),
        "experiment_grid": pd.DataFrame(grid_rows),
        "interaction": interaction_report(panel.name, alpha_by_horizon, factors, panel.active_mask, forward_by_horizon),
        "neutralized_ic": neutralized_ic_report(panel.name, alpha_by_horizon, factors, panel.active_mask, panel.constituents, forward_by_horizon),
        "weights": weights_by_strategy,
        "benchmark_weights": benchmark_weights,
        "next_returns": next_returns,
    }


def salvage_decision(experiment_grid: pd.DataFrame, oos_gate_report: pd.DataFrame) -> pd.DataFrame:
    primary = experiment_grid.query("cost_bps == 20.0").sort_values("active_sharpe", ascending=False).head(1)
    best_grid = primary.iloc[0] if not primary.empty else pd.Series(dtype=object)
    best_panel = best_grid.get("panel", None)
    panel_oos = oos_gate_report[oos_gate_report["panel"].eq(best_panel)] if not oos_gate_report.empty and best_panel is not None else oos_gate_report
    oos_mean = panel_oos["test_active_sharpe"].mean() if not panel_oos.empty else np.nan
    oos_positive_rate = panel_oos["test_active_sharpe"].gt(0).mean() if not panel_oos.empty else np.nan
    best_active_20 = best_grid.get("active_sharpe", np.nan)
    best_active_35_rows = experiment_grid[
        (experiment_grid["strategy"].eq(best_grid.get("strategy")))
        & (experiment_grid["panel"].eq(best_grid.get("panel")))
        & (experiment_grid["cost_bps"].eq(35.0))
    ]
    best_active_35 = best_active_35_rows["active_sharpe"].iloc[0] if not best_active_35_rows.empty else np.nan
    if pd.notna(oos_mean) and oos_mean > 0.30 and oos_positive_rate >= 0.60 and pd.notna(best_active_35) and best_active_35 > 0:
        decision = "candidate_for_stricter_review"
    elif pd.notna(best_active_20) and best_active_20 > 0:
        decision = "research_promising_not_promoted"
    else:
        decision = "feature_only_continue_mining"
    return pd.DataFrame(
        [
            {
                "decision": decision,
                "best_full_sample_panel": best_panel,
                "best_full_sample_strategy": best_grid.get("strategy", None),
                "best_full_sample_20bps_active_sharpe": best_active_20,
                "same_strategy_35bps_active_sharpe": best_active_35,
                "same_panel_oos_gate_mean_active_sharpe": oos_mean,
                "same_panel_oos_gate_positive_fold_rate": oos_positive_rate,
                "walk_forward_candidate_family": "predeclared_review_thesis",
                "promotion_rule": "needs predeclared-family OOS active Sharpe > 0.30, positive folds >= 60%, and 35 bps active Sharpe > 0",
            }
        ]
    )


def salvage_artifact_paths(base_dir: str | Path = ".") -> dict[str, Path]:
    base = Path(base_dir).resolve()
    artifact_dir = base / ARTIFACT_SUBDIR
    return {
        "orientation": artifact_dir / "alpha001_salvage_orientation_report.csv",
        "experiment_grid": artifact_dir / "alpha001_salvage_experiment_grid.csv",
        "interaction": artifact_dir / "alpha001_interaction_feature_report.csv",
        "neutralized_ic": artifact_dir / "alpha001_neutralized_ic_report.csv",
        "turnover_control": artifact_dir / "alpha001_turnover_control_report.csv",
        "oos_gate": artifact_dir / "alpha001_oos_gate_report.csv",
        "oos_candidate_universe": artifact_dir / "alpha001_oos_candidate_universe.csv",
        "decision": artifact_dir / "alpha001_salvage_decision_report.csv",
    }


def load_salvage_artifacts(base_dir: str | Path = ".") -> dict[str, pd.DataFrame]:
    paths = salvage_artifact_paths(base_dir)
    date_columns = {
        "oos_gate": ["fold_start", "fold_end"],
    }
    outputs = {}
    for name, path in paths.items():
        kwargs = {}
        if name in date_columns:
            kwargs["parse_dates"] = date_columns[name]
        outputs[name] = pd.read_csv(path, **kwargs)
    return outputs


def run_salvage_experiments(base_dir: str | Path = ".", refresh: bool = False) -> dict[str, pd.DataFrame]:
    base = Path(base_dir).resolve()
    artifact_dir = base / ARTIFACT_SUBDIR
    artifact_dir.mkdir(parents=True, exist_ok=True)
    paths = salvage_artifact_paths(base)
    if not refresh and all(path.exists() for path in paths.values()):
        return load_salvage_artifacts(base)

    panels = [load_panel(base, "nifty500_high_vol_top100")]
    expanded_mask_path = artifact_dir / "expanded_high_vol_universe_mask_top100.csv"
    if expanded_mask_path.exists():
        panels.append(load_panel(base, "expanded_high_vol_top100"))

    panel_outputs = {panel.name: run_panel_experiments(panel) for panel in panels}
    experiment_grid = pd.concat([out["experiment_grid"] for out in panel_outputs.values()], ignore_index=True)
    orientation = pd.concat([out["orientation"] for out in panel_outputs.values()], ignore_index=True)
    interaction = pd.concat([out["interaction"] for out in panel_outputs.values()], ignore_index=True)
    neutralized_ic = pd.concat([out["neutralized_ic"] for out in panel_outputs.values()], ignore_index=True)

    oos_reports = []
    for panel_name, panel_output in panel_outputs.items():
        gates = build_gate_frame(base, panel_output["benchmark_weights"].index)
        candidate_names = predeclared_walk_forward_candidate_names()
        candidate_weights = {
            name: panel_output["weights"][name]
            for name in candidate_names
            if name in panel_output["weights"]
        }
        if candidate_weights:
            oos_reports.append(
                walk_forward_gate_selection(
                    panel_name,
                    candidate_weights,
                    panel_output["benchmark_weights"],
                    panel_output["next_returns"],
                    gates,
                    cost_bps=20.0,
                )
            )
    oos_gate_report = pd.concat(oos_reports, ignore_index=True) if oos_reports else pd.DataFrame()
    turnover_control_report = (
        experiment_grid.query("cost_bps == 20.0")
        .assign(turnover_excess=lambda df: df["alpha_avg_daily_turnover"] - df["benchmark_avg_daily_turnover"])
        .sort_values(["active_sharpe", "alpha_avg_daily_turnover"], ascending=[False, True])
    )
    oos_candidate_universe = pd.DataFrame(
        [
            {
                "candidate_family": "predeclared_review_thesis",
                "strategy": name,
                "source": "fixed before fold scoring; not selected from full-sample leaderboard",
            }
            for name in predeclared_walk_forward_candidate_names()
        ]
    )
    decision = salvage_decision(experiment_grid, oos_gate_report)

    orientation.to_csv(paths["orientation"], index=False)
    experiment_grid.to_csv(paths["experiment_grid"], index=False)
    interaction.to_csv(paths["interaction"], index=False)
    neutralized_ic.to_csv(paths["neutralized_ic"], index=False)
    turnover_control_report.to_csv(paths["turnover_control"], index=False)
    oos_gate_report.to_csv(paths["oos_gate"], index=False)
    oos_candidate_universe.to_csv(paths["oos_candidate_universe"], index=False)
    decision.to_csv(paths["decision"], index=False)

    return {
        "orientation": orientation,
        "experiment_grid": experiment_grid,
        "interaction": interaction,
        "neutralized_ic": neutralized_ic,
        "turnover_control": turnover_control_report,
        "oos_gate": oos_gate_report,
        "oos_candidate_universe": oos_candidate_universe,
        "decision": decision,
    }


def candidate_artifact_paths(base_dir: str | Path = ".") -> dict[str, Path]:
    base = Path(base_dir).resolve()
    artifact_dir = base / ARTIFACT_SUBDIR
    return {
        "stress": artifact_dir / "alpha001_candidate_stress_report.csv",
        "fold": artifact_dir / "alpha001_candidate_fold_report.csv",
        "liquidity": artifact_dir / "alpha001_candidate_liquidity_capacity_report.csv",
        "exposure": artifact_dir / "alpha001_candidate_exposure_report.csv",
        "neutralized_portfolio": artifact_dir / "alpha001_candidate_neutralized_portfolio_report.csv",
        "latest_portfolio": artifact_dir / "alpha001_candidate_latest_portfolio.csv",
        "gate_policy": artifact_dir / "alpha001_candidate_gate_policy_report.csv",
        "pit_gap": artifact_dir / "alpha001_point_in_time_data_gap_report.csv",
        "decision": artifact_dir / "alpha001_candidate_stress_decision_report.csv",
    }


def load_candidate_artifacts(base_dir: str | Path = ".") -> dict[str, pd.DataFrame]:
    paths = candidate_artifact_paths(base_dir)
    date_columns = {
        "fold": ["fold_start", "fold_end"],
    }
    outputs = {}
    for name, path in paths.items():
        kwargs = {}
        if name in date_columns:
            kwargs["parse_dates"] = date_columns[name]
        outputs[name] = pd.read_csv(path, **kwargs)
    return outputs


def lagged_liquidity_mask(
    panel: PanelData,
    min_median_adv_rupees: float = 100_000_000.0,
    min_median_shares: float = 100_000.0,
    window: int = 60,
) -> pd.DataFrame:
    rupee_turnover = panel.raw_close.mul(panel.volume)
    median_adv = rupee_turnover.rolling(window, min_periods=window).median().shift(1)
    median_shares = panel.volume.rolling(window, min_periods=window).median().shift(1)
    return median_adv.ge(min_median_adv_rupees) & median_shares.ge(min_median_shares)


def symbol_tag_mask(constituents: pd.DataFrame, symbols: pd.Index, tag: str, include: bool) -> pd.Series:
    if "source_slugs" not in constituents.columns:
        return pd.Series(True, index=symbols)
    slug_map = constituents.drop_duplicates("Symbol").set_index("Symbol")["source_slugs"].astype(str)
    has_tag = slug_map.reindex(symbols).fillna("").str.contains(tag, case=False, regex=False)
    return has_tag if include else ~has_tag


def candidate_masks(panel: PanelData) -> dict[str, pd.DataFrame]:
    masks = {"base": panel.active_mask}
    liq100 = lagged_liquidity_mask(panel, 100_000_000.0, 100_000.0).reindex_like(panel.active_mask).fillna(False)
    liq250 = lagged_liquidity_mask(panel, 250_000_000.0, 200_000.0).reindex_like(panel.active_mask).fillna(False)
    masks["strict_liquidity_100m"] = panel.active_mask & liq100
    masks["strict_liquidity_250m"] = panel.active_mask & liq250
    first_valid = panel.adj_close.apply(lambda col: col.first_valid_index())
    first_valid = pd.to_datetime(first_valid)
    for years, sessions in [("1y", 252), ("2y", 504), ("3y", 756)]:
        seasoned = pd.DataFrame(False, index=panel.active_mask.index, columns=panel.active_mask.columns)
        for symbol, first_date in first_valid.items():
            if pd.isna(first_date):
                continue
            seasoned[symbol] = panel.active_mask.index >= (first_date + pd.tseries.offsets.BDay(sessions))
        masks[f"seasoned_{years}"] = panel.active_mask & seasoned
        masks[f"seasoned_{years}_strict_liquidity_100m"] = panel.active_mask & seasoned & liq100
    if panel.name.startswith("expanded"):
        ex_microcap_symbols = symbol_tag_mask(panel.constituents, panel.active_mask.columns, "nifty_microcap_250", include=False)
        ex_smallcap_symbols = symbol_tag_mask(panel.constituents, panel.active_mask.columns, "nifty_smallcap_250", include=False)
        nifty500_symbols = symbol_tag_mask(panel.constituents, panel.active_mask.columns, "nifty500", include=True)
        ex_microcap = pd.DataFrame(
            np.tile(ex_microcap_symbols.to_numpy(dtype=bool), (len(panel.active_mask), 1)),
            index=panel.active_mask.index,
            columns=panel.active_mask.columns,
        )
        ex_smallcap = pd.DataFrame(
            np.tile(ex_smallcap_symbols.to_numpy(dtype=bool), (len(panel.active_mask), 1)),
            index=panel.active_mask.index,
            columns=panel.active_mask.columns,
        )
        nifty500_only = pd.DataFrame(
            np.tile(nifty500_symbols.to_numpy(dtype=bool), (len(panel.active_mask), 1)),
            index=panel.active_mask.index,
            columns=panel.active_mask.columns,
        )
        masks["ex_microcap"] = panel.active_mask & ex_microcap
        masks["ex_small_and_microcap"] = panel.active_mask & ex_microcap & ex_smallcap
        masks["nifty500_only_inside_expanded"] = panel.active_mask & nifty500_only
        masks["ex_microcap_strict_liquidity_100m"] = panel.active_mask & ex_microcap & liq100
        masks["ex_microcap_strict_liquidity_250m"] = panel.active_mask & ex_microcap & liq250
        masks["nifty500_only_strict_liquidity_100m"] = panel.active_mask & nifty500_only & liq100
    return masks


def build_frozen_overlay_candidate(
    panel: PanelData,
    active_mask: pd.DataFrame,
    horizon: int = 5,
    smoothing: str = "ewm3",
    active_budget: float = 0.20,
    partial_adjustment: float = 0.50,
    no_trade_band: float = 0.0,
    signal_override: pd.DataFrame | None = None,
) -> dict[str, pd.DataFrame | pd.Series]:
    returns = panel.adj_close.pct_change(fill_method=None)
    future = forward_return(panel.adj_close, horizon)
    raw_alpha = fast_alpha001(panel.adj_close, returns, active_mask) if signal_override is None else signal_override.where(active_mask)
    oriented, direction, train_mean_ic = causal_orient_signal(raw_alpha, future, horizon=horizon)
    signal = smooth_signal(oriented, smoothing).where(active_mask)
    rebalance = weekly_rebalance_mask(signal.index)
    targets = overlay_targets(signal, active_mask, active_budget=active_budget)
    weights = carry_targets_on_rebalance(
        targets,
        rebalance,
        partial_adjustment=partial_adjustment,
        no_trade_band=no_trade_band,
    )
    benchmark = carry_targets_on_rebalance(equal_weight_targets(active_mask), rebalance)
    return {
        "raw_alpha": raw_alpha,
        "oriented_signal": oriented,
        "candidate_signal": signal,
        "weights": weights,
        "benchmark_weights": benchmark,
        "direction": direction,
        "train_mean_ic": train_mean_ic,
        "next_returns": next_session_returns(panel.adj_close),
        "future": future,
    }


def fold_report(
    panel: str,
    mask_name: str,
    weights: pd.DataFrame,
    benchmark_weights: pd.DataFrame,
    returns: pd.DataFrame,
    cost_bps: float,
    train_days: int = 504,
    test_days: int = 126,
    step_days: int = 126,
) -> pd.DataFrame:
    index = weights.index.intersection(benchmark_weights.index).intersection(returns.index)
    rows = []
    for start in range(0, max(0, len(index) - train_days - test_days + 1), step_days):
        test_idx = index[start + train_days : start + train_days + test_days]
        if len(test_idx) < 60:
            continue
        row = active_report_row(
            panel,
            "frozen_h5_ewm3_overlay20_partial50",
            5,
            "ewm3",
            cost_bps,
            weights.loc[test_idx],
            benchmark_weights.loc[test_idx],
            returns.loc[test_idx],
            {"mask": mask_name},
        )
        rows.append(
            {
                "panel": panel,
                "mask": mask_name,
                "cost_bps": cost_bps,
                "fold_start": test_idx.min(),
                "fold_end": test_idx.max(),
                "active_cagr": row["active_cagr"],
                "active_sharpe": row["active_sharpe"],
                "active_max_drawdown": row["active_max_drawdown"],
                "active_hit_rate": row["active_hit_rate"],
                "alpha_cagr": row["alpha_cagr"],
                "benchmark_cagr": row["benchmark_cagr"],
                "alpha_turnover": row["alpha_avg_daily_turnover"],
                "cost_drag_ann": row["cost_drag_ann"],
                "observations": row["active_observations"],
            }
        )
    return pd.DataFrame(rows)


def liquidity_capacity_report(
    panel: PanelData,
    mask_name: str,
    weights: pd.DataFrame,
    benchmark_weights: pd.DataFrame,
    participation_rates: tuple[float, ...] = (0.05, 0.10),
    aum_rupees: tuple[float, ...] = (100_000_000.0, 500_000_000.0, 1_000_000_000.0),
) -> pd.DataFrame:
    adv60 = panel.raw_close.mul(panel.volume).rolling(60, min_periods=60).median().shift(1).reindex_like(weights)
    rows = []
    for portfolio_name, w in [("candidate", weights), ("benchmark", benchmark_weights)]:
        trades = w.diff().abs().fillna(w.abs())
        traded = trades.gt(0) & adv60.gt(0)
        trade_count = int(traded.sum().sum())
        for participation in participation_rates:
            daily_capacity = adv60.mul(participation).div(trades.where(traded)).replace([np.inf, -np.inf], np.nan).min(axis=1).dropna()
            rows.append(
                {
                    "panel": panel.name,
                    "mask": mask_name,
                    "portfolio": portfolio_name,
                    "metric": f"capacity_at_{int(participation * 100)}pct_adv",
                    "trade_count": trade_count,
                    "p10_rupees": daily_capacity.quantile(0.10) if len(daily_capacity) else np.nan,
                    "median_rupees": daily_capacity.median() if len(daily_capacity) else np.nan,
                    "p90_rupees": daily_capacity.quantile(0.90) if len(daily_capacity) else np.nan,
                }
            )
        for aum in aum_rupees:
            required_participation = trades.mul(aum).div(adv60).where(traded).replace([np.inf, -np.inf], np.nan)
            rows.append(
                {
                    "panel": panel.name,
                    "mask": mask_name,
                    "portfolio": portfolio_name,
                    "metric": f"required_participation_for_{int(aum / 10_000_000)}cr_aum",
                    "trade_count": trade_count,
                    "p10_rupees": required_participation.stack().quantile(0.10),
                    "median_rupees": required_participation.stack().median(),
                    "p90_rupees": required_participation.stack().quantile(0.90),
                }
            )
    return pd.DataFrame(rows)


def exposure_report(panel: PanelData, mask_name: str, weights: pd.DataFrame, benchmark_weights: pd.DataFrame) -> pd.DataFrame:
    rows = []
    cons = panel.constituents.drop_duplicates("Symbol").set_index("Symbol").reindex(weights.columns)
    industry = cons["industry" if "industry" in cons.columns else "Industry"].fillna("unknown") if not cons.empty else pd.Series("unknown", index=weights.columns)
    slugs = cons["source_slugs"].fillna("") if "source_slugs" in cons.columns else pd.Series("", index=weights.columns)
    tags = {
        "microcap": slugs.str.contains("nifty_microcap_250", case=False, regex=False),
        "smallcap": slugs.str.contains("nifty_smallcap_250", case=False, regex=False),
        "midcap": slugs.str.contains("nifty_midcap", case=False, regex=False),
        "nifty500": slugs.str.contains("nifty500", case=False, regex=False),
    }
    for portfolio_name, w in [("candidate", weights), ("benchmark", benchmark_weights)]:
        avg_w = w.mean(axis=0)
        for tag, tag_mask in tags.items():
            rows.append(
                {
                    "panel": panel.name,
                    "mask": mask_name,
                    "portfolio": portfolio_name,
                    "exposure_type": f"tag_{tag}",
                    "exposure": avg_w.loc[tag_mask.reindex(avg_w.index).fillna(False)].sum(),
                }
            )
        industry_exposure = avg_w.groupby(industry.reindex(avg_w.index).fillna("unknown")).sum().sort_values(ascending=False).head(10)
        for name, exposure in industry_exposure.items():
            rows.append(
                {
                    "panel": panel.name,
                    "mask": mask_name,
                    "portfolio": portfolio_name,
                    "exposure_type": f"industry_{name}",
                    "exposure": exposure,
                }
            )
    return pd.DataFrame(rows)


def latest_portfolio_snapshot(panel: PanelData, mask_name: str, candidate: dict[str, pd.DataFrame | pd.Series]) -> pd.DataFrame:
    weights = candidate["weights"]
    benchmark_weights = candidate["benchmark_weights"]
    signal = candidate["candidate_signal"]
    signal_ffill = signal.ffill()
    active = weights.sub(benchmark_weights, fill_value=0.0)
    latest_dates = weights.abs().sum(axis=1)
    if latest_dates.gt(0).any():
        latest_date = latest_dates[latest_dates.gt(0)].index.max()
    else:
        return pd.DataFrame()

    symbols = (
        weights.loc[latest_date].abs().gt(1e-4)
        | benchmark_weights.loc[latest_date].abs().gt(1e-4)
        | active.loc[latest_date].abs().gt(1e-4)
    )
    symbols = symbols[symbols].index
    cons = panel.constituents.drop_duplicates("Symbol").set_index("Symbol").reindex(symbols)
    industry_col = "industry" if "industry" in cons.columns else "Industry" if "Industry" in cons.columns else None
    adv60 = panel.raw_close.mul(panel.volume).rolling(60, min_periods=60).median().shift(1)
    first_valid = panel.adj_close.apply(lambda col: col.first_valid_index())
    rows = []
    for symbol in symbols:
        slugs = str(cons.loc[symbol, "source_slugs"]) if "source_slugs" in cons.columns and symbol in cons.index else ""
        first_date = first_valid.get(symbol, pd.NaT)
        rows.append(
            {
                "date": latest_date,
                "panel": panel.name,
                "mask": mask_name,
                "symbol": symbol,
                "candidate_weight": weights.loc[latest_date, symbol],
                "benchmark_weight": benchmark_weights.loc[latest_date, symbol],
                "active_weight": active.loc[latest_date, symbol],
                "alpha001_signal": signal_ffill.loc[latest_date, symbol] if symbol in signal_ffill.columns else np.nan,
                "is_current_benchmark_member": bool(benchmark_weights.loc[latest_date, symbol] > 1e-12),
                "is_carried_position": bool((weights.loc[latest_date, symbol] > 1e-12) and (benchmark_weights.loc[latest_date, symbol] <= 1e-12)),
                "raw_close": panel.raw_close.loc[latest_date, symbol] if symbol in panel.raw_close.columns else np.nan,
                "lagged_60d_median_adv_rupees": adv60.loc[latest_date, symbol] if symbol in adv60.columns else np.nan,
                "industry": cons.loc[symbol, industry_col] if industry_col and symbol in cons.index else np.nan,
                "source_slugs": slugs,
                "is_microcap_tag": "nifty_microcap_250" in slugs,
                "is_smallcap_tag": "nifty_smallcap_250" in slugs,
                "is_midcap_tag": "nifty_midcap" in slugs,
                "is_nifty500_tag": "nifty500" in slugs,
                "first_valid_price_date": first_date,
                "listed_age_days_at_signal": (latest_date - first_date).days if pd.notna(first_date) else np.nan,
            }
        )
    return pd.DataFrame(rows).sort_values(["panel", "mask", "active_weight"], ascending=[True, True, False])


def neutralized_candidate_portfolios(panel: PanelData) -> pd.DataFrame:
    base_mask = panel.active_mask
    base = build_frozen_overlay_candidate(panel, base_mask)
    factors = style_factor_frames(panel)
    style_subset = {k: factors[k] for k in ["stock_vol_20d", "stock_mom_20d", "stock_mom_63d", "stock_reversal_5d", "stock_adv20_rupees"]}
    industry_dummies = industry_dummy_frame(panel.constituents, base_mask.columns)
    residual_variants = {
        "raw_oriented": base["oriented_signal"],
        "style_residual": residualize_signal(base["oriented_signal"], style_subset, base_mask, industry_dummies=None),
        "style_industry_residual": residualize_signal(base["oriented_signal"], style_subset, base_mask, industry_dummies=industry_dummies),
    }
    rows = []
    for variant, signal in residual_variants.items():
        candidate = build_frozen_overlay_candidate(panel, base_mask, signal_override=signal)
        for cost_bps in [20.0, 35.0, 50.0]:
            rows.append(
                active_report_row(
                    panel.name,
                    f"neutralized_{variant}",
                    5,
                    "ewm3",
                    cost_bps,
                    candidate["weights"],
                    candidate["benchmark_weights"],
                    candidate["next_returns"],
                )
            )
    return pd.DataFrame(rows)


def stress_decision(stress_report: pd.DataFrame, fold_report_frame: pd.DataFrame, neutralized_report: pd.DataFrame) -> pd.DataFrame:
    primary_mask = "base"
    primary_panel = "expanded_high_vol_top100"
    primary = stress_report.query("panel == @primary_panel and mask == @primary_mask and cost_bps == 20.0")
    strict = stress_report.query("panel == @primary_panel and mask == 'ex_microcap_strict_liquidity_100m' and cost_bps == 20.0")
    seasoned = stress_report.query("panel == @primary_panel and mask == 'seasoned_2y_strict_liquidity_100m' and cost_bps == 20.0")
    nifty500_inside = stress_report.query("panel == @primary_panel and mask == 'nifty500_only_inside_expanded' and cost_bps == 20.0")
    ex_small_micro = stress_report.query("panel == @primary_panel and mask == 'ex_small_and_microcap' and cost_bps == 20.0")
    folds = fold_report_frame.query("panel == @primary_panel and mask == @primary_mask and cost_bps == 20.0")
    neutral = neutralized_report.query("panel == @primary_panel and cost_bps == 20.0 and strategy == 'neutralized_style_industry_residual'")
    primary_sharpe = primary["active_sharpe"].iloc[0] if not primary.empty else np.nan
    strict_sharpe = strict["active_sharpe"].iloc[0] if not strict.empty else np.nan
    seasoned_sharpe = seasoned["active_sharpe"].iloc[0] if not seasoned.empty else np.nan
    nifty500_inside_sharpe = nifty500_inside["active_sharpe"].iloc[0] if not nifty500_inside.empty else np.nan
    ex_small_micro_sharpe = ex_small_micro["active_sharpe"].iloc[0] if not ex_small_micro.empty else np.nan
    fold_mean = folds["active_sharpe"].mean() if not folds.empty else np.nan
    fold_positive = folds["active_sharpe"].gt(0).mean() if not folds.empty else np.nan
    neutral_sharpe = neutral["active_sharpe"].iloc[0] if not neutral.empty else np.nan
    if pd.notna(primary_sharpe) and primary_sharpe > 0.50 and pd.notna(strict_sharpe) and strict_sharpe > 0 and pd.notna(fold_mean) and fold_mean > 0.30 and fold_positive >= 0.60:
        decision = "continue_candidate_development"
    elif pd.notna(primary_sharpe) and primary_sharpe > 0:
        decision = "fragile_continue_research"
    else:
        decision = "reject_candidate"
    return pd.DataFrame(
        [
            {
                "decision": decision,
                "primary_panel": primary_panel,
                "primary_mask": primary_mask,
                "primary_20bps_active_sharpe": primary_sharpe,
                "ex_microcap_strict_100m_20bps_active_sharpe": strict_sharpe,
                "seasoned_2y_strict_100m_20bps_active_sharpe": seasoned_sharpe,
                "nifty500_only_inside_expanded_20bps_active_sharpe": nifty500_inside_sharpe,
                "ex_small_and_microcap_20bps_active_sharpe": ex_small_micro_sharpe,
                "base_fold_mean_active_sharpe": fold_mean,
                "base_fold_positive_rate": fold_positive,
                "style_industry_residual_20bps_active_sharpe": neutral_sharpe,
                "roadblock": "point-in-time constituent history still unavailable" if decision != "reject_candidate" else "candidate failed stress criteria",
            }
        ]
    )


def point_in_time_data_gap_report(base_dir: str | Path = ".") -> pd.DataFrame:
    base = Path(base_dir).resolve()
    inputs = [
        ("nifty500_current_constituents", base / NIFTY500_DATA_SUBDIR / "nifty500_constituents.csv"),
        ("expanded_current_constituents", base / EXPANDED_DATA_SUBDIR / "expanded_parent_constituents.csv"),
    ]
    rows = []
    required_pit_columns = {"effective_date", "start_date", "end_date", "date_added", "date_removed"}
    for name, path in inputs:
        if not path.exists():
            rows.append(
                {
                    "dataset": name,
                    "path": str(path.relative_to(base)),
                    "exists": False,
                    "has_point_in_time_columns": False,
                    "classification": "missing",
                    "note": "constituent file not found",
                }
            )
            continue
        frame = pd.read_csv(path, nrows=5)
        columns = {str(col).strip().lower() for col in frame.columns}
        has_pit = bool(columns & required_pit_columns)
        rows.append(
            {
                "dataset": name,
                "path": str(path.relative_to(base)),
                "exists": True,
                "has_point_in_time_columns": has_pit,
                "classification": "usable_for_pit_backtest" if has_pit else "current_snapshot_only",
                "note": (
                    "contains effective/add/remove date columns"
                    if has_pit
                    else "historical membership cannot be reconstructed from this file alone; expanded-universe backtests remain survivorship-risk diagnostics"
                ),
            }
        )
    return pd.DataFrame(rows)


def gate_policy_report(base_dir: str | Path, fold_report_frame: pd.DataFrame) -> pd.DataFrame:
    base = Path(base_dir).resolve()
    oos_path = base / ARTIFACT_SUBDIR / "alpha001_oos_gate_report.csv"
    rows = []
    fixed = fold_report_frame.query("cost_bps == 20.0 and mask == 'base'")
    for panel, group in fixed.groupby("panel"):
        rows.append(
            {
                "panel": panel,
                "policy": "fixed_ungated_overlay",
                "mean_active_sharpe": group["active_sharpe"].mean(),
                "median_active_sharpe": group["active_sharpe"].median(),
                "worst_active_sharpe": group["active_sharpe"].min(),
                "positive_fold_rate": group["active_sharpe"].gt(0).mean(),
                "folds": len(group),
            }
        )
    if oos_path.exists():
        gated = pd.read_csv(oos_path)
        for panel, group in gated.groupby("panel"):
            rows.append(
                {
                    "panel": panel,
                    "policy": "train_selected_regime_gate",
                    "mean_active_sharpe": group["test_active_sharpe"].mean(),
                    "median_active_sharpe": group["test_active_sharpe"].median(),
                    "worst_active_sharpe": group["test_active_sharpe"].min(),
                    "positive_fold_rate": group["test_active_sharpe"].gt(0).mean(),
                    "folds": len(group),
                }
            )
    report = pd.DataFrame(rows)
    if report.empty:
        return report
    best_policy = (
        report.sort_values(["panel", "mean_active_sharpe", "worst_active_sharpe"], ascending=[True, False, False])
        .groupby("panel")
        .head(1)
        [["panel", "policy"]]
        .rename(columns={"policy": "preferred_policy"})
    )
    return report.merge(best_policy, on="panel", how="left")


def run_candidate_stress_tests(base_dir: str | Path = ".", refresh: bool = False) -> dict[str, pd.DataFrame]:
    base = Path(base_dir).resolve()
    paths = candidate_artifact_paths(base)
    if not refresh and all(path.exists() for path in paths.values()):
        return load_candidate_artifacts(base)

    artifact_dir = base / ARTIFACT_SUBDIR
    artifact_dir.mkdir(parents=True, exist_ok=True)
    panels = [load_panel(base, "nifty500_high_vol_top100")]
    if (artifact_dir / "expanded_high_vol_universe_mask_top100.csv").exists():
        panels.append(load_panel(base, "expanded_high_vol_top100"))

    stress_rows = []
    fold_frames = []
    liquidity_frames = []
    exposure_frames = []
    neutralized_frames = []
    latest_frames = []
    for panel in panels:
        for mask_name, mask in candidate_masks(panel).items():
            active_counts = mask.sum(axis=1).replace(0, np.nan)
            if active_counts.dropna().median() < 30:
                continue
            candidate = build_frozen_overlay_candidate(panel, mask)
            weights = candidate["weights"]
            benchmark = candidate["benchmark_weights"]
            returns = candidate["next_returns"]
            for cost_bps in [20.0, 35.0, 50.0]:
                stress_rows.append(
                    active_report_row(
                        panel.name,
                        "frozen_h5_ewm3_overlay20_partial50",
                        5,
                        "ewm3",
                        cost_bps,
                        weights,
                        benchmark,
                        returns,
                        {
                            "mask": mask_name,
                            "median_active_names": active_counts.median(),
                            "p10_active_names": active_counts.quantile(0.10),
                        },
                    )
                )
                fold_frames.append(fold_report(panel.name, mask_name, weights, benchmark, returns, cost_bps))
            liquidity_frames.append(liquidity_capacity_report(panel, mask_name, weights, benchmark))
            exposure_frames.append(exposure_report(panel, mask_name, weights, benchmark))
            if mask_name in {
                "base",
                "strict_liquidity_100m",
                "seasoned_2y_strict_liquidity_100m",
                "ex_microcap_strict_liquidity_100m",
                "nifty500_only_inside_expanded",
            }:
                latest_frames.append(latest_portfolio_snapshot(panel, mask_name, candidate))
        neutralized_frames.append(neutralized_candidate_portfolios(panel))

    stress = pd.DataFrame(stress_rows)
    folds = pd.concat(fold_frames, ignore_index=True) if fold_frames else pd.DataFrame()
    liquidity = pd.concat(liquidity_frames, ignore_index=True) if liquidity_frames else pd.DataFrame()
    exposure = pd.concat(exposure_frames, ignore_index=True) if exposure_frames else pd.DataFrame()
    neutralized = pd.concat(neutralized_frames, ignore_index=True) if neutralized_frames else pd.DataFrame()
    latest_portfolio = pd.concat(latest_frames, ignore_index=True) if latest_frames else pd.DataFrame()
    gate_policy = gate_policy_report(base, folds)
    pit_gap = point_in_time_data_gap_report(base)
    decision = stress_decision(stress, folds, neutralized)

    stress.to_csv(paths["stress"], index=False)
    folds.to_csv(paths["fold"], index=False)
    liquidity.to_csv(paths["liquidity"], index=False)
    exposure.to_csv(paths["exposure"], index=False)
    neutralized.to_csv(paths["neutralized_portfolio"], index=False)
    latest_portfolio.to_csv(paths["latest_portfolio"], index=False)
    gate_policy.to_csv(paths["gate_policy"], index=False)
    pit_gap.to_csv(paths["pit_gap"], index=False)
    decision.to_csv(paths["decision"], index=False)

    return {
        "stress": stress,
        "fold": folds,
        "liquidity": liquidity,
        "exposure": exposure,
        "neutralized_portfolio": neutralized,
        "latest_portfolio": latest_portfolio,
        "gate_policy": gate_policy,
        "pit_gap": pit_gap,
        "decision": decision,
    }


if __name__ == "__main__":
    outputs = run_salvage_experiments(Path.cwd())
    print("Best 20 bps salvage experiments")
    print(
        outputs["experiment_grid"]
        .query("cost_bps == 20.0")
        .sort_values("active_sharpe", ascending=False)
        .head(10)[["panel", "strategy", "active_sharpe", "active_cagr", "alpha_avg_daily_turnover"]]
        .to_string(index=False)
    )
    print("\nSalvage decision")
    print(outputs["decision"].to_string(index=False))
