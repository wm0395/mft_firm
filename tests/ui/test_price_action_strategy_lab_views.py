from __future__ import annotations

from types import SimpleNamespace
from typing import cast

import pandas as pd

import project.ui_services.price_action_strategy_lab_views as views


def test_list_price_action_strategy_lab_runs_loads_suite_metadata() -> None:
    runs = views.list_price_action_strategy_lab_runs()
    names = {run.name for run in runs}

    assert {"bo_alpha_suite", "nse_alpha_suite"} <= names

    bo_run = next(run for run in runs if run.name == "bo_alpha_suite")
    assert bo_run.config.universe.source == "market_collector_native"
    assert bo_run.config.universe.database_path.is_absolute()
    assert bo_run.config.backtests.horizons == (1, 5, 10)
    assert bo_run.summary_text.startswith("# Alpha Suite Run")
    assert len(bo_run.alpha_results) == 180


def test_load_price_action_strategy_lab_signal_and_top_symbols() -> None:
    run = next(
        run for run in views.list_price_action_strategy_lab_runs() if run.name == "bo_alpha_suite"
    )

    signal = views.load_price_action_strategy_lab_signal(
        run,
        "inverse_fisher_rsi_reversal_10",
    )
    symbols = views.top_signal_symbols(run, "inverse_fisher_rsi_reversal_10", limit=5)

    assert not signal.empty
    assert len(symbols) == 5
    assert all(symbol.endswith(".BO") for symbol in symbols)


def test_load_price_action_strategy_lab_chart_rows_extracts_symbol_history(
    monkeypatch,
) -> None:
    index = pd.to_datetime(["2026-01-01", "2026-01-02"])
    frame = pd.DataFrame({"TEST.BO": [10.0, 11.0]}, index=index)
    panel = SimpleNamespace(
        open=frame + 0.5,
        high=frame + 1.0,
        low=frame - 1.0,
        close=frame,
        volume=frame * 100.0,
    )
    monkeypatch.setattr(views, "load_price_action_strategy_lab_panel", lambda *_args, **_kwargs: panel)

    rows = views.load_price_action_strategy_lab_chart_rows(
        cast(views.PriceActionStrategyLabRun, SimpleNamespace()),
        "TEST.BO",
    )

    assert rows == (
        (index[0].to_pydatetime(), 10.5, 11.0, 9.0, 10.0, 1000.0),
        (index[1].to_pydatetime(), 11.5, 12.0, 10.0, 11.0, 1100.0),
    )
