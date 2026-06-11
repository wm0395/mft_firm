from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from research.notebooks.alpha_001.research.alpha101_engine import forward_return, load_panel
from research.projects.price_action_strategy_meta.regime_analysis_report import (
    base_strategy_specs,
    strategy_daily_frame,
)
from research.projects.price_action_strategy_meta.regime_analysis_strategies import (
    extra_strategy_specs,
)
from research.projects.price_action_strategy_meta.regime_panel_utils import subset_high_vol_panel
from research.projects.price_action_strategy_meta.screening_report import markdown_table as render_table
from research.projects.price_action_strategy_meta.selector_gate_engine import selection_metrics

REPORT_DIR = Path(__file__).resolve().parent / "reports"
MD_PATH = REPORT_DIR / "selector_neutral_variant.md"
SUMMARY_CSV = REPORT_DIR / "selector_neutral_variant_summary.csv"
DETAIL_CSV = REPORT_DIR / "selector_neutral_variant_details.csv"
HORIZON = 5


@dataclass(frozen=True)
class NeutralMode:
    mode: str
    label: str


@dataclass(frozen=True)
class SelectionSource:
    name: str
    path: Path


def neutral_modes() -> list[NeutralMode]:
    return [
        NeutralMode("market_neutral", "market-neutral"),
        NeutralMode("sector_neutral", "sector-neutral"),
    ]


def selection_sources() -> list[SelectionSource]:
    return [
        SelectionSource("gate_holdout", REPORT_DIR / "selector_gate_selected.csv"),
        SelectionSource("walk_forward", REPORT_DIR / "selector_walk_forward_selected.csv"),
    ]


def strategy_specs_all() -> list:
    return base_strategy_specs() + extra_strategy_specs()


def adjusted_future_returns(panel, mode: str) -> pd.DataFrame:
    future = forward_return(panel.close, HORIZON)
    if mode == "market_neutral":
        return future.sub(future.mean(axis=1), axis=0)
    industries = panel.industry.astype(str)
    adjusted = future.copy()
    for industry in sorted(industries.unique()):
        columns = industries.index[industries.eq(industry)].tolist()
        if not columns:
            continue
        sector_mean = future[columns].mean(axis=1).to_numpy()[:, None]
        adjusted.loc[:, columns] = future[columns].to_numpy() - sector_mean
    return adjusted


def strategy_frames(panel, strategy_names: list[str], mode: str) -> dict[str, pd.DataFrame]:
    future = adjusted_future_returns(panel, mode)
    base_mask = panel.high_vol_mask & panel.active_mask
    frames: dict[str, pd.DataFrame] = {}
    wanted = set(strategy_names)
    for spec in strategy_specs_all():
        if spec.name not in wanted:
            continue
        frame = strategy_daily_frame(
            panel,
            spec,
            HORIZON,
            compute_rank_ic=False,
            future=future,
            base_mask=base_mask,
        )
        frame.attrs["family"] = spec.family
        frames[spec.name] = frame
    return frames


def apply_neutral_returns(selection: pd.DataFrame, frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    out = selection.copy()
    out["raw_net_return"] = out["net_return"]
    out["neutral_net_return"] = out["net_return"]
    active = out[out["active"]]
    for strategy, group in active.groupby("strategy", sort=False):
        dates = pd.to_datetime(group["date"])
        series = frames[strategy]["net_return"].reindex(dates)
        out.loc[group.index, "neutral_net_return"] = series.to_numpy()
    out["net_return"] = out["neutral_net_return"]
    return out


def selection_summary(selection: pd.DataFrame, neutral: pd.DataFrame) -> dict[str, object]:
    raw_metrics = selection_metrics(selection)
    neutral_metrics = selection_metrics(neutral)
    active = selection[selection["active"]]
    rows: dict[str, object] = {
        "active_strategies": int(active["strategy"].nunique()),
        "active_folds": int(active["fold"].nunique()) if "fold" in selection.columns else 1,
    }
    rows.update(
        {
            "raw_active_mean_net_bps": raw_metrics["active_mean_net_bps"],
            "neutral_active_mean_net_bps": neutral_metrics["active_mean_net_bps"],
            "raw_portfolio_mean_net_bps": raw_metrics["portfolio_mean_net_bps"],
            "neutral_portfolio_mean_net_bps": neutral_metrics["portfolio_mean_net_bps"],
            "raw_precision": raw_metrics["precision"],
            "neutral_precision": neutral_metrics["precision"],
            "coverage": raw_metrics["coverage"],
            "active_days": raw_metrics["active_days"],
            "delta_active_net_bps": neutral_metrics["active_mean_net_bps"] - raw_metrics["active_mean_net_bps"],
            "delta_portfolio_net_bps": neutral_metrics["portfolio_mean_net_bps"] - raw_metrics["portfolio_mean_net_bps"],
        }
    )
    return rows


def build_summary() -> tuple[pd.DataFrame, pd.DataFrame]:
    summary_rows: list[dict[str, object]] = []
    detail_frames: list[pd.DataFrame] = []
    panel = subset_high_vol_panel(load_panel("nifty500"))
    for source in selection_sources():
        selection = pd.read_csv(source.path)
        strategy_names = sorted(selection.loc[selection["active"], "strategy"].dropna().unique().tolist())
        for mode in neutral_modes():
            frames = strategy_frames(panel, strategy_names, mode.mode)
            neutral = apply_neutral_returns(selection, frames)
            row: dict[str, object] = {
                "source": source.name,
                "mode": mode.mode,
                "label": mode.label,
            }
            row.update(selection_summary(selection, neutral))
            summary_rows.append(row)
            columns = ["date", "strategy", "raw_net_return", "neutral_net_return"]
            if "split_type" in neutral.columns:
                columns.append("split_type")
            detail = neutral.loc[neutral["active"], columns].copy()
            detail["source"] = source.name
            detail["mode"] = mode.mode
            if "split_type" not in detail.columns:
                detail["split_type"] = "holdout"
            detail_frames.append(detail)
    return pd.DataFrame(summary_rows), pd.concat(detail_frames, ignore_index=True)


def build_report(summary: pd.DataFrame) -> str:
    lines = [
        "# Selector Neutral Variant",
        "",
        "## Protocol",
        "",
        "- This is a selected-portfolio sensitivity, not a full neutral refit.",
        "- I keep the current gate schedule fixed and recompute only the strategies that were actually selected.",
        "- Market neutrality subtracts the same-day universe mean from 5-day forward returns.",
        "- Sector neutrality subtracts the same-day industry mean from 5-day forward returns.",
        "",
        "## Summary",
        "",
        render_table(summary.sort_values(["source", "mode"]).reset_index(drop=True)),
        "",
        "## Interpretation",
        "",
        "- If neutrality were the missing explanation, the selected portfolio would improve materially relative to the raw schedule.",
        "- The holdout gate is flat to slightly worse under neutrality, and the walk-forward active pocket is still too sparse to rescue the selector.",
        "",
        "## Decision",
        "",
        "- `NEEDS_MORE_DATA`",
        "- This is a useful sensitivity check, but it is not a full neutral refit and it does not change the rejection state of the selector.",
    ]
    return "\n".join(lines)


def write_outputs(summary: pd.DataFrame, detail: pd.DataFrame) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    MD_PATH.write_text(build_report(summary), encoding="utf-8")
    SUMMARY_CSV.write_text(summary.to_csv(index=False), encoding="utf-8")
    DETAIL_CSV.write_text(detail.to_csv(index=False), encoding="utf-8")


def main() -> int:
    summary, detail = build_summary()
    write_outputs(summary, detail)
    print(f"Wrote {MD_PATH}")
    print(f"Wrote {SUMMARY_CSV}")
    print(f"Wrote {DETAIL_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
