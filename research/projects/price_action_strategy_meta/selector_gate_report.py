from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from research.notebooks.alpha_001.research.alpha101_engine import load_panel
from research.projects.price_action_strategy_meta.regime_analysis_report import (
    base_strategy_specs,
    daily_group_summary,
    regime_frame,
    strategy_daily_frame,
)
from research.projects.price_action_strategy_meta.regime_analysis_strategies import (
    extra_strategy_specs,
)
from research.projects.price_action_strategy_meta.regime_panel_utils import (
    subset_high_vol_panel,
)
from research.projects.price_action_strategy_meta.selector_gate_engine import (
    candidate_scan,
    baseline_metrics,
    backtest_policy,
    selection_metrics,
)
from research.projects.price_action_strategy_meta.selector_types import UniverseData
from research.projects.price_action_strategy_meta.screening_report import (
    markdown_table as render_table,
)

REPORT_DIR = Path(__file__).resolve().parent / "reports"
MD_PATH = REPORT_DIR / "selector_gate.md"
BACKTEST_CSV = REPORT_DIR / "selector_gate_backtest.csv"
RULES_CSV = REPORT_DIR / "selector_gate_rules.csv"
HORIZON = 5
TRAIN_FRACTION = 0.7
REGIME_DIMS = (
    "vol_state",
    "trend_state",
    "breadth_state",
    "gap_state",
    "liquidity_state",
    "risk_state",
)
SECTOR_CSV = REPORT_DIR / "regime_sector_summary.csv"
LIQUIDITY_CSV = REPORT_DIR / "regime_liquidity_summary.csv"


def strategy_specs_all() -> list:
    return base_strategy_specs() + extra_strategy_specs()


STRATEGY_FAMILY = {spec.name: spec.family for spec in strategy_specs_all()}


def build_universe_data(universe: str) -> UniverseData:
    panel = subset_high_vol_panel(load_panel(universe))
    frames: dict[str, pd.DataFrame] = {}
    for spec in strategy_specs_all():
        frame = strategy_daily_frame(panel, spec, HORIZON)
        frame.attrs["family"] = spec.family
        frames[spec.name] = frame
    return {
        "regime": regime_frame(panel),
        "frames": frames,
    }


def split_mask(index: pd.Index) -> tuple[pd.Series, pd.Series, pd.Timestamp]:
    cutoff = index[int(len(index) * TRAIN_FRACTION)]
    train = pd.Series(index < cutoff, index=index)
    test = pd.Series(~train.to_numpy(), index=index)
    return train, test, cutoff


def training_summary(
    universe_data: dict[str, UniverseData],
    train_mask: pd.Series,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, object]] = []
    priors: list[dict[str, object]] = []
    for universe, data in universe_data.items():
        regime = data["regime"].loc[train_mask]
        for strategy, frame in data["frames"].items():
            train = frame.loc[train_mask].join(regime, how="left")
            priors.append(
                {
                    "universe": universe,
                    "strategy": strategy,
                    "mean_net_bps": float(train["net_return"].mean() * 10_000.0),
                }
            )
            for dimension in REGIME_DIMS:
                summary = daily_group_summary(train["net_return"], train[dimension])
                if summary.empty:
                    continue
                for row in summary.to_dict(orient="records"):
                    row.update(
                        {
                            "universe": universe,
                            "strategy": strategy,
                            "family": STRATEGY_FAMILY[strategy],
                            "regime_dimension": dimension,
                        }
                    )
                    rows.append(row)
    return pd.DataFrame(rows), pd.DataFrame(priors)


def context_table(path: Path, top_n: int = 5) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame = frame[frame["horizon"].eq(5)] if "horizon" in frame.columns else frame
    return frame.sort_values("mean_net_bps", ascending=False).head(top_n)


def backtest_table(frame: pd.DataFrame) -> pd.DataFrame:
    combined = pd.DataFrame([{"universe": "combined", **selection_metrics(frame)}])
    per_universe = pd.DataFrame(
        [{"universe": universe, **selection_metrics(group)} for universe, group in frame.groupby("universe")]
    )
    return pd.concat([combined, per_universe], ignore_index=True)


def protocol_lines(cutoff: pd.Timestamp) -> list[str]:
    return [
        "## Protocol",
        "",
        f"- Train/test cutoff date: `{cutoff.date().isoformat()}`",
        f"- Horizon: `{HORIZON}d` only; that is where the first-pass screen found the durable positive pocket.",
        f"- Split: first `{int(TRAIN_FRACTION * 100)}%` of dates train, remaining `{int((1 - TRAIN_FRACTION) * 100)}%` test.",
        "- Selector job: choose one strategy or abstain.",
        "- Strategy pool: the base screen plus the supplemental first-principles extras, including trend, reversal, structure, and regime helpers.",
        "- Confidence gate: a strategy must match at least two regime dimensions, clear a score threshold derived from positive train-set regime cells, and be supported by multiple strategies on the same day.",
        "- Costs: 10 bps already embedded in the strategy return series.",
    ]


def candidate_section(candidates: pd.DataFrame) -> list[str]:
    return ["## Candidate Scan", "", render_table(candidates.head(8)), ""]


def policy_section(
    policy,
    train_metrics: dict[str, float],
    test_metrics: dict[str, float],
    rules: pd.DataFrame,
) -> list[str]:
    return [
        "## Chosen Policy",
        "",
        f"- Chosen policy: `{policy.thresholds.name}`",
        f"- Train precision: `{train_metrics['precision']:.3f}`",
        f"- Train coverage: `{train_metrics['coverage']:.3f}`",
        f"- Test precision: `{test_metrics['precision']:.3f}`",
        f"- Test coverage: `{test_metrics['coverage']:.3f}`",
        f"- Test active days: `{int(test_metrics['active_days'])}`",
        f"- Min support: `{policy.thresholds.min_support}` strategies",
        "",
        render_table(rules.head(20)),
        "",
    ]


def backtest_section(selected_frame: pd.DataFrame, baselines: pd.DataFrame) -> list[str]:
    return [
        "## Test Backtest",
        "",
        render_table(
            backtest_table(selected_frame)[
                [
                    "universe",
                    "active_days",
                    "coverage",
                    "precision",
                    "active_mean_net_bps",
                    "portfolio_mean_net_bps",
                    "portfolio_median_net_bps",
                    "portfolio_sharpe_like",
                    "portfolio_max_drawdown_pct",
                ]
            ]
        ),
        "",
        "Comparison against the combined always-on baseline:",
        "",
        render_table(baselines),
        "",
    ]


def context_section() -> list[str]:
    return [
        "## Class Context",
        "",
        render_table(context_table(SECTOR_CSV)),
        "",
        render_table(context_table(LIQUIDITY_CSV)),
        "",
    ]


def takeaway_section() -> list[str]:
    return [
        "## Takeaway",
        "",
        "- The gate is intentionally sparse: it should abstain unless several regime dimensions agree and the train-set edge is strong.",
        "- If the out-of-sample precision does not stay above the always-on baseline, this policy should stay research-only.",
    ]


def gate_report(
    universe_data: dict[str, UniverseData],
    summary: pd.DataFrame,
    priors: pd.DataFrame,
    train_mask: pd.Series,
    test_mask: pd.Series,
    cutoff: pd.Timestamp,
) -> tuple[str, pd.DataFrame, pd.DataFrame]:
    candidates, policy, rules = candidate_scan(
        universe_data, summary, priors, train_mask, test_mask
    )
    selected_frame = backtest_policy(universe_data, policy, test_mask)
    train_frame = backtest_policy(universe_data, policy, train_mask)
    train_metrics = selection_metrics(train_frame)
    test_metrics = selection_metrics(selected_frame)
    baselines = baseline_metrics(universe_data, test_mask)
    rules = rules.sort_values(["universe", "strategy", "dimension", "weight"], ascending=[True, True, True, False])
    lines = [
        "# Selector Gate",
        "",
        *protocol_lines(cutoff),
        "",
        *candidate_section(candidates),
        *policy_section(policy, train_metrics, test_metrics, rules),
        *backtest_section(selected_frame, baselines),
        *context_section(),
        *takeaway_section(),
    ]
    return "\n".join(lines), candidates, rules


def write_outputs(md: str, candidates: pd.DataFrame, rules: pd.DataFrame) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    MD_PATH.write_text(md, encoding="utf-8")
    candidates.to_csv(BACKTEST_CSV, index=False)
    rules.to_csv(RULES_CSV, index=False)


def main() -> int:
    universe_data = {universe: build_universe_data(universe) for universe in ("nifty500", "expanded")}
    reference_index = next(iter(universe_data.values()))["regime"].index
    train_mask, test_mask, cutoff = split_mask(reference_index)
    summary, priors = training_summary(universe_data, train_mask)
    md, candidates, rules = gate_report(
        universe_data, summary, priors, train_mask, test_mask, cutoff
    )
    write_outputs(md, candidates, rules)
    print(f"Wrote {MD_PATH}")
    print(f"Wrote {BACKTEST_CSV}")
    print(f"Wrote {RULES_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
