from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from research.notebooks.alpha_001.research.alpha101_engine import load_panel
from research.projects.price_action_strategy_meta.regime_analysis_strategies import (
    extra_strategy_specs,
)
from research.projects.price_action_strategy_meta.regime_panel_utils import (
    subset_high_vol_panel,
)
from research.projects.price_action_strategy_meta.screening_report import (
    evaluate_strategy,
    family_summary,
    markdown_table as render_table,
    panel_leaderboard,
    stable_strategies,
)

REPORT_DIR = Path(__file__).resolve().parent / "reports"
CSV_PATH = REPORT_DIR / "extra_strategy_screening.csv"
MD_PATH = REPORT_DIR / "extra_strategy_screening.md"
HORIZONS = (1, 5)
UNIVERSES = ("nifty500", "expanded")
DISPLAY_UNIVERSES = ("nifty500_high_vol_top100", "expanded_high_vol_top100")


def build_results() -> pd.DataFrame:
    rows: list[dict[str, float | int | str]] = []
    for universe in UNIVERSES:
        panel = subset_high_vol_panel(load_panel(universe))
        for horizon in HORIZONS:
            for spec in extra_strategy_specs():
                print(f"screening {universe} horizon={horizon} strategy={spec.name}", flush=True)
                rows.append(evaluate_strategy(panel, spec, horizon))
    return pd.DataFrame(rows)


def build_report(results: pd.DataFrame) -> str:
    lines = [
        "# Extra Strategy Screening",
        "",
        "## Protocol",
        "",
        "- This supplemental pass screens the extra first-principles strategies only.",
        "- Each universe is reduced to its top 100 high-vol names so the extra screen matches the base screen and the regime scan.",
        "- The extra pool now includes trend, reversal, structure, and regime helpers such as supertrend, parabolic SAR, Aroon, Ichimoku, KST, inverse Fisher RSI, mass index, trendlines, volume profile, and choppiness.",
        "- Universe and horizon settings match the base screen so the comparison is apples-to-apples.",
        "- The goal is to isolate whether the expanded extras add any durable edge before they are treated as gate inputs.",
        "",
        "## Family Summary",
        "",
        render_table(family_summary(results).round(4)),
        "",
        "## Stable Winners",
        "",
        render_table(stable_strategies(results, positive=True).round(4)),
        "",
        "## Stable Losers",
        "",
        render_table(stable_strategies(results, positive=False).round(4)),
        "",
    ]
    for universe in DISPLAY_UNIVERSES:
        for horizon in HORIZONS:
            lines.extend(
                [
                    f"## {universe} / {horizon}d",
                    "",
                    "Top 5 by `net_mean_bps_10`:",
                    "",
                    render_table(panel_leaderboard(results, universe, horizon).round(4)),
                    "",
                    "Bottom 5 by `net_mean_bps_10`:",
                    "",
                    render_table(panel_leaderboard(results, universe, horizon, ascending=True).round(4)),
                    "",
                ]
            )
    return "\n".join(lines)


def write_outputs(results: pd.DataFrame) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    results.sort_values(["universe", "horizon", "family", "strategy"]).to_csv(CSV_PATH, index=False)
    MD_PATH.write_text(build_report(results), encoding="utf-8")


def main() -> int:
    results = build_results()
    write_outputs(results)
    print(f"Wrote {MD_PATH}")
    print(f"Wrote {CSV_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
