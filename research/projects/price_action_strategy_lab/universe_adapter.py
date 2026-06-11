from __future__ import annotations

from project.data.market_collector_panel import MarketCollectorPanel
from research.notebooks.alpha_001.research.alpha101_engine import Alpha101Panel


def to_alpha101_panel(panel: MarketCollectorPanel) -> Alpha101Panel:
    close = panel.close.copy()
    return Alpha101Panel(
        name=panel.name,
        open=panel.open,
        high=panel.high,
        low=panel.low,
        close=close,
        adj_close=close,
        volume=panel.volume,
        vwap=(panel.high + panel.low + close) / 3.0,
        returns=close.pct_change(fill_method=None),
        active_mask=panel.active_mask,
        high_vol_mask=panel.active_mask,
        constituents=panel.constituents,
        industry=panel.industry,
        pit_risk=panel.pit_risk,
    )
