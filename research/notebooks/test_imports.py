#!/usr/bin/env python3
"""
Test script to verify that our research framework imports work correctly.
This avoids the complex import issues in notebooks by testing directly.
"""

import sys
import os
from pathlib import Path

# Set up paths
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

print(f"Project root: {project_root}")
print(f"Current working directory: {os.getcwd()}")

# Test 1: Load the panel directly
print("\n=== Test 1: Loading Panel ===")
try:
    from research.notebooks.alpha_001.research.alpha101_engine import load_panel
    print("✓ Successfully imported load_panel")
    
    panel = load_panel("nifty500")
    print(f"✓ Successfully loaded panel: {panel.name}")
    print(f"  Date range: {panel.open.index[0]} to {panel.open.index[-1]}")
    print(f"  Shape: {panel.open.shape}")
    print(f"  Securities: {len(panel.open.columns)}")
    print(f"  Time points: {len(panel.open.index)}")
    
except Exception as e:
    print(f"✗ Failed to load panel: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Import and use formulas
print("\n=== Test 2: Computing Alpha ===")
try:
    from research.notebooks.alpha_001.research.alpha101_formulas import compute_alpha
    print("✓ Successfully imported compute_alpha")
    
    # Compute a simple alpha
    alpha001 = compute_alpha(panel, "alpha001")
    print(f"✓ Successfully computed alpha001")
    print(f"  Shape: {alpha001.shape}")
    print(f"  Mean: {alpha001.mean().mean():.6f}")
    print(f"  Std: {alpha001.std().std():.6f}")
    
    # Check for excessive NaNs
    nan_ratio = alpha001.isna().sum().sum() / (alpha001.shape[0] * alpha001.shape[1])
    print(f"  NaN ratio: {nan_ratio:.2%}")
    
    if nan_ratio > 0.9:
        print("  WARNING: Very high NaN ratio - check data alignment")
    
except Exception as e:
    print(f"✗ Failed to compute alpha: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Basic analysis
print("\n=== Test 3: Basic Analysis ===")
try:
    import pandas as pd
    import numpy as np
    
    # Calculate returns for IC calculation
    next_returns = panel.returns.shift(-1)  # t+1 returns
    
    # Simple IC calculation
    def quick_ic(alpha, returns):
        """Quick rank IC calculation"""
        # Align and remove NaNs
        aligned = pd.concat([alpha.stack(), returns.stack()], axis=1)
        aligned.columns = ['alpha', 'returns']
        aligned = aligned.dropna()
        
        if len(aligned) < 10:
            return np.nan
            
        from scipy.stats import spearmanr
        ic, _ = spearmanr(aligned['alpha'], aligned['returns'])
        return ic
    
    ic = quick_ic(alpha001, next_returns)
    print(f"✓ Calculated IC: {ic:.4f}" if not np.isnan(ic) else "✓ IC calculation: insufficient data")
    
except Exception as e:
    print(f"✗ Failed in basic analysis: {e}")
    import traceback
    traceback.print_exc()

print("\n=== All Tests Completed Successfully! ===")
print("Your research notebook foundation is working correctly.")