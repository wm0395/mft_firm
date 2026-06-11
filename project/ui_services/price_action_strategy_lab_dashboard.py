from __future__ import annotations

from dataclasses import asdict

import pandas as pd

from project.ui.components.empty_state import render_empty_state
from project.ui.components.trading_view_chart import trading_view_chart
from project.ui_services.price_action_strategy_lab_views import (
    load_price_action_strategy_lab_report_text,
    list_price_action_strategy_lab_runs,
    load_price_action_strategy_lab_chart_rows,
    load_price_action_strategy_lab_signal,
    load_price_action_strategy_lab_validation_summary,
)


def render_price_action_strategy_lab_section(st) -> None:
    st.markdown("<h2>Research Suite</h2>", unsafe_allow_html=True)
    runs = list_price_action_strategy_lab_runs()
    if not runs:
        render_empty_state(
            st,
            "No research runs found.",
            "Run the BO or NSE alpha suite to populate this dashboard section.",
            "The dashboard reads cached reports from the research project.",
            (("Runs", "0", "warning"), ("Next step", "Run alpha suite", "action")),
        )
        return
    with st.container(border=True):
        run = _select_run(st, runs)
        _render_context(st, run)
        _render_metrics(st, run)
        _render_summary(st, run)
        _render_validation(st, run)
        results = _results_frame(run)
        if results.empty:
            _empty_results(st, run)
            return
        selected_cost = _select_cost(st, run)
        cost_frame = _cost_frame(results, selected_cost)
        if cost_frame.empty:
            _empty_cost(st, selected_cost)
            return
        best_row = _best_row(cost_frame)
        selected_alpha = _select_alpha(st, run, str(best_row["alpha"]))
        selected_mode = _select_mode(st, run, str(best_row["mode"]))
        selected_horizon = _select_horizon(st, run, int(best_row["horizon"]))
        selected_row = _selected_row(
            cost_frame,
            selected_alpha,
            selected_mode,
            selected_horizon,
            selected_cost,
        )
        _render_selected(st, selected_row)
        _render_tables(st, run, cost_frame, selected_cost, selected_row)
        _render_preview_toggle(st, run, selected_row)


def _render_context(st, run) -> None:
    universe = run.config.universe
    st.caption(
        f"Suite: {run.name} • Source: {universe.source} • "
        f"Exchange: {universe.exchange or 'all'} • Window: "
        f"{_window_label(universe.start_timestamp, universe.end_timestamp)}"
    )


def _render_metrics(st, run) -> None:
    cache_hits = sum(1 for row in run.cache_events if row.cache_hit)
    cols = st.columns(5)
    _kpi(cols[0], "Alphas", str(len(run.config.alpha_names)), "Encoded signals")
    _kpi(cols[1], "Modes", str(len(run.config.expression_modes)), "Expression modes")
    _kpi(cols[2], "Horizons", str(len(run.config.backtests.horizons)), "Holding periods")
    _kpi(cols[3], "Costs", str(len(run.config.backtests.turnover_cost_bps)), "Cost points")
    _kpi(cols[4], "Cache Hits", f"{cache_hits}/{len(run.cache_events)}", "Signal cache")


def _render_summary(st, run) -> None:
    with st.expander("Run summary", expanded=False):
        st.markdown(run.summary_text or "No run summary available.", unsafe_allow_html=False)


def _render_validation(st, run) -> None:
    summary = load_price_action_strategy_lab_validation_summary(run)
    decision = load_price_action_strategy_lab_report_text(run, "alpha_suite_decision_report.md")
    if summary.empty and not decision:
        return
    with st.expander("Validation", expanded=False):
        if decision:
            st.markdown(decision, unsafe_allow_html=False)
        if not summary.empty:
            st.markdown("#### Validation Summary", unsafe_allow_html=True)
            st.dataframe(summary, use_container_width=True, height=280)


def _render_selected(st, row: pd.Series) -> None:
    st.markdown(
        f"#### {row['alpha']} • {row['mode']} • {int(row['horizon'])}d • {row['cost_bps']:g} bps",
        unsafe_allow_html=True,
    )
    st.caption(str(row["name"]))
    cols = st.columns(6)
    _kpi(cols[0], "Net Mean", f"{row['net_mean_bps']:.2f} bps", "After costs")
    _kpi(cols[1], "Gross Mean", f"{row['gross_mean_bps']:.2f} bps", "Before costs")
    _kpi(cols[2], "Turnover", f"{row['turnover']:.3f}", "Portfolio churn")
    _kpi(cols[3], "Coverage", f"{row['coverage']:.3f}", "Active universe share")
    _kpi(cols[4], "Win Rate", f"{row['win_rate']:.3f}", "Positive periods")
    _kpi(cols[5], "Obs", str(int(row["obs"])), "Active observations")


def _render_tables(st, run, cost_frame: pd.DataFrame, selected_cost: float, row: pd.Series) -> None:
    st.markdown("#### Top Results", unsafe_allow_html=True)
    st.dataframe(_top_results_frame(cost_frame), use_container_width=True, height=280)
    st.markdown(f"#### {row['alpha']} Across Modes and Horizons", unsafe_allow_html=True)
    st.dataframe(_alpha_slice_frame(cost_frame, str(row["alpha"])), use_container_width=True, height=280)
    st.markdown(f"#### Mode Summary at {selected_cost:g} bps", unsafe_allow_html=True)
    st.dataframe(_mode_summary_frame(run, selected_cost), use_container_width=True, height=260)


def _render_preview(st, run, row: pd.Series) -> None:
    alpha = str(row["alpha"])
    signal_frame = load_price_action_strategy_lab_signal(run, alpha)
    if signal_frame.empty:
        _empty_preview(st, alpha)
        return
    preview_symbol = _select_preview_symbol(st, signal_frame, alpha)
    signal_series = signal_frame[preview_symbol].dropna()
    rows = load_price_action_strategy_lab_chart_rows(run, preview_symbol)
    st.markdown("#### Chart Preview", unsafe_allow_html=True)
    st.caption(
        "The OHLCV chart uses the selected symbol. The score series below is the "
        "cached alpha signal for the same strategy, mode, horizon, and cost."
    )
    _render_html_chart(st, rows)
    st.markdown("#### Signal Score", unsafe_allow_html=True)
    st.line_chart(signal_series.tail(120))
    st.dataframe(signal_series.tail(40).to_frame(name="signal"), use_container_width=True)


def _render_preview_toggle(st, run, row: pd.Series) -> None:
    if _checkbox(st, "Preview chart", session_key="research_preview_chart"):
        _render_preview(st, run, row)


def _empty_results(st, run) -> None:
    render_empty_state(
        st,
        "No alpha results found.",
        "The run exists, but it does not contain alpha suite output yet.",
        "Open the report directory and confirm the CSVs exist.",
        (("Run", run.name, "warning"), ("Outputs", "Missing", "warning")),
    )


def _empty_cost(st, selected_cost: float) -> None:
    render_empty_state(
        st,
        "No rows match the selected cost.",
        "The cached results do not include this turnover cost point.",
        "Choose one of the cost values listed in the suite config.",
        (("Cost", f"{selected_cost:g} bps", "warning"), ("Rows", "0", "warning")),
    )


def _empty_preview(st, alpha: str) -> None:
    render_empty_state(
        st,
        "No signal matrix available.",
        "The cached alpha signal could not be loaded for the selected strategy.",
        "Previewing the chart requires the cached signal matrix.",
        (("Alpha", alpha, "warning"), ("Chart", "Unavailable", "warning")),
    )


def _select_run(st, runs) -> object:
    names = tuple(run.name for run in runs)
    selected = _selectbox(st, "Research run", names, index=0, session_key="research_run")
    run_map = {run.name: run for run in runs}
    return run_map[str(selected)]


def _select_alpha(st, run, default: str) -> str:
    options = run.config.alpha_names
    return str(
        _selectbox(
            st,
            "Alpha",
            options,
            index=_option_index(options, default),
            session_key="research_alpha",
        )
    )


def _select_mode(st, run, default: str) -> str:
    options = run.config.expression_modes
    return str(
        _selectbox(
            st,
            "Mode",
            options,
            index=_option_index(options, default),
            session_key="research_mode",
        )
    )


def _select_horizon(st, run, default: int) -> int:
    options = run.config.backtests.horizons
    return int(
        _selectbox(
            st,
            "Horizon",
            options,
            index=_option_index(options, default),
            session_key="research_horizon",
        )
    )


def _select_cost(st, run) -> float:
    costs = run.config.backtests.turnover_cost_bps
    default = 10.0 if 10.0 in costs else costs[0]
    return float(
        _selectbox(
            st,
            "Turnover cost (bps)",
            costs,
            index=_option_index(costs, default),
            session_key="research_cost",
            format_func=lambda value: f"{value:g} bps",
        )
    )


def _select_preview_symbol(st, signal_frame: pd.DataFrame, alpha: str) -> str:
    options = _signal_symbol_options(signal_frame)
    return _selectbox(
        st,
        f"Preview symbol for {alpha}",
        options,
        index=0,
        session_key="research_preview_symbol",
    )


def _render_html_chart(st, rows) -> None:
    html = trading_view_chart(list(rows))
    components = getattr(st, "components", None)
    html_fn = getattr(getattr(components, "v1", None), "html", None)
    if callable(html_fn):
        html_fn(html, height=580)
        return
    st.markdown(html, unsafe_allow_html=True)


def _results_frame(run) -> pd.DataFrame:
    return pd.DataFrame([asdict(row) for row in run.alpha_results])


def _cost_frame(frame: pd.DataFrame, cost_bps: float) -> pd.DataFrame:
    selected = frame.loc[frame["cost_bps"].round(9).eq(cost_bps)].copy()
    return selected.sort_values("net_mean_bps", ascending=False).reset_index(drop=True)


def _best_row(frame: pd.DataFrame) -> pd.Series:
    return frame.iloc[0]


def _selected_row(
    frame: pd.DataFrame,
    alpha: str,
    mode: str,
    horizon: int,
    cost_bps: float,
) -> pd.Series:
    mask = (
        frame["alpha"].eq(alpha)
        & frame["mode"].eq(mode)
        & frame["horizon"].eq(horizon)
        & frame["cost_bps"].round(9).eq(cost_bps)
    )
    selected = frame.loc[mask].sort_values("net_mean_bps", ascending=False)
    return selected.iloc[0] if not selected.empty else frame.iloc[0]


def _top_results_frame(frame: pd.DataFrame) -> pd.DataFrame:
    columns = (
        "alpha",
        "mode",
        "horizon",
        "cost_bps",
        "net_mean_bps",
        "gross_mean_bps",
        "coverage",
        "turnover",
        "win_rate",
    )
    return frame.loc[:, columns].head(10).round(3)


def _alpha_slice_frame(frame: pd.DataFrame, alpha: str) -> pd.DataFrame:
    columns = (
        "alpha",
        "mode",
        "horizon",
        "cost_bps",
        "net_mean_bps",
        "gross_mean_bps",
        "coverage",
        "turnover",
        "win_rate",
    )
    selected = frame.loc[frame["alpha"].eq(alpha), columns]
    return selected.sort_values(["mode", "horizon"]).round(3).reset_index(drop=True)


def _mode_summary_frame(run, cost_bps: float) -> pd.DataFrame:
    frame = pd.DataFrame([asdict(row) for row in run.mode_comparison])
    selected = frame.loc[frame["cost_bps"].round(9).eq(cost_bps)].copy()
    columns = (
        "mode",
        "horizon",
        "cost_bps",
        "alpha_count",
        "mean_net_bps",
        "median_net_bps",
        "mean_turnover",
        "mean_coverage",
    )
    return (
        selected.loc[:, columns]
        .sort_values("mean_net_bps", ascending=False)
        .round(3)
        .reset_index(drop=True)
    )


def _signal_symbol_options(signal_frame: pd.DataFrame, limit: int = 25) -> tuple[str, ...]:
    scores = signal_frame.abs().max(axis=0).dropna().sort_values(ascending=False)
    return tuple(str(symbol) for symbol in scores.head(limit).index)


def _option_index(options, value) -> int:
    try:
        return options.index(value)
    except ValueError:
        return 0


def _window_label(start_ts, end_ts) -> str:
    if start_ts and end_ts:
        start = start_ts.strftime("%b %d, %Y") if hasattr(start_ts, "strftime") else str(start_ts)
        end = end_ts.strftime("%b %d, %Y") if hasattr(end_ts, "strftime") else str(end_ts)
        return f"{start} – {end}"
    return "Coverage unavailable"


def _selectbox(st, label, options, *, index: int, session_key: str, format_func=None):
    selectbox = getattr(st, "selectbox", None)
    if not callable(selectbox):
        return options[index]
    try:
        selected = selectbox(
            label,
            options,
            index=index,
            key=session_key,
            format_func=format_func,
        )
    except TypeError:
        selected = selectbox(label, options, index=index, format_func=format_func)
    session_state = getattr(st, "session_state", None)
    if isinstance(session_state, dict):
        session_state[session_key] = selected
    return selected


def _checkbox(st, label: str, *, session_key: str, value: bool = False) -> bool:
    checkbox = getattr(st, "checkbox", None)
    if not callable(checkbox):
        return value
    try:
        selected = checkbox(label, value=value, key=session_key)
    except TypeError:
        selected = checkbox(label, value=value)
    session_state = getattr(st, "session_state", None)
    if isinstance(session_state, dict):
        session_state[session_key] = selected
    return bool(selected)


def _kpi(container, label, value, subtitle):
    with container:
        container.markdown(
            f'<div class="kpi-card">'
            f'<div class="kpi-card__label">{label}</div>'
            f'<div class="kpi-card__value">{value}</div>'
            f'<div style="color: #94a3b8; font-size: 0.72rem; margin-top: 0.2rem;">{subtitle}</div>'
            f"</div>",
            unsafe_allow_html=True,
        )
