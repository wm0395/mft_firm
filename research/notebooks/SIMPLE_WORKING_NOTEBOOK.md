# Simple Working Alpha Research Notebook

This notebook shows the EXACT steps users need to follow to successfully use the research framework.

## 🚫 THE PROBLEM
If you just try to run the imports directly, you'll get:
```
ModuleNotFoundError: No module named 'research.alpha101_engine'
```

## ✅ THE SOLUTION: 3 SETUP STEPS
You MUST do these steps FIRST, in order:

### STEP 1: Set Working Directory
```python
# THIS IS REQUIRED - you must be in the project root
import os
os.chdir('/home/wm0395/Investment/mft_project')  # ← CHANGE THIS IF NEEDED
print("Working directory:", os.getcwd())
```

### STEP 2: Configure Python Path
```python
# Add project root to Python path so modules can be found
import sys
if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())
print("Project root added to Python path")
```

### STEP 3: Import with Correct Path
```python
# NOW you can import using the FULL path
from research.notebooks.alpha_001.research.alpha101_engine import load_panel
from research.notebooks.alpha_001.research.alpha101_formulas import compute_alpha
print("Imports successful!")
```

## 📋 COMPLETE WORKING EXAMPLE

Copy and paste this entire block into your notebook:

```python
# ============================================================================
# REQUIRED SETUP STEPS - DO NOT SKIP
# ============================================================================

import os
import sys

# Step 1: Set working directory to project root
os.chdir('/home/wm0395/Investment/mft_project')
print("📁 Working directory:", os.getcwd())

# Step 2: Add project root to Python path
if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())
print("🔗 Project root added to Python path")

# Step 3: Import the research framework
from research.notebooks.alpha_001.research.alpha101_engine import load_panel
from research.notebooks.alpha_001.research.alpha101_formulas import compute_alpha
print("✅ Research framework imported successfully!")

# ============================================================================
# STEP 2: LOAD THE DATA
# ============================================================================

print("\n📥 Loading Nifty500 panel...")
panel = load_panel("nifty500")

print(f"📊 Panel: {panel.name}")
print(f"📅 Date range: {panel.open.index[0]} to {panel.open.index[-1]}")
print(f"📈 Shape: {panel.open.shape}")

# Check data quality
availability = panel.active_mask.mean().mean() * 100
print(f"📊 Data availability: {availability:.1f}%")

# Show data sample
print("\n🔍 Data sample (first security, first 5 days):")
print(f"   Open:  {panel.open.iloc[:5, 0].tolist()}")
print(f"   Volume:{panel.volume.iloc[:5, 0].tolist()}")

# ============================================================================
# STEP 3: COMPUTE ALPHAS
# ============================================================================

print("\n⚡ Computing Alphas...")

# Compute Alpha #1 (price reversal signal)
alpha001 = compute_alpha(panel, "alpha001")
print(f"🧮 Alpha #1: {alpha001.shape} | Mean: {alpha001.mean().mean():.6f} | Std: {alpha001.std().std():.6f}")

# Compute Alpha #2 (volume-price correlation)
alpha002 = compute_alpha(panel, "alpha002")
print(f"🧮 Alpha #2: {alpha002.shape} | Mean: {alpha002.mean().mean():.6f} | Std: {alpha002.std().std():.6f}")

# Compute Alpha #101 (simple open-close range)
alpha101 = compute_alpha(panel, "alpha101")
print(f"🧮 Alpha #101: {alpha101.shape} | Mean: {alpha101.mean().mean():.6f} | Std: {alpha101.std().std():.6f}")

# ============================================================================
# STEP 4: BASIC ANALYSIS
# ============================================================================

print("\n📊 Performing basic analysis...")

import pandas as pd
import numpy as np

# Calculate forward returns (next day)
next_returns = panel.returns.shift(-1)  # t+1 returns

def calculate_ic(alpha, returns):
    """Calculate rank Information Coefficient"""
    # Stack data
    alpha_stack = alpha.stack()
    returns_stack = returns.stack()
    
    # Remove NaNs
    valid = alpha_stack.notna() & returns_stack.notna()
    if valid.sum() < 10:
        return np.nan
    
    # Calculate Spearman correlation
    from scipy.stats import spearmanr
    ic, _ = spearmanr(alpha_stack[valid], returns_stack[valid])
    return ic

# Calculate ICs
ic_001 = calculate_ic(alpha001, next_returns)
ic_002 = calculate_ic(alpha002, next_returns)
ic_101 = calculate_ic(alpha101, next_returns)

print(f"📈 Alpha #1 IC: {ic_001:.4f}" if not np.isnan(ic_001) else "📈 Alpha #1 IC: insufficient data")
print(f"📈 Alpha #2 IC: {ic_002:.4f}" if not np.isnan(ic_002) else "📈 Alpha #2 IC: insufficient data")
print(f"📈 Alpha #101 IC: {ic_101:.4f}" if not np.isnan(ic_101) else "📈 Alpha #101 IC: insufficient data")

# Show recent values
print("\n📅 Recent average values (last 5 days):")
print(f"   Alpha #1: {alpha001.tail().mean(axis=1).tolist()}")
print(f"   Alpha #2: {alpha002.tail().mean(axis=1).tolist()}")
print(f"   Alpha #101: {alpha101.tail().mean(axis=1).tolist()}")

# Show volatility (annualized)
annual_factor = np.sqrt(252)
print(f"\n📊 Annualized volatilities:")
print(f"   Alpha #1: {alpha001.std().mean() * annual_factor:.4f}")
print(f"   Alpha #2: {alpha002.std().mean() * annual_factor:.4f}")
print(f"   Alpha #101: {alpha101.std().mean() * annual_factor:.4f}")

# ============================================================================
# STEP 5: SAVE RESULTS (OPTIONAL)
# ============================================================================

print("\n💾 Saving results (optional)...")

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

print(f"   💾 Results saved to {output_dir}/")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*60)
print("🎉 SUCCESS! Your research notebook is working! 🎉")
print("="*60)
print("✅ Data loaded: Nifty500 universe (~500 securities)")
print("✅ Alphas computed: #001, #002, #101")
print("✅ Analysis completed: IC, volatility, recent values")
print("✅ Results saved: research/artifacts/my_alpha_research/")
print("="*60)
print("📝 NEXT STEPS:")
print("   1. Try different alphas (alpha003 through alpha101)")
print("   2. Test the expanded universe: load_panel('expanded')")
print("   3. Analyze different holding periods (not just t+1)")
print("   4. Explore the research framework tools in:")
print("      research/notebooks/alpha_001/research/")
print("   5. Run sophisticated backtests and performance analysis")
print("="*60)
```

## ⚠️ IMPORTANT REMINDERS

1. **You MUST run the 3 setup steps FIRST** - otherwise you'll get import errors
2. **The working directory must be `/home/wm0395/Investment/mft_project`** (or wherever you cloned the project)
3. **First run will be slower** - it needs to read data from CSV files (~10-30 seconds)
4. **Subsequent runs will be fast** - due to caching in the `load_panel()` function
5. **You can compute ANY alpha** from `alpha001` to `alpha101` by changing the parameter

## 🛠️ TROUBLESHOOTING

**If you get `ModuleNotFoundError: No module named 'research.alpha101_engine'`:**
- You forgot to run the setup steps (Steps 1-3 above)
- Go back and run them in order

**If you get `FileNotFoundError` for CSV files:**
- You're not in the project root directory
- Run `os.chdir('/home/wm0395/Investment/mft_project')` first

**If you get dataclass errors:**
- This is a known issue with the research framework when imported incorrectly
- Following the 3 setup steps above will prevent this

## 🎯 YOU'RE READY TO RESEARCH!

Once you've successfully run the setup steps and the code above, you have a fully functional research environment for:
- Discovering and analyzing alpha signals
- Backtesting trading strategies
- Performing statistical analysis on financial data
- Developing and testing investment ideas

Happy researching! 🚀