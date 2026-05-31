#!/usr/bin/env python3
"""
Test that replicates the exact steps a user would follow in the notebook.
"""

import os
import sys

def test_notebook_steps():
    print("=== Testing Notebook Steps ===")
    
    # Step 1: Set Working Directory (as users must do)
    print("1. Setting working directory...")
    os.chdir('/home/wm0395/Investment/mft_project')
    print(f"   Current directory: {os.getcwd()}")
    
    # Step 2: Configure Python Path (as users must do)
    print("2. Configuring Python path...")
    if os.getcwd() not in sys.path:
        sys.path.insert(0, os.getcwd())
    print(f"   Added {os.getcwd()} to Python path")
    print(f"   Python path[0]: {sys.path[0]}")
    
    # Step 3: Import and use the research framework
    print("3. Importing research framework...")
    try:
        from research.notebooks.alpha_001.research.alpha101_engine import load_panel
        from research.notebooks.alpha_001.research.alpha101_formulas import compute_alpha
        print("   ✓ Successfully imported research framework")
    except Exception as e:
        print(f"   ✗ Import failed: {e}")
        print("   This is the key error users will see if they skip setup steps")
        return False
    
    # Step 4: Load data
    print("4. Loading Nifty500 panel...")
    try:
        panel = load_panel("nifty500")
        print(f"   ✓ Loaded panel: {panel.name}")
        print(f"   ✓ Date range: {panel.open.index[0]} to {panel.open.index[-1]}")
        print(f"   ✓ Shape: {panel.open.shape}")
    except Exception as e:
        print(f"   ✗ Panel loading failed: {e}")
        return False
    
    # Step 5: Check data quality
    print("5. Checking data quality...")
    try:
        active_pct = panel.active_mask.mean().mean() * 100
        print(f"   ✓ Average data availability: {active_pct:.1f}%")
    except Exception as e:
        print(f"   ✗ Data quality check failed: {e}")
        return False
    
    # Step 6: Compute alphas
    print("6. Computing alphas...")
    try:
        alpha001 = compute_alpha(panel, "alpha001")
        alpha002 = compute_alpha(panel, "alpha002")
        alpha101 = compute_alpha(panel, "alpha101")
        print(f"   ✓ Alpha #1 computed: {alpha001.shape}")
        print(f"   ✓ Alpha #2 computed: {alpha002.shape}")
        print(f"   ✓ Alpha #101 computed: {alpha101.shape}")
    except Exception as e:
        print(f"   ✗ Alpha computation failed: {e}")
        return False
    
    # Step 7: Basic validation
    print("7. Basic validation...")
    try:
        # Check that we got reasonable results
        assert alpha001.shape == panel.open.shape, "Alpha shape mismatch"
        assert not alpha001.isna().all().all(), "All alpha values are NaN"
        print(f"   ✓ Alpha #1 mean: {alpha001.mean().mean():.6f}")
        print(f"   ✓ Alpha #1 std: {alpha001.std().std():.6f}")
        
        # Show a sample of recent data
        print(f"   ✓ Recent Alpha #1 values (last 3 days):")
        recent_vals = alpha001.tail(3).mean(axis=1)
        for i, val in enumerate(recent_vals):
            print(f"     Day {-len(recent_vals)+i+1}: {val:.6f}")
            
    except Exception as e:
        print(f"   ✗ Validation failed: {e}")
        return False
    
    print("\n=== ALL STEPS COMPLETED SUCCESSFULLY! ===")
    print("Users who follow these exact steps will be able to use the notebook.")
    return True

if __name__ == "__main__":
    success = test_notebook_steps()
    if not success:
        print("\nNOTEBOOK TEST FAILED - Users will encounter errors if they don't follow setup steps correctly")
        sys.exit(1)
    else:
        print("\nNOTEBOOK TEST PASSED - The notebook instructions work correctly when followed properly")