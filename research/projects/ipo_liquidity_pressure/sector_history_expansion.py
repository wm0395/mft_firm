from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
SECTOR_DATA_DIR = REPO_ROOT / "research" / "data" / "expanded_high_vol_parent"


@dataclass(frozen=True)
class PanelPaths:
    close: Path
    adj_close: Path
    volume: Path


def main() -> None:
    root = Path(__file__).resolve().parent
    panel = _load_panel()
    constituents = _load_constituents()
    sector_history = _build_sector_history(panel, constituents)
    coverage = _build_coverage(sector_history)
    _write_outputs(root, sector_history, coverage)


def _load_panel() -> dict[str, pd.DataFrame]:
    paths = PanelPaths(
        close=SECTOR_DATA_DIR / "close.csv",
        adj_close=SECTOR_DATA_DIR / "adj_close.csv",
        volume=SECTOR_DATA_DIR / "volume.csv",
    )
    return {
        "close": _load_wide_panel(paths.close),
        "adj_close": _load_wide_panel(paths.adj_close),
        "volume": _load_wide_panel(paths.volume),
    }


def _load_constituents() -> pd.DataFrame:
    path = SECTOR_DATA_DIR / "expanded_parent_constituents.csv"
    frame = pd.read_csv(path, usecols=["Symbol", "industry"])
    return frame.dropna(subset=["industry"]).assign(Symbol=lambda df: df["Symbol"].astype(str))


def _load_wide_panel(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, index_col=0, parse_dates=True)
    frame.index = pd.to_datetime(frame.index).tz_localize(None).normalize()
    return frame.sort_index()


def _build_sector_history(panel: dict[str, pd.DataFrame], constituents: pd.DataFrame) -> pd.DataFrame:
    close = panel["close"]
    adj_close = panel["adj_close"]
    volume = panel["volume"]
    returns = adj_close.pct_change(fill_method=None)
    rows = []
    for sector, symbols in _sector_symbols(constituents).items():
        sector_returns = returns[symbols]
        frame = pd.DataFrame(
            {
                "date": adj_close.index,
                "sector": sector,
                "symbol_count": len(symbols),
                "active_symbol_count": sector_returns.notna().sum(axis=1).astype(int),
                "sector_return": sector_returns.mean(axis=1, skipna=True),
                "sector_turnover_crore": close[symbols].mul(volume[symbols], fill_value=float("nan")).sum(axis=1, skipna=True)
                / 10_000_000.0,
                "sector_breadth": sector_returns.gt(0.0).mean(axis=1, skipna=True),
                "source": "expanded_high_vol_parent",
            },
            index=adj_close.index,
        )
        frame["sector_pre_5d_return"] = _trailing_return_series(frame["sector_return"], 5)
        frame["sector_pre_20d_return"] = _trailing_return_series(frame["sector_return"], 20)
        rows.append(frame.reset_index(drop=True))
    return pd.concat(rows, ignore_index=True).sort_values(["sector", "date"])


def _sector_symbols(constituents: pd.DataFrame) -> dict[str, list[str]]:
    symbols: dict[str, list[str]] = {}
    for sector, frame in constituents.groupby("industry"):
        values = frame["Symbol"].astype(str).tolist()
        symbols[str(sector)] = values
    return symbols


def _trailing_return_series(series: pd.Series, lookback: int) -> pd.Series:
    values = []
    for i in range(len(series)):
        window = series.iloc[: i + 1].dropna().tail(lookback)
        values.append(_cumulative_return(window))
    return pd.Series(values, index=series.index, dtype=float)


def _cumulative_return(series: pd.Series) -> float:
    if series.empty:
        return float("nan")
    return float((1.0 + series).prod() - 1.0)


def _build_coverage(sector_history: pd.DataFrame) -> pd.DataFrame:
    coverage = sector_history.groupby("sector", as_index=False).agg(
        symbol_count=("symbol_count", "max"),
        rows=("date", "size"),
        first_date=("date", lambda s: s.min().date().isoformat()),
        last_date=("date", lambda s: s.max().date().isoformat()),
        mean_sector_return=("sector_return", "mean"),
        mean_turnover_crore=("sector_turnover_crore", "mean"),
    )
    return coverage.sort_values(["symbol_count", "sector"], ascending=[False, True])


def _write_outputs(root: Path, sector_history: pd.DataFrame, coverage: pd.DataFrame) -> None:
    data_dir = root / "data"
    report_path = root / "reports" / "sector_history_expansion.md"
    sector_history.to_parquet(data_dir / "sector_history.parquet", index=False)
    coverage.to_csv(data_dir / "sector_history_coverage.csv", index=False)
    report_path.write_text(_render_report(sector_history, coverage), encoding="utf-8")


def _render_report(sector_history: pd.DataFrame, coverage: pd.DataFrame) -> str:
    summary = pd.DataFrame(
        [
            {
                "rows": int(sector_history.shape[0]),
                "sectors": int(coverage.shape[0]),
                "date_start": sector_history["date"].min().date().isoformat(),
                "date_end": sector_history["date"].max().date().isoformat(),
                "mean_sector_return": float(sector_history["sector_return"].mean()),
                "mean_sector_turnover_crore": float(sector_history["sector_turnover_crore"].mean()),
            }
        ]
    )
    lines = [
        "# Sector History Expansion",
        "",
        "## Objective",
        "",
        "Build a point-in-time sector-return and sector-turnover proxy panel from the local expanded-universe OHLCV cache.",
        "",
        "## Outputs",
        "",
        f"- `sector_history.parquet`: {len(sector_history)} sector-day rows across the expanded universe.",
        "- `sector_history_coverage.csv`: sector-level symbol coverage and date coverage.",
        "",
        "## Panel Summary",
        "",
        _render_table(summary),
        "",
        "## Sector Coverage",
        "",
        _render_table(coverage.head(20)),
        "",
        "## Reading",
        "",
        "- The sector panel is built from local OHLCV and the expanded-parent industry mapping, so it gives the IPO study a point-in-time sector-return and sector-turnover proxy without new external feeds.",
        "- The panel is still proxy-based: it does not replace exchange-stamped delivery history or standalone cash-market turnover.",
        "- The sector layer can now be used to test whether same-sector pull/release effects survive a sector-relative control.",
    ]
    return "\n".join(lines)


def _render_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_empty_"
    columns = list(frame.columns)
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    rows = ["| " + " | ".join(_stringify_markdown_value(row[column]) for column in columns) + " |" for _, row in frame.iterrows()]
    return "\n".join([header, separator, *rows])


def _stringify_markdown_value(value: object) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


if __name__ == "__main__":
    main()
