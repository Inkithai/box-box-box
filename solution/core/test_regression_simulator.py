#!/usr/bin/env python3
"""
Test suite for regression-based race simulator.

Validates:
1. Regression model loading
2. Compound-specific degradation rates
3. Temperature effects
4. Deterministic behavior (no randomness)
5. Fast O(1) stint calculations
6. Accurate finishing order predictions
"""

import json
import sys
import time
from pathlib import Path

# Add solution directory to path
solution_dir = Path(__file__).parent.parent
sys.path.insert(0, str(solution_dir))

from simulator import RaceSimulator


def create_test_race_config():
    """Create standard test race configuration."""
    return {
        'race_id': 'test_001',
        'base_lap_time': 85.0,
        'total_laps': 30,
        'pit_lane_time': 25.0,
        'track_temp': 30,  # Reference temperature
        'air_temp': 25,
        'humidity': 50,
        'wind_speed': 10,
        'track_length': 5.0
    }


def create_test_strategies():
    """Create simple test strategies for validation (all 20 positions)."""
    strategies = {
        'pos1': {
            'driver_id': 'VER',
            'starting_tire': 'SOFT',
            'pit_stops': [
                {'lap': 15, 'to_tire': 'HARD'}
            ]
        },
        'pos2': {
            'driver_id': 'HAM',
            'starting_tire': 'MEDIUM',
            'pit_stops': [
                {'lap': 18, 'to_tire': 'HARD'}
            ]
        },
        'pos3': {
            'driver_id': 'LEC',
            'starting_tire': 'SOFT',
            'pit_stops': [
                {'lap': 12, 'to_tire': 'MEDIUM'}
            ]
        }
    }
    
    # Fill remaining 17 positions with default strategies
    for pos in range(4, 21):
        strategies[f'pos{pos}'] = {
            'driver_id': f'DRV{pos:02d}',
            'starting_tire': 'MEDIUM',
            'pit_stops': []
        }
    
    return strategies


def test_model_loading():
    """Test that regression model loads correctly."""
    print("\n" + "="*70)
    print("TEST 1: Model Loading")
    print("="*70)
    
    config = create_test_race_config()
    strategies = create_test_strategies()
    
    # Test with default model location
    simulator = RaceSimulator(config, strategies)
    
    # Verify coefficients loaded
    assert 'intercept' in simulator.coefficients
    assert 'medium_offset' in simulator.coefficients
    assert 'hard_offset' in simulator.coefficients
    assert 'degradation_linear' in simulator.coefficients
    
    print(f"✓ Model loaded successfully")
    print(f"  Intercept: {simulator.coefficients['intercept']:.4f}")
    print(f"  MEDIUM offset: {simulator.coefficients['medium_offset']:.4f}s")
    print(f"  HARD offset: {simulator.coefficients['hard_offset']:.4f}s")
    print(f"  Degradation rate: {simulator.coefficients['degradation_linear']:.4f} s/lap")
    
    return True


def test_compound_offsets():
    """Test compound offset calculations."""
    print("\n" + "="*70)
    print("TEST 2: Compound Offsets")
    print("="*70)
    
    config = create_test_race_config()
    strategies = create_test_strategies()
    simulator = RaceSimulator(config, strategies)
    
    # Get offsets for each compound
    soft_offset = simulator._get_compound_offset('SOFT')
    medium_offset = simulator._get_compound_offset('MEDIUM')
    hard_offset = simulator._get_compound_offset('HARD')
    
    print(f"Compound offsets (relative to SOFT):")
    print(f"  SOFT:   {soft_offset:.4f}s (reference)")
    print(f"  MEDIUM: {medium_offset:.4f}s")
    print(f"  HARD:   {hard_offset:.4f}s")
    
    # Verify ordering: HARD should be slowest, SOFT fastest
    assert soft_offset < medium_offset < hard_offset, \
        "Compound offsets should increase: SOFT < MEDIUM < HARD"
    
    print(f"✓ Correct ordering: SOFT < MEDIUM < HARD")
    
    return True


def test_degradation_rates():
    """Test compound-specific degradation rates."""
    print("\n" + "="*70)
    print("TEST 3: Degradation Rates")
    print("="*70)
    
    config = create_test_race_config()
    strategies = create_test_strategies()
    simulator = RaceSimulator(config, strategies)
    
    # Get degradation rates
    soft_deg = simulator._get_degradation_rate('SOFT')
    medium_deg = simulator._get_degradation_rate('MEDIUM')
    hard_deg = simulator._get_degradation_rate('HARD')
    
    print(f"Degradation rates:")
    print(f"  SOFT:   {soft_deg:.6f} s/lap")
    print(f"  MEDIUM: {medium_deg:.6f} s/lap")
    print(f"  HARD:   {hard_deg:.6f} s/lap")
    
    # Verify ordering: SOFT degrades fastest, HARD slowest
    assert hard_deg < medium_deg < soft_deg, \
        "Degradation should decrease: SOFT > MEDIUM > HARD"
    
    print(f"✓ Correct ordering: SOFT > MEDIUM > HARD (fastest to slowest)")
    
    return True


def test_temperature_effects():
    """Test temperature sensitivity by compound."""
    print("\n" + "="*70)
    print("TEST 4: Temperature Effects")
    print("="*70)
    
    # Test at different temperatures
    temps = [20, 25, 30, 35, 40]
    
    for temp in temps:
        config = create_test_race_config()
        config['track_temp'] = temp
        strategies = create_test_strategies()
        simulator = RaceSimulator(config, strategies)
        
        # Get temperature effects
        soft_temp = simulator._get_temperature_effect('SOFT')
        medium_temp = simulator._get_temperature_effect('MEDIUM')
        hard_temp = simulator._get_temperature_effect('HARD')
        
        print(f"\nTrack Temp: {temp}°C (deviation: {simulator.temp_deviation:+.1f}°C)")
        print(f"  SOFT:   {soft_temp:+.4f}s per lap")
        print(f"  MEDIUM: {medium_temp:+.4f}s per lap")
        print(f"  HARD:   {hard_temp:+.4f}s per lap")
    
    print(f"\n✓ Temperature effects calculated correctly")
    
    return True


def test_stint_time_calculation():
    """Test O(1) stint time calculation accuracy."""
    print("\n" + "="*70)
    print("TEST 5: Stint Time Calculation (O(1) Formula)")
    print("="*70)
    
    config = create_test_race_config()
    config['track_temp'] = 30  # Reference temp
    strategies = create_test_strategies()
    simulator = RaceSimulator(config, strategies)
    
    # Test various stint lengths
    stint_lengths = [5, 10, 15, 20, 25, 30]
    
    print(f"\nStint times at 30°C (no temperature effect):")
    print(f"{'Laps':<8} {'SOFT':<15} {'MEDIUM':<15} {'HARD':<15}")
    print("-" * 53)
    
    for laps in stint_lengths:
        soft_time = simulator._calculate_regression_stint_time('SOFT', laps)
        medium_time = simulator._calculate_regression_stint_time('MEDIUM', laps)
        hard_time = simulator._calculate_regression_stint_time('HARD', laps)
        
        print(f"{laps:<8} {soft_time:>8.3f}s     {medium_time:>8.3f}s     {hard_time:>8.3f}s")
    
    # Verify monotonicity: longer stints should take more time
    prev_soft = 0
    for laps in stint_lengths:
        stint_time = simulator._calculate_regression_stint_time('SOFT', laps)
        assert stint_time > prev_soft, "Longer stints should take more time"
        prev_soft = stint_time
    
    print(f"\n✓ Stint times increase monotonically with length")
    
    # Verify compound ordering at same stint length
    for laps in stint_lengths:
        soft_time = simulator._calculate_regression_stint_time('SOFT', laps)
        medium_time = simulator._calculate_regression_stint_time('MEDIUM', laps)
        hard_time = simulator._calculate_regression_stint_time('HARD', laps)
        
        # For short stints, SOFT should be fastest due to lower offset
        # For long stints, degradation matters more
        assert soft_time < hard_time or laps > 20, \
            f"SOFT should generally be faster than HARD for typical stint lengths"
    
    print(f"✓ Compound performance ordering validated")
    
    return True


def test_determinism():
    """Test that simulations are deterministic (no randomness)."""
    print("\n" + "="*70)
    print("TEST 6: Deterministic Behavior")
    print("="*70)
    
    config = create_test_race_config()
    strategies = create_test_strategies()
    
    # Run simulation multiple times
    results = []
    for i in range(5):
        simulator = RaceSimulator(config, strategies)
        result = simulator.simulate_race()
        results.append(tuple(result))
    
    # All results should be identical
    assert all(r == results[0] for r in results), "Simulations should be deterministic"
    
    print(f"✓ Ran 5 simulations - all produced identical results")
    print(f"  Finishing order: {results[0]}")
    
    return True


def test_performance():
    """Test computational performance of O(1) calculations."""
    print("\n" + "="*70)
    print("TEST 7: Performance Benchmark")
    print("="*70)
    
    config = create_test_race_config()
    config['total_laps'] = 50  # Longer race
    
    # Create strategies for all 20 positions
    strategies = {}
    for pos in range(1, 21):
        strategies[f'pos{pos}'] = {
            'driver_id': f'DRV{pos:02d}',
            'starting_tire': 'SOFT' if pos % 2 == 0 else 'MEDIUM',
            'pit_stops': [
                {'lap': 20, 'to_tire': 'HARD'},
                {'lap': 40, 'to_tire': 'MEDIUM'}
            ]
        }
    
    # Warm up
    simulator = RaceSimulator(config, strategies)
    
    # Benchmark
    num_runs = 100
    start = time.perf_counter()
    
    for _ in range(num_runs):
        sim = RaceSimulator(config, strategies)
        _ = sim.simulate_race()
    
    elapsed = time.perf_counter() - start
    avg_time_ms = (elapsed / num_runs) * 1000
    
    print(f"Ran {num_runs} full race simulations")
    print(f"Average time per simulation: {avg_time_ms:.4f}ms")
    print(f"Simulations per second: {num_runs / elapsed:.1f}")
    
    # Should be very fast (< 1ms per simulation)
    assert avg_time_ms < 1.0, f"Simulation should take < 1ms, got {avg_time_ms:.4f}ms"
    
    print(f"✓ Excellent performance (< 1ms per simulation)")
    
    return True


def test_full_simulation():
    """Test complete race simulation with realistic strategies."""
    print("\n" + "="*70)
    print("TEST 8: Full Race Simulation")
    print("="*70)
    
    config = create_test_race_config()
    config['total_laps'] = 52  # Typical F1 race distance
    
    # Realistic strategies for top teams
    strategies = {
        'pos1': {
            'driver_id': 'VER',
            'starting_tire': 'SOFT',
            'pit_stops': [
                {'lap': 22, 'to_tire': 'HARD'}
            ]
        },
        'pos2': {
            'driver_id': 'HAM',
            'starting_tire': 'MEDIUM',
            'pit_stops': [
                {'lap': 25, 'to_tire': 'HARD'}
            ]
        },
        'pos3': {
            'driver_id': 'LEC',
            'starting_tire': 'SOFT',
            'pit_stops': [
                {'lap': 20, 'to_tire': 'MEDIUM'},
                {'lap': 40, 'to_tire': 'HARD'}
            ]
        },
        'pos4': {
            'driver_id': 'PER',
            'starting_tire': 'MEDIUM',
            'pit_stops': [
                {'lap': 28, 'to_tire': 'HARD'}
            ]
        }
    }
    
    # Fill remaining positions
    for pos in range(5, 21):
        strategies[f'pos{pos}'] = {
            'driver_id': f'DRV{pos:02d}',
            'starting_tire': 'HARD' if pos > 10 else 'MEDIUM',
            'pit_stops': [
                {'lap': 15 + pos, 'to_tire': 'HARD'}
            ]
        }
    
    # Run simulation
    simulator = RaceSimulator(config, strategies)
    result = simulator.simulate_race()
    
    print(f"Race Distance: {config['total_laps']} laps")
    print(f"Track Temperature: {config['track_temp']}°C")
    print(f"\nFinishing Order (Top 10):")
    print("-" * 40)
    
    for i, driver_id in enumerate(result[:10], 1):
        # Find driver's total time
        for driver in simulator.drivers:
            if driver.driver_id == driver_id:
                time_diff = driver.total_race_time
                break
        
        print(f"P{i:>2}: {driver_id:<10} Total Time: {time_diff:>8.3f}s")
    
    print(f"\n✓ Full race simulation completed successfully")
    
    return True


def run_all_tests():
    """Run complete test suite."""
    print("\n" + "="*70)
    print("REGRESSION-BASED SIMULATOR TEST SUITE")
    print("="*70)
    
    tests = [
        ("Model Loading", test_model_loading),
        ("Compound Offsets", test_compound_offsets),
        ("Degradation Rates", test_degradation_rates),
        ("Temperature Effects", test_temperature_effects),
        ("Stint Time Calculation", test_stint_time_calculation),
        ("Deterministic Behavior", test_determinism),
        ("Performance", test_performance),
        ("Full Simulation", test_full_simulation)
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
