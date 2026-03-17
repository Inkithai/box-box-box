#!/usr/bin/env python3
"""
Fast Parameter Optimizer - Quick tuning for competition

Uses smarter search strategy focusing on most impactful parameters first.
"""

import json
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple
import time


def run_test(test_file: Path) -> Tuple[bool, List[str]]:
    """Run simulator on single test."""
    try:
        cmd = "python solution/race_simulator.py"
        with open(test_file, 'r') as f:
            input_data = f.read()
        
        result = subprocess.run(
            cmd,
            input=input_data,
            capture_output=True,
            text=True,
            shell=True
        )
        
        if result.returncode != 0:
            return False, []
        
        output = json.loads(result.stdout)
        return True, output.get('finishing_positions', [])
        
    except Exception as e:
        return False, []


def evaluate(test_files: List[Path], expected: Dict[str, List[str]]) -> int:
    """Count matching tests."""
    passed = 0
    for tf in test_files:
        ok, pred = run_test(tf)
        if ok and pred == expected.get(tf.stem, []):
            passed += 1
    return passed


def main():
    print("="*60)
    print("FAST PARAMETER OPTIMIZER")
    print("="*60)
    
    # Load tests
    test_dir = Path("data/test_cases/inputs")
    test_files = sorted(test_dir.glob("test_*.json"))[:20]
    
    expected_dir = Path("data/test_cases/expected_outputs")
    expected = {}
    for f in expected_dir.glob("test_*.json"):
        with open(f, 'r') as file:
            data = json.load(file)
            expected[f.stem] = data['finishing_positions']
    
    print(f"Testing on {len(test_files)} cases")
    
    # Read current tire_physics.py
    physics_file = Path("solution/models/tire_physics.py")
    content = physics_file.read_text()
    
    # Default parameters to try
    param_sets = [
        # Set 1: Current
        {'sl': 0.12, 'ml': 0.08, 'hl': 0.05},
        
        # Set 2: Higher degradation
        {'sl': 0.15, 'ml': 0.10, 'hl': 0.07},
        
        # Set 3: Lower degradation
        {'sl': 0.10, 'ml': 0.07, 'hl': 0.04},
        
        # Set 4: Extreme soft
        {'sl': 0.18, 'ml': 0.12, 'hl': 0.08},
        
        # Set 5: Moderate
        {'sl': 0.14, 'ml': 0.09, 'hl': 0.06},
    ]
    
    best_score = 0
    best_params = None
    
    start = time.time()
    
    for i, params in enumerate(param_sets):
        # Modify content
        modified = content
        modified = modified.replace(
            "linear_degradation=0.12,",
            f"linear_degradation={params['sl']},"
        )
        modified = modified.replace(
            "linear_degradation=0.08,",
            f"linear_degradation={params['ml']},"
        )
        modified = modified.replace(
            "linear_degradation=0.05,",
            f"linear_degradation={params['hl']},"
        )
        
        # Write temp
        physics_file.write_text(modified)
        
        # Test
        score = evaluate(test_files, expected)
        
        print(f"Set {i+1}: sl={params['sl']:.2f}, ml={params['ml']:.2f}, hl={params['hl']:.2f} → {score}/20")
        
        if score > best_score:
            best_score = score
            best_params = params
    
    elapsed = time.time() - start
    
    # Restore best
    if best_params:
        modified = content
        modified = modified.replace(
            "linear_degradation=0.12,",
            f"linear_degradation={best_params['sl']},"
        )
        modified = modified.replace(
            "linear_degradation=0.08,",
            f"linear_degradation={best_params['ml']},"
        )
        modified = modified.replace(
            "linear_degradation=0.05,",
            f"linear_degradation={best_params['hl']},"
        )
        physics_file.write_text(modified)
    
    print(f"\n✓ Best: sl={best_params['sl']:.2f}, ml={best_params['ml']:.2f}, hl={best_params['hl']:.2f}")
    print(f"  Score: {best_score}/20 ({best_score/20*100:.0f}%)")
    print(f"  Time: {elapsed:.1f}s")
    
    return best_score


if __name__ == '__main__':
    main()
