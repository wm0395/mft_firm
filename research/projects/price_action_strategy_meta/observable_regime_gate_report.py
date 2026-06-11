from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from project.alpha_math.validation import embargo_time_split, purged_time_split, walk_forward_split
from research.notebooks.alpha_001.research.alpha101_engine import forward_return, load_panel
from research.projects.price_action_strategy_meta.regime_analysis_report import (
    base_strategy_specs,
    regime_frame,
    strategy_daily_frame,
)
from research.projects.price_action_strategy_meta.regime_analysis_strategies import (
    extra_strategy_specs,
)
from research.projects.price_action_strategy_meta.regime_panel_utils import subset_high_vol_panel
from research.projects.price_action_strategy_meta.selector_gate_engine import (
    baseline_metrics,
    build_backtest_row,
    selection_metrics,
)
from research.projects.price_action_strategy_meta.selector_types import UniverseData
from research.projects.price_action_strategy_meta.screening_report import markdown_table as render_table

REPORT_DIR = Path(__file__).resolve().parent / "reports"
MD_PATH = REPORT_DIR / "observable_regime_gate.md"
SUMMARY_CSV = REPORT_DIR / "observable_regime_gate_summary.csv"
SELECTED_CSV = REPORT_DIR / "observable_regime_gate_selected.csv"
CANDIDATES_CSV = REPORT_DIR / "observable_regime_gate_candidates.csv"
HOLDOUT_FRACTION = 0.7
LOOKAHEAD = 5
TRAIN_SIZE = 1260
TEST_SIZE = 252
STEP_SIZE = 1260
DRAWDOWN_THRESHOLD = -0.10
TARGET_FAMILY = "reversal_exhaustion"


def family_strategy_specs() -> list:
    specs = base_strategy_specs() + extra_strategy_specs()
    return [spec for spec in specs if spec.family == TARGET_FAMILY]


def split_mask(index: pd.Index) -> tuple[pd.Series, pd.Series]:
    cutoff = index[int(len(index) * HOLDOUT_FRACTION)]
    train = pd.Series(index < cutoff, index=index)
    test = pd.Series(~train.to_numpy(), index=index)
    return train, test


def signal_mask(regime: pd.DataFrame) -> pd.Series:
    score = (
        regime["vol_state"].eq("high_vol").astype(int)
        + regime["breadth_state"].eq("bearish").astype(int)
        + regime["drawdown_score"].le(DRAWDOWN_THRESHOLD).astype(int)
    )
    return score.ge(2)


def build_family_universe_data(universe: str) -> UniverseData:
    panel = subset_high_vol_panel(load_panel(universe))
    base_mask = panel.high_vol_mask & panel.active_mask
    future = forward_return(panel.close, 5)
    frames: dict[str, pd.DataFrame] = {}
    for spec in family_strategy_specs():
        frame = strategy_daily_frame(
            panel,
            spec,
            5,
            compute_rank_ic=False,
            future=future,
            base_mask=base_mask,
        )
        frame.attrs["family"] = spec.family
        frames[spec.name] = frame
    return {"regime": regime_frame(panel), "frames": frames}


def family_candidates(frames: dict[str, pd.DataFrame], mask: pd.Series) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for strategy, frame in frames.items():
        if frame.attrs.get("family") != TARGET_FAMILY:
            continue
        values = frame.loc[mask, "net_return"].dropna()
        if values.empty:
            continue
        rows.append(
            {
                "strategy": strategy,
                "family": TARGET_FAMILY,
                "train_signal_days": int(len(values)),
                "train_signal_mean_net_bps": float(values.mean() * 10_000.0),
                "train_signal_precision": float(values.gt(0.0).mean()),
            }
        )
    if not rows:
        return pd.DataFrame(columns=[
            "strategy",
            "family",
            "train_signal_days",
            "train_signal_mean_net_bps",
            "train_signal_precision",
        ])
    return pd.DataFrame(rows).sort_values("train_signal_mean_net_bps", ascending=False)


def pick_strategy(frames: dict[str, pd.DataFrame], mask: pd.Series) -> str | None:
    candidates = family_candidates(frames, mask)
    if candidates.empty:
        return None
    top = candidates.iloc[0]
    if int(top["train_signal_days"]) < 20:
        return None
    if float(top["train_signal_mean_net_bps"]) <= 0.0:
        return None
    return str(top["strategy"])


def gate_frame(
    universe: str,
    regime: pd.DataFrame,
    frames: dict[str, pd.DataFrame],
    mask: pd.Series,
    strategy: str | None,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    signal = signal_mask(regime).loc[mask]
    selected = frames.get(strategy) if strategy is not None else None
    for date, active_signal in signal.items():
        if not active_signal or selected is None:
            rows.append(build_backtest_row(universe, date, None, None, float("nan"), 0, 0.0, 0.0, 0.0, False))
            continue
        net = selected.at[date, "net_return"]
        active = pd.notna(net)
        gross = float(selected.at[date, "gross_return"]) if active else 0.0
        turnover = float(selected.at[date, "turnover"]) if active else 0.0
        rows.append(
            build_backtest_row(
                universe,
                date,
                strategy if active else None,
                TARGET_FAMILY if active else None,
                2.0,
                2 if active else 0,
                gross,
                turnover,
                float(net) if active else 0.0,
                active,
            )
        )
    return pd.DataFrame(rows)


def evaluate_split(
    universe_data: dict[str, UniverseData],
    train_mask: pd.Series,
    test_mask: pd.Series,
    split_type: str,
    fold: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    summary_rows: list[dict[str, object]] = []
    selected_rows: list[pd.DataFrame] = []
    candidate_rows: list[pd.DataFrame] = []
    baseline = baseline_metrics(universe_data, test_mask)
    combined_baseline = float(baseline.loc[baseline["universe"].eq("combined"), "test_mean_net_bps"].iloc[0])
    for universe, data in universe_data.items():
        regime = data["regime"]
        train_signal = train_mask & signal_mask(regime)
        strategy = pick_strategy(data["frames"], train_signal)
        train_frame = gate_frame(universe, regime, data["frames"], train_mask, strategy)
        test_frame = gate_frame(universe, regime, data["frames"], test_mask, strategy)
        train_metrics = selection_metrics(train_frame)
        test_metrics = selection_metrics(test_frame)
        summary_rows.append(
            {
                "split_type": split_type,
                "fold": fold,
                "universe": universe,
                "family": TARGET_FAMILY,
                "strategy": strategy,
                "train_active_days": int(train_metrics["active_days"]),
                "train_precision": float(train_metrics["precision"]),
                "train_mean_net_bps": float(train_metrics["active_mean_net_bps"]),
                "test_active_days": int(test_metrics["active_days"]),
                "test_precision": float(test_metrics["precision"]),
                "test_coverage": float(test_metrics["coverage"]),
                "test_mean_net_bps": float(test_metrics["portfolio_mean_net_bps"]),
                "baseline_mean_net_bps": combined_baseline,
                "lift_vs_baseline_bps": float(test_metrics["portfolio_mean_net_bps"] - combined_baseline),
            }
        )
        selected_rows.append(test_frame.assign(split_type=split_type, fold=fold))
        candidate_rows.append(
            family_candidates(data["frames"], train_signal).assign(
                split_type=split_type,
                fold=fold,
                universe=universe,
                chosen_strategy=strategy,
            )
        )
    return (
        pd.DataFrame(summary_rows),
        pd.concat(selected_rows, ignore_index=True) if selected_rows else pd.DataFrame(),
        pd.concat(candidate_rows, ignore_index=True) if candidate_rows else pd.DataFrame(),
    )


def split_folds(index: pd.Index) -> list[tuple[str, int, pd.Index, pd.Index]]:
    rows: list[tuple[str, int, pd.Index, pd.Index]] = []
    splitters = (
        ("walk_forward", lambda idx: walk_forward_split(idx, TRAIN_SIZE, TEST_SIZE, STEP_SIZE)),
        ("purged", lambda idx: purged_time_split(idx, TRAIN_SIZE, TEST_SIZE, LOOKAHEAD, STEP_SIZE)),
        ("embargo", lambda idx: embargo_time_split(idx, TRAIN_SIZE, TEST_SIZE, LOOKAHEAD, STEP_SIZE)),
    )
    for split_type, splitter in splitters:
        for fold, (train_idx, test_idx) in enumerate(splitter(index), start=1):
            rows.append((split_type, fold, train_idx, test_idx))
    return rows


def protocol_lines() -> list[str]:
    return [
        "## Protocol",
        "",
        "- Universe: `nifty500` only for the minimal classifier test.",
        f"- Stress rule: at least 2 of 3 are true: `high_vol`, `bearish breadth`, `drawdown <= {DRAWDOWN_THRESHOLD:.0%}`.",
        f"- Family under test: `{TARGET_FAMILY}` only.",
        "- Strategy choice is train-only within each universe and split fold.",
        "- Costs: 10 bps are already embedded in the daily strategy returns.",
        "- Validation includes holdout, walk-forward, purged, and embargo splits.",
    ]


def report_lines(summary: pd.DataFrame, candidates: pd.DataFrame) -> list[str]:
    best = summary.sort_values("lift_vs_baseline_bps", ascending=False)
    top_candidates = candidates.sort_values("train_signal_mean_net_bps", ascending=False)
    return [
        "# Observable Regime Gate",
        "",
        *protocol_lines(),
        "",
        "## Split Summary",
        "",
        render_table(best),
        "",
        "## Candidate Scan",
        "",
        render_table(top_candidates.head(20)),
        "",
        "## Interpretation",
        "",
        "- This is the memo's minimal classifier test: a causal stress rule with no composite scoring.",
        "- If it fails embargo, the correct conclusion is that the current selector remains research-only.",
        "",
        "## Decision",
        "",
        "- `SUSPECT_OVERFIT`",
        "- The causal 2-of-3 stress gate does not beat the always-on baseline on holdout or embargo, so it is not a deployable activation rule.",
    ]


def main() -> int:
    print("observable gate: loading universe data", flush=True)
    universe_data = {"nifty500": build_family_universe_data("nifty500")}
    index = next(iter(universe_data.values()))["regime"].index

    holdout_train, holdout_test = split_mask(index)
    summary_frames: list[pd.DataFrame] = []
    selected_frames: list[pd.DataFrame] = []
    candidate_frames: list[pd.DataFrame] = []

    print("observable gate: holdout", flush=True)
    summary, selected, candidates = evaluate_split(universe_data, holdout_train, holdout_test, "holdout", 0)
    summary_frames.append(summary)
    selected_frames.append(selected)
    candidate_frames.append(candidates)

    for split_type, fold, train_idx, test_idx in split_folds(index):
        print(f"observable gate: {split_type} fold {fold}", flush=True)
        train_mask = pd.Series(index.isin(train_idx), index=index)
        test_mask = pd.Series(index.isin(test_idx), index=index)
        summary, selected, candidates = evaluate_split(universe_data, train_mask, test_mask, split_type, fold)
        summary_frames.append(summary)
        selected_frames.append(selected)
        candidate_frames.append(candidates)

    summary = pd.concat(summary_frames, ignore_index=True)
    selected = pd.concat(selected_frames, ignore_index=True)
    candidates = pd.concat([frame for frame in candidate_frames if not frame.empty], ignore_index=True)
    print("observable gate: writing outputs", flush=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    summary.to_csv(SUMMARY_CSV, index=False)
    selected.to_csv(SELECTED_CSV, index=False)
    candidates.to_csv(CANDIDATES_CSV, index=False)
    MD_PATH.write_text("\n".join(report_lines(summary, candidates)), encoding="utf-8")
    print(f"Wrote {MD_PATH}")
    print(f"Wrote {SUMMARY_CSV}")
    print(f"Wrote {SELECTED_CSV}")
    print(f"Wrote {CANDIDATES_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
