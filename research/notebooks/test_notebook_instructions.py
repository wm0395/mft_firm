#!/usr/bin/env python3
"""
Test script that follows the exact instructions from the simple notebook.
This verifies that users can successfully follow the notebook guide.
"""

import os
import sys

def test_notebook_workflow():
    print("=== Testing Notebook Workflow ===")
    
    # Step 1: Change to project directory (as instructed)
    print("1. Changing to project directory...")
    os.chdir('/home/wm0395/Investment/mft_project')
    print(f"   Current directory: {os.getcwd()}")
    
    # CRITICAL: Add current directory to Python path so 'research' module can be found
    # This is what users need to do when running from notebooks or other directories
    if os.getcwd() not in sys.path:
        sys.path.insert(0, os.getcwd())
    print(f"   Added {os.getcwd()} to Python path")
    
    # Step 2: Import the research framework (as instructed)
    print("2. Importing research framework...")
    try:
        from research.notebooks.alpha_001.research.alpha101_engine import load_panel
        from research.notebooks.alpha_001.research.alpha101_formulas import compute_alpha
        print("   ✓ Successfully imported")
    except Exception as e:
        print(f"   ✗ Import failed: {e}")
        return False
    
    # Step 3: Load the Nifty500 panel (as instructed)
    print("3. Loading Nifty500 panel...")
    try:
        panel = load_panel("nifty500")
        print(f"   ✓ Loaded panel: {panel.name}")
        print(f"   ✓ Date range: {panel.open.index[0]} to {panel.open.index[-1]}")
        print(f"   ✓ Shape: {panel.open.shape}")
    except Exception as e:
        print(f"   ✗ Panel loading failed: {e}")
        return False
        
    # Step 4: Check data quality (as instructed)
    print("4. Checking data quality...")
    try:
        active_pct = panel.active_mask.mean().mean() * 100
        print(f"   ✓ Average data availability: {active_pct:.1f}%")
    except Exception as e:
        print(f"   ✗ Data quality check failed: {e}")
        return False
    
    # Step 5: Computing Alphas (as instructed)
    print("5. Computing Alphas...")
    try:
        # Alpha #1
        alpha001 = compute_alpha(panel, "alpha001")
        print(f"   ✓ Alpha #1 computed: {alpha001.shape}")
        print(f"   ✓ Alpha #1 mean: {alpha001.mean().mean():.6f}")
        
        # Alpha #2
        alpha002 = compute_alpha(panel, "alpha002")
        print(f"   ✓ Alpha #2 computed: {alpha002.shape}")
        print(f"   ✓ Alpha #2 mean: {alpha002.mean().mean():.6f}")
        
        # Alpha #101
        alpha101 = compute_alpha(panel, "alpha101")
        print(f"   ✓ Alpha #101 computed: {alpha101.shape}")
        print(f"   ✓ Alpha #101 mean: {alpha101.mean().mean():.6f}")
        
    except Exception as e:
        print(f"   ✗ Alpha computation failed: {e}")
        return False
    
    # Step 6: Basic Analysis (as instructed)
    print("6. Performing Basic Analysis...")
    try:
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
        ic_001 = calculate_ic(alpha001, next_returns)
        ic_002 = calculate_ic(alpha002, next_returns)
        ic_101 = calculate_ic(alpha101, next_returns)
        
        print(f"   ✓ Alpha #1 IC: {ic_001:.4f}" if not np.isnan(ic_001) else "   ✓ Alpha #1 IC: insufficient data")
        print(f"   ✓ Alpha #2 IC: {ic_002:.4f}" if not np.isnan(ic_002) else "   ✓ Alpha #2 IC: insufficient data")
        print(f"   ✓ Alpha #101 IC: {ic_101:.4f}" if not np.isnan(ic_101) else "   ✓ Alpha #101 IC: insufficient data")
        
        # Show recent average values
        print("   ✓ Recent average values (last 5 days):")
        print(f"     Alpha #1: {alpha001.tail().mean(axis=1).tolist()[:3]}...")  # First 3 values
        print(f"     Alpha #2: {alpha002.tail().mean(axis=1).tolist()[:3]}...")
        print(f"     Alpha #101: {alpha101.tail().mean(axis=1).tolist()[:3]}...")
        
        # Show volatility
        annual_factor = np.sqrt(252)
        print(f"   ✓ Annualized volatilities:")
        print(f"     Alpha #1: {alpha001.std().mean() * annual_factor:.4f}")
        print(f"     Alpha #2: {alpha002.std().mean() * annual_factor:.4f}")
        print(f"     Alpha #101: {alpha101.std().mean() * annual_factor:.4f}")
        
    except Exception as e:
        print(f"   ✗ Basic analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 7: Saving Results (Optional - as instructed)
    print("7. Testing Results Saving (Optional)...")
    try:
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
            
        print(f"   ✓ Results saved to {output_dir}/")
        
    except Exception as e:
        print(f"   ✗ Saving results failed: {e}")
        return False
    
    print("\n=== ALL TESTS PASSED! ===")
    print("Users can successfully follow the notebook instructions.")
    return True

if __name__ == "__main__":
    success = test_notebook_workflow()
    if not success:
        sys.exit(1)