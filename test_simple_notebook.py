#!/usr/bin/env python3
"""
Test script that replicates EXACTLY what a user would do in the SIMPLE_WORKING_NOTEBOOK.md
"""

import os
import sys

def test_simple_notebook():
    print("=== Testing Simple Notebook Approach ===")
    
    # STEP 1: Set working directory to project root
    print("1. Setting working directory...")
    os.chdir('/home/wm0395/Investment/mft_project')
    print(f"   📁 Working directory: {os.getcwd()}")
    
    # STEP 2: Configure Python Path
    print("2. Configuring Python path...")
    if os.getcwd() not in sys.path:
        sys.path.insert(0, os.getcwd())
    print("   🔗 Project root added to Python path")
    
    # STEP 3: Import the research framework
    print("3. Importing research framework...")
    try:
        from research.notebooks.alpha_001.research.alpha101_engine import load_panel
        from research.notebooks.alpha_001.research.alpha101_formulas import compute_alpha
        print("   ✅ Research framework imported successfully!")
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        return False
    
    # ============================================================================
    # STEP 2: LOAD THE DATA
    # ============================================================================
    
    print("\n📥 Loading Nifty500 panel...")
    try:
        panel = load_panel("nifty500")
        print(f"   📊 Panel: {panel.name}")
        print(f"   📅 Date range: {panel.open.index[0]} to {panel.open.index[-1]}")
        print(f"   📈 Shape: {panel.open.shape}")
        
        # Check data quality
        availability = panel.active_mask.mean().mean() * 100
        print(f"   📊 Data availability: {availability:.1f}%")
        
        # Show data sample
        print("\n   🔍 Data sample (first security, first 5 days):")
        print(f"      Open:  {panel.open.iloc[:5, 0].tolist()}")
        print(f"      Volume:{panel.volume.iloc[:5, 0].tolist()}")
        
    except Exception as e:
        print(f"   ❌ Panel loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # ============================================================================
    # STEP 3: COMPUTE ALPHAS
    # ============================================================================
    
    print("\n⚡ Computing Alphas...")
    
    try:
        # Compute Alpha #1 (price reversal signal)
        alpha001 = compute_alpha(panel, "alpha001")
        print(f"   🧮 Alpha #1: {alpha001.shape} | Mean: {alpha001.mean().mean():.6f} | Std: {alpha001.std().std():.6f}")
        
        # Compute Alpha #2 (volume-price correlation)
        alpha002 = compute_alpha(panel, "alpha002")
        print(f"   🧮 Alpha #2: {alpha002.shape} | Mean: {alpha002.mean().mean():.6f} | Std: {alpha002.std().std():.6f}")
        
        # Compute Alpha #101 (simple open-close range)
        alpha101 = compute_alpha(panel, "alpha101")
        print(f"   🧮 Alpha #101: {alpha101.shape} | Mean: {alpha101.mean().mean():.6f} | Std: {alpha101.std().std():.6f}")
        
    except Exception as e:
        print(f"   ❌ Alpha computation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # ============================================================================
    # STEP 4: BASIC ANALYSIS
    # ============================================================================
    
    print("\n📊 Performing basic analysis...")
    
    try:
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
        
        print(f"   📈 Alpha #1 IC: {ic_001:.4f}" if not np.isnan(ic_001) else "   📈 Alpha #1 IC: insufficient data")
        print(f"   📈 Alpha #2 IC: {ic_002:.4f}" if not np.isnan(ic_002) else "   📈 Alpha #2 IC: insufficient data")
        print(f"   📈 Alpha #101 IC: {ic_101:.4f}" if not np.isnan(ic_101) else "   📈 Alpha #101 IC: insufficient data")
        
        # Show recent values
        print("\n   📅 Recent average values (last 5 days):")
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
        print(f"   �Basic analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # ============================================================================
    # STEP 5: SAVE RESULTS (OPTIONAL)
    # ============================================================================
    
    print("\n💾 Saving results (optional)...")
    
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
            
        print(f"   💾 Results saved to {output_dir}/")
        
    except Exception as e:
        print(f"   ❌ Saving results failed: {e}")
        return False
    
    print("\n" + "="*60)
    print("🎉 SUCCESS! The simple notebook approach works! 🎉")
    print("="*60)
    print("✅ All steps completed successfully")
    print("✅ Users can now follow the simple notebook instructions")
    print("="*60)
    
    return True

if __name__ == "__main__":
    success = test_simple_notebook()
    if not success:
        print("\n❌ TEST FAILED")
        sys.exit(1)
    else:
        print("\n✅ ALL TESTS PASSED")
