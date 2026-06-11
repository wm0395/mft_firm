from __future__ import annotations

import math
from pathlib import Path
from typing import Any, cast

import pandas as pd


SECTOR_PANEL_PATH = Path(__file__).resolve().parent / "data" / "sector_history.parquet"
SEED_EVENTS_PATH = Path(__file__).resolve().parent / "data" / "ipo_events_seed.csv"
PILOT_RESULTS_PATH = Path(__file__).resolve().parent / "data" / "ipo_pilot_event_study.csv"
CONSTITUENTS_PATH = Path(__file__).resolve().parent.parents[1] / "data" / "expanded_high_vol_parent" / "expanded_parent_constituents.csv"


def main() -> None:
    root = Path(__file__).resolve().parent
    seed = pd.read_csv(SEED_EVENTS_PATH)
    pilot = pd.read_csv(PILOT_RESULTS_PATH)
    sector_history = _load_sector_history(SECTOR_PANEL_PATH)
    sector_map = _load_sector_map(CONSTITUENTS_PATH)
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
    rows = []
    sector_groups = {sector: frame.reset_index(drop=True) for sector, frame in sector_history.groupby("sector")}
    for row in pilot.itertuples(index=False):
        sector = sector_map.get(str(row.symbol_after_listing))
        sector_frame = sector_groups.get(sector, pd.DataFrame())
        start = pd.to_datetime(row.window_start)
        end = pd.to_datetime(row.window_end)
        sector_window = sector_frame.loc[(sector_frame["date"] >= start) & (sector_frame["date"] <= end)] if not sector_frame.empty else pd.DataFrame()
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
    report_path = root / "reports" / "sector_conditioned_event_study.md"
    conditioned.to_csv(data_dir / "ipo_sector_conditioned_event_study.csv", index=False)
    report_path.write_text(_render_report(conditioned, seed, sector_map), encoding="utf-8")


def _render_report(conditioned: pd.DataFrame, seed: pd.DataFrame, sector_map: dict[str, str]) -> str:
    seed_symbols = seed["symbol_after_listing"].astype(str).tolist()
    mapped_symbols = [symbol for symbol in seed_symbols if symbol in sector_map]
    missing_symbols = [symbol for symbol in seed_symbols if symbol not in sector_map]
    same_sector = conditioned.loc[conditioned["basket_name"].eq("same_sector_peer")]
    lines = [
        "# Sector-Conditioned Event Study",
        "",
        "## Objective",
        "",
        "Test whether the same-sector peer signal survives a sector-return adjustment using the new sector proxy panel.",
        "",
        "## Coverage",
        "",
        f"- Sector mapping is available for {len(mapped_symbols)} of the {len(seed_symbols)} seed IPO symbols in the expanded-parent panel.",
        f"- Missing from the sector map for this pass: {', '.join(missing_symbols) if missing_symbols else 'none'}.",
        "",
        "## Same-Sector Peer Reading",
        "",
        _render_table(_summary_table(same_sector, "application")),
        "",
        _render_table(_summary_table(same_sector, "release_5")),
        "",
        "## Interpretation",
        "",
        "- The sector layer gives a direct falsification check for the same-sector basket instead of relying only on broad-market adjustment.",
        "- The sector-adjusted same-sector peer averages stay mixed across pressure buckets in both windows.",
        "- If the sector-adjusted same-sector peer averages remain mixed, sector drift is not rescuing the pull/release story.",
        "- The sector proxy panel is helpful, but it still does not replace direct turnover or delivery history.",
    ]
    return "\n".join(lines)


def _summary_table(frame: pd.DataFrame, window_name: str) -> pd.DataFrame:
    subset = frame.loc[frame["window_name"].eq(window_name)]
    summary = subset.groupby("pressure_class", as_index=False).agg(
        raw_abnormal_return=("abnormal_return", "mean"),
        sector_window_return=("sector_window_return", "mean"),
        sector_adjusted_abnormal_return=("sector_adjusted_abnormal_return", "mean"),
    )
    order = pd.CategoricalDtype(["extreme", "high", "medium", "low"], ordered=True)
    summary["pressure_class"] = summary["pressure_class"].astype(order)
    summary = summary.sort_values("pressure_class").reset_index(drop=True)
    return summary


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
