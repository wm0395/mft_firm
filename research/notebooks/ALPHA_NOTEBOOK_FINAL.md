# Alpha Research Notebook - FINAL WORKING VERSION

This notebook demonstrates how to successfully load data and compute alphas using the research framework.

## 🔑 KEY TO SUCCESS: SETUP STEPS

You MUST execute these setup steps FIRST, in order:

### 1. Set Working Directory to Project Root
```python
# CHANGE THIS TO YOUR ACTUAL PROJECT PATH IF DIFFERENT
import os
os.chdir('/home/wm0395/Investment/mft_project')
print("✅ Working directory set to:", os.getcwd())
```

### 2. Add Project Root to Python Path
```python
import sys
if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())
print("✅ Project root added to Python path")
```

### 3. Verify Imports Work
```python
# Test that we can import the research framework
try:
    from research.notebooks.alpha_001.research.alpha101_engine import load_panel
    from research.notebooks.alpha_001.research.alpha101_formulas import compute_alpha
    print("✅ Research framework imports successful")
except Exception as e:
    print("❌ Import failed:", e)
    print("💡 Make sure you completed steps 1 and 2 above!")
    raise
```

## 📊 STEP 1: LOAD THE DATA

```python
# Load the Nifty500 universe panel (this loads and caches the data)
print("📥 Loading Nifty500 panel...")
panel = load_panel("nifty500")

print(f"📊 Panel loaded: {panel.name}")
print(f"📅 Date range: {panel.open.index[0]} to {panel.open.index[-1]}")
print(f"📈 Shape: {panel.open.shape} ({len(panel.open.columns)} securities × {len(panel.open.index)} days)")

# Check data quality
availability = panel.active_mask.mean().mean() * 100
print(f"📊 Average data availability: {availability:.1f}%")

# Show a quick data sample
print("\n🔍 Data sample (first security, first 5 days):")
print(f"   Open prices:  {panel.open.iloc[:5, 0].tolist()}")
print(f"   Volume:       {panel.volume.iloc[:5, 0].tolist()}")
```

## ⚡ STEP 2: COMPUTE ALPHAS

```python
# Import the alpha computation functions
from research.notebooks.alpha_001.research.alpha101_formulas import compute_alpha

print("\n🧮 Computing Alpha #1 (price reversal signal)...")
alpha001 = compute_alpha(panel, "alpha001")
print(f"   Shape: {alpha001.shape}")
print(f"   Mean: {alpha001.mean().mean():.6f}")
print(f"   Std:  {alpha001.std().std():.6f}")

print("\n🧮 Computing Alpha #2 (volume-price correlation)...")
alpha002 = compute_alpha(panel, "alpha002")
print(f"   Shape: {alpha002.shape}")
print(f"   Mean: {alpha002.mean().mean():.6f}")
print(f"   Std:  {alpha002.std().std():.6f}")

print("\n🧮 Computing Alpha #101 (simple open-close range)...")
alpha101 = compute_alpha(panel, "alpha101")
print(f"   Shape: {alpha101.shape}")
print(f"   Mean: {alpha101.mean().mean():.6f}")
print(f"   Std:  {alpha101.std().std():.6f}")
```

## 📈 STEP 3: BASIC ANALYSIS

```python
import pandas as pd
import numpy as np

# Calculate forward returns for analysis (next day returns)
next_returns = panel.returns.shift(-1)  # t+1 returns

def calculate_ic(alpha, returns):
    """Calculate rank Information Coefficient between alpha and forward returns"""
    # Stack the data to work with all securities and dates at once
    alpha_stack = alpha.stack()
    returns_stack = returns.stack()
    
    # Keep only rows where both alpha and returns are valid (not NaN)
    valid_mask = alpha_stack.notna() & returns_stack.notna()
    
    if valid_mask.sum() < 10:  # Need minimum observations for correlation
        return np.nan
    
    # Extract valid data
    alpha_valid = alpha_stack[valid_mask]
    returns_valid = returns_stack[valid_mask]
    
    # Calculate Spearman's rank correlation (this is the Information Coefficient)
    from scipy.stats import spearmanr
    ic, p_value = spearmanr(alpha_valid, returns_valid)
    return ic

print("\n📊 Calculating Information Coefficients (IC)...")
ic_001 = calculate_ic(alpha001, next_returns)
ic_002 = calculate_ic(alpha002, next_returns)
ic_101 = calculate_ic(alpha101, next_returns)

print(f"   Alpha #1 IC: {ic_001:.4f}" if not np.isnan(ic_001) else "   Alpha #1 IC: insufficient data")
print(f"   Alpha #2 IC: {ic_002:.4f}" if not np.isnan(ic_002) else "   Alpha #2 IC: insufficient data")
print(f"   Alpha #101 IC: {ic_101:.4f}" if not np.isnan(ic_101) else "   Alpha #101 IC: insufficient data")

# Show recent average values (cross-sectional average for each day)
print("\n📅 Recent average values (last 5 days):")
print("   Alpha #1:", alpha001.tail().mean(axis=1).tolist())
print("   Alpha #2:", alpha002.tail().mean(axis=1).tolist())
print("   Alpha #101:", alpha101.tail().mean(axis=1).tolist())

# Show volatility (annualized)
annual_factor = np.sqrt(252)  # Approximately 252 trading days per year
print("\n📊 Annualized volatilities:")
print(f"   Alpha #1: {alpha001.std().mean() * annual_factor:.4f}")
print(f"   Alpha #2: {alpha002.std().mean() * annual_factor:.4f}")
print(f"   Alpha #101: {alpha101.std().mean() * annual_factor:.4f}")
```

## 💾 STEP 4: SAVE RESULTS (OPTIONAL)

```python
# Create directory for saving results
output_dir = "research/artifacts/my_alpha_research"
os.makedirs(output_dir, exist_ok=True)

# Save the computed alphas
print(f"\n💾 Saving results to {output_dir}/...")
alpha001.to_csv(f"{output_dir}/alpha001.csv")
alpha002.to_csv(f"{output_dir}/alpha002.csv")
alpha101.to_csv(f"{output_dir}/alpha101.csv")

# Save metadata about this research session
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

print("✅ Results saved successfully!")
```

## 📝 IMPORTANT NOTES

### 📁 Directory Structure
- Your notebook should be in: `/home/wm0395/Investment/mft_project/research/notebooks/`
- The project root is: `/home/wm0395/Investment/mft_project/`
- Data is loaded from: `/home/wm0395/Investment/mft_project/research/data/`

### 🔄 Performance
- **First run**: Will be slower as it reads data from CSV files (~10-30 seconds)
- **Subsequent runs**: Will be much faster due to caching in `load_panel()`

### 🌍 Available Universes
- `load_panel("nifty500")` - ~500 securities from Nifty500 index
- `load_panel("expanded")` - Expanded universe (more securities)

### 🔢 Available Alphas
- Alpha IDs: `alpha001` through `alpha101` (101 total)
- You can compute any alpha by calling `compute_alpha(panel, "alphaXXX")`

### 🛠️ Troubleshooting

**If you get `ModuleNotFoundError: No module named 'research'`:**
1. You forgot to set the working directory: `os.chdir('/home/wm0395/Investment/mft_project')`
2. You forgot to add project root to Python path: `sys.path.insert(0, os.getcwd())`

**If you get `FileNotFoundError` for CSV files:**
- You're not in the project root directory
- Fix: Run `os.chdir('/home/wm0395/Investment/mft_project')` first

### 🚀 Next Steps for Your Research

Now that you have this foundation working, you can:

1. **Explore all 101 alphas**: Compute and analyze them to find the best performers
2. **Test different holding periods**: Instead of just t+1 returns, try t+5, t+21, etc.
3. **Analyze by market regimes**: Split data by volatility, trend, or economic conditions
4. **Test alpha combinations**: Create factor models or weighted combinations
5. **Run sophisticated backtests**: Use the research framework's backtesting tools
6. **Explore the expanded universe**: See if you find better opportunities there
7. **Use additional research tools**: Check `research/notebooks/alpha_001/research/` for:
   - Backtesting and performance analysis functions
   - Risk-adjusted returns calculation (Sharpe, Sortino, etc.)
   - Turnover and cost modeling
   - Regime analysis tools
   - And much more

## 🎉 YOU'RE READY TO RESEARCH!

The research framework is now properly set up and ready for your alpha discovery and analysis work. Happy researching!