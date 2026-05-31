# Working Alpha Research Notebook

This notebook demonstrates how to successfully use the research framework to load data and compute alphas.

## IMPORTANT: Setup Instructions

**You MUST run these steps in order for the notebook to work:**

### Step 1: Set Working Directory
```python
# THIS IS CRITICAL - you must be in the project root
import os
os.chdir('/home/wm0395/Investment/mft_project')
print("Working directory:", os.getcwd())
```

### Step 2: Configure Python Path
```python
# Add the project root to Python path so 'research' module can be found
import sys
if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())
print("Python path configured")
```

## Step 3: Load Data and Compute Alphas

Now you can run the research code:
```python
# Import the research framework
from research.notebooks.alpha_001.research.alpha101_engine import load_panel
from research.notebooks.alpha_001.research.alpha101_formulas import compute_alpha

# Load the Nifty500 panel
print("Loading Nifty500 panel...")
panel = load_panel("nifty500")
print(f"✓ Loaded panel: {panel.name}")
print(f"✓ Date range: {panel.open.index[0]} to {panel.open.index[-1]}")
print(f"✓ Shape: {panel.open.shape}")

# Check data availability
active_pct = panel.active_mask.mean().mean() * 100
print(f"✓ Average data availability: {active_pct:.1f}%")

# Compute Alpha #1 (price reversal signal)
print("\nComputing Alpha #1...")
alpha001 = compute_alpha(panel, "alpha001")
print(f"✓ Alpha #1 computed. Shape: {alpha001.shape}")
print(f"✓ Alpha #1 mean: {alpha001.mean().mean():.6f}")
print(f"✓ Alpha #1 std: {alpha001.std().std():.6f}")

# Compute Alpha #2 (volume-price correlation)
print("\nComputing Alpha #2...")
alpha002 = compute_alpha(panel, "alpha002")
print(f"✓ Alpha #2 computed. Shape: {alpha002.shape}")
print(f"✓ Alpha #2 mean: {alpha002.mean().mean():.6f}")
print(f"✓ Alpha #2 std: {alpha002.std().std():.6f}")

# Compute Alpha #101 (simple open-close range)
print("\nComputing Alpha #101...")
alpha101 = compute_alpha(panel, "alpha101")
print(f"✓ Alpha #101 computed. Shape: {alpha101.shape}")
print(f"✓ Alpha #101 mean: {alpha101.mean().mean():.6f}")
print(f"✓ Alpha #101 std: {alpha101.std().std():.6f}")
```

## Step 4: Basic Analysis

Perform basic analysis on the computed alphas:
```python
import pandas as pd
import numpy as np

# Calculate forward returns for analysis (t+1)
next_returns = panel.returns.shift(-1)

def calculate_ic(alpha, returns):
    """Calculate rank Information Coefficient between alpha and forward returns"""
    # Stack and align data
    alpha_stack = alpha.stack()
    returns_stack = returns.stack()
    
    # Remove NaNs
    valid = alpha_stack.notna() & returns_stack.notna()
    if valid.sum() < 10:
        return np.nan
    
    # Calculate rank correlation (Spearman's rho)
    from scipy.stats import spearmanr
    ic, _ = spearmanr(alpha_stack[valid], returns_stack[valid])
    return ic

# Calculate IC for each alpha
print("\nCalculating Information Coefficients...")
ic_001 = calculate_ic(alpha001, next_returns)
ic_002 = calculate_ic(alpha002, next_returns)
ic_101 = calculate_ic(alpha101, next_returns)

print(f"Alpha #1 IC: {ic_001:.4f}" if not np.isnan(ic_001) else "Alpha #1 IC: insufficient data")
print(f"Alpha #2 IC: {ic_002:.4f}" if not np.isnan(ic_002) else "Alpha #2 IC: insufficient data")
print(f"Alpha #101 IC: {ic_101:.4f}" if not np.isnan(ic_101) else "Alpha #101 IC: insufficient data")

# Show recent values
print("\nRecent average values (last 5 days):")
print("Alpha #1:", alpha001.tail().mean(axis=1).tolist())
print("Alpha #2:", alpha002.tail().mean(axis=1).tolist())
print("Alpha #101:", alpha101.tail().mean(axis=1).tolist())

# Show volatility (annualized)
annual_factor = np.sqrt(252)  # trading days per year
print(f"\nAnnualized volatilities:")
print(f"Alpha #1: {alpha001.std().mean() * annual_factor:.4f}")
print(f"Alpha #2: {alpha002.std().mean() * annual_factor:.4f}")
print(f"Alpha #101: {alpha101.std().mean() * annual_factor:.4f}")
```

## Step 5: Save Results (Optional)

Save your results for later use:
```python
# Create output directory
output_dir = "research/artifacts/my_alpha_research"
os.makedirs(output_dir, exist_ok=True)

# Save alpha results
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

## Key Points to Remember

1. **Working Directory**: You MUST be in `/home/wm0395/Investment/mft_project` or run `os.chdir('/home/wm0395/Investment/mft_project')` first
2. **Python Path**: The project root (`/home/wm0395/Investment/mft_project`) must be in your Python path
3. **Import Paths**: Use the full path: `research.notebooks.alpha_001.research.alpha101_engine` and `research.notebooks.alpha_001.research.alpha101_formulas`
4. **Caching**: The `load_panel()` function uses caching, so the first call will be slow (reading CSV files), but subsequent calls will be fast
5. **Universes Available**: You can load either `"nifty500"` or `"expanded"` universes
6. **Alpha Range**: Alphas are available from `alpha001` to `alpha101`

## Troubleshooting

If you get `ModuleNotFoundError: No module named 'research'`:
- You forgot to set the working directory or add the project root to Python path
- Solution: Run `os.chdir('/home/wm0395/Investment/mft_project')` and `sys.path.insert(0, os.getcwd())`

If you get `FileNotFoundError` for CSV files:
- You're not in the project root directory
- Solution: Change to `/home/wm0395/Investment/mft_project` first

## Next Steps for Your Research

Now that you have this foundation working, you can:
1. Compute and analyze all 101 alphas to find the best performers
2. Test different holding periods (not just t+1 returns)
3. Analyze performance by market regime, volatility, or sector
4. Test alpha combinations or create factor models
5. Run more sophisticated backtests using the research framework's backtesting tools
6. Explore the expanded universe for more investment opportunities
7. Use the additional research tools in `research/notebooks/alpha_001/research/` for:
   - Backtesting and performance analysis
   - Risk-adjusted returns calculation
   - Turnover and cost modeling
   - Regime analysis
   - And much more

The research framework is now ready for your alpha discovery and analysis work!