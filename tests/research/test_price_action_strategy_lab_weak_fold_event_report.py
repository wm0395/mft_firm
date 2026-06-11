from __future__ import annotations

import pandas as pd

from research.projects.price_action_strategy_lab.weak_fold_event_report import weak_fold_events


def test_weak_fold_events_tags_known_event_and_gate() -> None:
    result = weak_fold_events(_folds(), _gates())
    row = result.loc[result["alpha"].eq("alpha_a")].iloc[0]

    assert row["event_label"] == "early_2025_broad_correction_fpi_outflows"
    assert row["selected_indicator"] == "gap_fade"
    assert row["selected_side"] == "low"


def test_weak_fold_events_marks_unmatched_windows() -> None:
    result = weak_fold_events(_folds(), _gates())
    row = result.loc[result["alpha"].eq("alpha_b")].iloc[0]

    assert row["event_label"] == "unmatched"


def _folds() -> pd.DataFrame:
    return pd.DataFrame(
        [
            _fold(1, "alpha_a", "2025-02-01", "2025-02-28", -7.0),
            _fold(2, "alpha_b", "2025-05-01", "2025-05-31", -7.0),
            _fold(3, "alpha_c", "2025-08-01", "2025-08-31", 2.0),
            _fold(4, "alpha_d", "2025-09-01", "2025-09-30", 3.0),
            _fold(5, "alpha_e", "2025-10-01", "2025-10-31", 4.0),
        ]
    )


def _fold(fold: int, alpha: str, start: str, end: str, ret: float) -> dict[str, object]:
    return {
        "fold": fold,
        "variant": "baseline",
        "alpha": alpha,
        "test_start": start,
        "test_end": end,
        "return_pct": ret,
        "max_drawdown_pct": ret,
    }


def _gates() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "fold": 1,
                "alpha": "alpha_a",
                "indicator": "gap_fade",
                "side": "low",
                "score": 2.0,
            }
        ]
    )
