# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: hydrogen
#       format_version: '1.3'
#       jupytext_version: 1.19.3
#   kernelspec:
#     display_name: .venv (3.12.3)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Testing out Ideas

# %% [markdown]
# ## Data

# %% [markdown]
# ### Loading from DuckDB (market_collector)

# %%
import os
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

# Set working directory to project root
os.chdir('/home/wm0395/Investment/mft_project')
if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())
print("Working directory:", os.getcwd())

# %%
# Connect to the project DuckDB database
DB_PATH = Path("project_mft.duckdb")
conn = duckdb.connect(str(DB_PATH), read_only=True)
print(f"Connected to {DB_PATH} ({DB_PATH.stat().st_size / 1e6:.0f} MB)")

# %%
# Explore available assets
assets = conn.execute("""
    select asset_id, symbol, name, sector, market, is_active
    from assets
    order by symbol
    limit 20
""").fetchdf()
assets

# %%
# Check date range of available market data
date_range = conn.execute("""
    select
        min(timestamp) as first_date,
        max(timestamp) as last_date,
        count(distinct asset_symbol) as symbols,
        count(*) as total_rows
    from raw_market_data
""").fetchdf()
date_range


# %% [markdown]
# ### Build Panel Data for Alpha101 Engine
#
# The alpha101 engine expects wide-format DataFrames (date index x symbols columns) for each OHLCV field.

# %%
def load_market_panel(conn, symbols=None, start_date=None, end_date=None):
    """Load OHLCV data from DuckDB and pivot into wide format for Alpha101Panel."""
    where_clauses = []
    if symbols is not None:
        placeholders = ",".join("?" for _ in symbols)
        where_clauses.append(f"asset_symbol in ({placeholders})")
    if start_date is not None:
        where_clauses.append(f"timestamp >= ?::timestamp")
    if end_date is not None:
        where_clauses.append(f"timestamp <= ?::timestamp")
    where_sql = " and ".join(where_clauses)
    if where_sql:
        where_sql = "where " + where_sql

    params = []
    if symbols is not None:
        params.extend(symbols)
    if start_date is not None:
        params.append(start_date)
    if end_date is not None:
        params.append(end_date)

    query = f"""
        select asset_symbol, timestamp, open, high, low, close, volume
        from raw_market_data
        {where_sql}
        order by timestamp, asset_symbol
    """
    df = conn.execute(query, params).fetchdf()

    def _pivot(col):
        return df.pivot_table(index="timestamp", columns="asset_symbol", values=col, aggfunc="first")

    panel = {
        "open": _pivot("open"),
        "high": _pivot("high"),
        "low": _pivot("low"),
        "close": _pivot("close"),
        "volume": _pivot("volume"),
        "adj_close": None,
    }
    panel["returns"] = panel["close"].pct_change(fill_method=None)

    # Build a simple industry map from assets table
    asset_info = conn.execute("""
        select symbol, coalesce(sector, 'unknown') as sector
        from assets
    """).fetchdf()
    industry = asset_info.set_index("symbol").sector

    return panel, industry


# Load a subset of liquid symbols for testing
top_symbols = conn.execute("""
    select asset_symbol
    from raw_market_data
    group by asset_symbol
    having count(*) > 1000
    order by count(*) desc
    limit 50
""").fetchdf()["asset_symbol"].tolist()
print(f"Top {len(top_symbols)} symbols by data density: {top_symbols[:5]}...")

# %%
# Build the panel
panel_dict, industry_series = load_market_panel(conn, symbols=top_symbols)
print(f"Panel shape: {panel_dict['close'].shape}")
print(f"Date range: {panel_dict['close'].index.min()} to {panel_dict['close'].index.max()}")
panel_dict["close"].tail(5)

# %% [markdown]
# ### Import and Use Alpha101 Engine
#
# Build an `Alpha101Panel` from the loaded data and compute alpha factors.

# %%
from research.notebooks.alpha_001.research.alpha101_engine import Alpha101Panel, clean
from research.notebooks.alpha_001.research.alpha101_formulas import compute_alpha, registry_frame

print("Research framework imported successfully!")

# %%
# Create an Alpha101Panel
# Note: adj_close can be set to close if split-adjusted data is not available
panel = Alpha101Panel(
    name="duckdb_panel",
    open=panel_dict["open"],
    high=panel_dict["high"],
    low=panel_dict["low"],
    close=panel_dict["close"],
    adj_close=panel_dict["close"],
    volume=panel_dict["volume"],
    vwap=(panel_dict["high"] + panel_dict["low"] + panel_dict["close"]) / 3.0,
    returns=panel_dict["returns"],
    active_mask=panel_dict["close"].notna() & panel_dict["volume"].notna() & (panel_dict["volume"] > 0),
    high_vol_mask=panel_dict["close"].notna(),
    constituents=conn.execute("select symbol, name, sector from assets").fetchdf(),
    industry=industry_series,
    pit_risk="duckdb_snapshot",
)
print(f"Panel '{panel.name}' created: {panel.close.shape}")

# %%
# List available alpha formulas
registry = registry_frame()
print(f"Available formulas: {len(registry)}")
registry.head(10)

# %%
# Compute a few alpha factors
alpha_ids = ["alpha001", "alpha002", "alpha003", "alpha004", "alpha005"]
results = {}
for aid in alpha_ids:
    print(f"Computing {aid}...")
    try:
        results[aid] = compute_alpha(panel, aid)
        print(f"  -> shape: {results[aid].shape}")
    except Exception as e:
        print(f"  -> ERROR: {e}")

# %%
# Examine alpha001 output
if "alpha001" in results:
    alpha = results["alpha001"]
    print(f"Alpha001 - shape: {alpha.shape}, date range: {alpha.index.min()} to {alpha.index.max()}")
    display(alpha.tail(10))
    
    # Basic statistics
    print(f"\nCross-sectional stats (latest date):")
    latest = alpha.iloc[-1].dropna()
    print(f"  Mean: {latest.mean():.4f}, Std: {latest.std():.4f}")
    print(f"  Min: {latest.min():.4f}, Max: {latest.max():.4f}")

# %%
# Clean up
conn.close()
print("Connection closed.")
