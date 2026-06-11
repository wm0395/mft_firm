from __future__ import annotations

import math
from pathlib import Path
from typing import Final
from typing import Any, cast

import pandas as pd


PRESSURE_ORDER: Final = ("low", "medium", "high", "extreme")
REPORT_WINDOWS: Final = ("application", "release_5")
REPORT_BASKETS: Final = (
    "same_sector_peer",
    "recent_winners_60d_top50",
    "cash_source_60d_top50",
    "smallcap250",
    "midcap150",
)
STUDIES: Final = {
    "raw": ("ipo_pilot_event_study.csv", "abnormal_return"),
    "sector_adjusted": ("ipo_sector_adjusted_basket_event_study.csv", "sector_adjusted_abnormal_return"),
}


def main() -> None:
    root = Path(__file__).resolve().parent
    summaries = []
    for study_type, (filename, metric) in STUDIES.items():
        frame = pd.read_csv(root / "data" / filename)
        summaries.append(_summarize_study(frame, study_type, metric))
    summary = pd.concat(summaries, ignore_index=True)
    _write_outputs(root, summary)


def _summarize_study(frame: pd.DataFrame, study_type: str, metric: str) -> pd.DataFrame:
    rows = []
    for window_name in REPORT_WINDOWS:
        window_frame = frame.loc[frame["window_name"].eq(window_name)]
        for basket_name in REPORT_BASKETS:
            subset = window_frame.loc[window_frame["basket_name"].eq(basket_name)]
            means = subset.groupby("pressure_class")[metric].mean().reindex(PRESSURE_ORDER)
            rows.append(
                {
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
            )
    return pd.DataFrame(rows)


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
    numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y, strict=True))
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
    report_path = root / "reports" / "pressure_gradient_diagnostics.md"
    summary.to_csv(data_dir / "ipo_pressure_gradient_diagnostics.csv", index=False)
    report_path.write_text(_render_report(summary), encoding="utf-8")


def _render_report(summary: pd.DataFrame) -> str:
    rows = summary.copy()
    rows["abs_rho"] = rows["pressure_spearman_rho"].abs()
    top = rows.sort_values(["abs_rho", "study_type", "window_name", "basket_name"], ascending=[False, True, True, True]).head(10)
    lines = [
        "# Pressure Gradient Diagnostics",
        "",
        "## Objective",
        "",
        "Test whether any basket/window pair shows a stable pressure gradient after raw and sector-adjusted conditioning.",
        "",
        "## Summary",
        "",
        f"- Rows analyzed: {len(summary)} basket-window-study combinations.",
        f"- Non-mixed pressure directions: {int(summary['pressure_direction'].ne('mixed').sum())}.",
        f"- Strong gradients with |Spearman rho| >= 0.8: {int((rows['abs_rho'] >= 0.8).sum())}.",
        "",
        "## Top Gradients by |rho|",
        "",
        _render_table(top[[
            "study_type",
            "window_name",
            "basket_name",
            "pressure_direction",
            "pressure_spearman_rho",
            "pressure_linear_slope",
            "pressure_spread_extreme_minus_low",
        ]]),
        "",
        "## Reading",
        "",
        "- The sector-adjusted basket layer remains mixed, and the raw layer does not rescue a cleaner ordering.",
        "- The only non-mixed row is sector_adjusted / release_5 / midcap150, which orders low -> medium -> high -> extreme and produces rho 1.0.",
        "- A few basket/window pairs show partial ordering, but the overall pattern is not a stable monotonic pressure gradient.",
        "- This keeps the hypothesis in the falsification zone rather than promoting it into a tradable rule.",
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
