from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any
import sys
import json

import pandas as pd  # type: ignore[import-untyped]


NOTEBOOK_ROOT = Path(__file__).resolve().parents[1] / "research/notebooks/alpha_001"
if str(NOTEBOOK_ROOT) not in sys.path:
    sys.path.insert(0, str(NOTEBOOK_ROOT))

MODULE_PATH = NOTEBOOK_ROOT / "research/alpha101_closed_loop.py"
SPEC = spec_from_file_location("alpha101_closed_loop_under_test", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE: Any = module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_summarize_closed_loop_reads_artifacts(tmp_path: Path) -> None:
    shortlist = pd.DataFrame(
        [
            {
                "panel": "nifty500_high_vol_top100",
                "alpha_id": "alpha040",
                "final_status": "promote_to_deeper_research",
                "input_quality_tier": "exact_ohlcv",
                "median_test_active_sharpe": 1.6,
                "median_test_active_cagr": 0.03,
                "median_test_rank_ic": 0.04,
                "median_turnover": 0.08,
            },
            {
                "panel": "nifty500_high_vol_top100",
                "alpha_id": "alpha051",
                "final_status": "feature_only",
                "input_quality_tier": "exact_ohlcv",
                "median_test_active_sharpe": 0.8,
                "median_test_active_cagr": 0.01,
                "median_test_rank_ic": 0.02,
                "median_turnover": 0.07,
            },
        ]
    )
    strict = pd.DataFrame(
        [
            {
                "panel": "nifty500_high_vol_top100",
                "alpha_id": "alpha040",
                "selected_mask": "strict_liquidity_100m",
                "median_test_active_sharpe": 1.6,
                "median_test_active_cagr": 0.03,
                "median_test_rank_ic": 0.04,
                "median_turnover": 0.08,
            }
        ]
    )
    validation = pd.DataFrame(
        [
            {"check": "one", "passed": True},
            {"check": "two", "passed": False},
        ]
    )
    batch2 = pd.DataFrame(
        [
            {
                "panel": "nifty500_high_vol_top100",
                "alpha_id": "alpha026",
                "median_test_active_sharpe": 1.5,
                "median_test_active_cagr": 0.02,
                "median_test_rank_ic": 0.03,
                "median_turnover": 0.06,
            }
        ]
    )
    shortlist.to_csv(tmp_path / MODULE.SHORTLIST_FILE, index=False)
    strict.to_csv(tmp_path / MODULE.STRICT_LIQUIDITY_FILE, index=False)
    pd.DataFrame([{"alpha_id": "stale", "median_test_active_sharpe": -1.0}]).to_csv(
        tmp_path / MODULE.STRICT_LIQUIDITY_POSITIVE_FOCUS_FILE,
        index=False,
    )
    validation.to_csv(tmp_path / MODULE.VALIDATION_FILE, index=False)
    batch2.to_csv(tmp_path / MODULE.BATCH2_SHORTLIST_FILE, index=False)

    summary = MODULE.summarize_closed_loop(tmp_path)
    md = MODULE.format_closed_loop_markdown(summary)

    assert summary["shortlist_rows"] == 2
    assert summary["promoted_exact_ohlcv_rows"] == 1
    assert summary["strict_liquidity_rows"] == 1
    assert summary["strict_liquidity_median_test_active_sharpe"] == 1.6
    assert summary["strict_liquidity_positive_sharpe_rate"] == 1.0
    assert summary["strict_liquidity_positive_focus_rows"] == 1
    assert summary["strict_liquidity_positive_focus"][0]["alpha_id"] == "alpha040"
    assert summary["validation_pass_rate"] == 0.5
    assert summary["validation_failed_checks"] == ["two"]
    assert summary["top_shortlist"][0]["alpha_id"] == "alpha040"
    assert "Strict Liquidity Positive Focus" in md
    assert "Alpha101 Closed Loop Summary" in md


def test_summarize_closed_loop_falls_back_to_snapshot(tmp_path: Path) -> None:
    snapshot = {
        "reports": {
            "robustness_batch1": {
                "final_status_counts": [{"final_status": "discard", "candidates": "2"}],
                "top_rows": [
                    {
                        "panel": "nifty500_high_vol_top100",
                        "alpha_id": "alpha040",
                        "selected_mask": "strict_liquidity_100m",
                        "final_status": "promote_to_deeper_research",
                        "input_quality_tier": "exact_ohlcv",
                        "median_test_active_sharpe": "1.6",
                    }
                ],
            },
            "robustness_batch2": {
                "results": [
                    {
                        "panel": "nifty500_high_vol_top100",
                        "alpha_id": "alpha026",
                        "median_test_active_sharpe": "1.5",
                    }
                ]
            },
        }
    }
    (tmp_path / MODULE.SNAPSHOT_FILE).write_text(json.dumps(snapshot))

    summary = MODULE.summarize_closed_loop(tmp_path)

    assert summary["shortlist_rows"] == 2
    assert summary["shortlist_rows_source"] == "snapshot_status_counts"
    assert summary["strict_liquidity_rows"] == 1
    assert summary["strict_liquidity_positive_focus_rows"] == 1
    assert summary["strict_liquidity_positive_focus"][0]["alpha_id"] == "alpha040"
    assert summary["validation_pass_rate"] is None
    assert summary["validation_status"] == "missing"
    assert summary["promoted_exact_ohlcv_rows"] == 1
    assert summary["shortlist_final_status_counts"] == {"discard": "2"}
    assert summary["top_batch2_shortlist"][0]["alpha_id"] == "alpha026"
