#!/usr/bin/env python3
"""
Test Runner - Python version for Windows
Runs all 100 test cases and calculates pass rate.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


def load_run_command() -> str:
    """Load solution command from run_command.txt."""
    cmd_file = Path("solution/run_command.txt")
    if not cmd_file.exists():
        print(f"Error: Run command file not found: {cmd_file}")
        sys.exit(1)
    
    return cmd_file.read_text().strip()


def get_test_files() -> List[Path]:
    """Get all test case files."""
    test_dir = Path("data/test_cases/inputs")
    if not test_dir.exists():
        print(f"Error: Test cases directory not found: {test_dir}")
        sys.exit(1)
    
    return sorted(test_dir.glob("test_*.json"))


def run_test(test_file: Path, solution_cmd: str) -> Tuple[bool, str, str]:
    """
    Run a single test case.
    
    Returns:
        Tuple of (success, output_or_error, expected_if_available)
    """
    test_name = test_file.stem
    answer_file = Path(f"data/test_cases/expected_outputs/{test_name}.json")
    
    try:
        # Run solution
        with open(test_file, 'r') as f:
            input_data = f.read()
        
        result = subprocess.run(
            solution_cmd,
            input=input_data,
            capture_output=True,
            text=True,
            shell=True
        )
        
        if result.returncode != 0:
            return False, f"Execution error: {result.stderr}", ""
        
        # Parse output
        try:
            output = json.loads(result.stdout)
            
            # Validate format
            if 'race_id' not in output or 'finishing_positions' not in output:
                return False, "Invalid output format (missing fields)", ""
            
            if len(output['finishing_positions']) != 20:
                return False, f"Wrong number of drivers: {len(output['finishing_positions'])}", ""
            
            # Compare with expected if available
            if answer_file.exists():
                with open(answer_file, 'r') as f:
                    expected = json.load(f)
                
                predicted = ','.join(output['finishing_positions'])
                expected_order = ','.join(expected['finishing_positions'])
                
                if predicted == expected_order:
                    return True, "Match", expected_order
                else:
                    return False, "Incorrect prediction", expected_order
            else:
                # No answer file, just validate format
                return True, "Format OK (no answer file)", ""
                
        except json.JSONDecodeError:
            return False, "Invalid JSON output", ""
            
    except Exception as e:
        return False, f"Exception: {str(e)}", ""


def main():
    """Run complete test suite."""
    print("=" * 60)
    print("Box Box Box - Test Runner (Python Version)")
    print("=" * 60)
    print()
    
    # Load configuration
    solution_cmd = load_run_command()
    test_files = get_test_files()
    
    print(f"Solution Command: {solution_cmd}")
    print(f"Test Cases Found: {len(test_files)}")
    print()
    print("Running tests...")
    print()
    
    # Run tests
    passed = 0
    failed = 0
    errors = 0
    
    for test_file in test_files:
        test_name = test_file.stem.replace('test_', 'TEST_')
        success, message, expected = run_test(test_file, solution_cmd)
        
        if success:
            print(f"[PASS] {test_name}")
            passed += 1
        else:
            print(f"[FAIL] {test_name} - {message}")
            failed += 1
    
    print()
    print("=" * 60)
    print("Results")
    print("=" * 60)
    print()
    print(f"Total Tests:    {len(test_files)}")
    print(f"Passed:         {passed}")
    print(f"Failed:         {failed}")
    print()
    
    pass_rate = (passed / len(test_files)) * 100 if test_files else 0
    print(f"Pass Rate:      {pass_rate:.1f}%")
    print()
    
    if passed == len(test_files):
        print("[EXCELLENT] Perfect score! All tests passed!")
    elif passed > 0:
        print("[GOOD] Some tests passed - keep improving!")
    else:
        print("[NEEDS WORK] No tests passed. Review implementation.")
    
    return passed == len(test_files)


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
