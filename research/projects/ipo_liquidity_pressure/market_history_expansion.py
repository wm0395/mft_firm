from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from project.data.repository import build_repository  # noqa: E402
from project.regimes.engine import RegimeEngine  # noqa: E402
from sector_history_expansion import (  # type: ignore[import-not-found]  # noqa: E402
    main as write_sector_history_outputs,
)


WINDOW = 20
INDEX_SYMBOLS = ("NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY")


@dataclass(frozen=True)
class PanelPaths:
    data_dir: Path
    close: Path
    adj_close: Path
    volume: Path


def main() -> None:
    root = Path(__file__).resolve().parent
    seed = pd.read_csv(root / "data" / "ipo_events_seed.csv")
    panels = _load_panels(root)
    repo = build_repository(REPO_ROOT / "project_mft.duckdb", read_only=True)
    try:
        index_frames = _load_index_frames(repo)
        seed_market_frames = {
            symbol: _market_frame(repo.get_market_data(symbol, None, None))
            for symbol in seed["symbol_after_listing"].astype(str)
        }
    finally:
        repo.close()

    index_prices = _build_index_prices(index_frames)
    market_liquidity = _build_market_liquidity(panels["expanded"], index_frames)
    coverage = _build_symbol_coverage(
        seed,
        panels["nifty500"]["adj_close"],
        panels["expanded"]["adj_close"],
        seed_market_frames,
    )
    _write_outputs(root, index_prices, market_liquidity, coverage, panels, index_frames)
    write_sector_history_outputs()


def _load_panels(root: Path) -> dict[str, dict[str, pd.DataFrame]]:
    specs = {
        "nifty500": PanelPaths(
            data_dir=REPO_ROOT / "research" / "data" / "nifty500_high_vol",
            close=REPO_ROOT / "research" / "data" / "nifty500_high_vol" / "close.csv",
            adj_close=REPO_ROOT / "research" / "data" / "nifty500_high_vol" / "adj_close.csv",
            volume=REPO_ROOT / "research" / "data" / "nifty500_high_vol" / "volume.csv",
        ),
        "expanded": PanelPaths(
            data_dir=REPO_ROOT / "research" / "data" / "expanded_high_vol_parent",
            close=REPO_ROOT / "research" / "data" / "expanded_high_vol_parent" / "close.csv",
            adj_close=REPO_ROOT / "research" / "data" / "expanded_high_vol_parent" / "adj_close.csv",
            volume=REPO_ROOT / "research" / "data" / "expanded_high_vol_parent" / "volume.csv",
        ),
    }
    return {
        name: {
            "close": _load_wide_panel(spec.close),
            "adj_close": _load_wide_panel(spec.adj_close),
            "volume": _load_wide_panel(spec.volume),
        }
        for name, spec in specs.items()
    }


def _load_wide_panel(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, index_col=0, parse_dates=True)
    frame.index = pd.to_datetime(frame.index).tz_localize(None).normalize()
    return frame.sort_index()


def _load_index_frames(repository) -> dict[str, pd.DataFrame]:
    frames: dict[str, pd.DataFrame] = {}
    for symbol in INDEX_SYMBOLS:
        rows = repository.get_market_data(symbol, None, None)
        frames[symbol] = _market_frame(rows)
    return frames


def _market_frame(rows: tuple[tuple[object, ...], ...]) -> pd.DataFrame:
    frame = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
    if frame.empty:
        return frame.set_index(pd.DatetimeIndex([], name="timestamp"))
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce").dt.tz_localize(None).dt.normalize()
    frame = frame.dropna(subset=["timestamp"]).sort_values("timestamp").set_index("timestamp")
    for field in ("open", "high", "low", "close", "volume"):
        frame[field] = pd.to_numeric(frame[field], errors="coerce")
    frame["return"] = frame["close"].pct_change(fill_method=None)
    return frame


def _build_index_prices(index_frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for symbol, frame in index_frames.items():
        if frame.empty:
            continue
        rows.append(
            frame.reset_index().assign(
                asset_symbol=symbol,
                source="project_mft.duckdb",
            )
        )
    if not rows:
        return pd.DataFrame(columns=["asset_symbol", "timestamp", "open", "high", "low", "close", "volume", "return", "source"])
    return pd.concat(rows, ignore_index=True)[
        ["asset_symbol", "timestamp", "open", "high", "low", "close", "volume", "return", "source"]
    ].sort_values(["asset_symbol", "timestamp"])


def _build_market_liquidity(
    panels: dict[str, pd.DataFrame],
    index_frames: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    expanded_close = panels["close"]
    expanded_adj_close = panels["adj_close"]
    expanded_volume = panels["volume"]
    returns = expanded_adj_close.pct_change(fill_method=None)
    liquidity = pd.DataFrame(
        {
            "date": expanded_adj_close.index,
            "expanded_turnover_crore": expanded_close.mul(expanded_volume, fill_value=float("nan")).sum(axis=1, skipna=True) / 10_000_000.0,
            "expanded_breadth": returns.gt(0.0).mean(axis=1, skipna=True),
            "expanded_mean_return": returns.mean(axis=1, skipna=True),
        }
    ).set_index("date")
    for symbol, frame in index_frames.items():
        close = frame["close"] if not frame.empty else pd.Series(dtype=float)
        liquidity[f"{symbol.lower()}_close"] = close.reindex(liquidity.index)
        liquidity[f"{symbol.lower()}_return"] = close.pct_change(fill_method=None).reindex(liquidity.index)
        liquidity[f"{symbol.lower()}_pre_5d_return"] = _trailing_return_series(close, liquidity.index, 5)
        liquidity[f"{symbol.lower()}_pre_20d_return"] = _trailing_return_series(close, liquidity.index, 20)
    regime = _build_regime_frame(index_frames["NIFTY"])
    liquidity = liquidity.join(regime, how="left")
    return liquidity.reset_index()


def _build_regime_frame(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    engine = RegimeEngine(window=WINDOW)
    for i, date in enumerate(frame.index):
        if i + 1 < WINDOW:
            rows.append({"date": date})
            continue
        recent = frame.iloc[i + 1 - WINDOW : i + 1]
        snapshot = engine.compute_regime(
            asset_id="asset:NIFTY",
            timestamp=date.isoformat(),
            market_data=tuple(recent.itertuples(index=True, name=None)),
        )
        rows.append(
            {
                "date": date,
                "nifty_regime_label": _regime_label(snapshot),
                "nifty_volatility_state": snapshot.volatility.state,
                "nifty_trend_state": snapshot.trend.state,
                "nifty_liquidity_state": snapshot.liquidity.state,
                "nifty_momentum_state": snapshot.momentum.state,
                "nifty_realized_volatility": snapshot.volatility.realized_volatility,
                "nifty_trend_slope": snapshot.trend.slope,
                "nifty_trend_strength": snapshot.trend.strength,
                "nifty_liquidity_volume_ma_ratio": snapshot.liquidity.volume_ma_ratio,
                "nifty_momentum_rsi": snapshot.momentum.rsi_value,
                "nifty_momentum_score": snapshot.momentum.momentum_score,
            }
        )
    return pd.DataFrame(rows).set_index("date")


def _regime_label(snapshot) -> str:
    if snapshot.volatility.state in {"high", "extreme"}:
        return "volatile"
    if snapshot.trend.state in {"strong_bull", "weak_bull"}:
        return "bull"
    if snapshot.trend.state in {"strong_bear", "weak_bear"}:
        return "bear"
    return "calm"


def _build_symbol_coverage(
    seed: pd.DataFrame,
    nifty_adj_close: pd.DataFrame,
    expanded_adj_close: pd.DataFrame,
    seed_market_frames: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    rows = []
    for event in seed.itertuples(index=False):
        symbol = str(event.symbol_after_listing)
        db_rows, db_first, db_last = _frame_window(seed_market_frames.get(symbol, pd.DataFrame()))
        nifty_rows, nifty_first, nifty_last = _wide_window(nifty_adj_close, symbol)
        expanded_rows, expanded_first, expanded_last = _wide_window(expanded_adj_close, symbol)
        best_source = _best_source(db_rows, expanded_rows, nifty_rows)
        rows.append(
            {
                "ipo_id": event.ipo_id,
                "company_name": event.company_name,
                "symbol_after_listing": symbol,
                "pressure_class": event.pressure_class,
                "subscription_total_multiple": float(event.subscription_total_multiple),
                "listing_date": event.listing_date,
                "project_mft_duckdb_rows": db_rows,
                "project_mft_duckdb_first_date": db_first,
                "project_mft_duckdb_last_date": db_last,
                "nifty500_high_vol_rows": nifty_rows,
                "nifty500_high_vol_first_date": nifty_first,
                "nifty500_high_vol_last_date": nifty_last,
                "expanded_high_vol_parent_rows": expanded_rows,
                "expanded_high_vol_parent_first_date": expanded_first,
                "expanded_high_vol_parent_last_date": expanded_last,
                "best_available_source": best_source,
            }
        )
    return pd.DataFrame(rows)


def _market_window(frame: pd.DataFrame, symbol: str) -> tuple[int, str | None, str | None]:
    if frame.empty:
        return 0, None, None
    series = frame["close"].dropna() if "close" in frame.columns else pd.Series(dtype=float)
    if series.empty:
        return 0, None, None
    return int(series.shape[0]), series.index.min().date().isoformat(), series.index.max().date().isoformat()


def _wide_window(frame: pd.DataFrame, symbol: str) -> tuple[int, str | None, str | None]:
    if symbol not in frame.columns:
        return 0, None, None
    series = frame[symbol].dropna()
    if series.empty:
        return 0, None, None
    return int(series.shape[0]), series.index.min().date().isoformat(), series.index.max().date().isoformat()


def _frame_window(frame: pd.DataFrame) -> tuple[int, str | None, str | None]:
    if frame.empty:
        return 0, None, None
    series = frame["close"].dropna() if "close" in frame.columns else pd.Series(dtype=float)
    if series.empty:
        return 0, None, None
    return int(series.shape[0]), series.index.min().date().isoformat(), series.index.max().date().isoformat()


def _best_source(db_rows: int, expanded_rows: int, nifty_rows: int) -> str:
    if db_rows > 0:
        return "project_mft.duckdb"
    if expanded_rows > 0:
        return "expanded_high_vol_parent"
    if nifty_rows > 0:
        return "nifty500_high_vol"
    return "missing"


def _trailing_return_series(series: pd.Series, index: pd.Index, lookback: int) -> pd.Series:
    out = []
    for date in index:
        window = series.loc[:date].dropna().tail(lookback)
        out.append(_cumulative_return(window))
    return pd.Series(out, index=index, dtype=float)


def _cumulative_return(series: pd.Series) -> float:
    if series.empty:
        return float("nan")
    return float((1.0 + series).prod() - 1.0)


def _write_outputs(
    root: Path,
    index_prices: pd.DataFrame,
    market_liquidity: pd.DataFrame,
    coverage: pd.DataFrame,
    panels: dict[str, dict[str, pd.DataFrame]],
    index_frames: dict[str, pd.DataFrame],
) -> None:
    data_dir = root / "data"
    report_path = root / "reports" / "market_history_expansion.md"
    index_prices.to_parquet(data_dir / "index_prices.parquet", index=False)
    market_liquidity.to_parquet(data_dir / "market_liquidity.parquet", index=False)
    coverage.to_csv(data_dir / "market_history_symbol_coverage.csv", index=False)
    report_path.write_text(_render_report(index_prices, market_liquidity, coverage, panels, index_frames), encoding="utf-8")


def _render_report(
    index_prices: pd.DataFrame,
    market_liquidity: pd.DataFrame,
    coverage: pd.DataFrame,
    panels: dict[str, dict[str, pd.DataFrame]],
    index_frames: dict[str, pd.DataFrame],
) -> str:
    panel_summary = pd.DataFrame(
        [
            {
                "panel": "nifty500_high_vol",
                "rows": int(panels["nifty500"]["adj_close"].shape[0]),
                "symbols": int(panels["nifty500"]["adj_close"].shape[1]),
                "date_start": panels["nifty500"]["adj_close"].index.min().date().isoformat(),
                "date_end": panels["nifty500"]["adj_close"].index.max().date().isoformat(),
                "seed_coverage": int((coverage["nifty500_high_vol_rows"] > 0).sum()),
            },
            {
                "panel": "expanded_high_vol_parent",
                "rows": int(panels["expanded"]["adj_close"].shape[0]),
                "symbols": int(panels["expanded"]["adj_close"].shape[1]),
                "date_start": panels["expanded"]["adj_close"].index.min().date().isoformat(),
                "date_end": panels["expanded"]["adj_close"].index.max().date().isoformat(),
                "seed_coverage": int((coverage["expanded_high_vol_parent_rows"] > 0).sum()),
            },
        ]
    )
    index_summary = pd.DataFrame(
        [
            {
                "asset_symbol": symbol,
                "rows": int(frame.shape[0]),
                "date_start": frame.index.min().date().isoformat() if not frame.empty else "",
                "date_end": frame.index.max().date().isoformat() if not frame.empty else "",
            }
            for symbol, frame in index_frames.items()
        ]
    )
    missing = coverage.loc[coverage["best_available_source"].eq("missing"), "company_name"].tolist()
    lines = [
        "# Market History Expansion",
        "",
        "## Objective",
        "",
        "Turn the local price cache into a point-in-time daily market-liquidity panel that can condition the IPO pull/release study.",
        "",
        "## Outputs",
        "",
        f"- `index_prices.parquet`: {len(index_prices)} index rows from the local `project_mft.duckdb` cache.",
        f"- `market_liquidity.parquet`: {len(market_liquidity)} daily rows keyed by trading date.",
        "- `market_history_symbol_coverage.csv`: seed-IPO source coverage by local market-history store.",
        "",
        "## Local Panel Summary",
        "",
        _render_table(panel_summary),
        "",
        "## Index History Summary",
        "",
        _render_table(index_summary),
        "",
        "## Seed Coverage Summary",
        "",
        f"- `project_mft.duckdb` has direct market rows for {int((coverage['project_mft_duckdb_rows'] > 0).sum())} of the {len(coverage)} seed IPO symbols.",
        f"- `nifty500_high_vol` covers {int((coverage['nifty500_high_vol_rows'] > 0).sum())} of the {len(coverage)} seed IPO symbols.",
        f"- `expanded_high_vol_parent` covers {int((coverage['expanded_high_vol_parent_rows'] > 0).sum())} of the {len(coverage)} seed IPO symbols.",
        f"- Missing from all three local price stores: {', '.join(missing) if missing else 'none'}.",
        "",
        "## Reading",
        "",
        "- The price cache is broad enough to anchor the event study: the wide panels run from 1996-01-01 to 2026-05-22, and the index cache runs from 2016-05-22 to 2026-05-21.",
        "- The bottleneck is still direct liquidity history. There is no local delivery-volume history or standalone cash-market turnover feed yet, but the repo now has a point-in-time sector-return and sector-turnover proxy panel.",
        "- The new market-liquidity panel is proxy-based: it combines expanded-universe turnover, breadth, mean return, and NIFTY regime states into a daily table.",
        "- That is enough to improve conditioning for the IPO hypothesis, but it is still not the final turnover-and-delivery data contract described in the project docs.",
    ]
    return "\n".join(lines)


def _render_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_empty_"
    columns = list(frame.columns)
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    rows = []
    for _, row in frame.iterrows():
        values = [_stringify_markdown_value(row[column]) for column in columns]
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join([header, separator, *rows])


def _stringify_markdown_value(value: object) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


if __name__ == "__main__":
    main()
