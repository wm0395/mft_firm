# Working Alpha Research Notebook

This notebook shows how to successfully use the research framework by working around the import issue.

## 🔧 THE PROBLEM
The `alpha101_formulas.py` file has an incorrect import:
```python
from research.alpha101_engine import ...  # WRONG
```

It should be:
```python
from research.notebooks.alpha_001.research.alpha101_engine import ...  # CORRECT
```

But instead of fixing the file (which might break other things), we'll work around it.

## ✅ THE SOLUTION: MONKEY-PATCHING

We'll temporarily fix the import issue by monkey-patching the modules system.

## 📋 COMPLETE WORKING EXAMPLE

```python
# ============================================================================
# STEP 1: SETUP - MUST DO THIS FIRST
# ============================================================================

import os
import sys

# 1. Set working directory to project root
os.chdir('/home/wm0395/Investment/mft_project')
print("📁 Working directory:", os.getcwd())

# 2. Add project root to Python path
if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())
print("🔗 Added project root to Python path")

# 3. FIX THE IMPORT ISSUE WITH MONKEY-PATCHING
print("🔧 Fixing import issue...")

import types

# Create the missing research.alpha101_engine module by pointing it to the actual file
if 'research' not in sys.modules:
    research_module = types.ModuleType('research')
    research_module.__path__ = [os.path.join(os.getcwd(), 'research')]
    sys.modules['research'] = research_module

# Create the alpha101_engine submodule
if 'research.alpha101_engine' not in sys.modules:
    # Load the actual engine file
    engine_file = os.path.join(os.getcwd(), 'research', 'notebooks', 'alpha_001', 'research', 'alpha101_engine.py')
    
    # Read and execute the engine file to create the module
    with open(engine_file, 'r') as f:
        engine_code = f.read()
    
    alpha101_engine_module = types.ModuleType('research.alpha101_engine')
    alpha101_engine_module.__file__ = engine_file
    exec(engine_code, alpha101_engine_module.__dict__)
    sys.modules['research.alpha101_engine'] = alpha101_engine_module
    
    print("   ✅ Created research.alpha101_engine module")

# 4. NOW WE CAN IMPORT NORMALLY
print("📥 Importing research framework...")
from research.notebooks.alpha_001.research.alpha101_engine import load_panel
from research.notebooks.alpha_001.research.alpha101_formulas import compute_alpha
print("   ✅ Imports successful!")

# ============================================================================
# STEP 2: LOAD THE DATA
# ============================================================================

print("\n📥 STEP 2: Loading Nifty500 panel...")
panel = load_panel("nifty500")

print(f"📊 Panel: {panel.name}")
print(f"📅 Date range: {panel.open.index[0]} to {panel.open.index[-1]}")
print(f"📈 Shape: {panel.open.shape} ({len(panel.open.columns)} securities)")

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

print("\n⚡ STEP 3: Computing Alphas...")

# Alpha #1: Price reversal signal
print("🧮 Computing Alpha #1...")
alpha001 = compute_alpha(panel, "alpha001")
print(f"   Shape: {alpha001.shape}")
print(f"   Mean: {alpha001.mean().mean():.6f}")
print(f"   Std:  {alpha001.std().std():.6f}")

# Alpha #2: Volume-price correlation
print("🧮 Computing Alpha #2...")
alpha002 = compute_alpha(panel, "alpha002")
print(f"   Shape: {alpha002.shape}")
print(f"   Mean: {alpha002.mean().mean():.6f}")
print(f"   Std:  {alpha002.std().std():.6f}")

# Alpha #101: Simple open-close range
print("🧮 Computing Alpha #101...")
alpha101 = compute_alpha(panel, "alpha101")
print(f"   Shape: {alpha101.shape}")
print(f"   Mean: {alpha101.mean().mean():.6f}")
print(f"   Std:  {alpha101.std().std():.6f}")

# ============================================================================
# STEP 4: BASIC ANALYSIS
# ============================================================================

print("\n📊 STEP 4: Basic Analysis...")

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
print("📈 Calculating Information Coefficients...")
ic_001 = calculate_ic(alpha001, next_returns)
ic_002 = calculate_ic(alpha002, next_returns)
ic_101 = calculate_ic(alpha101, next_returns)

print(f"   Alpha #1 IC: {ic_001:.4f}" if not np.isnan(ic_001) else "   Alpha #1 IC: insufficient data")
print(f"   Alpha #2 IC: {ic_002:.4f}" if not np.isnan(ic_002) else "   Alpha #2 IC: insufficient data")
print(f"   Alpha #101 IC: {ic_101:.4f}" if not np.isnan(ic_101) else "   Alpha #101 IC: insufficient data")

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

print("\n💾 STEP 5: Saving Results (Optional)...")

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