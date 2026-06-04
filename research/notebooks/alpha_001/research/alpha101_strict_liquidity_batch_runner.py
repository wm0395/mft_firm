from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd  # type: ignore[import-untyped]

NOTEBOOK_ROOT = Path(__file__).resolve().parents[1]
if str(NOTEBOOK_ROOT) not in sys.path:
    sys.path.insert(0, str(NOTEBOOK_ROOT))

if __package__:
    from .alpha101_robustness import strict_liquidity_primary_report  # type: ignore[import-untyped]  # noqa: E402
else:  # pragma: no cover
    from alpha101_robustness import strict_liquidity_primary_report  # type: ignore[import-untyped]  # noqa: E402


SHORTLIST_PATH = Path("research/artifacts/alpha101_research_factory/promoted_exact_shortlist_filled.csv")
POSITIVE_FOCUS_PATH = Path("research/artifacts/alpha101_research_factory/alpha101_strict_liquidity_positive_focus.csv")
CACHE_DIR = Path("research/artifacts/alpha101_research_factory/_strict_batches")
FINAL_CSV = Path("research/artifacts/alpha101_research_factory/alpha101_strict_liquidity_primary_report.csv")
BATCH_SIZE = 4
SHORTLIST_COLUMNS = {
    "panel",
    "alpha_id",
    "robustness_lane",
    "input_quality_tier",
    "final_status",
    "best_signal_transform",
    "best_strategy",
}


def aggregate_strict_batches(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    return frame.groupby(["panel", "alpha_id"], dropna=False).agg(
        robustness_lane=("robustness_lane", "first"),
        input_quality_tier=("input_quality_tier", "first"),
        folds=("folds", "first"),
        median_test_active_sharpe=("median_test_active_sharpe", "first"),
        median_test_active_cagr=("median_test_active_cagr", "first"),
        positive_test_sharpe_rate=("positive_test_sharpe_rate", "first"),
        median_test_rank_ic=("median_test_rank_ic", "first"),
        median_turnover=("median_turnover", "first"),
        worst_test_drawdown=("worst_test_drawdown", "first"),
        selected_mask=("selected_mask", "first"),
        selected_signal_transform=("selected_signal_transform", "first"),
        selected_strategy=("selected_strategy", "first"),
    ).reset_index().sort_values(["median_test_active_sharpe", "median_test_rank_ic"], ascending=False).reset_index(drop=True)


def batch_ranges(total: int, size: int) -> list[tuple[int, int]]:
    return [(start, min(total, start + size)) for start in range(0, total, size)]


def is_compatible_shortlist(path: Path) -> bool:
    if not path.exists():
        return False
    columns = set(pd.read_csv(path, nrows=0).columns)
    return SHORTLIST_COLUMNS.issubset(columns)


def resolve_shortlist_path() -> Path:
    if is_compatible_shortlist(POSITIVE_FOCUS_PATH):
        return POSITIVE_FOCUS_PATH
    if is_compatible_shortlist(SHORTLIST_PATH):
        return SHORTLIST_PATH
    raise FileNotFoundError("No schema-compatible strict-liquidity shortlist found")


def write_batch(shortlist: pd.DataFrame, start: int, end: int) -> pd.DataFrame:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    batch_path = CACHE_DIR / f"strict_{start:03d}_{end:03d}.csv"
    if batch_path.exists():
        return pd.read_csv(batch_path)
    batch = shortlist.iloc[start:end].copy()
    report = strict_liquidity_primary_report(pd.DataFrame(), batch)
    report.to_csv(batch_path, index=False)
    return report


def main() -> None:
    shortlist = pd.read_csv(resolve_shortlist_path())
    batches = []
    for index, (start, end) in enumerate(batch_ranges(len(shortlist), BATCH_SIZE), start=1):
        print(f"[strict-liquidity] batch {index} {start}:{end}", flush=True)
        batches.append(write_batch(shortlist, start, end))
        print(f"[strict-liquidity] batch {index} done", flush=True)
    combined = aggregate_strict_batches(pd.concat(batches, ignore_index=True, sort=False))
    combined.to_csv(FINAL_CSV, index=False)
    print(combined.head(25).to_string(index=False))


if __name__ == "__main__":
    main()
