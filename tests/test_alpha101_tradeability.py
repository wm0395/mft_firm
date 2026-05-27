from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any
import json
import sys

import pandas as pd  # type: ignore[import-untyped]


NOTEBOOK_ROOT = Path(__file__).resolve().parents[1] / "research/notebooks/alpha_001"
MODULE_PATH = NOTEBOOK_ROOT / "research/alpha101_tradeability.py"
if str(NOTEBOOK_ROOT) not in sys.path:
    sys.path.insert(0, str(NOTEBOOK_ROOT))
SPEC = spec_from_file_location("alpha101_tradeability_under_test", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE: Any = module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_build_tradeability_frame_classifies_strict_gate(tmp_path: Path) -> None:
    write_tradeability_inputs(tmp_path)

    frame = MODULE.build_tradeability_frame(tmp_path)

    statuses = frame.set_index("alpha_id")["tradeability_status"].to_dict()
    assert statuses["alpha024"] == "strict_liquidity_tradeable_candidate"
    assert statuses["alpha018"] == "strict_liquidity_not_tradeable_yet"
    assert statuses["alpha026"] == "high_vol_research_only_candidate"
    assert statuses["alpha003"] == "promoted_exact_missing_metrics_audit"
    assert frame.iloc[0]["alpha_id"] == "alpha024"
    assert frame["cache_status"].unique().tolist() == ["incomplete_factory_cache"]
    assert frame["promoted_universe_status"].value_counts().to_dict() == {
        "metrics_audit_covered": 3,
        "missing_metrics_audit": 1,
    }


def test_write_tradeability_metrics_outputs_csv_and_markdown(tmp_path: Path) -> None:
    write_tradeability_inputs(tmp_path)

    csv_path, md_path = MODULE.write_tradeability_metrics(tmp_path)
    csv = pd.read_csv(csv_path)
    markdown = md_path.read_text()

    assert csv_path.name == MODULE.TRADEABILITY_CSV
    assert md_path.name == MODULE.TRADEABILITY_MD
    assert csv["alpha_id"].tolist() == ["alpha024", "alpha026", "alpha018", "alpha003"]
    assert "Alpha101 Tradeable Strategy Metrics" in markdown
    assert "strict_liquidity_tradeable_candidate" in markdown
    assert "Research-Only High-Vol Candidates" in markdown
    assert "Promoted Exact-OHLCV Names Missing Metrics-Audit Evidence" in markdown
    assert "Promoted exact-OHLCV coverage: 3/4 names have metrics-audit rows" in markdown
    assert "strict_selected_signal_transform" in markdown
    assert "benchmark_sortino" in markdown
    assert "Factory task cache: 1/3 complete; 2 missing." in markdown


def write_tradeability_inputs(path: Path) -> None:
    audit_dir = path / "alpha101_metrics_audit"
    audit_dir.mkdir(parents=True)
    audit_rows().to_csv(path / MODULE.AUDIT_FILE, index=False)
    strict_rows().to_csv(path / MODULE.STRICT_FILE, index=False)
    write_research_state(path)
    (path / MODULE.PROGRESS_FILE).write_text(
        json.dumps({"completed_tasks": 1, "missing_tasks": 2, "total_tasks": 3})
    )


def audit_rows() -> pd.DataFrame:
    return pd.DataFrame(
        [
            audit_row("alpha024", 1.4, 0.47),
            audit_row("alpha018", 1.3, 0.46),
            audit_row("alpha026", 1.5, 0.44),
        ]
    )


def audit_row(alpha_id: str, test_sharpe: float, active_sharpe: float) -> dict[str, object]:
    row = {column: 0.0 for column in MODULE.OUTPUT_COLUMNS if column != "cache_status"}
    row.update(
        {
            "alpha_id": alpha_id,
            "panel": "expanded",
            "family": "price_reversal",
            "batch": "batch1",
            "robustness_lane": "clean_exact_ohlcv",
            "best_mask": "high_vol_top100",
            "best_signal_transform": "winsor_zscore",
            "best_strategy": "overlay20",
            "median_test_active_sharpe": test_sharpe,
            "active_sharpe": active_sharpe,
            "benchmark_sortino": 0.2,
            "benchmark_max_drawdown": -0.3,
            "benchmark_hit_rate": 0.4,
            "strategy_observations": 5,
            "benchmark_observations": 5,
        }
    )
    for column in [name for name in row if name.startswith("strict_")]:
        row.pop(column)
    row.pop("tradeability_status")
    return row


def write_research_state(path: Path) -> None:
    state_path = path.parents[1] / MODULE.RESEARCH_STATE_FILE
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps({"promotion_rows": promotion_rows()}))


def promotion_rows() -> list[dict[str, object]]:
    return [
        promotion_row("alpha024", 1.4),
        promotion_row("alpha018", 1.3),
        promotion_row("alpha026", 1.5),
        promotion_row("alpha003", 0.9),
    ]


def promotion_row(alpha_id: str, sharpe: float) -> dict[str, object]:
    return {
        "alpha_id": alpha_id,
        "batch": 2,
        "promotion_status": "near_miss",
        "median_test_active_sharpe": sharpe,
        "median_test_active_cagr": 0.01,
        "median_test_rank_ic": 0.02,
        "best_mask": "high_vol_top100",
        "best_signal_transform": "rank_centered",
        "best_strategy": "overlay20",
    }


def strict_rows() -> pd.DataFrame:
    return pd.DataFrame(
        [
            strict_row("alpha024", 0.8, 1.0),
            strict_row("alpha018", -0.1, 0.5),
        ]
    )


def strict_row(alpha_id: str, sharpe: float, rate: float) -> dict[str, object]:
    return {
        "alpha_id": alpha_id,
        "median_test_active_sharpe": sharpe,
        "median_test_active_cagr": 0.01,
        "positive_test_sharpe_rate": rate,
        "median_test_rank_ic": 0.02,
        "median_turnover": 0.03,
        "worst_test_drawdown": -0.04,
        "selected_mask": "strict_liquidity_100m",
        "selected_signal_transform": "winsor_zscore",
        "selected_strategy": "overlay20",
    }
