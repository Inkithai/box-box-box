#!/usr/bin/env python3
"""Quick test runner for Solution 2"""

import json
import subprocess
from pathlib import Path

def main():
    test_cases_dir = Path("data/test_cases/inputs")
    expected_outputs_dir = Path("data/test_cases/expected_outputs")
    
    # Use solution2
    solution_cmd = "python solution2/race_simulator_clean.py"
    
    print(f"\n{'='*70}")
    print(f"SOLUTION 2 - TEST RUNNER")
    print(f"{'='*70}")
    print(f"\nCommand: {solution_cmd}\n")
    
    test_files = sorted(test_cases_dir.glob("test_*.json"))
    total_tests = len(test_files)
    
    passed = 0
    failed = 0
    
    print(f"Running {total_tests} tests...\n")
    
    for i, test_file in enumerate(test_files[:20], 1):  # First 20 tests
        test_name = test_file.stem
        test_id = test_name.replace("test_", "TEST_")
        
        # Run solution
        result = subprocess.run(
            solution_cmd,
            shell=True,
            input=test_file.read_text(),
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            print(f"✗ {test_id} - Execution error")
            failed += 1
            continue
        
        try:
            output = json.loads(result.stdout)
            predicted = ",".join(output.get("finishing_positions", []))
            
            # Load expected
            answer_file = expected_outputs_dir / f"{test_name}.json"
            expected_data = json.loads(answer_file.read_text())
            expected = ",".join(expected_data.get("finishing_positions", []))
            
            if predicted == expected:
                print(f"✓ {test_id}")
                passed += 1
            else:
                print(f"✗ {test_id} - Wrong prediction")
                failed += 1
                
        except Exception as e:
            print(f"✗ {test_id} - Error: {e}")
            failed += 1
    
    print(f"\n{'='*70}")
    print(f"RESULTS (First 20 tests)")
    print(f"{'='*70}")
    print(f"Passed: {passed}/20")
    print(f"Failed: {failed}/20")
    
    if passed > 0:
        accuracy = (passed / 20) * 100
        print(f"Accuracy: {accuracy:.1f}%")
    print()

if __name__ == "__main__":
    main()
