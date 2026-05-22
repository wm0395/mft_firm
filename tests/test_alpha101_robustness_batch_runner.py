from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any
import sys

import pandas as pd  # type: ignore[import-untyped]


NOTEBOOK_ROOT = Path(__file__).resolve().parents[1] / "research/notebooks/alpha_001"
if str(NOTEBOOK_ROOT) not in sys.path:
    sys.path.insert(0, str(NOTEBOOK_ROOT))

MODULE_PATH = NOTEBOOK_ROOT / "research/alpha101_robustness_batch_runner.py"
SPEC = spec_from_file_location("alpha101_robustness_batch_runner_under_test", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE: Any = module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_batch_ranges_chunks_cleanly() -> None:
    assert MODULE.batch_ranges(9, 4) == [(0, 4), (4, 8), (8, 9)]


def test_batch_slice_ranges_selects_window() -> None:
    assert MODULE.batch_slice_ranges(9, 4, 1, 2) == [(4, 8)]


def test_load_or_write_batch_prefers_cached_files(tmp_path: Path, monkeypatch: Any) -> None:
    batch_dir = tmp_path / "robust_000_004"
    batch_dir.mkdir(parents=True)
    for name in MODULE.BATCH_TABLES:
        pd.DataFrame([{"value": 1}]).to_csv(batch_dir / f"{name}.csv", index=False)

    monkeypatch.setattr(MODULE, "BATCH_ROOT", tmp_path)

    cached = MODULE.load_or_write_batch(pd.DataFrame(), 0, 4, refresh=False, progress=False)

    assert set(cached) == set(MODULE.BATCH_TABLES)
    assert cached["walk_forward"].iloc[0]["value"] == 1


def test_build_final_outputs_uses_classification_helpers(monkeypatch: Any) -> None:
    candidate = pd.DataFrame([{"panel": "p", "alpha_id": "a"}])
    walk_forward = pd.DataFrame([{"panel": "p", "alpha_id": "a"}])
    cost = pd.DataFrame([{"cost_bps": 20.0}])
    universe = pd.DataFrame([{"selected_mask": "strict_liquidity_100m"}])
    proxy = pd.DataFrame([{"panel": "p", "alpha_id": "a", "proxy_dependent": False}])
    industry = pd.DataFrame([{"panel": "p", "alpha_id": "a"}])

    monkeypatch.setattr(
        MODULE,
        "classify_shortlist",
        lambda candidate_frame, walk_frame, proxy_frame: pd.DataFrame(
            [
                {
                    "panel": candidate_frame.iloc[0]["panel"],
                    "alpha_id": candidate_frame.iloc[0]["alpha_id"],
                    "final_status": "promote_to_deeper_research",
                    "input_quality_tier": "exact_ohlcv",
                    "median_test_active_sharpe": 1.0,
                    "median_test_active_cagr": 0.1,
                    "positive_test_sharpe_rate": 1.0,
                    "median_test_rank_ic": 0.2,
                    "median_turnover": 0.05,
                }
            ]
        ),
    )
    monkeypatch.setattr(
        MODULE,
        "strict_liquidity_primary_report",
        lambda walk_frame, shortlist_frame: pd.DataFrame(
            [
                {
                    "panel": "p",
                    "alpha_id": "a",
                    "selected_mask": "strict_liquidity_100m",
                    "median_test_active_sharpe": 1.0,
                }
            ]
        ),
    )
    monkeypatch.setattr(
        MODULE,
        "validation_report",
        lambda *args, **kwargs: pd.DataFrame([{"check": "ok", "passed": True}]),
    )

    outputs = MODULE.build_final_outputs(candidate, walk_forward, cost, universe, proxy, industry)

    assert outputs["shortlist"].iloc[0]["final_status"] == "promote_to_deeper_research"
    assert outputs["strict_liquidity_primary"].iloc[0]["selected_mask"] == "strict_liquidity_100m"
    assert bool(outputs["validation"].iloc[0]["passed"])
