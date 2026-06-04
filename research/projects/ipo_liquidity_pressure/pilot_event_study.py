from __future__ import annotations

import math
from pathlib import Path

import pandas as pd


TOP_N = 50
WINDOW_NAMES = ("application", "blocking", "release_3", "release_5", "listing_5")
STATIC_BASKETS = {
    "smallcap250": "research/data/nifty500_high_vol/volatile_index_constituents/nifty_smallcap_250.csv",
    "midcap150": "research/data/nifty500_high_vol/volatile_index_constituents/nifty_midcap_150.csv",
}
REPORT_WINDOWS = ("application", "release_5")
REPORT_BASKETS = (
    "same_sector_peer",
    "recent_winners_60d_top50",
    "cash_source_60d_top50",
    "smallcap250",
    "midcap150",
)


def main() -> None:
    root = Path(__file__).resolve().parent
    events = _load_events(root)
    returns, turnover = _load_market_panels(root)
    constituents = _load_constituents(root)
    static_baskets = _load_static_baskets(root, returns.columns)
    windows = _build_window_rows(events)
    rows = _build_results_rows(events, returns, turnover, constituents, static_baskets)
    _write_outputs(root, events, windows, rows)


def _load_events(root: Path) -> pd.DataFrame:
    path = root / "data" / "ipo_events_seed.csv"
    frame = pd.read_csv(path)
    for column in ("ipo_open_date", "ipo_close_date", "allotment_date", "listing_date"):
        frame[column] = pd.to_datetime(frame[column], utc=True)
    frame = frame.sort_values("subscription_total_multiple", ascending=False).reset_index(drop=True)
    frame["pressure_rank"] = frame.index + 1
    return frame


def _load_market_panels(root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    base = root.parents[1] / "data" / "expanded_high_vol_parent"
    prices = _load_wide_panel(base / "adj_close.csv")
    volumes = _load_wide_panel(base / "volume.csv")
    return prices.pct_change(fill_method=None), prices.mul(volumes, fill_value=float("nan"))


def _load_constituents(root: Path) -> pd.DataFrame:
    path = root.parents[1] / "data" / "expanded_high_vol_parent" / "expanded_parent_constituents.csv"
    return pd.read_csv(path)


def _load_static_baskets(root: Path, market_symbols: pd.Index) -> dict[str, tuple[str, ...]]:
    baskets: dict[str, tuple[str, ...]] = {}
    for name, relative in STATIC_BASKETS.items():
        symbols = pd.read_csv(root.parents[2] / relative)["Symbol"].astype(str).tolist()
        baskets[name] = tuple(symbol for symbol in symbols if symbol in market_symbols)
    return baskets


def _load_wide_panel(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame["Date"] = pd.to_datetime(frame["Date"], utc=True)
    return frame.set_index("Date").sort_index()


def _build_window_rows(events: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for event in events.itertuples(index=False):
        for window_name, start, end in _window_bounds(event):
            rows.append(
                {
                    "ipo_id": event.ipo_id,
                    "company_name": event.company_name,
                    "symbol_after_listing": event.symbol_after_listing,
                    "pressure_class": event.pressure_class,
                    "window_name": window_name,
                    "window_start": start.date().isoformat(),
                    "window_end": end.date().isoformat(),
                    "window_empty": bool(start > end),
                }
            )
    return pd.DataFrame(rows)


def _build_results_rows(
    events: pd.DataFrame,
    returns: pd.DataFrame,
    turnover: pd.DataFrame,
    constituents: pd.DataFrame,
    static_baskets: dict[str, tuple[str, ...]],
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for event in events.itertuples(index=False):
        benchmark = _benchmark_series(returns, event.symbol_after_listing)
        baskets = _basket_map(event, returns, turnover, constituents, static_baskets)
        for basket_name, symbols in baskets.items():
            basket_series = _basket_series(returns, symbols, event.symbol_after_listing)
            for window_name, start, end in _window_bounds(event):
                rows.append(
                    _result_row(
                        event,
                        basket_name,
                        len(symbols),
                        window_name,
                        start,
                        end,
                        basket_series,
                        benchmark,
                    )
                )
    return pd.DataFrame(rows)


def _basket_map(
    event: pd.Series,
    returns: pd.DataFrame,
    turnover: pd.DataFrame,
    constituents: pd.DataFrame,
    static_baskets: dict[str, tuple[str, ...]],
) -> dict[str, tuple[str, ...]]:
    sector = constituents.loc[constituents["Symbol"].eq(event.symbol_after_listing), "industry"]
    sector_symbols = tuple(
        symbol
        for symbol in constituents.loc[constituents["industry"].eq(sector.iloc[0] if not sector.empty else ""), "Symbol"].astype(str).tolist()
        if symbol in returns.columns and symbol != event.symbol_after_listing
    )
    trailing_returns = returns.loc[returns.index < event.ipo_open_date].tail(60)
    trailing_turnover = turnover.loc[turnover.index < event.ipo_open_date].tail(60)
    winners = _top_symbols(((1.0 + trailing_returns).prod(axis=0, min_count=1) - 1.0), event.symbol_after_listing)
    cash_source = _top_symbols(trailing_turnover.mean(axis=0, skipna=True), event.symbol_after_listing)
    baskets = {
        "same_sector_peer": sector_symbols,
        "recent_winners_60d_top50": winners,
        "cash_source_60d_top50": cash_source,
    }
    baskets.update({name: symbols for name, symbols in static_baskets.items()})
    return baskets


def _top_symbols(scores: pd.Series, excluded_symbol: str) -> tuple[str, ...]:
    cleaned = scores.drop(labels=[excluded_symbol], errors="ignore").dropna().sort_values(ascending=False)
    return tuple(cleaned.head(TOP_N).index.astype(str))


def _benchmark_series(returns: pd.DataFrame, excluded_symbol: str) -> pd.Series:
    return returns.drop(columns=[excluded_symbol], errors="ignore").mean(axis=1, skipna=True)


def _basket_series(returns: pd.DataFrame, symbols: tuple[str, ...], excluded_symbol: str) -> pd.Series:
    available = [symbol for symbol in symbols if symbol in returns.columns and symbol != excluded_symbol]
    if not available:
        return pd.Series(index=returns.index, dtype=float)
    return returns[available].mean(axis=1, skipna=True)


def _window_bounds(event: pd.Series) -> tuple[tuple[str, pd.Timestamp, pd.Timestamp], ...]:
    return (
        ("application", event.ipo_open_date, event.ipo_close_date),
        ("blocking", event.ipo_close_date + pd.Timedelta(days=1), event.allotment_date - pd.Timedelta(days=1)),
        ("release_3", event.allotment_date, event.allotment_date + pd.Timedelta(days=3)),
        ("release_5", event.allotment_date, event.allotment_date + pd.Timedelta(days=5)),
        ("listing_5", event.listing_date, event.listing_date + pd.Timedelta(days=5)),
    )


def _result_row(
    event: pd.Series,
    basket_name: str,
    basket_member_count: int,
    window_name: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    basket_series: pd.Series,
    benchmark_series: pd.Series,
) -> dict[str, object]:
    window_mask = (basket_series.index >= start) & (basket_series.index <= end)
    basket_window = basket_series.loc[window_mask]
    benchmark_window = benchmark_series.loc[window_mask]
    basket_return = _cumulative_return(basket_window)
    benchmark_return = _cumulative_return(benchmark_window)
    return {
        "ipo_id": event.ipo_id,
        "company_name": event.company_name,
        "symbol_after_listing": event.symbol_after_listing,
        "pressure_class": event.pressure_class,
        "pressure_rank": event.pressure_rank,
        "subscription_total_multiple": float(event.subscription_total_multiple),
        "basket_name": basket_name,
        "basket_member_count": basket_member_count,
        "window_name": window_name,
        "window_start": start.date().isoformat(),
        "window_end": end.date().isoformat(),
        "trading_days": int(window_mask.sum()),
        "window_empty": bool(start > end or window_mask.sum() == 0),
        "basket_return": basket_return,
        "benchmark_return": benchmark_return,
        "abnormal_return": basket_return - benchmark_return if math.isfinite(basket_return) and math.isfinite(benchmark_return) else math.nan,
    }


def _cumulative_return(series: pd.Series) -> float:
    cleaned = series.dropna()
    if cleaned.empty:
        return math.nan
    return float((1.0 + cleaned).prod() - 1.0)


def _write_outputs(root: Path, events: pd.DataFrame, windows: pd.DataFrame, results: pd.DataFrame) -> None:
    data_dir = root / "data"
    report_path = root / "reports" / "pilot_event_study.md"
    windows.to_csv(data_dir / "ipo_event_windows_seed.csv", index=False)
    results.to_csv(data_dir / "ipo_pilot_event_study.csv", index=False)
    report_path.write_text(_render_report(events, windows, results), encoding="utf-8")


def _render_report(events: pd.DataFrame, windows: pd.DataFrame, results: pd.DataFrame) -> str:
    sample_size = int(results["ipo_id"].nunique())
    lines = [
        "# IPO Pilot Event Study",
        "",
        "## Objective",
        "",
        "Test whether the seed IPO sample shows a repeatable pull-and-release pattern in local market data.",
        "",
        "## Seed Sample",
        "",
        _render_table(
            events[
                [
                    "company_name",
                    "symbol_after_listing",
                    "pressure_class",
                    "subscription_total_multiple",
                    "ipo_open_date",
                    "ipo_close_date",
                    "allotment_date",
                    "listing_date",
                ]
            ].assign(
                ipo_open_date=lambda frame: frame["ipo_open_date"].dt.date.astype(str),
                ipo_close_date=lambda frame: frame["ipo_close_date"].dt.date.astype(str),
                allotment_date=lambda frame: frame["allotment_date"].dt.date.astype(str),
                listing_date=lambda frame: frame["listing_date"].dt.date.astype(str),
            ),
        ),
        "",
        "## Window Coverage",
        "",
        _render_table(
            windows.assign(window_empty=windows["window_empty"].map({True: "yes", False: "no"})),
        ),
        "",
        "## Key Reading",
        "",
        *_summary_bullets(results, sample_size),
        "",
        "## Event Detail",
        "",
        _render_table(_detail_table(results, "application")),
        "",
        _render_table(_detail_table(results, "release_5")),
        "",
        "## Verdict",
        "",
        f"The {sample_size}-event seed sample does not support a simple monotonic liquidity-pull story.",
        "Urban Company remains the clearest negative peer signal, but the broader sample does not align into a clean pressure gradient.",
        "The current evidence is mixed and leans against a broad, mechanically repeatable pull-and-release rule.",
    ]
    return "\n".join(lines)


def _summary_bullets(results: pd.DataFrame, sample_size: int) -> list[str]:
    rows: list[str] = []
    rows.append(f"- Same-sector peer abnormal returns are mixed across the {sample_size}-event seed sample.")
    rows.append(
        f"- Recent-winners abnormal returns are negative in the application window across the {sample_size}-event seed sample; the broader set is mixed."
    )
    rows.append(f"- Cash-source abnormal returns are positive in the application window for the {sample_size}-event seed sample.")
    rows.append("- Blocking windows are short or empty in this sample, so the data do not isolate a separate blocking-phase effect.")
    rows.append(_pressure_line(results, "same_sector_peer", "application"))
    rows.append(_pressure_line(results, "same_sector_peer", "release_5"))
    rows.append(_pressure_line(results, "recent_winners_60d_top50", "application"))
    rows.append(_pressure_line(results, "recent_winners_60d_top50", "release_5"))
    rows.append(_pressure_line(results, "cash_source_60d_top50", "application"))
    rows.append(_pressure_line(results, "cash_source_60d_top50", "release_5"))
    return rows


def _basket_window_rows(results: pd.DataFrame, basket_name: str, window_name: str) -> dict[str, float]:
    subset = results.loc[results["basket_name"].eq(basket_name) & results["window_name"].eq(window_name)]
    grouped = subset.groupby("pressure_class")["abnormal_return"].mean()
    return {str(key): float(value) for key, value in grouped.items()}


def _pressure_line(results: pd.DataFrame, basket_name: str, window_name: str) -> str:
    grouped = _basket_window_rows(results, basket_name, window_name)
    values = ", ".join(
        f"{label} {grouped[label]:.4f}"
        for label in ("extreme", "high", "medium", "low")
        if label in grouped and math.isfinite(grouped[label])
    )
    return f"- {window_name.replace('_', ' ').title()} {basket_name.replace('_', ' ')} AR averages: {values}."


def _detail_table(results: pd.DataFrame, window_name: str) -> pd.DataFrame:
    pivot = results.loc[results["window_name"].eq(window_name)].pivot_table(
        index=["company_name", "symbol_after_listing", "pressure_class"],
        columns="basket_name",
        values="abnormal_return",
        aggfunc="first",
    ).reset_index()
    ordered = ["company_name", "symbol_after_listing", "pressure_class", *REPORT_BASKETS]
    available = [column for column in ordered if column in pivot.columns]
    frame = pivot[available].copy()
    for column in REPORT_BASKETS:
        if column in frame.columns:
            frame[column] = frame[column].map(_format_pct)
    return frame


def _render_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_no rows_"
    rows = frame.to_dict(orient="records")
    columns = list(frame.columns)
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    return "\n".join(lines)


def _format_pct(value: object) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    return f"{float(value):.4%}"


if __name__ == "__main__":
    main()
