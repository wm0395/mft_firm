from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from project.alpha_math.validation import embargo_time_split, purged_time_split, walk_forward_split
from research.projects.price_action_strategy_meta.selector_gate_engine import (
    backtest_policy,
    baseline_metrics,
    candidate_scan_train_only,
    selection_metrics,
)
from research.projects.price_action_strategy_meta.selector_gate_report import build_universe_data, training_summary
from research.projects.price_action_strategy_meta.selector_types import UniverseData
from research.projects.price_action_strategy_meta.selector_walk_forward_report import FoldResult, abstain_policy, build_masks
from research.projects.price_action_strategy_meta.screening_report import markdown_table as render_table

REPORT_DIR = Path(__file__).resolve().parent / "reports"
MD_PATH = REPORT_DIR / "selector_split_sensitivity.md"
SUMMARY_CSV = REPORT_DIR / "selector_split_sensitivity_summary.csv"
FOLDS_CSV = REPORT_DIR / "selector_split_sensitivity_folds.csv"
LOOKAHEAD = 5


@dataclass(frozen=True)
class Variant:
    sweep: str
    setting: str
    shift: int
    train_size: int
    test_size: int
    step_size: int
    embargo: int
    split_types: tuple[str, ...]


def split_folds(index: pd.Index, variant: Variant) -> list[tuple[str, int, pd.Index, pd.Index]]:
    shifted = index[variant.shift :]
    splitters = {
        "walk_forward": lambda idx: walk_forward_split(idx, variant.train_size, variant.test_size, variant.step_size),
        "purged": lambda idx: purged_time_split(idx, variant.train_size, variant.test_size, LOOKAHEAD, variant.step_size),
        "embargo": lambda idx: embargo_time_split(idx, variant.train_size, variant.test_size, variant.embargo, variant.step_size),
    }
    rows: list[tuple[str, int, pd.Index, pd.Index]] = []
    for split_type in variant.split_types:
        for fold, (train_idx, test_idx) in enumerate(splitters[split_type](shifted), start=1):
            rows.append((split_type, fold, train_idx, test_idx))
    return rows


def evaluate_fold(
    universe_data: dict[str, UniverseData],
    index: pd.Index,
    split_type: str,
    fold: int,
    train_idx: pd.Index,
    test_idx: pd.Index,
) -> FoldResult:
    train_mask, test_mask = build_masks(index, train_idx, test_idx)
    summary, priors = training_summary(universe_data, train_mask)
    try:
        policy = candidate_scan_train_only(universe_data, summary, priors, train_mask)
    except ValueError:
        policy = abstain_policy()
    train_frame = backtest_policy(universe_data, policy, train_mask)
    test_frame = backtest_policy(universe_data, policy, test_mask)
    train_metrics = selection_metrics(train_frame)
    test_metrics = selection_metrics(test_frame)
    baseline = baseline_metrics(universe_data, test_mask)
    combined_baseline = float(baseline.loc[baseline["universe"].eq("combined"), "test_mean_net_bps"].iloc[0])
    return FoldResult(
        split_type=split_type,
        fold=fold,
        policy=policy.thresholds.name,
        train_start=str(train_idx[0].date()),
        train_end=str(train_idx[-1].date()),
        test_start=str(test_idx[0].date()),
        test_end=str(test_idx[-1].date()),
        train_precision=float(train_metrics["precision"]),
        train_coverage=float(train_metrics["coverage"]),
        train_mean_net_bps=float(train_metrics["portfolio_mean_net_bps"]),
        test_precision=float(test_metrics["precision"]),
        test_coverage=float(test_metrics["coverage"]),
        test_mean_net_bps=float(test_metrics["portfolio_mean_net_bps"]),
        baseline_mean_net_bps=combined_baseline,
        lift_vs_baseline_bps=float(test_metrics["portfolio_mean_net_bps"] - combined_baseline),
    )


def evaluate_variant(
    universe_data: dict[str, UniverseData],
    index: pd.Index,
    variant: Variant,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    fold_rows = [
        evaluate_fold(universe_data, index, split_type, fold, train_idx, test_idx)
        for split_type, fold, train_idx, test_idx in split_folds(index, variant)
    ]
    fold_frame = pd.DataFrame([row.__dict__ for row in fold_rows]).assign(
        sweep=variant.sweep,
        setting=variant.setting,
    )
    summary = (
        fold_frame.groupby(["sweep", "setting", "split_type"], as_index=False)
        .agg(
            folds=("fold", "count"),
            active_folds=("policy", lambda s: int((s != "abstain").sum())),
            test_precision=("test_precision", "mean"),
            test_coverage=("test_coverage", "mean"),
            test_mean_net_bps=("test_mean_net_bps", "mean"),
            baseline_mean_net_bps=("baseline_mean_net_bps", "mean"),
            lift_vs_baseline_bps=("lift_vs_baseline_bps", "mean"),
        )
        .sort_values(["sweep", "setting", "split_type"])
    )
    return summary, fold_frame


def variants() -> list[Variant]:
    shifted = [
        Variant("shifted_boundaries", f"shift_{shift}", shift, 1260, 252, 1260, 5, ("walk_forward", "purged", "embargo"))
        for shift in (0, 63, 126)
    ]
    embargo = [
        Variant("embargo_length", f"embargo_{embargo}", 0, 1260, 252, 1260, embargo, ("embargo",))
        for embargo in (0, 5, 10, 20)
    ]
    windows = [
        Variant("train_window", f"train_{train}", 0, train, 252, train, 5, ("walk_forward", "embargo"))
        for train in (1000, 1260, 1500)
    ]
    return shifted + embargo + windows


def build_report(summary: pd.DataFrame) -> str:
    lines = ["# Selector Split Sensitivity", "", "## Protocol", ""]
    lines.extend(
        [
            "- Shifted boundary tests rerun the current selector after dropping the earliest portion of the date index.",
            "- Embargo-length tests rerun the embargo split with alternate embargo windows.",
            "- Train-window tests rerun the leakage-controlled selector with shorter and longer training spans.",
        ]
    )
    lines.extend(["", "## Summary", "", render_table(summary), "", "## Interpretation", ""])
    lines.extend(
        [
            "- If the selector were durable, the lift would not collapse under modest boundary and window perturbations.",
            "- If the selector is fragile, these sweeps should remain below the always-on baseline or swing sharply across settings.",
            "", "## Decision", "", "- `SUSPECT_OVERFIT`",
            "- The current split-sensitive sweeps are still intended as falsification checks, not as deployment evidence.",
        ]
    )
    return "\n".join(lines)


def write_outputs(summary: pd.DataFrame, folds: pd.DataFrame) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    MD_PATH.write_text(build_report(summary), encoding="utf-8")
    SUMMARY_CSV.write_text(summary.to_csv(index=False), encoding="utf-8")
    FOLDS_CSV.write_text(folds.to_csv(index=False), encoding="utf-8")


def main() -> int:
    universe_data: dict[str, UniverseData] = {}
    for universe in ("nifty500", "expanded"):
        universe_data[universe] = build_universe_data(universe)
    index = next(iter(universe_data.values()))["regime"].index
    summary_frames: list[pd.DataFrame] = []
    fold_frames: list[pd.DataFrame] = []
    for variant in variants():
        summary, folds = evaluate_variant(universe_data, index, variant)
        summary_frames.append(summary)
        fold_frames.append(folds)
    summary = pd.concat(summary_frames, ignore_index=True)
    folds = pd.concat(fold_frames, ignore_index=True)
    write_outputs(summary, folds)
    print(f"Wrote {MD_PATH}")
    print(f"Wrote {SUMMARY_CSV}")
    print(f"Wrote {FOLDS_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
