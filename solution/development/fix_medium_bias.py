#!/usr/bin/env python3
"""
Quick Parameter Adjuster - Fix the MEDIUM tire bias

Based on batch diagnostic showing 80% MEDIUM predictions vs 20% expected
"""

import json
from pathlib import Path

def main():
    params_file = Path("solution2/params.json")
    
    # Load current params
    with open(params_file, 'r') as f:
        params = json.load(f)
    
    print("="*80)
    print("PARAMETER ADJUSTMENT TO FIX MEDIUM BIAS")
    print("="*80)
    
    print(f"\nCurrent Parameters:")
    print(f"  SOFT offset: {params['compound_offset']['SOFT']:.2f}s")
    print(f"  MEDIUM offset: {params['compound_offset']['MEDIUM']:.2f}s")
    print(f"  HARD offset: {params['compound_offset']['HARD']:.2f}s")
    print(f"\n  SOFT deg_a: {params['deg_a']['SOFT']:.4f}")
    print(f"  MEDIUM deg_a: {params['deg_a']['MEDIUM']:.4f}")
    print(f"  HARD deg_a: {params['deg_a']['HARD']:.4f}")
    
    # Diagnosis
    print(f"\n{'='*80}")
    print("DIAGNOSIS")
    print("="*80)
    print(f"\n⚠️  PROBLEM: You're predicting 80% MEDIUM winners (should be 20%)")
    print(f"⚠️  PROBLEM: You're predicting 0% HARD winners (should be 40%)")
    print(f"✓  GOOD: Your SOFT prediction is close (20% vs 40%)")
    
    print(f"\n{'='*80}")
    print("RECOMMENDED ADJUSTMENTS")
    print("="*80)
    
    # Adjustment strategy
    print(f"\n1. Make MEDIUM tires LESS competitive:")
    print(f"   Increase MEDIUM degradation")
    print(f"   Current deg_a: {params['deg_a']['MEDIUM']:.4f}")
    print(f"   Suggested: 0.0035-0.0045")
    
    print(f"\n2. Make HARD tires MORE competitive:")
    print(f"   Reduce HARD offset penalty")
    print(f"   Current offset: {params['compound_offset']['HARD']:.2f}s")
    print(f"   Suggested: 0.25-0.35s")
    
    print(f"\n3. Keep SOFT tires similar:")
    print(f"   Current setup is reasonable")
    
    # Apply adjustments
    print(f"\n{'='*80}")
    print("APPLYING ADJUSTMENTS...")
    print("="*80)
    
    # Backup first
    backup_file = Path("solution2/params_before_medium_fix.json")
    with open(backup_file, 'w') as f:
        json.dump(params, f, indent=2)
    print(f"\n✓ Backed up to: {backup_file}")
    
    # Adjust parameters
    params['compound_offset']['HARD'] = 0.30  # Reduce penalty
    params['deg_a']['MEDIUM'] = 0.0040  # Increase degradation
    params['deg_b']['MEDIUM'] = 0.012   # Slightly higher linear deg
    
    print(f"\nNew Parameters:")
    print(f"  SOFT offset: {params['compound_offset']['SOFT']:.2f}s (unchanged)")
    print(f"  MEDIUM offset: {params['compound_offset']['MEDIUM']:.2f}s (unchanged)")
    print(f"  HARD offset: {params['compound_offset']['HARD']:.2f}s (reduced from {0.4:.2f})")
    print(f"\n  SOFT deg_a: {params['deg_a']['SOFT']:.4f} (unchanged)")
    print(f"  MEDIUM deg_a: {params['deg_a']['MEDIUM']:.4f} (increased from {0.0015:.4f})")
    print(f"  HARD deg_a: {params['deg_a']['HARD']:.4f} (unchanged)")
    
    # Save new params
    with open(params_file, 'w') as f:
        json.dump(params, f, indent=2)
    
    print(f"\n✓ Saved to: {params_file}")
    
    print(f"\n{'='*80}")
    print("NEXT STEPS")
    print("="*80)
    print(f"\n1. Test the changes:")
    print(f"   python solution2/batch_diagnostic.py")
    print(f"\n2. Check if MEDIUM/HARD balance improved")
    print(f"\n3. If over-corrected, adjust incrementally")
    print(f"\n{'='*80}")

if __name__ == "__main__":
    main()
