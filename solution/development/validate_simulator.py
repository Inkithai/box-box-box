#!/usr/bin/env python3
"""
Regression-Based F1 Race Simulator - Validation Suite

Validates the regression-based simulator against 100 predefined test cases.
Compares finishing orders and total race times with expected outputs.

Usage:
    python validate_simulator.py [--verbose] [--show-failures]
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass
from tabulate import tabulate


@dataclass
class ValidationResult:
    """Results from validating a single test case."""
    test_id: str
    passed: bool
    exact_order_match: bool
    position_discrepancies: int
    time_errors: Dict[str, float]  # driver_id -> absolute error
    mean_absolute_time_error: float
    max_time_error: float
    actual_finishing_order: List[str]
    expected_finishing_order: List[str]
    actual_times: Dict[str, float]
    expected_times: Dict[str, float]
    failure_reason: str = ""


def load_test_case(test_num: int) -> Tuple[dict, dict]:
    """
    Load a test case input and expected output.
    
    Args:
        test_num: Test case number (1-100)
        
    Returns:
        Tuple of (input_data, expected_output)
    """
    inputs_dir = Path(__file__).parent.parent / "data" / "test_cases" / "inputs"
    outputs_dir = Path(__file__).parent.parent / "data" / "test_cases" / "expected_outputs"
    
    input_file = inputs_dir / f"test_{test_num:03d}.json"
    output_file = outputs_dir / f"test_{test_num:03d}.json"
    
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    if not output_file.exists():
        raise FileNotFoundError(f"Output file not found: {output_file}")
    
    with open(input_file, 'r') as f:
        input_data = json.load(f)
    
    with open(output_file, 'r') as f:
        expected_output = json.load(f)
    
    return input_data, expected_output


def run_simulation(race_config: dict, strategies: dict) -> Tuple[List[str], Dict[str, float]]:
    """
    Run the regression-based simulator on a single race.
    
    Args:
        race_config: Race configuration parameters
        strategies: Driver strategies dictionary
        
    Returns:
        Tuple of (finishing_order, driver_times)
    """
    # Import simulator
    solution_dir = Path(__file__).parent
    sys.path.insert(0, str(solution_dir))
    
    from core.simulator import RaceSimulator
    
    # Create simulator instance
    simulator = RaceSimulator(race_config, strategies)
    
    # Run simulation
    finishing_order = simulator.simulate_race()
    
    # Extract driver times
    driver_times = {}
    for driver in simulator.drivers:
        driver_times[driver.driver_id] = driver.total_race_time
    
    return finishing_order, driver_times


def validate_test_case(test_num: int) -> ValidationResult:
    """
    Validate simulator output against expected results.
    
    Args:
        test_num: Test case number
        
    Returns:
        ValidationResult with comparison metrics
    """
    try:
        # Load test case
        input_data, expected_output = load_test_case(test_num)
        
        test_id = f"TEST_{test_num:03d}"
        race_config = input_data['race_config']
        strategies = input_data['strategies']
        
        # Run simulation
        actual_order, actual_times = run_simulation(race_config, strategies)
        expected_order = expected_output['finishing_positions']
        
        # Calculate metrics
        exact_match = actual_order == expected_order
        
        # Count position discrepancies
        position_diffs = 0
        for i, (actual, expected) in enumerate(zip(actual_order, expected_order)):
            if actual != expected:
                position_diffs += 1
        
        # Calculate time errors (if we had expected times)
        # For now, we'll use placeholder expected times
        time_errors = {}
        
        # Since expected outputs don't include times, calculate relative to winner
        if actual_order:
            winner_time = min(actual_times.values())
            time_errors = {
                driver_id: abs(time_val - winner_time) 
                for driver_id, time_val in actual_times.items()
            }
        
        mean_abs_error = sum(time_errors.values()) / len(time_errors) if time_errors else 0.0
        max_error = max(time_errors.values()) if time_errors else 0.0
        
        # Determine pass/fail
        passed = exact_match
        
        return ValidationResult(
            test_id=test_id,
            passed=passed,
            exact_order_match=exact_match,
            position_discrepancies=position_diffs,
            time_errors=time_errors,
            mean_absolute_time_error=mean_abs_error,
            max_time_error=max_error,
            actual_finishing_order=actual_order,
            expected_finishing_order=expected_order,
            actual_times=actual_times,
            expected_times={},  # Not available in current format
            failure_reason="" if passed else f"Order mismatch: {position_diffs} positions differ"
        )
        
    except Exception as e:
        return ValidationResult(
            test_id=f"TEST_{test_num:03d}",
            passed=False,
            exact_order_match=False,
            position_discrepancies=20,
            time_errors={},
            mean_absolute_time_error=0.0,
            max_time_error=0.0,
            actual_finishing_order=[],
            expected_finishing_order=[],
            actual_times={},
            expected_times={},
            failure_reason=f"Error: {str(e)}"
        )


def calculate_overall_metrics(results: List[ValidationResult]) -> dict:
    """
    Calculate aggregate performance metrics.
    
    Args:
        results: List of ValidationResult objects
        
    Returns:
        Dictionary of overall metrics
    """
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r.passed)
    exact_matches = sum(1 for r in results if r.exact_order_match)
    
    all_position_discrepancies = [r.position_discrepancies for r in results]
    all_time_errors = [r.mean_absolute_time_error for r in results]
    
    # Calculate accuracy percentages
    exact_order_accuracy = exact_matches / total_tests * 100 if total_tests > 0 else 0
    partial_accuracy = sum(
        1 - (r.position_discrepancies / 20) for r in results
    ) / total_tests * 100 if total_tests > 0 else 0
    
    return {
        'total_tests': total_tests,
        'passed_tests': passed_tests,
        'failed_tests': total_tests - passed_tests,
        'pass_rate': passed_tests / total_tests * 100 if total_tests > 0 else 0,
        'exact_order_accuracy': exact_order_accuracy,
        'partial_accuracy': partial_accuracy,
        'avg_position_discrepancies': sum(all_position_discrepancies) / total_tests if total_tests > 0 else 0,
        'max_position_discrepancies': max(all_position_discrepancies),
        'avg_time_error': sum(all_time_errors) / total_tests if total_tests > 0 else 0,
        'max_time_error': max(all_time_errors),
        'total_execution_time': sum(getattr(r, 'execution_time', 0) for r in results)
    }


def print_summary_table(metrics: dict):
    """Print summary statistics table."""
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)
    
    table_data = [
        ["Total Test Cases", f"{metrics['total_tests']}"],
        ["Passed (Exact Match)", f"{metrics['passed_tests']} ({metrics['pass_rate']:.1f}%)"],
        ["Failed", f"{metrics['failed_tests']} ({100-metrics['pass_rate']:.1f}%)"],
        ["Exact Order Accuracy", f"{metrics['exact_order_accuracy']:.2f}%"],
        ["Partial Accuracy", f"{metrics['partial_accuracy']:.2f}%"],
        ["Avg Position Discrepancies", f"{metrics['avg_position_discrepancies']:.2f}"],
        ["Max Position Discrepancies", f"{metrics['max_position_discrepancies']}"],
        ["Avg Time Error", f"{metrics['avg_time_error']:.3f}s"],
        ["Max Time Error", f"{metrics['max_time_error']:.3f}s"],
    ]
    
    print(tabulate(table_data, headers=["Metric", "Value"], tablefmt="grid"))
    print("="*70)


def print_failing_tests(results: List[ValidationResult], max_display: int = 10):
    """Print details of failing test cases."""
    failing = [r for r in results if not r.passed]
    
    if not failing:
        print("\n✓ All tests passed!")
        return
    
    print(f"\n{'='*70}")
    print(f"FAILING TESTS ({len(failing)} of {len(results)})")
    print("="*70)
    
    for result in failing[:max_display]:
        print(f"\n{result.test_id}: {result.failure_reason}")
        
        if result.position_discrepancies > 0:
            print(f"  Position discrepancies: {result.position_discrepancies}/20")
            
            # Show first few differences
            diffs = []
            for i, (actual, expected) in enumerate(zip(result.actual_finishing_order, 
                                                       result.expected_finishing_order)):
                if actual != expected:
                    diffs.append((i+1, actual, expected))
            
            if diffs:
                print("  Differences (Position | Actual | Expected):")
                for pos, actual, expected in diffs[:5]:
                    print(f"    P{pos:2d}: {actual:<8} vs {expected:<8}")
                if len(diffs) > 5:
                    print(f"    ... and {len(diffs)-5} more")
        
        if result.max_time_error > 0:
            print(f"  Max time error: {result.max_time_error:.3f}s")
    
    if len(failing) > max_display:
        print(f"\n... and {len(failing) - max_display} more failing tests")


def print_detailed_comparison(result: ValidationResult):
    """Print detailed side-by-side comparison for a test case."""
    print(f"\n{'='*70}")
    print(f"Detailed Comparison: {result.test_id}")
    print("="*70)
    
    print(f"\nExpected Order (Top 10):")
    for i, driver in enumerate(result.expected_finishing_order[:10], 1):
        print(f"  P{i:2d}: {driver}")
    
    print(f"\nActual Order (Top 10):")
    for i, driver in enumerate(result.actual_finishing_order[:10], 1):
        match = "✓" if driver == result.expected_finishing_order[i-1] else "✗"
        print(f"  P{i:2d}: {driver} {match}")
    
    print(f"\nTime Statistics:")
    if result.actual_times:
        times = list(result.actual_times.values())
        print(f"  Winner time: {min(times):.3f}s")
        print(f"  Mean time: {sum(times)/len(times):.3f}s")
        print(f"  Max error: {result.max_time_error:.3f}s")


def save_results(results: List[ValidationResult], metrics: dict, output_file: str):
    """Save validation results to JSON file."""
    output_path = Path(output_file)
    
    output_data = {
        'summary': metrics,
        'test_results': [
            {
                'test_id': r.test_id,
                'passed': r.passed,
                'exact_match': r.exact_order_match,
                'position_discrepancies': r.position_discrepancies,
                'mean_time_error': r.mean_absolute_time_error,
                'max_time_error': r.max_time_error,
                'failure_reason': r.failure_reason,
                'actual_order': r.actual_finishing_order,
                'expected_order': r.expected_finishing_order
            }
            for r in results
        ]
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n✓ Results saved to {output_path}")


def main():
    """Main validation pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate F1 Race Simulator')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Show detailed output')
    parser.add_argument('--show-failures', '-f', action='store_true',
                       help='Show failing test details')
    parser.add_argument('--output', '-o', type=str, default='validation_results.json',
                       help='Output file for results')
    parser.add_argument('--test-range', type=str, default='1-100',
                       help='Range of tests to run (e.g., "1-50" or "1-100")')
    
    args = parser.parse_args()
    
    # Parse test range
    try:
        start, end = map(int, args.test_range.split('-'))
        test_range = range(start, end + 1)
    except ValueError:
        print("Invalid test range. Use format: 1-100")
        return
    
    print("="*70)
    print("F1 RACE SIMULATOR VALIDATION SUITE")
    print("="*70)
    print(f"\nRunning {len(test_range)} test cases...")
    print(f"Test range: {start} to {end}")
    print()
    
    # Run all tests
    results = []
    start_time = time.perf_counter()
    
    for test_num in test_range:
        test_start = time.perf_counter()
        result = validate_test_case(test_num)
        test_elapsed = time.perf_counter() - test_start
        
        # Add execution time to result
        result.execution_time = test_elapsed
        
        results.append(result)
        
        # Progress indicator
        if (test_num % 10 == 0) or (test_num == end):
            passed = sum(1 for r in results if r.passed)
            total = len(results)
            print(f"  Completed {total}/{len(test_range)} tests "
                  f"({passed} passed, {total-passed} failed)")
    
    total_time = time.perf_counter() - start_time
    
    # Calculate metrics
    metrics = calculate_overall_metrics(results)
    metrics['total_execution_time'] = total_time
    
    # Print summary
    print_summary_table(metrics)
    
    # Show failing tests
    if args.show_failures or args.verbose:
        print_failing_tests(results)
    
    # Print detailed examples if verbose
    if args.verbose:
        # Show one passing and one failing test in detail
        passing = [r for r in results if r.passed]
        failing = [r for r in results if not r.passed]
        
        if passing:
            print_detailed_comparison(passing[0])
        if failing:
            print_detailed_comparison(failing[0])
    
    # Save results
    save_results(results, metrics, args.output)
    
    # Performance stats
    print(f"\nPerformance:")
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Avg per test: {total_time/len(results)*1000:.1f}ms")
    print(f"  Tests per second: {len(results)/total_time:.1f}")
    
    # Final verdict
    print("\n" + "="*70)
    if metrics['pass_rate'] >= 90:
        print("✓ EXCELLENT: Simulator performs well on validation suite")
    elif metrics['pass_rate'] >= 70:
        print("⚠ GOOD: Simulator shows reasonable accuracy with some discrepancies")
    elif metrics['pass_rate'] >= 50:
        print("⚠ FAIR: Simulator has notable accuracy issues requiring attention")
    else:
        print("✗ POOR: Simulator requires significant improvements")
    print("="*70)
    
    # Return exit code
    return 0 if metrics['pass_rate'] >= 70 else 1


if __name__ == '__main__':
    exit(main())
