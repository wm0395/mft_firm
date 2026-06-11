from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Final, cast

import pandas as pd


PRESSURE_ORDER: Final = ("low", "medium", "high", "extreme")
WINDOW_ORDER: Final = ("application", "blocking", "release_3", "release_5", "listing_5")
BASKET_ORDER: Final = (
    "same_sector_peer",
    "recent_winners_60d_top50",
    "cash_source_60d_top50",
    "smallcap250",
    "midcap150",
)


def main() -> None:
    root = Path(__file__).resolve().parent
    raw = pd.read_csv(root / "data" / "ipo_pilot_event_study.csv")
    adjusted = pd.read_csv(root / "data" / "ipo_sector_adjusted_basket_event_study.csv")
    summary = pd.concat(
        [
            _midcap_stability_rows(raw, "raw", "abnormal_return"),
            _midcap_stability_rows(adjusted, "sector_adjusted", "sector_adjusted_abnormal_return"),
            _release_5_basket_rows(adjusted),
        ],
        ignore_index=True,
    )
    _write_outputs(root, summary)


def _midcap_stability_rows(frame: pd.DataFrame, study_type: str, metric: str) -> pd.DataFrame:
    rows = []
    for window_name in WINDOW_ORDER:
        subset = frame.loc[frame["window_name"].eq(window_name) & frame["basket_name"].eq("midcap150")]
        means = subset.groupby("pressure_class")[metric].mean().reindex(PRESSURE_ORDER)
        rows.append(_row("midcap_path", study_type, window_name, "midcap150", means))
    return pd.DataFrame(rows)


def _release_5_basket_rows(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    subset = frame.loc[frame["window_name"].eq("release_5")]
    for basket_name in BASKET_ORDER:
        basket_subset = subset.loc[subset["basket_name"].eq(basket_name)]
        means = basket_subset.groupby("pressure_class")["sector_adjusted_abnormal_return"].mean().reindex(PRESSURE_ORDER)
        rows.append(_row("basket_neighborhood", "sector_adjusted", "release_5", basket_name, means))
    return pd.DataFrame(rows)


def _row(section: str, study_type: str, window_name: str, basket_name: str, means: pd.Series) -> dict[str, object]:
    return {
        "section": section,
        "study_type": study_type,
        "window_name": window_name,
        "basket_name": basket_name,
        "low_mean": _value(means["low"]),
        "medium_mean": _value(means["medium"]),
        "high_mean": _value(means["high"]),
        "extreme_mean": _value(means["extreme"]),
        "pressure_spearman_rho": _spearman_rho(means),
        "pressure_linear_slope": _linear_slope(means),
        "pressure_direction": _direction(means),
        "pressure_spread_extreme_minus_low": _spread(means),
    }


def _value(value: object) -> float:
    if value is None or pd.isna(value):
        return math.nan
    return float(cast(Any, value))


def _spearman_rho(means: pd.Series) -> float:
    series = means.astype(float)
    if series.isna().any():
        return math.nan
    pressure_rank = pd.Series([1.0, 2.0, 3.0, 4.0], index=PRESSURE_ORDER)
    return float(pressure_rank.corr(series, method="spearman"))


def _linear_slope(means: pd.Series) -> float:
    series = means.astype(float)
    if series.isna().any():
        return math.nan
    x = [1.0, 2.0, 3.0, 4.0]
    y = series.tolist()
    x_mean = sum(x) / len(x)
    y_mean = sum(y) / len(y)
    numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y))
    denominator = sum((xi - x_mean) ** 2 for xi in x)
    return float(numerator / denominator) if denominator else math.nan


def _direction(means: pd.Series) -> str:
    series = means.dropna().tolist()
    if len(series) != len(PRESSURE_ORDER):
        return "insufficient"
    if all(left <= right for left, right in zip(series, series[1:])):
        return "nondecreasing"
    if all(left >= right for left, right in zip(series, series[1:])):
        return "nonincreasing"
    return "mixed"


def _spread(means: pd.Series) -> float:
    series = means.astype(float)
    if series.isna().any():
        return math.nan
    return float(series["extreme"] - series["low"])


def _write_outputs(root: Path, summary: pd.DataFrame) -> None:
    data_dir = root / "data"
    report_path = root / "reports" / "pressure_gradient_stability.md"
    summary.to_csv(data_dir / "ipo_pressure_gradient_stability.csv", index=False)
    report_path.write_text(_render_report(summary), encoding="utf-8")


def _render_report(summary: pd.DataFrame) -> str:
    rows = summary.copy()
    rows["abs_rho"] = rows["pressure_spearman_rho"].abs()
    midcap_rows = rows.loc[rows["section"].eq("midcap_path")].copy()
    release_rows = rows.loc[rows["section"].eq("basket_neighborhood")].copy()
    lines = [
        "# Pressure Gradient Stability",
        "",
        "## Objective",
        "",
        "Stress-test the one clean sector-adjusted pressure-gradient case against adjacent windows and nearby basket definitions.",
        "",
        "## Summary",
        "",
        f"- Rows analyzed: {len(summary)} stability combinations.",
        f"- Midcap150 rows analyzed: {len(midcap_rows)}.",
        f"- Non-mixed midcap150 rows: {int(midcap_rows['pressure_direction'].ne('mixed').sum())}.",
        f"- Non-mixed release_5 sector-adjusted baskets: {int(release_rows['pressure_direction'].ne('mixed').sum())}.",
        "",
        "## Midcap150 Across Windows",
        "",
        _render_table(midcap_rows[[
            "section",
            "study_type",
            "window_name",
            "pressure_direction",
            "pressure_spearman_rho",
            "pressure_linear_slope",
            "pressure_spread_extreme_minus_low",
        ]]),
        "",
        "## Release_5 Sector-Adjusted Basket Neighborhood",
        "",
        _render_table(release_rows[[
            "section",
            "basket_name",
            "pressure_direction",
            "pressure_spearman_rho",
            "pressure_linear_slope",
            "pressure_spread_extreme_minus_low",
        ]]),
        "",
        "## Reading",
        "",
        "- The clean sector-adjusted midcap150 release_5 case does not generalize to adjacent windows.",
        "- The release_5 basket neighborhood remains mixed outside midcap150, so the one clean case looks isolated rather than structural.",
        "- This makes the sector-adjusted gradient look like a narrow lead, not a stable pressure regime.",
    ]
    return "\n".join(lines)


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
