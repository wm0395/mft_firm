from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

from project.ui._streamlit import get_streamlit
from project.ui.components.empty_state import render_empty_state
from project.ui.components.page_hero import render_page_hero
from project.ui.components.trading_view_chart import trading_view_chart
from project.ui.state import set_selected_asset


RANGE_OPTIONS = ("1M", "3M", "6M", "1Y", "2Y", "5Y", "All")
DEFAULT_RANGE = "1Y"


def render(repository) -> None:
    st = get_streamlit()
    st.title("Charts")

    assets = _load_assets(repository)
    if not assets:
        render_empty_state(
            st,
            "No assets available.",
            "Add assets before opening the chart view.",
            "The chart cannot render until the asset universe is populated.",
            (
                ("Assets", "0 registered", "warning"),
                ("Chart", "Unavailable", "warning"),
                ("Next step", "Load universe", "action"),
            ),
        )
        return

    symbols = [a.symbol for a in assets]
    asset_map = {a.symbol: a for a in assets}

    selected, range_label = _render_controls(st, symbols, asset_map)
    if selected:
        set_selected_asset(st.session_state, selected)

    start_date, end_date, window_label = _get_date_range(range_label)
    render_page_hero(
        f"Inspect {_format_asset(selected, asset_map)} at a glance.",
        "Chart, metrics, and raw data stay synchronized to the same filters.",
        context=(
            ("Asset", selected),
            ("Range", range_label),
            ("Window", window_label),
            ("Universe", len(assets)),
        ),
    )

    st.markdown("<hr class='ui-divider'>", unsafe_allow_html=True)

    data = _fetch_data(repository, selected, start_date, end_date)
    if data:
        _render_chart(st, data)
        st.markdown("<hr class='ui-divider'>", unsafe_allow_html=True)
        _render_kpis(st, data)
        st.markdown("<hr class='ui-divider'>", unsafe_allow_html=True)
        _render_raw_data(st, data)
    else:
        _render_empty(st, selected, window_label)


def _load_assets(repository):
    return list(repository.list_assets())


def _format_asset(symbol, asset_map):
    a = asset_map.get(symbol)
    if a:
        name = getattr(a, "name", "")
        return f"{symbol} — {name}" if name else symbol
    return symbol


def _render_controls(st, symbols, asset_map) -> tuple[str, str]:
    current = st.session_state.get("selected_asset_symbol")
    if current not in symbols:
        current = symbols[0] if symbols else None
    idx = symbols.index(current) if current in symbols else 0

    cols = st.columns(3)
    with cols[0]:
        selected = _selectbox(
            st,
            "Asset",
            symbols,
            index=idx,
            format_func=lambda s: _format_asset(s, asset_map),
            session_key="chart_asset",
        )
        a = asset_map.get(selected)
        if a:
            parts = []
            for attr in ("name", "sector", "market"):
                v = getattr(a, attr, None)
                if v:
                    parts.append(str(v))
            if parts:
                st.markdown(
                    f'<div style="color: #94a3b8; font-size: 0.78rem; '
                    f'margin-top: -0.3rem;">{" · ".join(parts)}</div>',
                    unsafe_allow_html=True,
                )
    with cols[1]:
        presets = _selectbox(
            st,
            "Range",
            RANGE_OPTIONS,
            index=RANGE_OPTIONS.index(
                st.session_state.get("charts_range", DEFAULT_RANGE)
            )
            if st.session_state.get("charts_range") in RANGE_OPTIONS
            else RANGE_OPTIONS.index(DEFAULT_RANGE),
            session_key="charts_range",
        )
    with cols[2]:
        _start_date, _end_date, window_label = _get_date_range(presets)
        st.markdown(
            f'<div style="margin-top: 1.6rem; color: #94a3b8; font-size: 0.85rem;">'
            f"{window_label}</div>",
            unsafe_allow_html=True,
        )
    return selected, presets


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


def _get_date_range(preset: str) -> tuple[date | None, date | None, str]:
    end = datetime.now(timezone.utc)
    if preset == "All":
        return None, None, "Full history"
    days = {"1M": 30, "3M": 90, "6M": 180, "1Y": 365, "2Y": 730, "5Y": 1825}
    start = end - timedelta(days=days.get(preset, 365))
    window = f"{start.strftime('%b %d, %Y')} – {end.strftime('%b %d, %Y')}"
    return start.date(), end.date(), window


def _fetch_data(repository, symbol, start_date, end_date):
    getter = getattr(repository, "get_market_data", None)
    if not getter:
        return []
    start_dt = (
        datetime.combine(start_date, time.min, tzinfo=timezone.utc)
        if start_date is not None
        else None
    )
    end_dt = (
        datetime.combine(end_date, time.max, tzinfo=timezone.utc)
        if end_date is not None
        else None
    )
    try:
        data = getter(symbol, start_dt, end_dt)
        return list(data) if data else []
    except Exception as e:
        get_streamlit().error(f"Failed to load data: {e}")
        return []


def _render_chart(st, data) -> None:
    html = trading_view_chart(data)
    st.components.v1.html(html, height=580)


def _render_kpis(st, data) -> None:
    st.markdown("<h2>Key Metrics</h2>", unsafe_allow_html=True)
    closes = [r[4] for r in data]
    if not closes:
        return
    first, last = closes[0], closes[-1]
    change = last - first
    change_pct = (change / first * 100) if first else 0.0
    high = max(closes)
    low = min(closes)
    total_vol = sum(r[5] for r in data)
    avg_vol = total_vol / len(data)
    returns = (last - first) / first * 100 if first else 0

    _kpi_row(
        st,
        [
            ("Close", f"{last:.2f}", f"{change:+.2f}", change_pct),
            ("Returns", f"{returns:+.2f}%", "", None),
            ("High", f"{high:.2f}", "", None),
            ("Low", f"{low:.2f}", "", None),
            ("Avg Volume", f"{avg_vol:,.0f}", "", None),
            ("Total Volume", f"{total_vol:,.0f}", "", None),
        ],
    )


def _kpi_row(st, metrics):
    cols = st.columns(len(metrics))
    for col, (label, value, change_str, change_pct) in zip(cols, metrics, strict=False):
        with col:
            delta_class = ""
            delta_html = ""
            if change_str and change_pct is not None:
                delta_class = "positive" if change_pct >= 0 else "negative"
                delta_html = (
                    f'<div class="kpi-card__change {delta_class}">{change_str}</div>'
                )
            st.markdown(
                f'<div class="kpi-card">'
                f'<div class="kpi-card__label">{label}</div>'
                f'<div class="kpi-card__value">{value}</div>'
                f"{delta_html}</div>",
                unsafe_allow_html=True,
            )


def _render_raw_data(st, data) -> None:
    with st.expander("View Raw Data", expanded=False):
        rows = []
        for r in data:
            ts, open_, high, low, close_, volume = r
            rows.append(
                {
                    "Date": (
                        ts.strftime("%Y-%m-%d")
                        if hasattr(ts, "strftime")
                        else str(ts)
                    ),
                    "Open": round(float(open_), 2),
                    "High": round(float(high), 2),
                    "Low": round(float(low), 2),
                    "Close": round(float(close_), 2),
                    "Volume": f"{float(volume):,.0f}",
                }
            )
        st.dataframe(rows, use_container_width=True, height=300)


def _render_empty(st, selected, window_label) -> None:
    render_empty_state(
        st,
        f"No market data for {selected}.",
        f"The selected range ({window_label}) returned no rows.",
        "Widen the date window or verify that market data has been loaded.",
        (
            ("Asset", selected, "warning"),
            ("Range", window_label, "ok"),
            ("Next step", "Load data", "action"),
        ),
    )
    with st.expander("Troubleshooting", expanded=False):
        st.markdown(
            """
        - Try a wider date range
        - Verify the asset symbol is correct
        - Check that market data has been loaded for this asset

        You can load market data using the CLI:
        ```
        mft data sync --symbol SYMBOL
        ```
        """
        )
