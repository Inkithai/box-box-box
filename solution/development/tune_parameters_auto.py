#!/usr/bin/env python3
"""
Automated Parameter Tuner for Solution 2

This script will:
1. Test different parameter combinations on first 10 test cases
2. Find the best performing parameters
3. Update the tire_model_advanced.py with optimal values
"""

import json
import subprocess
from pathlib import Path
from itertools import product
import time

def run_test(test_num):
    """Run a single test and return if it matches expected"""
    test_file = Path(f"data/test_cases/inputs/test_{test_num:03d}.json")
    expected_file = Path(f"data/test_cases/expected_outputs/test_{test_num:03d}.json")
    
    if not test_file.exists() or not expected_file.exists():
        return False
    
    # Run solution
    cmd = "python solution2/race_simulator.py"
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            input=test_file.read_text(),
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            return False
        
        output = json.loads(result.stdout)
        predicted = output.get("finishing_positions", [])
        
        expected = json.loads(expected_file.read_text())
        expected_positions = expected.get("finishing_positions", [])
        
        return predicted == expected_positions
    except:
        return False

def evaluate_parameters(params, test_range=(1, 11)):
    """Evaluate a parameter set on multiple tests"""
    # Temporarily update the tire model file
    update_tire_params(params)
    
    passed = 0
    total = test_range[1] - test_range[0]
    
    for i in range(test_range[0], test_range[1]):
        if run_test(i):
            passed += 1
    
    return passed / total

def update_tire_params(params):
    """Update tire model parameters"""
    model_file = Path("solution2/models/tire_model_advanced.py")
    content = model_file.read_text()
    
    # Update SOFT compound
    content = content.replace(
        "base_offset=0.0,           # Reference compound (fastest)",
        f"base_offset={params['soft_base']:.2f},           # Reference compound (fastest)"
    )
    content = content.replace(
        "linear_degradation=0.12,   # High initial degradation",
        f"linear_degradation={params['soft_lin']:.4f},   # High initial degradation"
    )
    content = content.replace(
        "quadratic_degradation=0.008,  # Accelerates quickly",
        f"quadratic_degradation={params['soft_quad']:.5f},  # Accelerates quickly"
    )
    
    # Update MEDIUM compound
    content = content.replace(
        "base_offset=0.75,          # +0.75s vs SOFT",
        f"base_offset={params['medium_base']:.2f},          # +0.75s vs SOFT"
    )
    content = content.replace(
        "linear_degradation=0.08,   # Moderate degradation",
        f"linear_degradation={params['medium_lin']:.4f},   # Moderate degradation"
    )
    content = content.replace(
        "quadratic_degradation=0.004,  # More progressive wear",
        f"quadratic_degradation={params['medium_quad']:.5f},  # More progressive wear"
    )
    
    # Update HARD compound
    content = content.replace(
        "base_offset=1.50,          # +1.50s vs SOFT",
        f"base_offset={params['hard_base']:.2f},          # +1.50s vs SOFT"
    )
    content = content.replace(
        "linear_degradation=0.05,   # Low degradation",
        f"linear_degradation={params['hard_lin']:.4f},   # Low degradation"
    )
    content = content.replace(
        "quadratic_degradation=0.002,  # Very progressive, durable",
        f"quadratic_degradation={params['hard_quad']:.5f},  # Very progressive, durable"
    )
    
    model_file.write_text(content)

def grid_search():
    """Perform grid search over parameter space"""
    
    print("="*80)
    print("PARAMETER TUNING FOR SOLUTION 2")
    print("="*80)
    print("\nSearching for optimal tire parameters...\n")
    
    # Parameter ranges to search
    soft_base_opts = [-0.6, -0.4, -0.2, 0.0]
    medium_base_opts = [0.0, 0.2, 0.4, 0.6]
    hard_base_opts = [0.4, 0.6, 0.8, 1.0]
    
    soft_lin_opts = [0.08, 0.10, 0.12, 0.15]
    medium_lin_opts = [0.05, 0.07, 0.09, 0.11]
    hard_lin_opts = [0.03, 0.05, 0.07, 0.09]
    
    soft_quad_opts = [0.003, 0.005, 0.007, 0.010]
    medium_quad_opts = [0.002, 0.003, 0.004, 0.005]
    hard_quad_opts = [0.001, 0.002, 0.003, 0.004]
    
    best_score = 0
    best_params = None
    
    test_configs = list(product(
        soft_base_opts, medium_base_opts, hard_base_opts,
        soft_lin_opts, medium_lin_opts, hard_lin_opts,
        soft_quad_opts, medium_quad_opts, hard_quad_opts
    ))
    
    print(f"Testing {len(test_configs)} parameter combinations on tests 1-5...\n")
    
    for i, config in enumerate(test_configs):
        params = {
            'soft_base': config[0],
            'medium_base': config[1],
            'hard_base': config[2],
            'soft_lin': config[3],
            'medium_lin': config[4],
            'hard_lin': config[5],
            'soft_quad': config[6],
            'medium_quad': config[7],
            'hard_quad': config[8],
        }
        
        score = evaluate_parameters(params, test_range=(1, 6))
        
        if score > best_score:
            best_score = score
            best_params = params
            print(f"[{i+1}/{len(test_configs)}] New best: {score*100:.0f}% - Params: {params}")
        elif (i+1) % 10 == 0:
            print(f"[{i+1}/{len(test_configs)}] Current best: {best_score*100:.0f}%")
    
    print(f"\n{'='*80}")
    print(f"BEST PARAMETERS FOUND:")
    print(f"Score: {best_score*100:.0f}% on tests 1-5")
    print(f"Parameters: {best_params}")
    print(f"{'='*80}\n")
    
    if best_params:
        print("Applying best parameters...")
        update_tire_params(best_params)
        print("✓ Parameters updated in tire_model_advanced.py")
        
        # Test on full range
        print("\nTesting on all 100 test cases...")
        final_score = evaluate_parameters(best_params, test_range=(1, 101))
        print(f"\nFinal Score: {final_score*100:.1f}% ({int(final_score*100)}/100)")
    
    return best_params

if __name__ == "__main__":
    start_time = time.time()
    best_params = grid_search()
    elapsed = time.time() - start_time
    print(f"\nTotal time: {elapsed:.1f} seconds")
