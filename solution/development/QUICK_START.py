#!/usr/bin/env python3
"""
QUICK START - Improve Accuracy in 3 Steps

Run this script to automatically:
1. Analyze historical data
2. Run parameter tuning
3. Test results
"""

import subprocess
from pathlib import Path

def main():
    print("="*80)
    print("🚀 SOLUTION 2 - QUICK ACCURACY BOOST")
    print("="*80)
    print()
    
    # Step 1: Historical Analysis
    print("STEP 1: Analyzing Historical Data...")
    print("-"*80)
    result = subprocess.run(
        ["python", "solution2/historical_analyzer.py"],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    print("\n" + "="*80)
    print()
    
    # Step 2: Auto-Tuning
    print("STEP 2: Running Parameter Auto-Tuner...")
    print("-"*80)
    print("(This will take 5-10 minutes)\n")
    
    result = subprocess.run(
        ["python", "solution2/auto_tuner_grid.py"],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    print("\n" + "="*80)
    print()
    
    # Step 3: Quick Test
    print("STEP 3: Testing Results on First 20 Cases...")
    print("-"*80)
    
    result = subprocess.run(
        ["python", "solution2/quick_test.py"],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    
    print("\n" + "="*80)
    print("✅ COMPLETE!")
    print("="*80)
    print()
    print("Next Steps:")
    print("1. If accuracy improved (>20%), continue manual tuning")
    print("2. If still 0%, review historical analyzer recommendations")
    print("3. Manually adjust params.json based on insights")
    print()
    print("See ACCURACY_IMPROVEMENT_PLAN.md for detailed guide")
    print()

if __name__ == "__main__":
    main()
