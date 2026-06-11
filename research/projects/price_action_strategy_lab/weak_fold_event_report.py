from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class MarketEvent:
    start: date
    end: date
    label: str
    mechanism: str
    source_url: str


@dataclass(frozen=True)
class WeakFoldEventReportPaths:
    weak_folds: Path
    markdown: Path


EVENTS: tuple[MarketEvent, ...] = (
    MarketEvent(
        date(2025, 1, 1),
        date(2025, 3, 31),
        "early_2025_broad_correction_fpi_outflows",
        "Broad correction, mid/smallcap stress, FPI outflows, tariff/crude/rate worries.",
        "https://nsearchives.nseindia.com/web/sites/default/files/inline-files/Market%20Pulse_March%202025.pdf",
    ),
    MarketEvent(
        date(2025, 7, 20),
        date(2025, 7, 31),
        "july_2025_broad_based_selling",
        "Broad selling around weak global cues, earnings concern, and trade uncertainty.",
        "https://www.outlookmoney.com/market-intelligence/sensex-nifty-50-fall-for-second-straight-day-why-market-fell-today",
    ),
    MarketEvent(
        date(2026, 2, 1),
        date(2026, 3, 15),
        "feb_2026_it_global_tech_selloff",
        "IT/global-tech derating and AI-disruption concern spilled into Indian equities.",
        "https://www.moneycontrol.com/news/business/markets/infosys-ltimindtree-tcs-other-it-stocks-plunge-6-amid-global-tech-selloff-here-s-why-13809833.html",
    ),
)


def write_weak_fold_event_report(report_dir: Path) -> WeakFoldEventReportPaths:
    folds = _read(report_dir, "soft_throttle_walk_forward_alpha_fold_metrics.csv")
    gates = _read(report_dir, "soft_throttle_walk_forward_selected_gates.csv")
    weak_folds = weak_fold_events(folds, gates)
    paths = WeakFoldEventReportPaths(
        report_dir / "weak_fold_event_attribution.csv",
        report_dir / "weak_fold_event_attribution.md",
    )
    weak_folds.to_csv(paths.weak_folds, index=False)
    paths.markdown.write_text(_markdown(weak_folds), encoding="utf-8")
    return paths


def weak_fold_events(folds: pd.DataFrame, gates: pd.DataFrame) -> pd.DataFrame:
    if folds.empty:
        return pd.DataFrame()
    baseline = folds.loc[folds["variant"].eq("baseline")].copy()
    baseline = baseline.loc[baseline["return_pct"].le(baseline["return_pct"].quantile(0.20))]
    rows = [_weak_fold_row(row, gates) for row in baseline.itertuples()]
    return pd.DataFrame(rows).sort_values(["return_pct", "alpha"], ascending=[True, True])


def _weak_fold_row(row: object, gates: pd.DataFrame) -> dict[str, object]:
    test_start = pd.Timestamp(getattr(row, "test_start")).date()
    test_end = pd.Timestamp(getattr(row, "test_end")).date()
    event = _matching_event(test_start, test_end)
    gate = _matching_gate(gates, int(getattr(row, "fold")), str(getattr(row, "alpha")))
    return {
        "fold": int(getattr(row, "fold")),
        "alpha": str(getattr(row, "alpha")),
        "test_start": str(test_start),
        "test_end": str(test_end),
        "return_pct": float(getattr(row, "return_pct")),
        "max_drawdown_pct": float(getattr(row, "max_drawdown_pct")),
        "event_label": event.label if event else "unmatched",
        "event_mechanism": event.mechanism if event else "",
        "event_source_url": event.source_url if event else "",
        "selected_indicator": str(gate.get("indicator", "")),
        "selected_side": str(gate.get("side", "")),
        "selected_score": float(gate.get("score", 0.0)),
    }


def _matching_event(test_start: date, test_end: date) -> MarketEvent | None:
    for event in EVENTS:
        if test_start <= event.end and test_end >= event.start:
            return event
    return None


def _matching_gate(gates: pd.DataFrame, fold: int, alpha: str) -> pd.Series:
    if gates.empty:
        return pd.Series(dtype=object)
    match = gates.loc[gates["fold"].eq(fold) & gates["alpha"].eq(alpha)]
    return match.iloc[0] if not match.empty else pd.Series(dtype=object)


def _markdown(weak_folds: pd.DataFrame) -> str:
    lines = ["# Weak Fold Event Attribution", "", "## Worst Baseline Alpha Folds", ""]
    cols = [
        "fold",
        "alpha",
        "test_start",
        "test_end",
        "return_pct",
        "event_label",
        "selected_indicator",
        "selected_side",
    ]
    lines.append(_markdown_table(weak_folds[[col for col in cols if col in weak_folds]].head(25)))
    lines.extend(["", "## Interpretation", ""])
    lines.append("- Event labels are explanatory hypotheses only, not model inputs.")
    lines.append("- Any event-derived indicator must be timestamped, lagged, and tested OOS.")
    lines.append("- Use this report to explain failures before adding new blockers.")
    return "\n".join(lines)


def _markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_No rows._"
    cols = list(frame.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for row in frame.itertuples(index=False):
        lines.append("| " + " | ".join(_cell(item) for item in row) + " |")
    return "\n".join(lines)


def _cell(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def _read(report_dir: Path, name: str) -> pd.DataFrame:
    path = report_dir / name
    return pd.read_csv(path) if path.exists() else pd.DataFrame()
