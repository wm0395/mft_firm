# Simple Alpha Research Notebook

This notebook shows how to use the research framework to:
1. Load OHLCV data
2. Compute Alpha101 formulaic alphas
3. Perform basic analysis

## Step 1: Setup and Data Loading

Run this code in your notebook to load the data:
```python
# Change to project directory first (important for relative paths)
import os
os.chdir('/home/wm0395/Investment/mft_project')

# Import the research framework
from research.notebooks.alpha_001.research.alpha101_engine import load_panel
from research.notebooks.alpha_001.research.alpha101_formulas import compute_alpha

# Load the Nifty500 panel (this will be cached)
print("Loading Nifty500 panel...")
panel = load_panel("nifty500")
print(f"Loaded panel: {panel.name}")
print(f"Date range: {panel.open.index[0]} to {panel.open.index[-1]}")
print(f"Shape: {panel.open.shape} ({len(panel.open.columns)} securities, {len(panel.open.index)} time points)")

# Check data quality
active_pct = panel.active_mask.mean().mean() * 100
print(f"Average data availability: {active_pct:.1f}%")
```

## Step 2: Computing Alphas

Compute some example alphas:
```python
# Compute Alpha #1 (price reversal signal)
print("Computing Alpha #1...")
alpha001 = compute_alpha(panel, "alpha001")
print(f"Alpha #1 shape: {alpha001.shape}")
print(f"Alpha #1 mean: {alpha001.mean().mean():.6f}")
print(f"Alpha #1 std: {alpha001.std().std():.6f}")

# Compute Alpha #2 (volume-price correlation)
print("Computing Alpha #2...")
alpha002 = compute_alpha(panel, "alpha002")
print(f"Alpha #2 shape: {alpha002.shape}")
print(f"Alpha #2 mean: {alpha002.mean().mean():.6f}")
print(f"Alpha #2 std: {alpha002.std().std():.6f}")

# Compute Alpha #101 (simple open-close range)
print("Computing Alpha #101...")
alpha101 = compute_alpha(panel, "alpha101")
print(f"Alpha #101 shape: {alpha101.shape}")
print(f"Alpha #101 mean: {alpha101.mean().mean():.6f}")
print(f"Alpha #101 std: {alpha101.std().std():.6f}")
```

## Step 3: Basic Analysis

Analyze the computed alphas:
```python
import pandas as pd
import numpy as np

# Calculate forward returns for analysis
next_returns = panel.returns.shift(-1)  # t+1 returns

def calculate_ic(alpha, returns):
    """Calculate rank Information Coefficient"""
    # Stack data and remove NaNs
    alpha_stack = alpha.stack()
    returns_stack = returns.stack()
    
    # Combine and clean
    combined = pd.concat([alpha_stack, returns_stack], axis=1)
    combined.columns = ['alpha', 'returns']
    combined = combined.dropna()
    
    if len(combined) < 10:
        return np.nan
    
    # Calculate Spearman correlation (rank IC)
    from scipy.stats import spearmanr
    ic, _ = spearmanr(combined['alpha'], combined['returns'])
    return ic

# Calculate IC for each alpha
print("Calculating Information Coefficients...")
ic_001 = calculate_ic(alpha001, next_returns)
ic_002 = calculate_ic(alpha002, next_returns)
ic_101 = calculate_ic(alpha101, next_returns)

print(f"Alpha #1 IC: {ic_001:.4f}" if not np.isnan(ic_001) else "Alpha #1 IC: insufficient data")
print(f"Alpha #2 IC: {ic_002:.4f}" if not np.isnan(ic_002) else "Alpha #2 IC: insufficient data")
print(f"Alpha #101 IC: {ic_101:.4f}" if not np.isnan(ic_101) else "Alpha #101 IC: insufficient data")

# Show recent average values
print("\nRecent average values (last 5 days):")
print("Alpha #1:", alpha001.tail().mean(axis=1).tolist())
print("Alpha #2:", alpha002.tail().mean(axis=1).tolist())
print("Alpha #101:", alpha101.tail().mean(axis=1).tolist())

# Show volatility
annual_factor = np.sqrt(252)
print(f"\nAnnualized volatilities:")
print(f"Alpha #1: {alpha001.std().mean() * annual_factor:.4f}")
print(f"Alpha #2: {alpha002.std().mean() * annual_factor:.4f}")
print(f"Alpha #101: {alpha101.std().mean() * annual_factor:.4f}")
```

## Step 4: Saving Results (Optional)

Save your results for later use:
```python
# Create output directory
output_dir = "research/artifacts/my_alpha_research"
os.makedirs(output_dir, exist_ok=True)

# Save alphas
alpha001.to_csv(f"{output_dir}/alpha001.csv")
alpha002.to_csv(f"{output_dir}/alpha002.csv")
alpha101.to_csv(f"{output_dir}/alpha101.csv")

# Save metadata
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

print(f"Results saved to {output_dir}/")
```

## Important Notes

1. **Directory Matters**: Always run `os.chdir('/home/wm0395/Investment/mft_project')` first or run notebooks from the project root
2. **Data Availability**: The Nifty500 dataset covers 1996-01-01 to 2026-05-22 with ~49% average data availability
3. **Universes Available**: You can also load the "expanded" universe with `load_panel("expanded")`
4. **Alpha List**: There are 101 alphas available (alpha001 through alpha101)
5. **Performance**: The first load takes time (reading CSVs), but subsequent calls are fast due to caching

## Next Steps for Your Research

Now that you have this foundation, you can:
1. Compute and analyze all 101 alphas
2. Test different holding periods (not just t+1 returns)
3. Analyze performance by market regime or volatility
4. Test alpha combinations or factor models
5. Run more sophisticated backtests using the research framework's backtesting tools

The research framework provides many additional tools in `research/notebooks/alpha_001/research/` for:
- Backtesting and performance analysis
- Risk-adjusted returns calculation
- Turnover and cost modeling
- Regime analysis
- And much more