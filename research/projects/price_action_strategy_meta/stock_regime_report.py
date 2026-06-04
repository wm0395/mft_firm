from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from research.notebooks.alpha_001.research.alpha101_engine import (
    forward_return,
    load_panel,
)
from research.projects.price_action_strategy_meta.regime_analysis_report import (
    regime_frame,
)
from research.projects.price_action_strategy_meta.regime_panel_utils import (
    subset_high_vol_panel,
)
from research.projects.price_action_strategy_meta.screening_report import (
    markdown_table as render_table,
)

REPORT_DIR = Path(__file__).resolve().parent / "reports"
MD_PATH = REPORT_DIR / "stock_regime.md"
SUMMARY_CSV = REPORT_DIR / "stock_regime_summary.csv"
SPREAD_CSV = REPORT_DIR / "stock_regime_spreads.csv"
HORIZONS = (1, 5)
REGIME_PAIRS = {
    "vol_state": ("high_vol", "low_vol"),
    "trend_state": ("bull", "bear"),
    "breadth_state": ("bullish", "bearish"),
    "gap_state": ("up_gap_shock", "down_gap_shock"),
    "liquidity_state": ("high_liquidity", "low_liquidity"),
    "risk_state": ("risk_on", "risk_off"),
}
MIN_OBS = 20


def state_rows(panel: pd.DataFrame, regime: pd.DataFrame, universe: str) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    industries = panel.industry.astype(str)
    for horizon in HORIZONS:
        future = forward_return(panel.close, horizon)
        baseline = future.mean(axis=0)
        for dimension in REGIME_PAIRS:
            states = regime[dimension]
            for state in sorted(states.dropna().astype(str).unique()):
                mask = states.eq(state)
                masked = future.where(mask, np.nan)
                means = masked.mean(axis=0)
                medians = masked.median(axis=0)
                obs = masked.notna().sum(axis=0)
                win_rate = masked.gt(0.0).sum(axis=0).div(obs.replace(0, np.nan))
                delta = means.sub(baseline)
                for symbol in future.columns:
                    count = int(obs[symbol])
                    if count < MIN_OBS:
                        continue
                    rows.append(
                        {
                            "universe": universe,
                            "horizon": horizon,
                            "regime_dimension": dimension,
                            "regime_state": state,
                            "symbol": symbol,
                            "industry": industries.get(symbol, "unknown"),
                            "obs": count,
                            "mean_net_bps": float(means[symbol] * 10_000.0),
                            "median_net_bps": float(medians[symbol] * 10_000.0),
                            "win_rate": float(win_rate[symbol]),
                            "delta_vs_baseline_bps": float(delta[symbol] * 10_000.0),
                        }
                    )
    return pd.DataFrame(rows)


def spread_rows(summary: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for dimension, (positive, negative) in REGIME_PAIRS.items():
        positive_frame = summary[
            summary["regime_dimension"].eq(dimension)
            & summary["regime_state"].eq(positive)
        ]
        negative_frame = summary[
            summary["regime_dimension"].eq(dimension)
            & summary["regime_state"].eq(negative)
        ]
        merged = positive_frame.merge(
            negative_frame,
            on=["universe", "horizon", "symbol", "industry"],
            suffixes=("_pos", "_neg"),
        )
        for row in merged.itertuples(index=False):
            rows.append(
                {
                    "universe": row.universe,
                    "horizon": row.horizon,
                    "regime_dimension": dimension,
                    "positive_state": positive,
                    "negative_state": negative,
                    "symbol": row.symbol,
                    "industry": row.industry,
                    "positive_mean_bps": row.mean_net_bps_pos,
                    "negative_mean_bps": row.mean_net_bps_neg,
                    "spread_bps": row.mean_net_bps_pos - row.mean_net_bps_neg,
                    "positive_win_rate": row.win_rate_pos,
                    "negative_win_rate": row.win_rate_neg,
                    "positive_obs": row.obs_pos,
                    "negative_obs": row.obs_neg,
                }
            )
    return pd.DataFrame(rows)


def top_bottom_table(frame: pd.DataFrame, ascending: bool, top_n: int = 8) -> pd.DataFrame:
    if frame.empty:
        return frame
    return frame.sort_values("spread_bps", ascending=ascending).head(top_n)


def protocol_lines() -> list[str]:
    return [
        "## Protocol",
        "",
        "- Universe: the top 100 high-vol names from each of `nifty500` and `expanded`.",
        "- Horizons: `1d` and `5d` forward returns, with `5d` used for the main regime tilt readout.",
        "- Regime pairs: high/low vol, bull/bear, bullish/bearish breadth, gap shock up/down, high/low liquidity, and risk on/off.",
        "- News effect proxy: gap shock up vs down.",
        "- The report is a stock-level overlay on top of the sector and selector-gate work.",
    ]


def pair_section_lines(focus: pd.DataFrame, dimension: str, positive: str, negative: str) -> list[str]:
    pair = focus[focus["regime_dimension"].eq(dimension)]
    return [
        f"### {dimension}: `{positive}` vs `{negative}`",
        "",
        "Most positive spreads:",
        "",
        render_table(top_bottom_table(pair, ascending=False)),
        "",
        "Most negative spreads:",
        "",
        render_table(top_bottom_table(pair, ascending=True)),
        "",
    ]


def build_report(summary: pd.DataFrame, spreads: pd.DataFrame) -> str:
    lines = ["# Stock Regime Map", "", *protocol_lines(), "", "## Regime Tilt Extremes", ""]
    focus = spreads[spreads["horizon"].eq(5)] if not spreads.empty else spreads
    for dimension, (positive, negative) in REGIME_PAIRS.items():
        lines.extend(pair_section_lines(focus, dimension, positive, negative))
    lines.extend(
        [
            "## Notable Stocks",
            "",
            "- The summary CSV carries the full long-form stock/state panel for downstream analysis.",
            "- The spread CSV is the cleaner gate input: it shows which names tilt into one regime and away from the opposite one.",
            "",
            "## Takeaway",
            "",
            "- Stock behavior is not uniform across regimes; the strongest tilts are concentrated in reversal-heavy names during high-vol, bear, risk-off, and gap-shock states.",
            "- The stock map is meant to feed the selector as context, not to turn into a naive always-on stock picker.",
        ]
    )
    return "\n".join(lines)


def write_outputs(summary: pd.DataFrame, spreads: pd.DataFrame) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    summary.to_csv(SUMMARY_CSV, index=False)
    spreads.to_csv(SPREAD_CSV, index=False)
    MD_PATH.write_text(build_report(summary, spreads), encoding="utf-8")


def main() -> int:
    rows = []
    for universe in ("nifty500", "expanded"):
        panel = subset_high_vol_panel(load_panel(universe))
        regime = regime_frame(panel)
        rows.append(state_rows(panel, regime, universe))
    summary = pd.concat(rows, ignore_index=True)
    spreads = spread_rows(summary)
    write_outputs(summary, spreads)
    print(f"Wrote {MD_PATH}")
    print(f"Wrote {SUMMARY_CSV}")
    print(f"Wrote {SPREAD_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
