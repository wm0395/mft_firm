from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from research.projects.price_action_strategy_lab.backtest_modes import BacktestConfig, run_backtest
from research.projects.price_action_strategy_lab.chart_pack import (
    ChartPackConfig,
    generate_chart_pack,
    signals_from_positions,
)
from research.projects.price_action_strategy_lab.costs import turnover_cost
from research.projects.price_action_strategy_lab.run_lab import run_lab
from research.projects.price_action_strategy_lab.selector_registry import selector_registry


def test_backtest_selector_chart_and_runner_workflow(tmp_path: Path) -> None:
    dates = pd.date_range("2024-01-01", periods=4, freq="D")
    signal = pd.DataFrame({"AAA": [3.0, 2.0, -2.0, 1.0], "BBB": [-2.0, 1.0, 3.0, -1.0]}, index=dates)
    forward = pd.DataFrame({"AAA": [0.02, 0.01, -0.01, 0.03], "BBB": [-0.01, 0.02, 0.01, -0.02]}, index=dates)
    config = BacktestConfig("toy", "cross_sectional_quintile", 1, turnover_cost(10.0))

    result = run_backtest(signal, forward, config)
    assert result.active.tolist() == [True, True, True, True]
    assert result.net_return.dropna().mean() > 0.0

    selectors = selector_registry()
    decision = selectors[0].builder((result,))
    assert decision.chosen_name == "toy"
    assert not decision.abstain

    ohlcv = _ohlcv(dates)
    signals = signals_from_positions(result.positions, result.name, result.reason_code)
    chart = generate_chart_pack(ohlcv, signals, ChartPackConfig("AAA", tmp_path))
    assert chart.html_path.exists()
    assert "AAA" in chart.html_path.read_text(encoding="utf-8")
    assert chart.signal_count > 0

    data_path = tmp_path / "market.csv"
    config_path = tmp_path / "config.json"
    _runner_data(dates).to_csv(data_path, index=False)
    config_path.write_text(
        json.dumps(
            {
                "data_csv": str(data_path),
                "report_dir": str(tmp_path / "reports"),
                "chart_symbols": ["AAA"],
                "backtests": [
                    {
                        "name": "toy_cs",
                        "mode": "cross_sectional_quintile",
                        "horizon": 1,
                        "cost": {"turnover_bps": 10.0},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    lab_result = run_lab(config_path)
    assert lab_result.run_summary_path.exists()
    assert lab_result.alpha_results_path.exists()
    assert lab_result.selector_results_path.exists()
    assert lab_result.chart_index_path.exists()


def _ohlcv(dates: pd.DatetimeIndex) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "open": [10.0, 10.5, 10.3, 10.8],
            "high": [10.8, 10.7, 10.9, 11.2],
            "low": [9.8, 10.1, 10.0, 10.5],
            "close": [10.4, 10.2, 10.7, 11.0],
            "volume": [1000, 1200, 900, 1500],
        },
        index=dates,
    )


def _runner_data(dates: pd.DatetimeIndex) -> pd.DataFrame:
    rows = []
    for date in dates:
        rows.append(_runner_row(date, "AAA", 3.0, 0.02))
        rows.append(_runner_row(date, "BBB", -3.0, -0.01))
    return pd.DataFrame(rows)


def _runner_row(
    date: pd.Timestamp,
    symbol: str,
    signal: float,
    forward_return: float,
) -> dict[str, float | str | bool | pd.Timestamp]:
    return {
        "date": date,
        "symbol": symbol,
        "open": 10.0,
        "high": 11.0,
        "low": 9.5,
        "close": 10.5,
        "volume": 1000.0,
        "signal": signal,
        "forward_return": forward_return,
        "active": True,
    }
