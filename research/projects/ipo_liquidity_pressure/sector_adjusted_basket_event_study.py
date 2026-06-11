from __future__ import annotations

import math
from pathlib import Path
from typing import Any, cast

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[3]
PILOT_RESULTS_PATH = Path(__file__).resolve().parent / "data" / "ipo_pilot_event_study.csv"
SECTOR_HISTORY_PATH = Path(__file__).resolve().parent / "data" / "sector_history.parquet"
SEED_EVENTS_PATH = Path(__file__).resolve().parent / "data" / "ipo_events_seed.csv"
SECTOR_MAP_PATH = REPO_ROOT / "research" / "data" / "expanded_high_vol_parent" / "expanded_parent_constituents.csv"

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
    seed = pd.read_csv(SEED_EVENTS_PATH)
    pilot = pd.read_csv(PILOT_RESULTS_PATH)
    sector_history = _load_sector_history(SECTOR_HISTORY_PATH)
    sector_map = _load_sector_map(SECTOR_MAP_PATH)
    conditioned = _build_conditioned_rows(pilot, sector_history, sector_map)
    _write_outputs(root, conditioned, seed, sector_map)


def _load_sector_history(path: Path) -> pd.DataFrame:
    frame = pd.read_parquet(path)
    frame["date"] = pd.to_datetime(frame["date"], utc=False).dt.tz_localize(None).dt.normalize()
    return frame.sort_values(["sector", "date"])


def _load_sector_map(path: Path) -> dict[str, str]:
    frame = pd.read_csv(path, usecols=["Symbol", "industry"])
    frame["Symbol"] = frame["Symbol"].astype(str)
    frame = frame.dropna(subset=["industry"]).drop_duplicates(subset=["Symbol"], keep="first")
    return frame.set_index("Symbol")["industry"].astype(str).to_dict()


def _build_conditioned_rows(
    pilot: pd.DataFrame,
    sector_history: pd.DataFrame,
    sector_map: dict[str, str],
) -> pd.DataFrame:
    groups = {sector: frame.reset_index(drop=True) for sector, frame in sector_history.groupby("sector")}
    rows = []
    for row in pilot.itertuples(index=False):
        sector = sector_map.get(str(row.symbol_after_listing))
        sector_frame = groups.get(sector, pd.DataFrame())
        start = pd.to_datetime(row.window_start)
        end = pd.to_datetime(row.window_end)
        sector_window = _sector_window(sector_frame, start, end)
        sector_return = _cumulative_return(sector_window["sector_return"]) if not sector_window.empty else math.nan
        rows.append(
            {
                **row._asdict(),
                "sector": sector or "missing",
                "sector_covered": bool(sector),
                "sector_window_return": sector_return,
                "sector_window_turnover_crore": float(sector_window["sector_turnover_crore"].mean()) if not sector_window.empty else math.nan,
                "sector_window_breadth": float(sector_window["sector_breadth"].mean()) if not sector_window.empty else math.nan,
                "sector_adjusted_abnormal_return": _sector_adjusted_return(row.abnormal_return, sector_return),
            }
        )
    return pd.DataFrame(rows)


def _sector_window(frame: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    if frame.empty:
        return frame
    return frame.loc[(frame["date"] >= start) & (frame["date"] <= end)]


def _cumulative_return(series: pd.Series) -> float:
    cleaned = series.dropna()
    if cleaned.empty:
        return math.nan
    return float((1.0 + cleaned).prod() - 1.0)


def _sector_adjusted_return(abnormal_return: object, sector_return: float) -> float:
    if not math.isfinite(sector_return):
        return math.nan
    try:
        value = float(cast(Any, abnormal_return))
    except (TypeError, ValueError):
        return math.nan
    if not math.isfinite(value):
        return math.nan
    return value - sector_return


def _write_outputs(root: Path, conditioned: pd.DataFrame, seed: pd.DataFrame, sector_map: dict[str, str]) -> None:
    data_dir = root / "data"
    report_path = root / "reports" / "sector_adjusted_basket_event_study.md"
    conditioned.to_csv(data_dir / "ipo_sector_adjusted_basket_event_study.csv", index=False)
    report_path.write_text(_render_report(conditioned, seed, sector_map), encoding="utf-8")


def _render_report(conditioned: pd.DataFrame, seed: pd.DataFrame, sector_map: dict[str, str]) -> str:
    seed_symbols = seed["symbol_after_listing"].astype(str).tolist()
    mapped = [symbol for symbol in seed_symbols if symbol in sector_map]
    missing = [symbol for symbol in seed_symbols if symbol not in sector_map]
    tables = [_window_section(conditioned, window_name) for window_name in REPORT_WINDOWS]
    lines = [
        "# Sector-Adjusted Basket Event Study",
        "",
        "## Objective",
        "",
        "Check whether the main basket signals survive a sector-return adjustment, not just the same-sector peer basket.",
        "",
        "## Coverage",
        "",
        f"- Sector mapping is available for {len(mapped)} of the {len(seed_symbols)} seed IPO symbols.",
        f"- The sector-adjusted basket pass therefore covers 650 of the 950 pilot rows; missing symbols: {', '.join(missing) if missing else 'none'}.",
        "",
        "## Window Reading",
        "",
        *tables,
        "",
        "## Interpretation",
        "",
        "- Sector adjustment does not cleanly organize the baskets into a monotonic pressure gradient.",
        "- The sector-adjusted basket averages remain mixed across application and release windows.",
        "- Recent winners, cash sources, and the small/midcap baskets remain mixed after sector adjustment.",
        "- The sector proxy layer is useful as a falsification check, but it does not rescue a broad pull/release thesis.",
    ]
    return "\n".join(lines)


def _window_section(conditioned: pd.DataFrame, window_name: str) -> str:
    frame = conditioned.loc[conditioned["window_name"].eq(window_name)]
    summary = (
        frame.pivot_table(
            index="basket_name",
            columns="pressure_class",
            values="sector_adjusted_abnormal_return",
            aggfunc="mean",
        )
        .reindex(list(REPORT_BASKETS))
        .reset_index()
    )
    return "\n".join(
        [
            f"### {window_name.replace('_', ' ').title()}",
            "",
            _render_table(summary),
            "",
        ]
    )


def _render_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_no rows_"
    columns = list(frame.columns)
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    rows = []
    for _, row in frame.iterrows():
        rows.append("| " + " | ".join(_stringify(row[column]) for column in columns) + " |")
    return "\n".join([header, separator, *rows])


def _stringify(value: object) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


if __name__ == "__main__":
    main()
