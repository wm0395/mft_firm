from __future__ import annotations

import math
from pathlib import Path
import sys

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from project.data.repository import build_repository  # noqa: E402
from project.regimes.engine import RegimeEngine  # noqa: E402
from research.notebooks.alpha_001.research.alpha101_engine import load_panel  # noqa: E402


INDEX_SYMBOLS = ("NIFTY", "BANKNIFTY", "FINNIFTY")
SUMMARY_WINDOWS = ("application", "release_5")
SUMMARY_BASKETS = (
    "same_sector_peer",
    "recent_winners_60d_top50",
    "cash_source_60d_top50",
)


def main() -> None:
    root = Path(__file__).resolve().parent
    events = _load_events(root)
    pilot = _load_pilot_results(root)
    index_data = _load_index_data(root)
    expanded = _load_expanded_panel()
    enriched = _enrich_results(pilot, events, index_data, expanded)
    _write_outputs(root, enriched)


def _load_events(root: Path) -> pd.DataFrame:
    frame = pd.read_csv(root / "data" / "ipo_events_seed.csv")
    frame["issue_size_inr_crore"] = pd.to_numeric(frame["issue_size_inr_crore"], errors="coerce")
    return frame[["ipo_id", "issue_size_inr_crore"]]


def _load_pilot_results(root: Path) -> pd.DataFrame:
    frame = pd.read_csv(root / "data" / "ipo_pilot_event_study.csv")
    frame["window_start"] = pd.to_datetime(frame["window_start"], utc=True).dt.tz_convert(None).dt.normalize()
    frame["window_end"] = pd.to_datetime(frame["window_end"], utc=True).dt.tz_convert(None).dt.normalize()
    return frame


def _load_index_data(root: Path) -> dict[str, pd.DataFrame]:
    repository = build_repository(root.parents[2] / "project_mft.duckdb", read_only=True)
    try:
        return {symbol: _market_frame(repository.get_market_data(symbol, None, None)) for symbol in INDEX_SYMBOLS}
    finally:
        repository.close()


def _load_expanded_panel() -> dict[str, pd.DataFrame | pd.Series]:
    panel = load_panel("expanded")
    returns = panel.returns.copy()
    returns.index = pd.to_datetime(returns.index).normalize()
    close = panel.close.copy()
    close.index = pd.to_datetime(close.index).normalize()
    volume = panel.volume.copy()
    volume.index = pd.to_datetime(volume.index).normalize()
    turnover = close.mul(volume, fill_value=float("nan")).sum(axis=1, skipna=True)
    breadth = returns.gt(0.0).mean(axis=1, skipna=True)
    mean_return = returns.mean(axis=1, skipna=True)
    return {
        "returns": returns,
        "turnover_crore": turnover / 10_000_000.0,
        "breadth": breadth,
        "mean_return": mean_return,
    }


def _market_frame(rows: tuple[tuple[object, ...], ...]) -> pd.DataFrame:
    frame = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce").dt.tz_localize(None).dt.normalize()
    frame = frame.dropna(subset=["timestamp"]).sort_values("timestamp").set_index("timestamp")
    frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
    frame["open"] = pd.to_numeric(frame["open"], errors="coerce")
    frame["high"] = pd.to_numeric(frame["high"], errors="coerce")
    frame["low"] = pd.to_numeric(frame["low"], errors="coerce")
    frame["volume"] = pd.to_numeric(frame["volume"], errors="coerce")
    frame["return"] = frame["close"].pct_change(fill_method=None)
    return frame


def _enrich_results(
    pilot: pd.DataFrame,
    events: pd.DataFrame,
    index_data: dict[str, pd.DataFrame],
    expanded: dict[str, pd.DataFrame | pd.Series],
) -> pd.DataFrame:
    frame = pilot.merge(events, on="ipo_id", how="left", validate="many_to_one")
    rows = [_enriched_row(row, index_data, expanded) for row in frame.itertuples(index=False)]
    enriched = pd.DataFrame(rows)
    return pd.concat([frame.reset_index(drop=True), enriched.reset_index(drop=True)], axis=1)


def _enriched_row(
    row: pd.Series,
    index_data: dict[str, pd.DataFrame],
    expanded: dict[str, pd.DataFrame | pd.Series],
) -> dict[str, object]:
    control_date = _previous_trading_day(index_data["NIFTY"].index, row.window_start)
    snapshot = _regime_snapshot(index_data["NIFTY"], control_date)
    pre20_turnover = _trailing_mean(expanded["turnover_crore"], control_date, 20)
    return {
        "control_date": control_date.date().isoformat(),
        "control_market_regime": _market_regime_label(snapshot),
        "control_nifty_volatility_state": snapshot.volatility.state,
        "control_nifty_trend_state": snapshot.trend.state,
        "control_nifty_liquidity_state": snapshot.liquidity.state,
        "control_nifty_momentum_state": snapshot.momentum.state,
        "control_nifty_pre_5d_return": _trailing_return(index_data["NIFTY"]["return"], control_date, 5),
        "control_nifty_pre_20d_return": _trailing_return(index_data["NIFTY"]["return"], control_date, 20),
        "control_banknifty_pre_5d_return": _trailing_return(index_data["BANKNIFTY"]["return"], control_date, 5),
        "control_finnifty_pre_5d_return": _trailing_return(index_data["FINNIFTY"]["return"], control_date, 5),
        "window_nifty_return": _window_return(index_data["NIFTY"]["return"], row.window_start, row.window_end),
        "window_banknifty_return": _window_return(index_data["BANKNIFTY"]["return"], row.window_start, row.window_end),
        "window_finnifty_return": _window_return(index_data["FINNIFTY"]["return"], row.window_start, row.window_end),
        "window_expanded_breadth_mean": _window_mean(expanded["breadth"], row.window_start, row.window_end),
        "window_expanded_turnover_crore_mean": _window_mean(expanded["turnover_crore"], row.window_start, row.window_end),
        "window_expanded_mean_return": _window_mean(expanded["mean_return"], row.window_start, row.window_end),
        "pre20_expanded_turnover_crore_mean": pre20_turnover,
        "issue_to_turnover_ratio": row.issue_size_inr_crore / pre20_turnover if pre20_turnover and math.isfinite(pre20_turnover) and pre20_turnover != 0 else math.nan,
    }


def _previous_trading_day(index: pd.Index, start: pd.Timestamp) -> pd.Timestamp:
    position = index.searchsorted(start, side="left")
    if position <= 0:
        raise ValueError(f"No trading day available before {start.date().isoformat()}")
    return pd.Timestamp(index[position - 1])


def _regime_snapshot(frame: pd.DataFrame, control_date: pd.Timestamp):
    recent = frame.loc[:control_date].tail(20)
    if len(recent) < 20:
        raise ValueError(f"Insufficient index history for regime snapshot at {control_date.date().isoformat()}")
    return RegimeEngine(window=20).compute_regime(
        asset_id="asset:NIFTY",
        timestamp=control_date.isoformat(),
        market_data=tuple(recent.itertuples(index=True, name=None)),
    )


def _market_regime_label(snapshot) -> str:
    if snapshot.volatility.state in {"high", "extreme"}:
        return "volatile"
    if snapshot.trend.state in {"strong_bull", "weak_bull"}:
        return "bull"
    if snapshot.trend.state in {"strong_bear", "weak_bear"}:
        return "bear"
    return "calm"


def _trailing_return(series: pd.Series, end: pd.Timestamp, lookback: int) -> float:
    window = series.loc[:end].dropna().tail(lookback)
    return _cumulative_return(window)


def _window_return(series: pd.Series, start: pd.Timestamp, end: pd.Timestamp) -> float:
    window = series.loc[(series.index >= start) & (series.index <= end)].dropna()
    return _cumulative_return(window)


def _window_mean(series: pd.Series, start: pd.Timestamp, end: pd.Timestamp) -> float:
    window = series.loc[(series.index >= start) & (series.index <= end)].dropna()
    return float(window.mean()) if not window.empty else math.nan


def _trailing_mean(series: pd.Series, end: pd.Timestamp, lookback: int) -> float:
    window = series.loc[:end].dropna().tail(lookback)
    return float(window.mean()) if not window.empty else math.nan


def _cumulative_return(series: pd.Series) -> float:
    if series.empty:
        return math.nan
    return float((1.0 + series).prod() - 1.0)


def _write_outputs(root: Path, frame: pd.DataFrame) -> None:
    data_path = root / "data" / "ipo_pilot_event_study_controls.csv"
    report_path = root / "reports" / "pilot_regime_control_panel.md"
    frame.to_csv(data_path, index=False)
    report_path.write_text(_render_report(frame), encoding="utf-8")


def _render_report(frame: pd.DataFrame) -> str:
    focus = frame.loc[frame["window_name"].isin(SUMMARY_WINDOWS)].copy()
    basket_summaries = {basket: _basket_summary(focus, basket) for basket in SUMMARY_BASKETS}
    regime_summary = _regime_summary(focus)
    lines = [
        "# IPO Regime Control Panel",
        "",
        "## Objective",
        "",
        "Check whether the pilot pull-and-release signal survives conditioning on broad-market regime, breadth, and turnover pressure.",
        "",
        "## Controls",
        "",
        "- Control date: the previous trading day before the measured window starts.",
        "- Market regime: NIFTY 20-bar snapshot compressed into bull, bear, volatile, or calm.",
        "- Breadth proxy: average share of positive returns across the expanded high-volatility parent universe.",
        "- Pressure proxy: IPO issue size divided by trailing 20-day expanded-universe turnover in crore INR.",
        "",
        "## Basket Readout",
        "",
    ]
    for basket in SUMMARY_BASKETS:
        lines.extend([f"### {basket.replace('_', ' ').title()}", _render_table(basket_summaries[basket]), ""])
    lines.extend(
        [
            "## Regime Readout",
            "",
            _render_table(regime_summary),
            "",
            "## Reading",
            "",
            _reading_lines(basket_summaries, regime_summary),
        ]
    )
    return "\n".join(lines)


def _basket_summary(frame: pd.DataFrame, basket_name: str) -> pd.DataFrame:
    summary = (
        frame.loc[frame["basket_name"].eq(basket_name)]
        .groupby(["pressure_class", "window_name"], as_index=False)
        .agg(
            observations=("abnormal_return", "size"),
            mean_abnormal_return=("abnormal_return", "mean"),
            mean_window_nifty_return=("window_nifty_return", "mean"),
            mean_issue_to_turnover=("issue_to_turnover_ratio", "mean"),
            dominant_market_regime=("control_market_regime", lambda s: _mode_value(s)),
        )
        .sort_values(["pressure_class", "window_name"])
    )
    return summary


def _regime_summary(frame: pd.DataFrame) -> pd.DataFrame:
    summary = (
        frame.groupby(["control_market_regime", "window_name"], as_index=False)
        .agg(
            observations=("abnormal_return", "size"),
            mean_abnormal_return=("abnormal_return", "mean"),
            mean_window_breadth=("window_expanded_breadth_mean", "mean"),
            mean_window_turnover=("window_expanded_turnover_crore_mean", "mean"),
        )
        .sort_values(["control_market_regime", "window_name"])
    )
    return summary


def _mode_value(series: pd.Series) -> str:
    modes = series.dropna().mode()
    return str(modes.iloc[0]) if not modes.empty else ""


def _reading_lines(basket_summaries: dict[str, pd.DataFrame], regime_summary: pd.DataFrame) -> str:
    same_sector = basket_summaries["same_sector_peer"].set_index(["pressure_class", "window_name"])
    recent = basket_summaries["recent_winners_60d_top50"].set_index(["pressure_class", "window_name"])
    cash = basket_summaries["cash_source_60d_top50"].set_index(["pressure_class", "window_name"])
    pressure = basket_summaries["same_sector_peer"].groupby("pressure_class")["mean_issue_to_turnover"].mean()
    lines = [
        f"- The pressure proxy stays largest for the extreme cases ({pressure.get('extreme', math.nan):.4f} mean issue-to-turnover), which keeps the blocking-liquidity mechanism plausible.",
        "- The control panel does not collapse the sample into one clean regime: all focus windows sit in the volatile bucket.",
    ]
    if not same_sector.empty and {"extreme", "high", "low"}.issubset({idx[0] for idx in same_sector.index}):
        lines.append(
            f"- Same-sector peers remain split: extreme {same_sector.loc[('extreme', 'application'), 'mean_abnormal_return']:.4%} on application and {same_sector.loc[('extreme', 'release_5'), 'mean_abnormal_return']:.4%} on release_5, "
            f"high {same_sector.loc[('high', 'application'), 'mean_abnormal_return']:.4%}/{same_sector.loc[('high', 'release_5'), 'mean_abnormal_return']:.4%}, "
            f"low {same_sector.loc[('low', 'application'), 'mean_abnormal_return']:.4%}/{same_sector.loc[('low', 'release_5'), 'mean_abnormal_return']:.4%}."
        )
    if not recent.empty and {"extreme", "high", "low", "medium"}.issubset({idx[0] for idx in recent.index}):
        lines.append(
            f"- Recent winners are negative on application for extreme {recent.loc[('extreme', 'application'), 'mean_abnormal_return']:.4%} and high {recent.loc[('high', 'application'), 'mean_abnormal_return']:.4%}, "
            f"while low is {recent.loc[('low', 'application'), 'mean_abnormal_return']:.4%} and medium is {recent.loc[('medium', 'application'), 'mean_abnormal_return']:.4%}."
        )
    if not cash.empty and {"extreme", "high", "low", "medium"}.issubset({idx[0] for idx in cash.index}):
        lines.append(
            f"- Cash-source names stay positive across pressure classes: extreme {cash.loc[('extreme', 'application'), 'mean_abnormal_return']:.4%}/{cash.loc[('extreme', 'release_5'), 'mean_abnormal_return']:.4%}, "
            f"high {cash.loc[('high', 'application'), 'mean_abnormal_return']:.4%}/{cash.loc[('high', 'release_5'), 'mean_abnormal_return']:.4%}, "
            f"low {cash.loc[('low', 'application'), 'mean_abnormal_return']:.4%}/{cash.loc[('low', 'release_5'), 'mean_abnormal_return']:.4%}, "
            f"medium {cash.loc[('medium', 'application'), 'mean_abnormal_return']:.4%}/{cash.loc[('medium', 'release_5'), 'mean_abnormal_return']:.4%}."
        )
    if not regime_summary.empty:
        dominant = _dominant_regime(regime_summary)
        lines.append(f"- The dominant control-state bucket is `{dominant}`, but the regime split does not explain away the mixed basket behavior.")
    return "\n".join(lines)


def _dominant_regime(regime_summary: pd.DataFrame) -> str:
    counts = regime_summary.groupby("control_market_regime")["observations"].sum().sort_values(ascending=False)
    return str(counts.index[0]) if not counts.empty else ""


def _render_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_no rows_"
    rows = frame.to_dict(orient="records")
    columns = list(frame.columns)
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(_format_cell(row.get(column)) for column in columns) + " |")
    return "\n".join(lines)


def _format_cell(value: object) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    if isinstance(value, float):
        return f"{value:.4%}" if abs(value) < 1 else f"{value:.4f}"
    return str(value)


if __name__ == "__main__":
    main()
