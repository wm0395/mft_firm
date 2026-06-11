from __future__ import annotations

import contextlib
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Literal, cast

import pandas as pd

import project.ui_services.price_action_strategy_lab_dashboard as dashboard_ui
import project.ui_services.price_action_strategy_lab_views as views


class _FakeColumn:
    def __init__(self, parent) -> None:
        self.parent = parent

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> Literal[False]:
        return False

    def markdown(self, text: str, unsafe_allow_html: bool = False) -> None:
        self.parent.markdowns.append((text, unsafe_allow_html))


class _FakeStreamlit:
    def __init__(
        self,
        selectbox_values: dict[str, object] | None = None,
        checkbox_values: dict[str, bool] | None = None,
    ) -> None:
        self.session_state: dict[str, object] = {}
        self.selectbox_values = selectbox_values or {}
        self.checkbox_values = checkbox_values or {}
        self.markdowns: list[tuple[str, bool]] = []
        self.captions: list[str] = []
        self.dataframes: list[object] = []
        self.line_charts: list[object] = []
        self.html_payloads: list[tuple[str, int]] = []
        self.components = SimpleNamespace(v1=SimpleNamespace(html=self._html))

    def markdown(self, text: str, unsafe_allow_html: bool = False) -> None:
        self.markdowns.append((text, unsafe_allow_html))

    def caption(self, text: str) -> None:
        self.captions.append(text)

    def dataframe(self, data, **_kwargs) -> None:
        self.dataframes.append(data)

    def line_chart(self, data, **_kwargs) -> None:
        self.line_charts.append(data)

    def selectbox(self, label: str, options, index: int = 0, **_kwargs):
        return self.selectbox_values.get(label, options[index])

    def checkbox(self, label: str, value: bool = False, **_kwargs) -> bool:
        return self.checkbox_values.get(label, value)

    def columns(self, count: int):
        return tuple(_FakeColumn(self) for _ in range(count))

    def container(self, **_kwargs):
        return contextlib.nullcontext()

    def expander(self, *_args, **_kwargs):
        return contextlib.nullcontext()

    def _html(self, html: str, height: int = 0) -> None:
        self.html_payloads.append((html, height))


def test_render_price_action_strategy_lab_section_renders_preview(monkeypatch) -> None:
    run, signal_frame, chart_rows, fake_st = _build_preview_case()

    monkeypatch.setattr(
        dashboard_ui,
        "list_price_action_strategy_lab_runs",
        lambda: (run,),
    )
    monkeypatch.setattr(
        dashboard_ui,
        "load_price_action_strategy_lab_signal",
        lambda _run, _alpha: signal_frame,
    )
    monkeypatch.setattr(
        dashboard_ui,
        "load_price_action_strategy_lab_chart_rows",
        lambda _run, _symbol: chart_rows,
    )

    dashboard_ui.render_price_action_strategy_lab_section(fake_st)

    assert any("Research Suite" in html for html, unsafe in fake_st.markdowns if unsafe)
    assert any("inverse_fisher_rsi_reversal_10" in html for html, unsafe in fake_st.markdowns)
    assert fake_st.dataframes
    assert fake_st.line_charts
    assert fake_st.html_payloads


def test_render_price_action_strategy_lab_section_uses_empty_state(monkeypatch) -> None:
    fake_st = _FakeStreamlit()
    captured: dict[str, tuple[object, ...]] = {}

    monkeypatch.setattr(dashboard_ui, "list_price_action_strategy_lab_runs", lambda: ())
    monkeypatch.setattr(
        dashboard_ui,
        "render_empty_state",
        lambda *args: captured.setdefault("empty", args),
    )

    dashboard_ui.render_price_action_strategy_lab_section(fake_st)

    empty = cast(
        tuple[object, str, str, str, tuple[tuple[str, str, str], ...]],
        captured["empty"],
    )
    _, title, summary, note, chips = empty
    assert title == "No research runs found."
    assert "Run the BO or NSE alpha suite" in summary
    assert "cached reports" in note
    assert chips[0] == ("Runs", "0", "warning")


def _build_preview_case():
    signal_frame = pd.DataFrame(
        {
            "TEST.BO": [0.1, 0.2, 0.3],
            "ALT.BO": [0.9, 0.8, 0.7],
        },
        index=pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03"]),
    )
    chart_rows = (
        (datetime(2026, 1, 1, tzinfo=UTC), 10.0, 11.0, 9.5, 10.5, 1000.0),
        (datetime(2026, 1, 2, tzinfo=UTC), 10.5, 11.5, 10.0, 11.0, 1200.0),
    )
    fake_st = _FakeStreamlit(
        selectbox_values={
            "Research run": "bo_alpha_suite",
            "Turnover cost (bps)": 10.0,
            "Alpha": "inverse_fisher_rsi_reversal_10",
            "Mode": "cross_sectional_quintile",
            "Horizon": 10,
            "Preview symbol for inverse_fisher_rsi_reversal_10": "TEST.BO",
        },
        checkbox_values={"Preview chart": True},
    )
    return _build_run(), signal_frame, chart_rows, fake_st


def _build_run() -> views.PriceActionStrategyLabRun:
    return views.PriceActionStrategyLabRun(
        name="bo_alpha_suite",
        report_dir=Path("/tmp/reports/bo_alpha_suite"),
        config_path=Path("/tmp/configs/bo_alpha_suite.yaml"),
        config=_build_config(),
        summary_text="# Alpha Suite Run\n\n- alpha rows: 3\n- cache hits: 1/1",
        alpha_results=_build_alpha_results(),
        mode_comparison=_build_mode_comparison(),
        cache_events=_build_cache_events(),
        modified_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _build_config() -> views.PriceActionStrategyLabSuiteConfig:
    return views.PriceActionStrategyLabSuiteConfig(
        universe=_build_universe(),
        alpha_names=(
            "bollinger_percent_b_mean_reversion_20",
            "inverse_fisher_rsi_reversal_10",
        ),
        expression_modes=(
            "cross_sectional_quintile",
            "time_series_threshold",
            "ranked_long_only",
        ),
        backtests=_build_backtests(),
        compute=_build_compute(),
    )


def _build_universe() -> views.PriceActionStrategyLabUniverseConfig:
    universe = views.PriceActionStrategyLabUniverseConfig(
        name="all_bo_market_collector",
        source="market_collector_native",
        database_path=Path("/tmp/market.duckdb"),
        exchange="",
        symbol_suffix=".BO",
        timeframe="1d",
        start_timestamp=datetime(2025, 1, 1, tzinfo=UTC),
        end_timestamp=datetime(2025, 12, 31, tzinfo=UTC),
        min_history_days=252,
        max_missing_ratio=0.15,
        require_ohlcv=True,
    )
    return universe


def _build_backtests() -> views.PriceActionStrategyLabBacktestConfig:
    return views.PriceActionStrategyLabBacktestConfig(
        horizons=(1, 5, 10),
        turnover_cost_bps=(0.0, 5.0, 10.0, 25.0),
        min_active_names=20,
        threshold=0.0,
        top_quantile=0.8,
        bottom_quantile=0.2,
    )


def _build_compute() -> views.PriceActionStrategyLabComputeConfig:
    return views.PriceActionStrategyLabComputeConfig(
        cache_dir=Path("/tmp/cache"),
        report_dir=Path("/tmp/reports"),
        max_workers=1,
    )


def _build_alpha_results() -> tuple[views.PriceActionStrategyLabResultRow, ...]:
    return (
        _build_result_row(
            "inverse_fisher_rsi_reversal_10",
            "cross_sectional_quintile",
            10,
            324,
            0.928,
            94.766,
            82.830,
            0.559,
            0.75,
        ),
        _build_result_row(
            "inverse_fisher_rsi_reversal_10",
            "ranked_long_only",
            10,
            324,
            0.928,
            72.742,
            66.671,
            0.284,
            0.72,
        ),
        _build_result_row(
            "bollinger_percent_b_mean_reversion_20",
            "ranked_long_only",
            10,
            323,
            0.925,
            84.421,
            76.893,
            0.343,
            0.74,
        ),
    )


def _build_result_row(
    alpha: str,
    mode: str,
    horizon: int,
    obs: int,
    coverage: float,
    gross_mean_bps: float,
    net_mean_bps: float,
    turnover: float,
    win_rate: float,
) -> views.PriceActionStrategyLabResultRow:
    return views.PriceActionStrategyLabResultRow(
        alpha,
        10.0,
        f"{alpha}:{mode}:{horizon}d:10bps",
        mode,
        horizon,
        obs,
        obs,
        coverage,
        gross_mean_bps,
        net_mean_bps,
        turnover,
        win_rate,
        True,
    )


def _build_mode_comparison() -> tuple[views.PriceActionStrategyLabModeComparisonRow, ...]:
    return (
        views.PriceActionStrategyLabModeComparisonRow(
            "cross_sectional_quintile",
            10,
            10.0,
            2,
            61.0,
            61.0,
            0.560,
            0.928,
        ),
        views.PriceActionStrategyLabModeComparisonRow(
            "ranked_long_only",
            10,
            10.0,
            2,
            55.0,
            55.0,
            0.314,
            0.926,
        ),
        views.PriceActionStrategyLabModeComparisonRow(
            "time_series_threshold",
            10,
            10.0,
            2,
            35.0,
            35.0,
            0.450,
            0.920,
        ),
    )


def _build_cache_events() -> tuple[views.PriceActionStrategyLabCacheEventRow, ...]:
    return (
        views.PriceActionStrategyLabCacheEventRow(
            "inverse_fisher_rsi_reversal_10",
            True,
            Path("/tmp/cache/signals/one.pkl"),
        ),
    )
