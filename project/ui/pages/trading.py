from __future__ import annotations

from project.ui._streamlit import get_streamlit
from project.ui.components.empty_state import render_empty_state
from project.ui.components.page_hero import render_page_hero


SECTION_OPTIONS = ("📋 Trade Ideas", "💼 Positions", "📊 Reports")


def render(repository) -> None:
    st = get_streamlit()
    st.title("Trading")
    section = _section_selector(st)
    if not callable(getattr(st, "markdown", None)):
        st.caption("Choose a section to load only the data you need.")
    if section == SECTION_OPTIONS[0]:
        _render_trade_ideas(repository, st)
    elif section == SECTION_OPTIONS[1]:
        _render_positions(repository, st)
    else:
        _render_reports(repository, st)


def _section_selector(st) -> str:
    current = getattr(st, "session_state", {}).get(
        "trading_section",
        SECTION_OPTIONS[0],
    )
    selectbox = getattr(st, "selectbox", None)
    if not callable(selectbox):
        return current if current in SECTION_OPTIONS else SECTION_OPTIONS[0]
    index = SECTION_OPTIONS.index(current) if current in SECTION_OPTIONS else 0
    try:
        selected = selectbox(
            "Section",
            SECTION_OPTIONS,
            index=index,
            key="trading_section",
        )
    except TypeError:
        selected = selectbox("Section", SECTION_OPTIONS, index=index)
    session_state = getattr(st, "session_state", None)
    if isinstance(session_state, dict):
        session_state["trading_section"] = selected
    return selected


def _load_asset_map(repository):
    return {a.asset_id: a for a in repository.list_assets()}


def _render_trade_ideas(repository, st) -> None:
    st.markdown("<h2>Trade Ideas</h2>", unsafe_allow_html=True)
    ideas = _fetch_trade_ideas(repository)
    open_ideas = _fetch_open_ideas(repository)
    render_page_hero(
        "Review pending trade ideas before they become positions.",
        "Open ideas stay on top so the queue is obvious.",
        (
            ("Ideas", len(ideas)),
            ("Open", len(open_ideas)),
            ("Reviewed", len(ideas) - len(open_ideas)),
        ),
    )

    cols = st.columns(3)
    _kpi(cols[0], "Total Ideas", str(len(ideas)))
    _kpi(cols[1], "Open", str(len(open_ideas)), "action" if open_ideas else "ok")
    _kpi(cols[2], "Reviewed", str(len(ideas) - len(open_ideas)))

    if open_ideas:
        st.markdown('<div style="margin-top: 1rem;"></div>', unsafe_allow_html=True)
        st.dataframe(open_ideas, use_container_width=True)
    else:
        _render_trade_ideas_empty_state(st, ideas)
        if ideas:
            with st.expander("All Trade Ideas", expanded=False):
                st.dataframe(ideas, use_container_width=True)


def _render_positions(repository, st) -> None:
    st.markdown("<h2>Positions</h2>", unsafe_allow_html=True)
    positions = _fetch_positions(repository)

    if positions:
        open_count = sum(1 for p in positions if p["Status"] == "open")
        closed_count = sum(1 for p in positions if p["Status"] == "closed")
        pnl_values = [
            float(p["PnL"])
            for p in positions
            if p["PnL"] not in ("-", "", "—")
        ]
        total_pnl = sum(pnl_values)
        render_page_hero(
            "Monitor open exposure and realized PnL in one place.",
            "Closed positions remain listed below the current book.",
            (
                ("Open", open_count),
                ("Closed", closed_count),
                ("PnL", f"{total_pnl:+.2f}"),
            ),
        )
        cols = st.columns(4)
        _kpi(cols[0], "Total", str(len(positions)))
        _kpi(cols[1], "Open", str(open_count), "action" if open_count else "ok")
        _kpi(cols[2], "Closed", str(closed_count))
        _kpi(
            cols[3],
            "Realized PnL",
            f"{total_pnl:+.2f}",
            "ok" if total_pnl >= 0 else "warning",
        )
        st.markdown('<div style="margin-top: 1rem;"></div>', unsafe_allow_html=True)
        st.dataframe(positions, use_container_width=True)
    else:
        render_empty_state(
            st,
            "No positions yet.",
            "Approved trade ideas will appear here after execution.",
            "Use the Trade Ideas section to approve the next trade.",
            chips=(
                ("Open", "0", "warning"),
                ("Closed", "0", "ok"),
                ("Next step", "Approve an idea", "action"),
            ),
        )


def _render_reports(repository, st) -> None:
    st.markdown("<h2>Reports</h2>", unsafe_allow_html=True)
    backtests = _fetch_backtests(repository)
    outcomes = _fetch_outcomes(repository)
    render_page_hero(
        "Compare backtests with realized trade outcomes.",
        "Use the two tables below to spot drift between simulation and execution.",
        (
            ("Backtests", len(backtests)),
            ("Outcomes", len(outcomes)),
            ("Focus", "Historical"),
        ),
    )
    cols = st.columns(2)
    with cols[0]:
        _kpi(cols[0], "Backtests", str(len(backtests)))
    with cols[1]:
        _kpi(cols[1], "Trade Outcomes", str(len(outcomes)))
    st.markdown('<div style="margin-top: 1rem;"></div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if backtests:
            st.markdown(
                '<div class="section-card__title">Backtest Results</div>',
                unsafe_allow_html=True,
            )
            st.dataframe(backtests, use_container_width=True)
        else:
            render_empty_state(
                st,
                "No backtest results yet.",
                "Run strategy research to generate performance results.",
                "Backtests appear after a research run completes.",
                chips=(
                    ("Backtests", "0 recorded", "warning"),
                    ("Source", "Research", "ok"),
                    ("Next step", "Run research", "action"),
                ),
            )
    with col2:
        if outcomes:
            st.markdown(
                '<div class="section-card__title">Trade Outcomes</div>',
                unsafe_allow_html=True,
            )
            st.dataframe(outcomes, use_container_width=True)
        else:
            render_empty_state(
                st,
                "No trade outcomes recorded yet.",
                "Closed trades have not populated this report yet.",
                "Trade outcomes update automatically when positions close.",
                chips=(
                    ("Outcomes", "0 recorded", "warning"),
                    ("Source", "Positions", "ok"),
                    ("Next step", "Review positions", "action"),
                ),
            )


def _fetch_trade_ideas(repository):
    try:
        raw = repository.get_trade_ideas()
        assets = _load_asset_map(repository)
        return [
            {
                "Symbol": _sym(assets, t.asset_id),
                "Direction": t.direction,
                "Confidence": f"{t.confidence:.2f}",
                "Timestamp": getattr(t, "timestamp", "") or "",
            }
            for t in raw
        ]
    except Exception:
        return []


def _fetch_open_ideas(repository):
    try:
        raw = repository.get_open_trade_ideas()
        assets = _load_asset_map(repository)
        return [
            {
                "Symbol": _sym(assets, t.asset_id),
                "Direction": t.direction,
                "Confidence": f"{t.confidence:.2f}",
                "Timestamp": getattr(t, "timestamp", "") or "",
            }
            for t in raw
        ]
    except Exception:
        return []


def _fetch_positions(repository):
    try:
        raw = repository.get_positions()
        ideas = {t.trade_id: t for t in repository.get_trade_ideas()}
        assets = _load_asset_map(repository)
        return [
            {
                "Symbol": (
                    _sym(assets, ideas[p.trade_id].asset_id)
                    if p.trade_id in ideas
                    else "?"
                ),
                "Direction": (
                    ideas[p.trade_id].direction if p.trade_id in ideas else "?"
                ),
                "Status": p.status,
                "Entry": f"{p.entry_price:.2f}",
                "Exit": f"{p.exit_price:.2f}" if p.exit_price is not None else "—",
                "PnL": f"{p.pnl:.2f}" if p.pnl is not None else "—",
            }
            for p in raw
        ]
    except Exception:
        return []


def _fetch_backtests(repository):
    try:
        raw = repository.get_backtest_results()
        return [
            {
                "Return": f'{getattr(b, "total_return_pct", 0):.2f}%',
                "Sharpe": f'{getattr(b, "sharpe_ratio", 0):.2f}',
                "Trades": str(getattr(b, "total_trades", 0)),
            }
            for b in raw
        ]
    except Exception:
        return []


def _fetch_outcomes(repository):
    try:
        raw = repository.get_trade_outcomes()
        return [
            {
                "PnL": f'{getattr(o, "pnl", 0):.2f}',
            }
            for o in raw
        ]
    except Exception:
        return []


def _render_trade_ideas_empty_state(st, ideas) -> None:
    if ideas:
        render_empty_state(
            st,
            "No open trade ideas.",
            "The review queue is currently clear.",
            "Open the history below to inspect closed ideas and their decision trails.",
            chips=(
                ("Queue", "0 open", "warning"),
                ("Reviewed", f"{len(ideas)} closed", "ok"),
                ("Next step", "Review history", "action"),
            ),
        )
        return
    render_empty_state(
        st,
        "No trade ideas yet.",
        "Research has not generated any ideas for review.",
        "Run strategy research to create the first idea.",
        chips=(
            ("Queue", "0 open", "warning"),
            ("Source", "Research", "ok"),
            ("Next step", "Run research", "action"),
        ),
    )


def _sym(assets, asset_id):
    a = assets.get(asset_id)
    return a.symbol if a else asset_id[:8]


def _kpi(container, label, value, state="ok"):
    with container:
        badge = ""
        if state == "action":
            badge = (
                '<div style="margin-top: 0.2rem;">'
                '<span class="badge badge--info">ACTION NEEDED</span></div>'
            )
        elif state == "warning":
            badge = (
                '<div style="margin-top: 0.2rem;">'
                '<span class="badge badge--warning">ATTENTION</span></div>'
            )
        container.markdown(
            f'<div class="kpi-card">'
            f'<div class="kpi-card__label">{label}</div>'
            f'<div class="kpi-card__value">{value}</div>'
            f"{badge}</div>",
            unsafe_allow_html=True,
        )
