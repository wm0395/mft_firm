#!/usr/bin/env python3
"""
Test the working notebook approach by simulating the exact steps.
"""

import os
import sys

def test_working_approach():
    print("=== Testing Working Notebook Approach ===")
    
    # STEP 1: SETUP - MUST DO THIS FIRST
    print("1. Setting up environment...")
    
    # 1. Set working directory to project root
    os.chdir('/home/wm0395/Investment/mft_project')
    print(f"   📁 Working directory: {os.getcwd()}")
    
    # 2. Add project root to Python path
    if os.getcwd() not in sys.path:
        sys.path.insert(0, os.getcwd())
    print(f"   🔗 Added project root to Python path")
    
    # 3. FIX THE IMPORT ISSUE WITH MONKEY-PATCHING
    print("   🔧 Fixing import issue...")
    
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
        
        # Verify the file exists
        if not os.path.exists(engine_file):
            print(f"   ❌ Engine file not found: {engine_file}")
            return False
            
        # Read and execute the engine file to create the module
        with open(engine_file, 'r') as f:
            engine_code = f.read()
        
        alpha101_engine_module = types.ModuleType('research.alpha101_engine')
        alpha101_engine_module.__file__ = engine_file
        exec(engine_code, alpha101_engine_module.__dict__)
        sys.modules['research.alpha101_engine'] = alpha101_engine_module
        
        print("   ✅ Created research.alpha101_engine module")
    
    # 4. NOW WE CAN IMPORT NORMALLY
    print("   📥 Importing research framework...")
    try:
        from research.notebooks.alpha_001.research.alpha101_engine import load_panel
        from research.notebooks.alpha_001.research.alpha101_formulas import compute_alpha
        print("   ✅ Imports successful!")
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        return False
    
    # ============================================================================
    # STEP 2: LOAD THE DATA
    # ============================================================================
    
    print("\n2. Loading Nifty500 panel...")
    try:
        panel = load_panel("nifty500")
        print(f"   📊 Panel: {panel.name}")
        print(f"   📅 Date range: {panel.open.index[0]} to {panel.open.index[-1]}")
        print(f"   📈 Shape: {panel.open.shape} ({len(panel.open.columns)} securities)")
        
        # Check data quality
        availability = panel.active_mask.mean().mean() * 100
        print(f"   📊 Data availability: {availability:.1f}%")
        
        # Show data sample
        print("   🔍 Data sample (first security, first 5 days):")
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
    
    print("\n3. Computing Alphas...")
    try:
        # Alpha #1: Price reversal signal
        print("   🧮 Computing Alpha #1...")
        alpha001 = compute_alpha(panel, "alpha001")
        print(f"      Shape: {alpha001.shape}")
        print(f"      Mean: {alpha001.mean().mean():.6f}")
        print(f"      Std:  {alpha001.std().std():.6f}")
        
        # Alpha #2: Volume-price correlation
        print("   🧮 Computing Alpha #2...")
        alpha002 = compute_alpha(panel, "alpha002")
        print(f"      Shape: {alpha002.shape}")
        print(f"      Mean: {alpha002.mean().mean():.6f}")
        print(f"      Std:  {alpha002.std().std():.6f}")
        
        # Alpha #101: Simple open-close range
        print("   🧮 Computing Alpha #101...")
        alpha101 = compute_alpha(panel, "alpha101")
        print(f"      Shape: {alpha101.shape}")
        print(f"      Mean: {alpha101.mean().mean():.6f}")
        print(f"      Std:  {alpha101.std().std():.6f}")
        
    except Exception as e:
        print(f"   ❌ Alpha computation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # ============================================================================
    # STEP 4: BASIC ANALYSIS
    # ============================================================================
    
    print("\n4. Performing Basic Analysis...")
    try:
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
        print("   📈 Calculating Information Coefficients...")
        ic_001 = calculate_ic(alpha001, next_returns)
        ic_002 = calculate_ic(alpha002, next_returns)
        ic_101 = calculate_ic(alpha101, next_returns)
        
        print(f"      Alpha #1 IC: {ic_001:.4f}" if not np.isnan(ic_001) else "      Alpha #1 IC: insufficient data")
        print(f"      Alpha #2 IC: {ic_002:.4f}" if not np.isnan(ic_002) else "      Alpha #2 IC: insufficient data")
        print(f"      Alpha #101 IC: {ic_101:.4f}" if not np.isnan(ic_101) else "      Alpha #101 IC: insufficient data")
        
        # Show recent values
        print("   📅 Recent average values (last 5 days):")
        print(f"      Alpha #1: {alpha001.tail().mean(axis=1).tolist()}")
        print(f"      Alpha #2: {alpha002.tail().mean(axis=1).tolist()}")
        print(f"      Alpha #101: {alpha101.tail().mean(axis=1).tolist()}")
        
        # Show volatility (annualized)
        annual_factor = np.sqrt(252)
        print(f"   📊 Annualized volatilities:")
        print(f"      Alpha #1: {alpha001.std().mean() * annual_factor:.4f}")
        print(f"      Alpha #2: {alpha002.std().mean() * annual_factor:.4f}")
        print(f"      Alpha #101: {alpha101.std().mean() * annual_factor:.4f}")
        
    except Exception as e:
        print(f"   ❌ Basic analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # ============================================================================
    # STEP 5: SAVE RESULTS (OPTIONAL)
    # ============================================================================
    
    print("\n5. Testing Results Saving (Optional)...")
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
    print("🎉 SUCCESS! The working notebook approach is functional! 🎉")
    print("="*60)
    print("✅ All steps completed successfully")
    print("✅ Users can now follow the working notebook instructions")
    print("="*60)
    
    return True

if __name__ == "__main__":
    success = test_working_approach()
    if not success:
        print("\n❌ TEST FAILED")
        sys.exit(1)
    else:
        print("\n✅ ALL TESTS PASSED")