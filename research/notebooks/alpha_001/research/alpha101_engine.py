from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd  # type: ignore[import-untyped]


ANNUALIZATION = 252
ALPHA101_ARTIFACT_DIR = Path("research/artifacts/alpha101_research_factory")
NIFTY500_DATA_DIR = Path("research/data/nifty500_high_vol")
EXPANDED_DATA_DIR = Path("research/data/expanded_high_vol_parent")
ALPHA001_ARTIFACT_DIR = Path("research/artifacts/alpha001_research_to_alpha")


@dataclass(frozen=True)
class Alpha101Panel:
    name: str
    open: pd.DataFrame
    high: pd.DataFrame
    low: pd.DataFrame
    close: pd.DataFrame
    adj_close: pd.DataFrame
    volume: pd.DataFrame
    vwap: pd.DataFrame
    returns: pd.DataFrame
    active_mask: pd.DataFrame
    high_vol_mask: pd.DataFrame
    constituents: pd.DataFrame
    industry: pd.Series
    pit_risk: str


def read_frame(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, index_col=0, parse_dates=True)
    frame.index = pd.to_datetime(frame.index).tz_localize(None)
    return frame.sort_index()


def read_bool_frame(path: Path, index: pd.Index | None = None, columns: pd.Index | None = None) -> pd.DataFrame:
    frame = pd.read_csv(path, index_col=0, parse_dates=True)
    frame.index = pd.to_datetime(frame.index).tz_localize(None)
    out = frame.astype(str).apply(lambda col: col.str.lower().isin({"true", "1", "yes"}))
    if index is not None or columns is not None:
        out = out.reindex(index=index if index is not None else out.index, columns=columns if columns is not None else out.columns).fillna(False)
    return out.astype(bool)


def _load_constituents(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    if "Symbol" not in frame.columns:
        raise ValueError(f"Constituent file missing Symbol column: {path}")
    return frame


@lru_cache(maxsize=2)
def load_panel(name: str) -> Alpha101Panel:
    if name == "nifty500":
        data_dir = NIFTY500_DATA_DIR
        constituents_path = data_dir / "nifty500_constituents.csv"
        high_vol_mask_path = ALPHA001_ARTIFACT_DIR / "dynamic_high_vol_universe_mask_top100.csv"
    elif name == "expanded":
        data_dir = EXPANDED_DATA_DIR
        constituents_path = data_dir / "expanded_parent_constituents.csv"
        high_vol_mask_path = ALPHA001_ARTIFACT_DIR / "expanded_high_vol_universe_mask_top100.csv"
    else:
        raise ValueError(f"Unknown panel: {name}")

    open_px = read_frame(data_dir / "open.csv")
    high = read_frame(data_dir / "high.csv")
    low = read_frame(data_dir / "low.csv")
    close = read_frame(data_dir / "close.csv")
    adj_close = read_frame(data_dir / "adj_close.csv")
    volume = read_frame(data_dir / "volume.csv")
    common = open_px.columns.intersection(high.columns).intersection(low.columns).intersection(close.columns).intersection(adj_close.columns).intersection(volume.columns)
    open_px = open_px[common]
    high = high[common]
    low = low[common]
    close = close[common]
    adj_close = adj_close[common]
    volume = volume[common]
    adjustment = adj_close.div(close.replace(0.0, np.nan))
    open_px = open_px.mul(adjustment)
    high = high.mul(adjustment)
    low = low.mul(adjustment)
    close = adj_close.copy()
    vwap = (high + low + close) / 3.0
    returns = adj_close.pct_change(fill_method=None)
    active_mask = adj_close.notna() & close.notna() & volume.notna() & volume.gt(0)
    high_vol_mask = read_bool_frame(high_vol_mask_path, index=adj_close.index, columns=common) if high_vol_mask_path.exists() else active_mask.copy()
    constituents = _load_constituents(constituents_path)
    industry_col = "Industry" if "Industry" in constituents.columns else "industry" if "industry" in constituents.columns else None
    industry = (
        constituents.drop_duplicates("Symbol").set_index("Symbol")[industry_col].reindex(common).fillna("unknown")
        if industry_col
        else pd.Series("unknown", index=common)
    )
    return Alpha101Panel(
        name=name,
        open=open_px,
        high=high,
        low=low,
        close=close,
        adj_close=adj_close,
        volume=volume,
        vwap=vwap,
        returns=returns,
        active_mask=active_mask.astype(bool),
        high_vol_mask=high_vol_mask.astype(bool),
        constituents=constituents,
        industry=industry,
        pit_risk="current_snapshot_constituents_no_point_in_time_membership",
    )


def clean(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.replace([np.inf, -np.inf], np.nan)


def returns(close: pd.DataFrame) -> pd.DataFrame:
    return close.pct_change(fill_method=None)


def ts_sum(frame: pd.DataFrame, window: float) -> pd.DataFrame:
    w = int(round(window))
    return frame.rolling(w, min_periods=w).sum()


def sma(frame: pd.DataFrame, window: float) -> pd.DataFrame:
    w = int(round(window))
    return frame.rolling(w, min_periods=w).mean()


def stddev(frame: pd.DataFrame, window: float) -> pd.DataFrame:
    w = int(round(window))
    return frame.rolling(w, min_periods=w).std()


def correlation(x: pd.DataFrame, y: pd.DataFrame, window: float) -> pd.DataFrame:
    w = int(round(window))
    return clean(x.rolling(w, min_periods=w).corr(y))


def covariance(x: pd.DataFrame, y: pd.DataFrame, window: float) -> pd.DataFrame:
    w = int(round(window))
    return clean(x.rolling(w, min_periods=w).cov(y))


def delta(frame: pd.DataFrame, period: float = 1) -> pd.DataFrame:
    return frame.diff(int(round(period)))


def delay(frame: pd.DataFrame, period: float = 1) -> pd.DataFrame:
    return frame.shift(int(round(period)))


def rank(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.rank(axis=1, pct=True, method="average")


def centered_rank(frame: pd.DataFrame) -> pd.DataFrame:
    return rank(frame) - 0.5


def row_zscore(frame: pd.DataFrame) -> pd.DataFrame:
    mean = frame.mean(axis=1)
    std = frame.std(axis=1, ddof=0).replace(0.0, np.nan)
    return frame.sub(mean, axis=0).div(std, axis=0)


def winsorized_zscore(frame: pd.DataFrame, lower: float = 0.02, upper: float = 0.98) -> pd.DataFrame:
    lo = frame.quantile(lower, axis=1)
    hi = frame.quantile(upper, axis=1)
    clipped = frame.clip(lower=lo, upper=hi, axis=0)
    return row_zscore(clipped)


def scale(frame: pd.DataFrame, k: float = 1.0) -> pd.DataFrame:
    denom = frame.abs().sum(axis=1).replace(0.0, np.nan)
    return frame.mul(k).div(denom, axis=0)


def signed_power(frame: pd.DataFrame, power: float) -> pd.DataFrame:
    return np.sign(frame) * (frame.abs() ** power)


def product(frame: pd.DataFrame, window: float) -> pd.DataFrame:
    w = int(round(window))
    return frame.rolling(w, min_periods=w).apply(np.prod, raw=True)


def ts_min(frame: pd.DataFrame, window: float) -> pd.DataFrame:
    w = int(round(window))
    return frame.rolling(w, min_periods=w).min()


def ts_max(frame: pd.DataFrame, window: float) -> pd.DataFrame:
    w = int(round(window))
    return frame.rolling(w, min_periods=w).max()


def _rolling_last_rank(values: np.ndarray) -> float:
    last = values[-1]
    if np.isnan(last):
        return np.nan
    valid = values[~np.isnan(values)]
    if len(valid) == 0:
        return np.nan
    return float(1 + np.sum(valid < last))


def ts_rank(frame: pd.DataFrame, window: float) -> pd.DataFrame:
    w = int(round(window))
    return frame.rolling(w, min_periods=w).apply(_rolling_last_rank, raw=True)


def ts_argmax(frame: pd.DataFrame, window: float) -> pd.DataFrame:
    w = int(round(window))
    values = frame.to_numpy(dtype=float, copy=False)
    out = np.full(values.shape, np.nan)
    if len(frame) < w:
        return pd.DataFrame(out, index=frame.index, columns=frame.columns)
    windows = np.lib.stride_tricks.sliding_window_view(values, window_shape=w, axis=0)
    all_nan = np.isnan(windows).all(axis=-1)
    filled = np.where(np.isnan(windows), -np.inf, windows)
    pos = np.argmax(filled, axis=-1).astype(float) + 1.0
    pos[all_nan] = np.nan
    out[w - 1 :] = pos
    return pd.DataFrame(out, index=frame.index, columns=frame.columns)


def ts_argmin(frame: pd.DataFrame, window: float) -> pd.DataFrame:
    w = int(round(window))
    values = frame.to_numpy(dtype=float, copy=False)
    out = np.full(values.shape, np.nan)
    if len(frame) < w:
        return pd.DataFrame(out, index=frame.index, columns=frame.columns)
    windows = np.lib.stride_tricks.sliding_window_view(values, window_shape=w, axis=0)
    all_nan = np.isnan(windows).all(axis=-1)
    filled = np.where(np.isnan(windows), np.inf, windows)
    pos = np.argmin(filled, axis=-1).astype(float) + 1.0
    pos[all_nan] = np.nan
    out[w - 1 :] = pos
    return pd.DataFrame(out, index=frame.index, columns=frame.columns)


def decay_linear(frame: pd.DataFrame, period: float) -> pd.DataFrame:
    p = int(round(period))
    weights = np.arange(1, p + 1, dtype=float)
    denom = weights.sum()
    return frame.rolling(p, min_periods=p).apply(lambda x: float(np.nansum(x * weights) / denom), raw=True)


def indneutralize(frame: pd.DataFrame, groups: pd.Series) -> pd.DataFrame:
    aligned_groups = groups.reindex(frame.columns).fillna("unknown")
    values = frame.astype(float)
    out = values.copy()
    for group in aligned_groups.dropna().unique():
        cols = aligned_groups.index[aligned_groups.eq(group)]
        out.loc[:, cols] = values.loc[:, cols].sub(values.loc[:, cols].mean(axis=1), axis=0)
    return out


def adv(volume: pd.DataFrame, window: float) -> pd.DataFrame:
    return sma(volume, window)


def forward_return(price: pd.DataFrame, horizon: int) -> pd.DataFrame:
    return price.shift(-horizon).div(price).sub(1.0)


def next_session_return(price: pd.DataFrame) -> pd.DataFrame:
    return price.pct_change(fill_method=None).shift(-1)


def fast_rank_ic_by_date(signal: pd.DataFrame, future: pd.DataFrame, min_names: int = 10) -> pd.Series:
    idx = signal.index.intersection(future.index)
    cols = signal.columns.intersection(future.columns)
    s = signal.loc[idx, cols].astype(float)
    f = future.loc[idx, cols].astype(float)
    valid = s.notna() & f.notna()
    count = valid.sum(axis=1).astype(float)
    x = s.rank(axis=1, method="average").where(valid)
    y = f.rank(axis=1, method="average").where(valid)
    xm = x.sum(axis=1).div(count)
    ym = y.sum(axis=1).div(count)
    xc = x.sub(xm, axis=0).where(valid, 0.0)
    yc = y.sub(ym, axis=0).where(valid, 0.0)
    denom = np.sqrt(xc.pow(2).sum(axis=1) * yc.pow(2).sum(axis=1))
    ic = xc.mul(yc).sum(axis=1).div(denom).replace([np.inf, -np.inf], np.nan)
    ic[count < min_names] = np.nan
    return ic.rename("rank_ic")


def causal_orient(signal: pd.DataFrame, future: pd.DataFrame, horizon: int, train_window: int = 504, min_obs: int = 126) -> tuple[pd.DataFrame, pd.Series]:
    raw_ic = fast_rank_ic_by_date(signal, future)
    train_mean = raw_ic.shift(horizon).rolling(train_window, min_periods=min_obs).mean()
    direction = pd.Series(np.where(train_mean >= 0, 1.0, -1.0), index=signal.index)
    direction[train_mean.isna()] = np.nan
    return signal.mul(direction, axis=0), direction


def equal_weight_targets(active_mask: pd.DataFrame) -> pd.DataFrame:
    counts = active_mask.sum(axis=1).replace(0, np.nan)
    return active_mask.astype(float).div(counts, axis=0).fillna(0.0)


def weekly_rebalance_mask(index: pd.DatetimeIndex) -> pd.Series:
    weeks = pd.Series(index.to_period("W-FRI"), index=index)
    mask = weeks.ne(weeks.shift(1))
    if len(mask):
        mask.iloc[0] = True
    return mask.astype(bool)


def carry_on_rebalance(targets: pd.DataFrame, rebalance_mask: pd.Series, partial: float = 1.0, band: float = 0.0) -> pd.DataFrame:
    rebalance_mask = rebalance_mask.reindex(targets.index).fillna(False).astype(bool)
    if partial == 1.0 and band == 0.0:
        row_mask = pd.DataFrame(
            np.repeat(rebalance_mask.to_numpy()[:, None], len(targets.columns), axis=1),
            index=targets.index,
            columns=targets.columns,
        )
        return targets.where(row_mask, np.nan).ffill().fillna(0.0)
    weights = pd.DataFrame(0.0, index=targets.index, columns=targets.columns)
    last = pd.Series(0.0, index=targets.columns)
    for i, date in enumerate(targets.index):
        if i == 0 or bool(rebalance_mask.loc[date]):
            target = targets.loc[date].fillna(0.0)
            if band > 0:
                diff = target - last
                target = last + diff.where(diff.abs() >= band, 0.0)
            if partial < 1.0:
                target = last + partial * (target - last)
            total = target.abs().sum()
            if total > 0 and target.sum() > 0:
                target = target / target.sum()
            last = target.reindex(targets.columns).fillna(0.0)
        weights.loc[date] = last
    return weights


def normalized_positive(frame: pd.DataFrame) -> pd.DataFrame:
    clipped = clean(frame).clip(lower=0.0).fillna(0.0)
    denom = clipped.sum(axis=1).replace(0.0, np.nan)
    return clipped.div(denom, axis=0).fillna(0.0)


def score_tilt_weights(signal: pd.DataFrame, active_mask: pd.DataFrame, intensity: float = 0.25) -> pd.DataFrame:
    z = row_zscore(signal.where(active_mask))
    raw = (1.0 + intensity * z).clip(lower=0.05).where(active_mask)
    return normalized_positive(raw).where(active_mask, 0.0)


def overlay_weights(signal: pd.DataFrame, active_mask: pd.DataFrame, active_budget: float = 0.20) -> pd.DataFrame:
    base = equal_weight_targets(active_mask)
    z = winsorized_zscore(signal.where(active_mask)).where(active_mask, 0.0)
    active = z.div(z.abs().sum(axis=1).replace(0.0, np.nan), axis=0).fillna(0.0) * active_budget
    return normalized_positive(base + active).where(active_mask, 0.0)


def top_bucket_weights(signal: pd.DataFrame, active_mask: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    masked = signal.where(active_mask)
    ranks = masked.rank(axis=1, ascending=False, method="first")
    selected = ranks.le(top_n)
    return equal_weight_targets(selected)


def long_short_weights(signal: pd.DataFrame, active_mask: pd.DataFrame, leg_n: int = 10) -> pd.DataFrame:
    masked = signal.where(active_mask)
    long_sel = masked.rank(axis=1, ascending=False, method="first").le(leg_n)
    short_sel = masked.rank(axis=1, ascending=True, method="first").le(leg_n)
    longs = equal_weight_targets(long_sel) * 0.5
    shorts = equal_weight_targets(short_sel) * -0.5
    return longs.add(shorts, fill_value=0.0)


def portfolio_returns(weights: pd.DataFrame, returns_frame: pd.DataFrame) -> pd.Series:
    aligned = returns_frame.reindex(index=weights.index, columns=weights.columns)
    valid = weights.abs().gt(0) & aligned.notna()
    no_exposure = weights.abs().sum(axis=1).eq(0)
    gross = weights.mul(aligned).sum(axis=1, min_count=1)
    return gross.where(valid.any(axis=1) | no_exposure)


def performance_metrics(returns_series: pd.Series, turnover: pd.Series | None = None) -> dict:
    r = returns_series.dropna().astype(float)
    if r.empty:
        return {"cagr": np.nan, "ann_return": np.nan, "ann_vol": np.nan, "sharpe": np.nan, "sortino": np.nan, "max_drawdown": np.nan, "hit_rate": np.nan, "avg_daily_turnover": np.nan, "observations": 0}
    equity = (1 + r).cumprod()
    years = len(r) / ANNUALIZATION
    ann_return = r.mean() * ANNUALIZATION
    ann_vol = r.std(ddof=0) * math.sqrt(ANNUALIZATION)
    downside = r.where(r < 0).dropna()
    downside_vol = downside.std(ddof=0) * math.sqrt(ANNUALIZATION) if len(downside) > 1 else np.nan
    drawdown = equity.div(equity.cummax()).sub(1.0)
    return {
        "cagr": equity.iloc[-1] ** (1 / years) - 1 if years > 0 and equity.iloc[-1] > 0 else np.nan,
        "ann_return": ann_return,
        "ann_vol": ann_vol,
        "sharpe": ann_return / ann_vol if ann_vol and not pd.isna(ann_vol) else np.nan,
        "sortino": ann_return / downside_vol if downside_vol and not pd.isna(downside_vol) else np.nan,
        "max_drawdown": drawdown.min(),
        "hit_rate": r.gt(0).mean(),
        "avg_daily_turnover": turnover.reindex(r.index).mean() if turnover is not None else np.nan,
        "observations": len(r),
    }


def backtest_weights(weights: pd.DataFrame, next_returns: pd.DataFrame, cost_bps: float) -> dict:
    gross = portfolio_returns(weights, next_returns)
    turnover = weights.diff().abs().sum(axis=1, min_count=1).fillna(weights.abs().sum(axis=1))
    costs = turnover * (cost_bps / 10000.0)
    net = gross - costs
    valid = net.dropna().index
    return {
        "returns": net.reindex(valid),
        "gross_returns": gross.reindex(valid),
        "turnover": turnover.reindex(valid).fillna(0.0),
        "costs": costs.reindex(valid).fillna(0.0),
        "metrics": performance_metrics(net, turnover),
    }


def operator_validation() -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=5)
    fixture = pd.DataFrame({"A": [1, 2, 3, 4, 5], "B": [5, 4, 3, 2, 1]}, index=idx, dtype=float)
    rows = [
        {"check": "rank_bounds", "passed": bool(rank(fixture).max().max() <= 1 and rank(fixture).min().min() > 0)},
        {"check": "delta", "passed": bool(delta(fixture, 1).iloc[-1, 0] == 1)},
        {"check": "delay", "passed": bool(delay(fixture, 1).iloc[-1, 0] == 4)},
        {"check": "ts_argmax", "passed": bool(ts_argmax(fixture[["A"]], 5).iloc[-1, 0] == 5)},
        {"check": "ts_argmin", "passed": bool(ts_argmin(fixture[["A"]], 5).iloc[-1, 0] == 1)},
        {"check": "signed_power", "passed": bool(signed_power(pd.DataFrame({"x": [-2.0]}), 2).iloc[0, 0] == -4.0)},
        {"check": "scale_abs_sum", "passed": bool(abs(scale(fixture).abs().sum(axis=1).dropna().iloc[-1] - 1.0) < 1e-10)},
    ]
    return pd.DataFrame(rows)
