from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

import numpy as np
import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from project.alpha_math.validation import embargo_time_split, purged_time_split, walk_forward_split
from research.projects.price_action_strategy_meta.selector_gate_engine import (
    GatePolicy,
    GateThresholds,
    backtest_policy,
    baseline_metrics,
    candidate_scan_train_only,
    selection_metrics,
)
from research.projects.price_action_strategy_meta.selector_gate_report import (
    build_universe_data,
    training_summary,
)
from research.projects.price_action_strategy_meta.selector_types import UniverseData
from research.projects.price_action_strategy_meta.screening_report import (
    markdown_table as render_table,
)

REPORT_DIR = Path(__file__).resolve().parent / "reports"
MD_PATH = REPORT_DIR / "selector_walk_forward.md"
SUMMARY_CSV = REPORT_DIR / "selector_walk_forward_summary.csv"
REGIME_CSV = REPORT_DIR / "selector_walk_forward_regime.csv"
SELECTED_CSV = REPORT_DIR / "selector_walk_forward_selected.csv"
RULES_CSV = REPORT_DIR / "selector_walk_forward_rules.csv"
HORIZON = 5
TRAIN_SIZE = 1260
TEST_SIZE = 252
STEP_SIZE = 1260
LOOKAHEAD = 5
EMBARGO = 5
SPLITS = (
    ("walk_forward", lambda index: walk_forward_split(index, TRAIN_SIZE, TEST_SIZE, STEP_SIZE)),
    ("purged", lambda index: purged_time_split(index, TRAIN_SIZE, TEST_SIZE, LOOKAHEAD, STEP_SIZE)),
    ("embargo", lambda index: embargo_time_split(index, TRAIN_SIZE, TEST_SIZE, EMBARGO, STEP_SIZE)),
)
REGIME_DIMS = (
    "vol_state",
    "trend_state",
    "breadth_state",
    "gap_state",
    "liquidity_state",
    "risk_state",
    "drawdown_state",
)


@dataclass(frozen=True)
class FoldResult:
    split_type: str
    fold: int
    policy: str
    train_start: str
    train_end: str
    test_start: str
    test_end: str
    train_precision: float
    train_coverage: float
    train_mean_net_bps: float
    test_precision: float
    test_coverage: float
    test_mean_net_bps: float
    baseline_mean_net_bps: float
    lift_vs_baseline_bps: float


def build_masks(index: pd.Index, train_idx: pd.Index, test_idx: pd.Index) -> tuple[pd.Series, pd.Series]:
    train = pd.Series(index.isin(train_idx), index=index)
    test = pd.Series(index.isin(test_idx), index=index)
    return train, test


def abstain_policy() -> GatePolicy:
    return GatePolicy(
        thresholds=GateThresholds("abstain", 0.0, 1.0, 0.0, 0, 1, 999.0, 1),
        rules=(),
        strategy_bonus=(),
    )


def fold_state_rows(
    selected_frame: pd.DataFrame,
    regime: pd.DataFrame,
    split_type: str,
    fold: int,
    universe: str,
) -> list[dict[str, object]]:
    merged = selected_frame.set_index("date").join(regime, how="left")
    active = merged[merged["active"]]
    rows: list[dict[str, object]] = []
    for dimension in REGIME_DIMS:
        total_counts = merged.groupby(dimension).size()
        for state, total_obs in total_counts.items():
            total = merged[merged[dimension].eq(state)]
            active_state = active[active[dimension].eq(state)]
            if len(total) == 0:
                continue
            std = float(active_state["net_return"].std(ddof=0))
            rows.append(
                {
                    "split_type": split_type,
                    "fold": fold,
                    "universe": universe,
                    "regime_dimension": dimension,
                    "regime_state": str(state),
                    "total_obs": int(total_obs),
                    "active_obs": int(len(active_state)),
                    "coverage": float(len(active_state) / len(total)),
                    "precision": float(active_state["net_return"].gt(0.0).mean()) if len(active_state) else float("nan"),
                    "mean_net_bps": float(active_state["net_return"].mean() * 10_000.0) if len(active_state) else float("nan"),
                    "tstat": float(active_state["net_return"].mean() / std * np.sqrt(len(active_state))) if std > 0.0 else float("nan"),
                }
            )
    return rows


def evaluate_fold(
    universe_data: dict[str, UniverseData],
    index: pd.Index,
    split_type: str,
    fold: int,
    train_idx: pd.Index,
    test_idx: pd.Index,
) -> tuple[
    FoldResult,
    list[dict[str, object]],
    pd.DataFrame,
    pd.DataFrame,
]:
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
    regime_rows: list[dict[str, object]] = []
    for universe, data in universe_data.items():
        universe_test = test_frame[test_frame["universe"].eq(universe)]
        regime_rows.extend(
            fold_state_rows(universe_test, data["regime"].loc[test_mask], split_type, fold, universe)
        )
    selected_frame = test_frame.assign(split_type=split_type, fold=fold)
    fold_result = FoldResult(
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
    rules = pd.DataFrame([rule.__dict__ for rule in policy.rules]).assign(split_type=split_type, fold=fold)
    return fold_result, regime_rows, selected_frame, rules


def split_folds(index: pd.Index) -> list[tuple[str, int, pd.Index, pd.Index]]:
    rows: list[tuple[str, int, pd.Index, pd.Index]] = []
    for split_type, splitter in SPLITS:
        for fold, (train_idx, test_idx) in enumerate(splitter(index), start=1):
            rows.append((split_type, fold, train_idx, test_idx))
    return rows


def protocol_lines() -> list[str]:
    return [
        "## Protocol",
        "",
        f"- Horizon: `{HORIZON}d`.",
        f"- Split sizes: train `{TRAIN_SIZE}`, test `{TEST_SIZE}`, step `{STEP_SIZE}`.",
        f"- Split families: walk-forward, purged lookahead `{LOOKAHEAD}`, and embargo `{EMBARGO}`.",
        "- Strategy pool: the base screen plus the supplemental first-principles extras, so the fold refit sees the broader trend, reversal, structure, and regime set.",
        "- The selector is refit on each training fold using the same candidate scan as the gate prototype, then filtered by the consensus support floor.",
        "- Family alignment bonus: reversal is favored in high-vol, bear, risk-off, gap-shock, and deep-drawdown states; trend is favored in bull and risk-on states; low-liquidity states are penalized.",
        "- This is the missing leakage-control layer for the selector gate.",
    ]


def split_summary_lines(fold_table: pd.DataFrame) -> list[str]:
    aggregate = (
        fold_table.groupby("split_type", as_index=False)
        .agg(
            folds=("fold", "count"),
            train_precision=("train_precision", "mean"),
            test_precision=("test_precision", "mean"),
            test_coverage=("test_coverage", "mean"),
            test_mean_net_bps=("test_mean_net_bps", "mean"),
            baseline_mean_net_bps=("baseline_mean_net_bps", "mean"),
            lift_vs_baseline_bps=("lift_vs_baseline_bps", "mean"),
        )
        .sort_values("lift_vs_baseline_bps", ascending=False)
    )
    return ["## Split Summary", "", render_table(aggregate), ""]


def fold_detail_lines(fold_table: pd.DataFrame) -> list[str]:
    return ["## Fold Detail", "", render_table(fold_table.head(15)), ""]


def regime_holdout_lines(regime: pd.DataFrame) -> list[str]:
    top_regimes = (
        regime.groupby(["split_type", "regime_dimension", "regime_state"], as_index=False)
        .agg(
            mean_net_bps=("mean_net_bps", "mean"),
            precision=("precision", "mean"),
            coverage=("coverage", "mean"),
            active_obs=("active_obs", "sum"),
            total_obs=("total_obs", "sum"),
            tstat=("tstat", "mean"),
        )
        .sort_values("mean_net_bps", ascending=False)
    )
    return ["## Regime Holdout", "", render_table(top_regimes.head(20)), ""]


def takeaway_lines() -> list[str]:
    return [
        "## Takeaway",
        "",
        "- All three split families remain below the combined always-on baseline on average.",
        "- Only fold 5 activates; folds 1-4 abstain, so the scan is not persistent across time.",
        "- Embargo remains negative on fold 5, so the selector stays research-only.",
    ]


def build_report(summary: pd.DataFrame, regime: pd.DataFrame) -> str:
    fold_table = summary.sort_values(["split_type", "fold"]).reset_index(drop=True)
    lines = [
        "# Walk-Forward Gate",
        "",
        *protocol_lines(),
        "",
        *split_summary_lines(fold_table),
        *fold_detail_lines(fold_table),
        *regime_holdout_lines(regime),
        *takeaway_lines(),
    ]
    return "\n".join(lines)


def write_outputs(summary: pd.DataFrame, regime: pd.DataFrame, selected: pd.DataFrame, rules: pd.DataFrame) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    summary.to_csv(SUMMARY_CSV, index=False)
    regime.to_csv(REGIME_CSV, index=False)
    selected.to_csv(SELECTED_CSV, index=False)
    rules.to_csv(RULES_CSV, index=False)
    MD_PATH.write_text(build_report(summary, regime), encoding="utf-8")


def main() -> int:
    universe_data: dict[str, UniverseData] = {}
    for name in ("nifty500", "expanded"):
        print(f"walk-forward: building {name}", flush=True)
        universe_data[name] = build_universe_data(name)
    index = next(iter(universe_data.values()))["regime"].index
    fold_rows: list[FoldResult] = []
    regime_rows: list[dict[str, object]] = []
    selected_frames: list[pd.DataFrame] = []
    rule_frames: list[pd.DataFrame] = []
    for split_type, fold, train_idx, test_idx in split_folds(index):
        print(
            f"walk-forward {split_type} fold {fold}: train {train_idx[0].date()}..{train_idx[-1].date()} test {test_idx[0].date()}..{test_idx[-1].date()}",
            flush=True,
        )
        fold_result, fold_regime_rows, selected_frame, rules = evaluate_fold(
            universe_data, index, split_type, fold, train_idx, test_idx
        )
        print(
            f"walk-forward {split_type} fold {fold}: policy {fold_result.policy} lift {fold_result.lift_vs_baseline_bps:.3f} bps",
            flush=True,
        )
        fold_rows.append(fold_result)
        regime_rows.extend(fold_regime_rows)
        selected_frames.append(selected_frame)
        rule_frames.append(rules)
    summary = pd.DataFrame([row.__dict__ for row in fold_rows])
    regime = pd.DataFrame(regime_rows)
    selected = pd.concat(selected_frames, ignore_index=True) if selected_frames else pd.DataFrame()
    rules = pd.concat(rule_frames, ignore_index=True) if rule_frames else pd.DataFrame()
    write_outputs(summary, regime, selected, rules)
    print(f"Wrote {MD_PATH}")
    print(f"Wrote {SUMMARY_CSV}")
    print(f"Wrote {REGIME_CSV}")
    print(f"Wrote {SELECTED_CSV}")
    print(f"Wrote {RULES_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
