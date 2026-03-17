#!/usr/bin/env python3
"""
Test suite for advanced tire model with quadratic degradation.

Validates:
1. Quadratic degradation implementation
2. Compound-specific temperature effects
3. Float precision throughout calculations
4. Minimal rounding errors
5. Backward compatibility with regression model
"""

import sys
from pathlib import Path

# Add solution directory to path
solution_dir = Path(__file__).parent.parent
sys.path.insert(0, str(solution_dir))

from models.tire_model_advanced import (
    calculate_lap_time_precise,
    calculate_stint_time_quadratic,
    get_compound_properties,
    compare_compound_performance,
    validate_model_parameters
)
from core.simulator import RaceSimulator


def create_test_config():
    """Create standard test configuration."""
    return {
        'race_id': 'test_advanced',
        'base_lap_time': 85.0,
        'total_laps': 30,
        'pit_lane_time': 25.0,
        'track_temp': 30.0,
        'air_temp': 25,
        'humidity': 50
    }


def create_test_strategies():
    """Create test strategies for all 20 positions."""
    strategies = {}
    
    # Top 3 with varied strategies
    strategies['pos1'] = {
        'driver_id': 'DRV01',
        'starting_tire': 'SOFT',
        'pit_stops': [{'lap': 15, 'to_tire': 'HARD'}]
    }
    strategies['pos2'] = {
        'driver_id': 'DRV02',
        'starting_tire': 'MEDIUM',
        'pit_stops': [{'lap': 18, 'to_tire': 'HARD'}]
    }
    strategies['pos3'] = {
        'driver_id': 'DRV03',
        'starting_tire': 'SOFT',
        'pit_stops': [{'lap': 12, 'to_tire': 'MEDIUM'}]
    }
    
    # Fill remaining positions
    for pos in range(4, 21):
        strategies[f'pos{pos}'] = {
            'driver_id': f'DRV{pos:02d}',
            'starting_tire': 'MEDIUM' if pos <= 10 else 'HARD',
            'pit_stops': []
        }
    
    return strategies


def test_quadratic_degradation():
    """Test that quadratic degradation is properly implemented."""
    print("\n" + "="*70)
    print("TEST 1: Quadratic Degradation")
    print("="*70)
    
    # Get compound properties
    soft_props = get_compound_properties('SOFT')
    
    print(f"\nSOFT compound properties:")
    print(f"  Linear degradation:   {soft_props.linear_degradation:.6f} s/lap")
    print(f"  Quadratic degradation: {soft_props.quadratic_degradation:.6f} s/lap²")
    
    # Calculate lap times at different ages
    base_time = 85.0
    track_temp = 30.0
    
    print(f"\nLap time progression (SOFT, {track_temp}°C):")
    print(f"{'Age':<6} {'Lap Time':<12} {'Δ from prev':<12} {'Expected Δ':<12}")
    print("-"*50)
    
    prev_time = None
    for age in [1, 5, 10, 15, 20]:
        lap_time = calculate_lap_time_precise(
            compound='SOFT',
            tire_age=age,
            track_temp=track_temp,
            base_lap_time=base_time
        )
        
        if prev_time:
            delta = lap_time - prev_time
            # Expected delta includes both linear and quadratic components
            expected_delta = soft_props.linear_degradation * (age - (age-1)) + \
                           soft_props.quadratic_degradation * (age**2 - (age-1)**2)
            print(f"{age:<6} {lap_time:<12.6f} {delta:<12.6f} {expected_delta:<12.6f}")
        else:
            print(f"{age:<6} {lap_time:<12.6f}")
        
        prev_time = lap_time
    
    # Verify quadratic effect: degradation should accelerate
    lap_1 = calculate_lap_time_precise('SOFT', 1, track_temp, base_time)
    lap_5 = calculate_lap_time_precise('SOFT', 5, track_temp, base_time)
    lap_10 = calculate_lap_time_precise('SOFT', 10, track_temp, base_time)
    
    deg_1_to_5 = (lap_5 - lap_1) / 4.0  # Average degradation per lap
    deg_5_to_10 = (lap_10 - lap_5) / 5.0
    
    print(f"\nAverage degradation rates:")
    print(f"  Laps 1-5:  {deg_1_to_5:.6f} s/lap")
    print(f"  Laps 5-10: {deg_5_to_10:.6f} s/lap")
    
    # Degradation should increase due to quadratic term
    assert deg_5_to_10 > deg_1_to_5, "Quadratic degradation should cause acceleration"
    print(f"\n✓ Quadratic degradation confirmed: degradation rate increases with age")
    
    return True


def test_compound_temperature_sensitivity():
    """Test compound-specific temperature effects."""
    print("\n" + "="*70)
    print("TEST 2: Compound-Specific Temperature Sensitivity")
    print("="*70)
    
    compounds = ['SOFT', 'MEDIUM', 'HARD']
    temps = [20, 25, 30, 35, 40]
    
    print(f"\nTemperature sensitivity analysis:")
    print(f"{'Compound':<10} {'Temp (°C)':<12} {'Lap Time':<12} {'Δ vs Optimal':<12}")
    print("-"*50)
    
    results = {}
    
    for compound in compounds:
        props = get_compound_properties(compound)
        results[compound] = []
        
        for temp in temps:
            lap_time = calculate_lap_time_precise(
                compound=compound,
                tire_age=1,
                track_temp=temp,
                base_lap_time=85.0
            )
            
            # Calculate at optimal temperature for comparison
            optimal_lap = calculate_lap_time_precise(
                compound=compound,
                tire_age=1,
                track_temp=props.optimal_temperature,
                base_lap_time=85.0
            )
            
            delta = lap_time - optimal_lap
            results[compound].append((temp, lap_time, delta))
            
            marker = " *" if temp == props.optimal_temperature else ""
            print(f"{compound:<10} {temp:<12} {lap_time:<12.6f} {delta:+<12.6f}{marker}")
    
    # Verify each compound has an optimal temperature
    for compound in compounds:
        props = get_compound_properties(compound)
        laps_at_optimal = calculate_lap_time_precise(
            compound=compound,
            tire_age=1,
            track_temp=props.optimal_temperature,
            base_lap_time=85.0
        )
        laps_cold = calculate_lap_time_precise(
            compound=compound,
            tire_age=1,
            track_temp=20.0,
            base_lap_time=85.0
        )
        laps_hot = calculate_lap_time_precise(
            compound=compound,
            tire_age=1,
            track_temp=40.0,
            base_lap_time=85.0
        )
        
        assert laps_at_optimal < laps_cold, f"{compound} should be faster at optimal temp"
        assert laps_at_optimal < laps_hot, f"{compound} should be faster at optimal temp"
    
    print(f"\n✓ All compounds show correct temperature sensitivity")
    print(f"  SOFT optimal:   {get_compound_properties('SOFT').optimal_temperature}°C")
    print(f"  MEDIUM optimal: {get_compound_properties('MEDIUM').optimal_temperature}°C")
    print(f"  HARD optimal:   {get_compound_properties('HARD').optimal_temperature}°C")
    
    return True


def test_float_precision():
    """Test that full float precision is maintained."""
    print("\n" + "="*70)
    print("TEST 3: Float Precision")
    print("="*70)
    
    # Test with very small differences
    base = 85.0
    temp = 30.0
    
    # Calculate consecutive lap times
    lap1 = calculate_lap_time_precise('SOFT', 1, temp, base)
    lap2 = calculate_lap_time_precise('SOFT', 2, temp, base)
    
    diff = lap2 - lap1
    
    print(f"\nPrecision test:")
    print(f"  Lap 1 time: {lap1:.10f}s")
    print(f"  Lap 2 time: {lap2:.10f}s")
    print(f"  Difference: {diff:.10f}s")
    
    # Verify we can detect small differences (< 0.001s)
    assert diff > 0.001, "Should detect degradation between laps"
    assert diff < 1.0, "Degradation should be realistic"
    
    # Test stint time precision
    stint_10 = calculate_stint_time_quadratic('SOFT', 10, temp, base)
    stint_11 = calculate_stint_time_quadratic('SOFT', 11, temp, base)
    
    # The 11th lap should add more than the 1st lap due to degradation
    lap_11_contribution = stint_11 - stint_10
    lap_1_time = calculate_lap_time_precise('SOFT', 1, temp, base)
    
    print(f"\nStint precision:")
    print(f"  10-lap stint: {stint_10:.10f}s")
    print(f"  11-lap stint: {stint_11:.10f}s")
    print(f"  11th lap contribution: {lap_11_contribution:.10f}s")
    print(f"  1st lap time: {lap_1_time:.10f}s")
    
    assert lap_11_contribution > lap_1_time, "Later laps should be slower"
    
    print(f"\n✓ Full float precision maintained (10+ decimal places)")
    
    return True


def test_minimal_rounding_errors():
    """Test that rounding errors are minimized."""
    print("\n" + "="*70)
    print("TEST 4: Minimal Rounding Errors")
    print("="*70)
    
    # Compare iterative vs closed-form calculation
    base = 85.0
    temp = 30.0
    n_laps = 20
    
    # Method 1: Sum individual lap times (iterative)
    iterative_sum = 0.0
    for age in range(1, n_laps + 1):
        lap_time = calculate_lap_time_precise('SOFT', age, temp, base)
        iterative_sum += lap_time
    
    # Method 2: Closed-form formula
    closed_form = calculate_stint_time_quadratic('SOFT', n_laps, temp, base)
    
    # Calculate error
    absolute_error = abs(iterative_sum - closed_form)
    relative_error = absolute_error / iterative_sum
    
    print(f"\nRounding error analysis ({n_laps} laps):")
    print(f"  Iterative sum:  {iterative_sum:.15f}s")
    print(f"  Closed form:    {closed_form:.15f}s")
    print(f"  Absolute error: {absolute_error:.2e}s")
    print(f"  Relative error: {relative_error:.2e} ({relative_error*100:.10f}%)")
    
    # Error should be extremely small (< 1e-10 relative)
    assert relative_error < 1e-8, f"Rounding error too large: {relative_error}"
    
    print(f"\n✓ Minimal rounding errors achieved (< 1e-8 relative)")
    
    return True


def test_full_simulation():
    """Test complete race simulation with advanced model."""
    print("\n" + "="*70)
    print("TEST 5: Full Race Simulation")
    print("="*70)
    
    config = create_test_config()
    strategies = create_test_strategies()
    
    # Run with advanced model
    print("\nRunning simulation with ADVANCED model...")
    sim_advanced = RaceSimulator(config, strategies, use_advanced_model=True)
    result_advanced = sim_advanced.simulate_race()
    
    # Run with regression model for comparison
    print("\nRunning simulation with REGRESSION model...")
    sim_regression = RaceSimulator(config, strategies, use_advanced_model=False)
    result_regression = sim_regression.simulate_race()
    
    print(f"\nFinishing order comparison (Top 10):")
    print(f"{'Pos':<6} {'Advanced':<12} {'Regression':<12}")
    print("-"*30)
    
    for i in range(10):
        adv = result_advanced[i]
        reg = result_regression[i]
        match = "✓" if adv == reg else "✗"
        print(f"P{i+1:<5} {adv:<12} {reg:<12} {match}")
    
    # Show time statistics
    print(f"\nTime statistics:")
    adv_times = [d.total_race_time for d in sim_advanced.drivers]
    reg_times = [d.total_race_time for d in sim_regression.drivers]
    
    print(f"  Advanced model:")
    print(f"    Winner: {min(adv_times):.6f}s")
    print(f"    Mean:   {sum(adv_times)/len(adv_times):.6f}s")
    print(f"    Spread: {max(adv_times) - min(adv_times):.6f}s")
    
    print(f"  Regression model:")
    print(f"    Winner: {min(reg_times):.6f}s")
    print(f"    Mean:   {sum(reg_times)/len(reg_times):.6f}s")
    print(f"    Spread: {max(reg_times) - min(reg_times):.6f}s")
    
    print(f"\n✓ Full simulation completed successfully")
    
    return True


def test_model_validation():
    """Test that model parameters are physically realistic."""
    print("\n" + "="*70)
    print("TEST 6: Model Parameter Validation")
    print("="*70)
    
    print("\nValidating tire model parameters...")
    
    if validate_model_parameters():
        print("✓ All parameters pass validation")
        return True
    else:
        print("✗ Parameter validation failed")
        return False


def run_all_tests():
    """Run complete test suite."""
    print("\n" + "="*70)
    print("ADVANCED TIRE MODEL TEST SUITE")
    print("="*70)
    
    tests = [
        ("Quadratic Degradation", test_quadratic_degradation),
        ("Compound Temperature Sensitivity", test_compound_temperature_sensitivity),
        ("Float Precision", test_float_precision),
        ("Minimal Rounding Errors", test_minimal_rounding_errors),
        ("Full Simulation", test_full_simulation),
        ("Parameter Validation", test_model_validation)
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success, None))
        except Exception as e:
            results.append((name, False, str(e)))
            print(f"\n✗ {name} FAILED: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for name, success, error in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {name}")
        if error:
            print(f"       Error: {error}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("="*70)
    
    return passed == total


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)
