from __future__ import annotations

from research.notebooks.alpha_001.research.alpha101_engine import Alpha101Panel


def subset_high_vol_panel(panel: Alpha101Panel, top_n: int = 100) -> Alpha101Panel:
    shares = panel.high_vol_mask.mean(axis=0).sort_values(ascending=False).head(top_n)
    columns = shares.index
    return Alpha101Panel(
        name=f"{panel.name}_high_vol_top{top_n}",
        open=panel.open[columns],
        high=panel.high[columns],
        low=panel.low[columns],
        close=panel.close[columns],
        adj_close=panel.adj_close[columns],
        volume=panel.volume[columns],
        vwap=panel.vwap[columns],
        returns=panel.returns[columns],
        active_mask=panel.active_mask[columns],
        high_vol_mask=panel.high_vol_mask[columns],
        constituents=panel.constituents,
        industry=panel.industry.reindex(columns),
        pit_risk=panel.pit_risk,
    )
