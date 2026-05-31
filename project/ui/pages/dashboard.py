from __future__ import annotations

from collections import Counter

from project.data.quality import build_data_quality_report
from project.ui._streamlit import get_streamlit


def render(repository) -> None:
    st = get_streamlit()
    st.title("Dashboard")

    assets = _load_assets(repository)
    data_summary = _load_data_summary(repository)

    _render_hero(st, assets, data_summary)
    _render_metrics(st, assets, data_summary)
    _render_quick_actions(st, assets)
    _render_quality(st, repository, assets)
    _render_asset_table(st, assets)


def _load_assets(repository):
    return list(repository.list_assets())


def _load_data_summary(repository):
    try:
        row = repository._db.fetch_all(
            """
            select count(distinct asset_symbol) as symbols,
                   count(*) as total_rows,
                   min(timestamp) as data_start,
                   max(timestamp) as data_end
            from raw_market_data
            """
        )
        if row:
            r = row[0]
            return {
                "symbols": r[0],
                "total_rows": r[1],
                "data_start": r[2],
                "data_end": r[3],
            }
    except Exception:
        pass
    return {}


def _format_num(n):
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def _render_hero(st, assets, data_summary) -> None:
    sectors = Counter(getattr(a, "sector", "Unknown") or "Unknown" for a in assets)
    top_sectors = sectors.most_common(3)
    total_rows = data_summary.get("total_rows", 0)
    chips = "".join(
        f'<span class="ui-hero__chip">'
        f'<span class="ui-hero__chip-label">{s}</span>'
        f'<span class="ui-hero__chip-value">{c}</span>'
        f"</span>"
        for s, c in top_sectors
    )
    st.markdown(
        f"""
    <section class="ui-hero">
      <div class="ui-hero__eyebrow">Platform Overview</div>
      <div class="ui-hero__summary">
        Tracking <strong>{len(assets)} assets</strong> with
        <strong>{_format_num(total_rows)}</strong> market data records
      </div>
      <div class="ui-hero__chips">{chips}</div>
    </section>
    """,
        unsafe_allow_html=True,
    )


def _render_metrics(st, assets, data_summary) -> None:
    total_rows = data_summary.get("total_rows", 0)
    symbols_with_data = data_summary.get("symbols", 0)
    ds = data_summary.get("data_start")
    de = data_summary.get("data_end")
    date_range = ""
    if ds and de:
        dsf = ds.strftime("%b %d, %Y") if hasattr(ds, "strftime") else str(ds)
        def_ = de.strftime("%b %d, %Y") if hasattr(de, "strftime") else str(de)
        date_range = f"{dsf} – {def_}"
    active = sum(1 for a in assets if getattr(a, "is_active", True))
    sectors = len(set(getattr(a, "sector", None) for a in assets if getattr(a, "sector", None)))
    markets = len(set(getattr(a, "market", None) for a in assets if getattr(a, "market", None)))

    cols = st.columns(5)
    _kpi(cols[0], "Total Assets", str(len(assets)), "All registered assets")
    _kpi(cols[1], "Active", str(active), f"Across {sectors} sectors, {markets} markets")
    _kpi(cols[2], "With Data", str(symbols_with_data), "Assets with market data")
    _kpi(cols[3], "Data Rows", _format_num(total_rows), "Total market data points")
    _kpi(cols[4], "Date Range", date_range or "N/A", "Data coverage")


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


def _render_quick_actions(st, assets) -> None:
    st.markdown('<h2>Quick Actions</h2>', unsafe_allow_html=True)
    cols = st.columns(4)
    with cols[0]:
        if st.button("📊 View Charts", use_container_width=True, type="primary"):
            st.session_state["ui_page"] = "Charts"
            st.rerun()
    with cols[1]:
        top = assets[0].symbol if assets else ""
        if st.button("📈 Chart Top Asset", use_container_width=True):
            st.session_state["ui_page"] = "Charts"
            st.session_state["selected_asset_symbol"] = top
            st.rerun()
    with cols[2]:
        if st.button("📋 View Trading", use_container_width=True):
            st.session_state["ui_page"] = "Trading"
            st.rerun()
    with cols[3]:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()


def _render_quality(st, repository, assets) -> None:
    st.markdown('<h2>Data Quality</h2>', unsafe_allow_html=True)
    symbols = tuple(a.symbol for a in assets[:30])
    if not symbols:
        st.info("No assets to check.")
        return
    with st.container():
        try:
            quality = build_data_quality_report(repository, symbols)
            status = str(quality.status)
            badge = f'<span class="badge badge--{status}">{status.upper()}</span>'
            cols = st.columns(4)
            _kpi(cols[0], "Status", badge, "Overall data quality")
            _kpi(cols[1], "Symbols Checked", str(len(quality.requested_symbols)), f"First {min(30, len(assets))} assets")
            _kpi(cols[2], "Sources", str(quality.source_count), "Data sources")
            _kpi(cols[3], "Max Staleness", f"{quality.max_staleness_days}d", "Allowed gap")
        except Exception as e:
            st.info(f"Quality report unavailable: {e}")


def _render_asset_table(st, assets) -> None:
    st.markdown('<h2>Asset Universe</h2>', unsafe_allow_html=True)
    search = st.text_input(
        "",
        placeholder="Search by symbol or name...",
        label_visibility="collapsed",
    )
    filtered = assets
    if search:
        sl = search.lower()
        filtered = [
            a
            for a in assets
            if sl in (getattr(a, "symbol", "") or "").lower()
            or sl in (getattr(a, "name", "") or "").lower()
        ]
    total = len(filtered)
    st.markdown(
        f'<div style="color: #94a3b8; font-size: 0.8rem; margin: -0.5rem 0 0.75rem;">'
        f"{total} of {len(assets)} assets shown</div>",
        unsafe_allow_html=True,
    )
    if not filtered:
        st.info("No assets match your search.")
        return
    rows = []
    for a in filtered:
        rows.append(
            {
                "Symbol": getattr(a, "symbol", ""),
                "Name": getattr(a, "name", ""),
                "Sector": getattr(a, "sector", ""),
                "Market": getattr(a, "market", ""),
            }
        )
    st.dataframe(rows, use_container_width=True, height=420)
