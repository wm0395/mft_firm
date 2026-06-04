#!/usr/bin/env python3
"""
Final test that replicates exactly what a user would do in the notebook.
This follows the instructions in ALPHA_NOTEBOOK_FINAL.md exactly.
"""

import os
import sys

def test_complete_notebook():
    print("=== Testing Complete Notebook Workflow ===")
    
    # EXACT STEPS FROM THE NOTEBOOK:
    
    # 1. Set Working Directory to Project Root
    print("1. Setting working directory...")
    os.chdir('/home/wm0395/Investment/mft_project')
    print(f"   ✅ Working directory set to: {os.getcwd()}")
    
    # 2. Add Project Root to Python Path
    print("2. Adding project root to Python path...")
    if os.getcwd() not in sys.path:
        sys.path.insert(0, os.getcwd())
    print("   ✅ Project root added to Python path")
    print(f"   ✅ Python path[0]: {sys.path[0]}")
    
    # 3. Verify Imports Work
    print("3. Verifying imports work...")
    try:
        from research.notebooks.alpha_001.research.alpha101_engine import load_panel
        from research.notebooks.alpha_001.research.alpha101_formulas import compute_alpha
        print("   ✅ Research framework imports successful")
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        print("   💡 This means setup steps 1 or 2 were missed or done incorrectly")
        return False
    
    # 4. LOAD THE DATA
    print("4. Loading the data...")
    try:
        panel = load_panel("nifty500")
        print(f"   📊 Panel loaded: {panel.name}")
        print(f"   📅 Date range: {panel.open.index[0]} to {panel.open.index[-1]}")
        print(f"   📈 Shape: {panel.open.shape}")
        
        # Check data quality
        availability = panel.active_mask.mean().mean() * 100
        print(f"   📊 Average data availability: {availability:.1f}%")
        
    except Exception as e:
        print(f"   ❌ Data loading failed: {e}")
        return False
    
    # 5. COMPUTE ALPHAS
    print("5. Computing alphas...")
    try:
        alpha001 = compute_alpha(panel, "alpha001")
        alpha002 = compute_alpha(panel, "alpha002")
        alpha101 = compute_alpha(panel, "alpha101")
        print(f"   ✅ Alpha #1 computed: {alpha001.shape}")
        print(f"   ✅ Alpha #2 computed: {alpha002.shape}")
        print(f"   ✅ Alpha #101 computed: {alpha101.shape}")
    except Exception as e:
        print(f"   ❌ Alpha computation failed: {e}")
        return False
    
    # 6. BASIC ANALYSIS
    print("6. Performing basic analysis...")
    try:
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

        ic_001 = calculate_ic(alpha001, next_returns)
        ic_002 = calculate_ic(alpha002, next_returns)
        ic_101 = calculate_ic(alpha101, next_returns)
        
        print(f"   📊 Alpha #1 IC: {ic_001:.4f}" if not np.isnan(ic_001) else "   📊 Alpha #1 IC: insufficient data")
        print(f"   📊 Alpha #2 IC: {ic_002:.4f}" if not np.isnan(ic_002) else "   📊 Alpha #2 IC: insufficient data")
        print(f"   📊 Alpha #101 IC: {ic_101:.4f}" if not np.isnan(ic_101) else "   📊 Alpha #101 IC: insufficient data")
        
        # Show recent average values
        print("   📅 Recent average values (last 5 days):")
        print(f"      Alpha #1: {alpha001.tail().mean(axis=1).tolist()}")
        print(f"      Alpha #2: {alpha002.tail().mean(axis=1).tolist()}")
        print(f"      Alpha #101: {alpha101.tail().mean(axis=1).tolist()}")
        
        # Show volatility (annualized)
        annual_factor = np.sqrt(252)
        print("   📊 Annualized volatilities:")
        print(f"      Alpha #1: {alpha001.std().mean() * annual_factor:.4f}")
        print(f"      Alpha #2: {alpha002.std().mean() * annual_factor:.4f}")
        print(f"      Alpha #101: {alpha101.std().mean() * annual_factor:.4f}")
        
    except Exception as e:
        print(f"   ❌ Basic analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 7. SAVE RESULTS (OPTIONAL)
    print("7. Testing results saving (optional)...")
    try:
        # Create directory for saving results
        output_dir = "research/artifacts/my_alpha_research"
        os.makedirs(output_dir, exist_ok=True)
        
        # Save the computed alphas
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
            
        print(f"   ✅ Results saved to {output_dir}/")
        
    except Exception as e:
        print(f"   ❌ Saving results failed: {e}")
        return False
    
    print("\n🎉 ALL STEPS COMPLETED SUCCESSFULLY! 🎉")
    print("✅ Users who follow these exact steps will be able to use the notebook.")
    print("✅ The research framework is working correctly.")
    return True

if __name__ == "__main__":
    success = test_complete_notebook()
    if not success:
        print("\n❌ NOTEBOOK TEST FAILED")
        print("💡 Users will encounter errors if they don't follow the setup steps correctly")
        sys.exit(1)
    else:
        print("\n🎯 NOTEBOOK TEST PASSED")
        print("🎯 The notebook instructions work correctly when followed properly")
