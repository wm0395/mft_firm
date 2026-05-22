from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
from typing import Any
import sys

import pandas as pd  # type: ignore[import-untyped]


MODULE_PATH = Path(__file__).resolve().parents[1] / "research/notebooks/alpha_001/research/alpha101_robustness.py"
NOTEBOOK_ROOT = Path(__file__).resolve().parents[1] / "research/notebooks/alpha_001"
if str(NOTEBOOK_ROOT) not in sys.path:
    sys.path.insert(0, str(NOTEBOOK_ROOT))
SPEC = spec_from_file_location("alpha101_robustness_under_test", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE: Any = module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_strict_liquidity_primary_report_filters_selected_mask() -> None:
    walk_forward = pd.DataFrame(
        [
            {
                "panel": "nifty500_high_vol_top100",
                "alpha_id": "alpha040",
                "robustness_lane": "clean_exact_ohlcv",
                "input_quality_tier": "exact_ohlcv",
                "fold": "oos_2024",
                "selected_mask": "strict_liquidity_100m",
                "selected_signal_transform": "winsor_zscore",
                "selected_strategy": "overlay20",
                "test_active_sharpe": 1.5,
                "test_active_cagr": 0.03,
                "test_mean_rank_ic": 0.04,
                "alpha_avg_daily_turnover": 0.08,
                "test_active_max_drawdown": -0.12,
            },
            {
                "panel": "nifty500_high_vol_top100",
                "alpha_id": "alpha012",
                "robustness_lane": "clean_exact_ohlcv",
                "input_quality_tier": "exact_ohlcv",
                "fold": "oos_2024",
                "selected_mask": "high_vol_top100",
                "selected_signal_transform": "ewm3",
                "selected_strategy": "ewm3_overlay20",
                "test_active_sharpe": 1.2,
                "test_active_cagr": 0.02,
                "test_mean_rank_ic": 0.03,
                "alpha_avg_daily_turnover": 0.09,
                "test_active_max_drawdown": -0.15,
            },
        ]
    )

    report = MODULE.strict_liquidity_primary_report(walk_forward)

    assert report["alpha_id"].tolist() == ["alpha040"]
    assert report["selected_mask"].tolist() == ["strict_liquidity_100m"]
    assert report["median_test_active_sharpe"].iat[0] == 1.5


def test_validation_report_marks_strict_liquidity_primary_reported() -> None:
    candidate_frame = pd.DataFrame(
        [
            {"alpha_id": "alpha001", "robustness_lane": "baseline_alpha001", "input_quality_tier": "exact_ohlcv"},
            {"alpha_id": "alpha040", "robustness_lane": "clean_exact_ohlcv", "input_quality_tier": "exact_ohlcv"},
        ]
    )
    walk_forward = pd.DataFrame(
        [
            {"selection_scope": "train_selected_only", "selected_mask": "strict_liquidity_100m"},
        ]
    )
    shortlist = pd.DataFrame([{"final_status": "promote_to_deeper_research"}])
    strict_report = pd.DataFrame([{"selected_mask": "strict_liquidity_100m"}])

    validation = MODULE.validation_report(candidate_frame, walk_forward, shortlist, strict_report)

    row = validation.set_index("check").loc["strict_liquidity_primary_reported"]
    assert bool(row["passed"])


def test_strict_liquidity_primary_report_uses_fixed_mask_rescore_for_shortlist() -> None:
    shortlist = pd.DataFrame(
        [
            {
                "panel": "expanded",
                "alpha_id": "alpha040",
                "robustness_lane": "clean_exact_ohlcv",
                "input_quality_tier": "exact_ohlcv",
                "final_status": "promote_to_deeper_research",
                "best_signal_transform": "winsor_zscore",
                "best_strategy": "overlay20",
            },
            {
                "panel": "expanded",
                "alpha_id": "alpha002",
                "robustness_lane": "clean_near_miss_batch2",
                "input_quality_tier": "exact_ohlcv",
                "final_status": "feature_only",
                "best_signal_transform": "rank_centered",
                "best_strategy": "overlay20",
            },
        ]
    )
    calls: list[tuple[str, str, str, str]] = []
    original = MODULE.fixed_mask_rescore

    def fake_fixed_mask_rescore(
        panel_name: str,
        alpha_id: str,
        lane: str,
        input_quality_tier: str,
        signal_transform: str,
        strategy: str,
        fold: tuple[str, str, str, str, str],
        cost_bps: float,
        mask_name: str = "strict_liquidity_100m",
        panel: str | None = None,
        raw: str | None = None,
        **_: object,
    ) -> dict[str, object]:
        calls.append((alpha_id, signal_transform, strategy, fold[0]))
        return {
            "panel": panel_name,
            "alpha_id": alpha_id,
            "robustness_lane": lane,
            "input_quality_tier": input_quality_tier,
            "fold": fold[0],
            "train_start": fold[1],
            "train_end": fold[2],
            "test_start": fold[3],
            "test_end": fold[4],
            "selection_scope": "strict_liquidity_mask_fixed",
            "selected_mask": mask_name,
            "selected_signal_transform": signal_transform,
            "selected_strategy": strategy,
            "cost_bps": cost_bps,
            "train_active_cagr": 0.1,
            "train_active_sharpe": 1.0,
            "train_active_max_drawdown": -0.1,
            "test_active_cagr": 0.2,
            "test_active_sharpe": 2.0,
            "test_active_sortino": 3.0,
            "test_active_max_drawdown": -0.2,
            "test_active_hit_rate": 1.0,
            "test_observations": 42,
            "train_mean_rank_ic": 0.01,
            "test_mean_rank_ic": 0.02,
            "test_rank_icir": 1.0,
            "test_positive_ic_rate": 1.0,
            "alpha_avg_daily_turnover": 0.07,
            "alpha_full_cagr": 0.3,
            "benchmark_full_cagr": 0.1,
        }

    MODULE.fixed_mask_rescore = fake_fixed_mask_rescore
    try:
        report = MODULE.strict_liquidity_primary_report(pd.DataFrame(), shortlist)
    finally:
        MODULE.fixed_mask_rescore = original

    assert report["alpha_id"].tolist() == ["alpha040"]
    assert report["selected_mask"].tolist() == ["strict_liquidity_100m"]
    assert calls == [
        ("alpha040", "winsor_zscore", "overlay20", fold[0]) for fold in MODULE.ROBUSTNESS_FOLDS
    ]


def test_snapshot_fallback_recovers_candidate_and_batch2_lanes(tmp_path: Path) -> None:
    snapshot = {
        "reports": {
            "factory": {
                "top_25": [
                    {
                        "panel": "expanded",
                        "alpha_id": "alpha040",
                        "family": "volume_liquidity",
                        "input_quality_tier": "exact_ohlcv",
                        "classification": "candidate",
                        "research_score": 1.91,
                        "best_5d_ic": 0.04,
                        "best_20bps_active_sharpe": 1.58,
                        "best_mask": "high_vol_top100",
                        "best_signal_transform": "winsor_zscore",
                        "best_strategy": "overlay20",
                    }
                ]
            },
            "robustness_batch1": {
                "top_rows": [
                    {
                        "panel": "expanded",
                        "alpha_id": "alpha001",
                        "robustness_lane": "baseline_alpha001",
                        "input_quality_tier": "exact_ohlcv",
                        "final_status": "baseline_comparator",
                        "median_test_active_sharpe": "0.6936531205501564",
                        "median_test_active_cagr": "0.011994270700546927",
                        "median_test_rank_ic": "0.02255003200152462",
                        "median_turnover": "0.0670979629419882",
                        "positive_test_sharpe_rate": "1.0",
                    }
                ]
            },
            "robustness_batch2": {
                "combined_promoted_exact_ohlcv": [
                    {
                        "alpha_id": "alpha026",
                        "batch": "batch2",
                        "panel": "expanded",
                        "robustness_lane": "clean_near_miss_batch2",
                        "final_status": "promote_to_deeper_research",
                        "median_test_active_sharpe": "1.5056593269482264",
                        "median_test_active_cagr": "0.0266942662450238",
                        "median_test_rank_ic": "0.030147566165233584",
                        "median_turnover": "0.06753089428264267",
                        "positive_test_sharpe_rate": "1.0",
                    }
                ],
                "results": [
                    {
                        "alpha_id": "alpha008",
                        "panel": "expanded",
                        "robustness_lane": "clean_near_miss_batch2",
                        "final_status": "feature_only",
                        "median_test_active_sharpe": "0.37692261363315127",
                        "median_test_active_cagr": "0.006369399206878179",
                        "median_test_rank_ic": "0.01961470784682228",
                        "median_turnover": "0.06868266007973482",
                        "positive_test_sharpe_rate": "1.0",
                    }
                ],
            },
        }
    }
    (tmp_path / MODULE.SNAPSHOT_FILE).write_text(json.dumps(snapshot))
    original_dir = MODULE.ROBUSTNESS_DIR
    MODULE.ROBUSTNESS_DIR = tmp_path
    try:
        leaderboard, registry = MODULE.load_discovery_tables()
        assert not leaderboard.empty
        assert "alpha040" in leaderboard["alpha_id"].tolist()
        assert not registry.empty

        lanes = MODULE.candidate_lanes(clean_n=1, proxy_n=0, snapshot_n=0)
        assert "alpha040" in lanes["alpha_id"].tolist()
        assert "alpha001" in lanes["alpha_id"].tolist()

        batch2 = MODULE.clean_near_miss_lanes(alpha_ids=("alpha008",))
        row = batch2.iloc[0]
        assert row["alpha_id"] == "alpha008"
        assert row["input_quality_tier"] == "exact_ohlcv"
        assert row["best_signal_transform"]
        assert row["best_strategy"]
    finally:
        MODULE.ROBUSTNESS_DIR = original_dir
