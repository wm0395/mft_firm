from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
import sys

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import pytest


NOTEBOOK_ROOT = Path(__file__).resolve().parents[1] / "research/notebooks/alpha_001"
MODULE_PATH = NOTEBOOK_ROOT / "research/alpha101_metrics_audit.py"
if str(NOTEBOOK_ROOT) not in sys.path:
    sys.path.insert(0, str(NOTEBOOK_ROOT))
SPEC = spec_from_file_location("alpha101_metrics_audit_under_test", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE: Any = module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_load_benchmark_returns_reads_cached_csv(tmp_path: Path) -> None:
    frame = pd.DataFrame(
        {
            "timestamp": [
                "2024-01-01T00:00:00+00:00",
                "2024-01-02T00:00:00+00:00",
                "2024-01-03T00:00:00+00:00",
            ],
            "close": [100.0, 101.0, 103.0],
        }
    )
    path = tmp_path / "NIFTY.csv"
    frame.to_csv(path, index=False)

    returns = MODULE.load_benchmark_returns(path)

    assert returns.name == "nifty50"
    assert len(returns) == 2
    assert np.isclose(returns.iloc[0], 0.01)
    assert np.isclose(returns.iloc[1], 103.0 / 101.0 - 1.0)


def test_load_benchmark_returns_reads_cached_duckdb(tmp_path: Path) -> None:
    path = tmp_path / "cache.duckdb"
    repository = MODULE.DataRepository(MODULE.DuckDBAccess(path))
    repository.initialize()
    repository.add_asset("NIFTY", "NIFTY 50", "index", "NSE")
    repository.ingest_market_data(
        "NIFTY", datetime(2024, 1, 1, 18, 30, tzinfo=UTC), 99.0, 101.0, 98.0, 100.0, 1.0
    )
    repository.ingest_market_data(
        "NIFTY", datetime(2024, 1, 2, 18, 30, tzinfo=UTC), 100.0, 103.0, 99.0, 102.0, 1.0
    )
    repository.close()

    returns = MODULE.load_benchmark_returns(path)

    assert returns.name == "nifty50"
    assert len(returns) == 1
    assert returns.index[0] == pd.Timestamp("2024-01-03")
    assert np.isclose(returns.iloc[0], 0.02)


def test_rolling_metrics_and_relative_metrics() -> None:
    index = pd.date_range("2024-01-01", periods=5, freq="D")
    strategy = pd.Series([0.01, 0.02, 0.03, 0.04, 0.05], index=index, name="strategy")
    benchmark = pd.Series([0.005, 0.01, 0.015, 0.02, 0.025], index=index, name="nifty50")

    rolling = MODULE.rolling_return_metrics(strategy, windows=(3,))
    relative = MODULE.rolling_relative_metrics(strategy, benchmark, windows=(3,))

    window = strategy.iloc[-3:]
    expected_vol = float(window.std(ddof=0) * np.sqrt(252))
    expected_sharpe = float(window.mean() / window.std(ddof=0) * np.sqrt(252))

    assert np.isclose(rolling["rolling_vol_3"].iloc[-1], expected_vol)
    assert np.isclose(rolling["rolling_sharpe_3"].iloc[-1], expected_sharpe)
    assert np.isclose(relative["rolling_corr_3"].iloc[-1], 1.0)
    assert np.isclose(relative["rolling_beta_3"].iloc[-1], 2.0)


def test_average_holding_period_and_trade_count() -> None:
    index = pd.date_range("2024-01-01", periods=7, freq="D")
    weights = pd.DataFrame(
        {
            "a": [1.0, 1.0, 1.0, 0.0, 0.0, -1.0, -1.0],
            "b": [0.0, 0.0, 2.0, 2.0, 0.0, 0.0, 0.0],
        },
        index=index,
    )

    holding_period = MODULE.average_holding_period(weights)
    trades = MODULE.trade_count(weights)

    assert np.isclose(holding_period, 7.0 / 3.0)
    assert trades == 5


def test_load_benchmark_returns_missing_path_raises(tmp_path: Path) -> None:
    missing = tmp_path / "missing.csv"

    with pytest.raises(FileNotFoundError, match="Missing cached NIFTY benchmark series"):
        MODULE.load_benchmark_returns(missing)
