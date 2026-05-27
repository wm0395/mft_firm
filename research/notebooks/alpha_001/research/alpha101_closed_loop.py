from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pandas as pd  # type: ignore[import-untyped]


SUMMARY_JSON = "alpha101_closed_loop_summary.json"
SUMMARY_MD = "alpha101_closed_loop_summary.md"
SNAPSHOT_FILE = "alpha101_metrics_snapshot.json"
SHORTLIST_FILE = "alpha101_robustness_shortlist.csv"
STRICT_LIQUIDITY_FILE = "alpha101_strict_liquidity_primary_report.csv"
STRICT_LIQUIDITY_POSITIVE_FOCUS_FILE = "alpha101_strict_liquidity_positive_focus.csv"
VALIDATION_FILE = "alpha101_robustness_validation.csv"
BATCH2_SHORTLIST_FILE = "alpha101_robustness_batch2_shortlist.csv"


def read_csv_if_exists(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def read_snapshot_if_exists(path: Path) -> dict[str, object]:
    return json.loads(path.read_text()) if path.exists() else {}


def frame_from_rows(rows: list[dict[str, object]]) -> pd.DataFrame:
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def counts_from_snapshot(rows: object, label_key: str, value_key: str) -> dict[str, object]:
    if not isinstance(rows, list):
        return {}
    counts: dict[str, object] = {}
    for row in rows:
        if isinstance(row, dict) and label_key in row and value_key in row:
            counts[str(row[label_key])] = row[value_key]
    return counts


def snapshot_count_total(counts: dict[str, object]) -> int | None:
    total = 0
    for value in counts.values():
        try:
            total += int(value)
        except (TypeError, ValueError):
            return None
    return total if counts else None


def _top_rows(frame: pd.DataFrame, sort_col: str, limit: int = 10) -> list[dict[str, object]]:
    if frame.empty or sort_col not in frame.columns:
        return []
    working = frame.copy()
    numeric_sort = pd.to_numeric(working[sort_col], errors="coerce")
    if numeric_sort.notna().any():
        working[sort_col] = numeric_sort
    cols = [col for col in working.columns if col in {sort_col, "panel", "alpha_id", "robustness_lane", "input_quality_tier", "final_status", "median_test_active_sharpe", "median_test_active_cagr", "median_test_rank_ic", "median_turnover", "selected_mask", "selected_signal_transform", "selected_strategy"}]
    return working.sort_values(sort_col, ascending=False).head(limit)[cols].to_dict(orient="records")


def positive_focus_rows(frame: pd.DataFrame, sort_col: str, limit: int = 8) -> list[dict[str, object]]:
    if frame.empty or sort_col not in frame.columns:
        return []
    working = frame.copy()
    working[sort_col] = pd.to_numeric(working[sort_col], errors="coerce")
    focus = working[working[sort_col].gt(0)].copy()
    if focus.empty:
        focus = working.copy()
    return _top_rows(focus, sort_col, limit)


def strict_positive_focus(frame: pd.DataFrame) -> list[dict[str, object]]:
    if frame.empty or "median_test_active_sharpe" not in frame.columns:
        return []
    working = frame.copy()
    working["median_test_active_sharpe"] = pd.to_numeric(working["median_test_active_sharpe"], errors="coerce")
    focus = working[working["median_test_active_sharpe"].gt(0)].copy()
    if "positive_test_sharpe_rate" in focus.columns:
        rate = pd.to_numeric(focus["positive_test_sharpe_rate"], errors="coerce")
        focus = focus[rate.ge(0.75)].copy()
    return _top_rows(focus, "median_test_active_sharpe", 8)


def validation_pass_rate(validation: pd.DataFrame) -> float | None:
    if validation.empty or "passed" not in validation.columns:
        return None
    return float(validation["passed"].astype(bool).mean())


def summarize_closed_loop(artifact_dir: Path) -> dict[str, object]:
    shortlist = read_csv_if_exists(artifact_dir / SHORTLIST_FILE)
    strict_liquidity = read_csv_if_exists(artifact_dir / STRICT_LIQUIDITY_FILE)
    validation = read_csv_if_exists(artifact_dir / VALIDATION_FILE)
    batch2_shortlist = read_csv_if_exists(artifact_dir / BATCH2_SHORTLIST_FILE)
    snapshot = read_snapshot_if_exists(artifact_dir / SNAPSHOT_FILE)
    reports = cast(dict[str, object], snapshot.get("reports", {})) if snapshot else {}
    used_snapshot = shortlist.empty and bool(snapshot)
    if used_snapshot:
        batch1 = cast(dict[str, object], reports.get("robustness_batch1", {}))
        batch2 = cast(dict[str, object], reports.get("robustness_batch2", {}))
        shortlist = frame_from_rows(cast(list[dict[str, object]], batch1.get("top_rows", [])))
        batch2_shortlist = frame_from_rows(cast(list[dict[str, object]], batch2.get("results", [])))
        if strict_liquidity.empty and not shortlist.empty and "selected_mask" in shortlist.columns:
            strict_liquidity = shortlist[shortlist["selected_mask"].eq("strict_liquidity_100m")].copy()
    strict_numeric = strict_liquidity.copy()
    if not strict_numeric.empty and "median_test_active_sharpe" in strict_numeric.columns:
        strict_numeric["median_test_active_sharpe"] = pd.to_numeric(strict_numeric["median_test_active_sharpe"], errors="coerce")
    strict_positive = strict_positive_focus(strict_numeric)
    pass_rate = validation_pass_rate(validation)
    batch1_counts = cast(object, cast(dict[str, object], reports.get("robustness_batch1", {})).get("final_status_counts", []))
    shortlist_counts = shortlist["final_status"].value_counts(dropna=False).to_dict() if "final_status" in shortlist.columns and not used_snapshot else counts_from_snapshot(batch1_counts, "final_status", "candidates")
    shortlist_rows = snapshot_count_total(shortlist_counts) if used_snapshot else len(shortlist)
    summary = {
        "artifact_dir": str(artifact_dir),
        "shortlist_rows": int(shortlist_rows if shortlist_rows is not None else len(shortlist)),
        "shortlist_rows_source": "snapshot_status_counts" if used_snapshot and shortlist_rows is not None else "csv_or_rows",
        "shortlist_final_status_counts": shortlist_counts,
        "strict_liquidity_rows": int(len(strict_liquidity)),
        "strict_liquidity_median_test_active_sharpe": float(strict_numeric["median_test_active_sharpe"].median()) if not strict_numeric.empty and "median_test_active_sharpe" in strict_numeric.columns else float("nan"),
        "strict_liquidity_positive_sharpe_rate": float(strict_numeric["median_test_active_sharpe"].gt(0).mean()) if not strict_numeric.empty and "median_test_active_sharpe" in strict_numeric.columns else float("nan"),
        "strict_liquidity_selected_mask_counts": strict_liquidity["selected_mask"].value_counts(dropna=False).to_dict() if "selected_mask" in strict_liquidity.columns else {},
        "strict_liquidity_positive_focus_rows": int(len(strict_positive)),
        "strict_liquidity_positive_focus": strict_positive,
        "validation_rows": int(len(validation)),
        "validation_pass_rate": pass_rate,
        "validation_status": "present" if pass_rate is not None else "missing",
        "validation_failed_checks": validation.loc[~validation["passed"].astype(bool), "check"].tolist() if not validation.empty and {"passed", "check"}.issubset(validation.columns) else [],
        "batch2_shortlist_rows": int(len(batch2_shortlist)),
        "promoted_exact_ohlcv_rows": int(shortlist.query("final_status == 'promote_to_deeper_research' and input_quality_tier == 'exact_ohlcv'").shape[0]) if not shortlist.empty and {"final_status", "input_quality_tier"}.issubset(shortlist.columns) else 0,
        "top_shortlist": _top_rows(shortlist, "median_test_active_sharpe"),
        "top_strict_liquidity": _top_rows(strict_liquidity, "median_test_active_sharpe"),
        "top_batch2_shortlist": _top_rows(batch2_shortlist, "median_test_active_sharpe"),
    }
    return summary


def format_closed_loop_markdown(summary: dict[str, object]) -> str:
    validation_failures = cast(list[str], summary["validation_failed_checks"])
    pass_rate = summary["validation_pass_rate"]
    pass_rate_text = "missing" if pass_rate is None else str(pass_rate)
    failures_text = "Validation evidence missing" if summary["validation_status"] == "missing" else "None"
    if validation_failures:
        failures_text = ", ".join(validation_failures)
    return "\n".join(
        [
            "# Alpha101 Closed Loop Summary",
            "",
            f"- artifact_dir: `{summary['artifact_dir']}`",
            f"- shortlist_rows: `{summary['shortlist_rows']}`",
            f"- promoted_exact_ohlcv_rows: `{summary['promoted_exact_ohlcv_rows']}`",
            f"- strict_liquidity_rows: `{summary['strict_liquidity_rows']}`",
            f"- strict_liquidity_median_test_active_sharpe: `{summary['strict_liquidity_median_test_active_sharpe']}`",
            f"- strict_liquidity_positive_sharpe_rate: `{summary['strict_liquidity_positive_sharpe_rate']}`",
            f"- strict_liquidity_positive_focus_rows: `{summary['strict_liquidity_positive_focus_rows']}`",
            f"- validation_pass_rate: `{pass_rate_text}`",
            f"- validation_status: `{summary['validation_status']}`",
            "",
            "## Validation Failures",
            failures_text,
            "",
            "## Strict Liquidity Positive Focus",
            json.dumps(summary["strict_liquidity_positive_focus"], indent=2, sort_keys=True),
            "",
            "## Top Shortlist",
            json.dumps(summary["top_shortlist"], indent=2, sort_keys=True),
            "",
            "## Top Strict Liquidity",
            json.dumps(summary["top_strict_liquidity"], indent=2, sort_keys=True),
        ]
    )


def write_closed_loop_summary(artifact_dir: Path) -> tuple[Path, Path]:
    summary = summarize_closed_loop(artifact_dir)
    json_path = artifact_dir / SUMMARY_JSON
    md_path = artifact_dir / SUMMARY_MD
    positive_focus_path = artifact_dir / STRICT_LIQUIDITY_POSITIVE_FOCUS_FILE
    json_path.write_text(json.dumps(summary, allow_nan=False, indent=2, sort_keys=True))
    md_path.write_text(format_closed_loop_markdown(summary))
    pd.DataFrame(cast(list[dict[str, object]], summary["strict_liquidity_positive_focus"])).to_csv(positive_focus_path, index=False)
    return json_path, md_path


if __name__ == "__main__":
    write_closed_loop_summary(Path("research/artifacts/alpha101_research_factory"))
