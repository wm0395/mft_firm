# My Alpha Research Notebook

This notebook demonstrates how to:
1. Load OHLCV data using the research framework
2. Compute Alpha101 formulaic alphas
3. Perform basic analysis on the results

## 1. Loading the Data

First, we'll load either the Nifty500 or Expanded universe panel:
```python
# Import necessary modules
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)

# Import the panel loading function from the research framework
from research.notebooks.alpha_001.research.alpha101_engine import load_panel

print("Loading Nifty500 panel...")
panel = load_panel("nifty500")
print(f"Panel loaded: {panel.name}")
print(f"Date range: {panel.open.index[0]} to {panel.open.index[-1]}")
print(f"Number of securities: {len(panel.open.columns)}")
print(f"Number of time points: {len(panel.open.index)}")

# Check data availability
active_ratio = panel.active_mask.mean().mean()
print(f"Average data availability: {active_ratio:.1%}")

# Display basic info about the data
print("\nData samples:")
print(f"Open price sample (first 5 days, first security): {panel.open.iloc[:5, 0].tolist()}")
print(f"Volume sample (first 5 days, first security): {panel.volume.iloc[:5, 0].tolist()}")
```

## 2. Computing Alphas

Let's compute a few example alphas and examine their properties:
```python
# Import the alpha computation functions
from research.notebooks.alpha_001.research.alpha101_formulas import compute_alpha

# Compute Alpha #1 (a classic price reversal signal)
print("\nComputing Alpha #1...")
alpha001 = compute_alpha(panel, "alpha001")
print(f"Alpha #1 computed. Shape: {alpha001.shape}")
print(f"Alpha #1 mean: {alpha001.mean().mean():.6f}")
print(f"Alpha #1 std: {alpha001.std().std():.6f}")

# Compute Alpha #2 (volume-price correlation)
print("\nComputing Alpha #2...")
alpha002 = compute_alpha(panel, "alpha002")
print(f"Alpha #2 computed. Shape: {alpha002.shape}")
print(f"Alpha #2 mean: {alpha002.mean().mean():.6f}")
print(f"Alpha #2 std: {alpha002.std().std():.6f}")

# Compute Alpha #101 (simple open-close range)
print("\nComputing Alpha #101...")
alpha101 = compute_alpha(panel, "alpha101")
print(f"Alpha #101 computed. Shape: {alpha101.shape}")
print(f"Alpha #101 mean: {alpha101.mean().mean():.6f}")
print(f"Alpha #101 std: {alpha101.std().std():.6f}")
```

## 3. Basic Analysis

Let's examine some basic properties of the computed alphas:
```python
import pandas as pd
import numpy as np

# Align returns with alpha (forward returns for analysis)
# Using next period returns
next_returns = panel.returns.shift(-1)  # t+1 returns

# Calculate Information Coefficient (IC) for each alpha
def calculate_ic(alpha, returns):
    """Calculate rank IC between alpha and forward returns"""
    # Stack and align data
    alpha_stack = alpha.stack()
    returns_stack = returns.stack()
    
    # Remove NaNs
    valid = alpha_stack.notna() & returns_stack.notna()
    if valid.sum() < 10:
        return np.nan
    
    # Calculate rank correlation
    from scipy.stats import spearmanr
    ic, _ = spearmanr(alpha_stack[valid], returns_stack[valid])
    return ic

# Calculate IC for each alpha over time (simplified - cross-sectional IC)
print("\nCalculating IC statistics...")
ic_001 = calculate_ic(alpha001, next_returns)
ic_002 = calculate_ic(alpha002, next_returns)
ic_101 = calculate_ic(alpha101, next_returns)

print(f"Alpha #1 IC: {ic_001:.4f}" if not np.isnan(ic_001) else "Alpha #1 IC: insufficient data")
print(f"Alpha #2 IC: {ic_002:.4f}" if not np.isnan(ic_002) else "Alpha #2 IC: insufficient data")
print(f"Alpha #101 IC: {ic_101:.4f}" if not np.isnan(ic_101) else "Alpha #101 IC: insufficient data")

# Show recent values
print("\nRecent values (last 5 days):")
print("Alpha #1 (last 5 days, cross-sectional mean):")
print(alpha001.tail().mean(axis=1))
print("\nAlpha #2 (last 5 days, cross-sectional mean):")
print(alpha002.tail().mean(axis=1))
print("\nAlpha #101 (last 5 days, cross-sectional mean):")
print(alpha101.tail().mean(axis=1))

# Show volatility of the alphas
print("\nAlpha volatilities (annualized):")
annual_factor = np.sqrt(252)  # trading days per year
print(f"Alpha #1 annualized vol: {alpha001.std().mean() * annual_factor:.4f}")
print(f"Alpha #2 annualized vol: {alpha002.std().mean() * annual_factor:.4f}")
print(f"Alpha #101 annualized vol: {alpha101.std().mean() * annual_factor:.4f}")
```

## 4. Saving Results (Optional)

If you want to save your results for later use or sharing:
```python
# Save alpha results to CSV for later use or sharing
output_dir = "research/artifacts/my_alpha_research"
os.makedirs(output_dir, exist_ok=True)

alpha001.to_csv(f"{output_dir}/alpha001.csv")
alpha002.to_csv(f"{output_dir}/alpha002.csv")
alpha101.to_csv(f"{output_dir}/alpha101.csv")

print(f"\nResults saved to {output_dir}/")

# Save metadata about the run
metadata = {
    "universe": panel.name,
    "date_range": [str(panel.open.index[0]), str(panel.open.index[-1])],
    "n_securities": len(panel.open.columns),
    "n_timepoints": len(panel.open.index),
    "alpha001_mean": float(alpha001.mean().mean()),
    "alpha001_std": float(alpha001.std().std()),
    "alpha002_mean": float(alpha002.mean().mean()),
    "alpha002_std": float(alpha002.std().std()),
    "alpha101_mean": float(alpha101.mean().mean()),
    "alpha101_std": float(alpha101.std().std()),
}

import json
with open(f"{output_dir}/metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)

print("Metadata saved.")
```

## 5. Next Steps for Your Research

Now that you have the foundation, you can:
1. Experiment with different alphas from the 101 formulaic set
2. Try different universes (switch "nifty500" to "expanded" in load_panel())
3. Analyze factor returns over different time periods
4. Test combinations of alphas
5. Run more sophisticated backtests using the research framework