#!/usr/bin/env python3
"""
Test Suite - Clean F1 Race Simulator

Comprehensive tests for:
- Tire physics model (quadratic degradation)
- Driver stint management
- Race simulation engine
- JSON I/O interface
- Deterministic behavior
- Performance benchmarks
"""

import sys
import json
import time
from pathlib import Path

# Add solution directory to path
solution_dir = Path(__file__).parent.parent
sys.path.insert(0, str(solution_dir))

from models.tire_physics import (
    calculate_lap_time,
    calculate_stint_time,
    get_compound,
    TIRE_COMPOUNDS
)
from core.driver_clean import Driver, create_drivers_from_strategies
from core.simulator_clean import RaceSimulator, simulate_race_json


def test_tire_physics():
    """Test tire physics calculations."""
    print("=" * 60)
    print("TIRE PHYSICS TESTS")
    print("=" * 60)
    
    # Test 1: Compound properties
    print("\n1. Testing compound properties...")
    for compound in ['SOFT', 'MEDIUM', 'HARD']:
        props = get_compound(compound)
        assert props.name == compound
        assert props.base_offset >= 0
        assert props.linear_degradation > 0
        assert props.quadratic_degradation > 0
        print(f"   ✓ {compound}: linear={props.linear_degradation:.4f}, quad={props.quadratic_degradation:.6f}")
    
    # Test 2: Lap time calculation
    print("\n2. Testing lap time calculation...")
    lap_time = calculate_lap_time('SOFT', 5, 30.0, 85.0)
    expected_base = 85.0 + 0.0  # base + SOFT offset
    expected_deg = 0.12 * 5 + 0.0048 * (5 ** 2)  # linear + quadratic
    expected_temp = 0.035 * abs(30.0 - 28.0)  # temp effect
    expected_total = expected_base + expected_deg + expected_temp
    
    assert abs(lap_time - expected_total) < 1e-10, f"Lap time mismatch: {lap_time} vs {expected_total}"
    print(f"   ✓ Lap time at age 5: {lap_time:.6f}s")
    
    # Test 3: Degradation progression
    print("\n3. Testing degradation progression...")
    times = []
    for age in [1, 5, 10, 15, 20]:
        t = calculate_lap_time('SOFT', age, 30.0, 85.0)
        times.append(t)
        print(f"      Age {age:2d}: {t:.6f}s (Δ{(t-times[0]):.3f}s)")
    
    # Verify degradation is increasing (monotonic)
    for i in range(1, len(times)):
        assert times[i] > times[i-1], "Degradation should increase lap time"
    print("   ✓ Monotonic degradation confirmed")
    
    # Test 4: Stint time calculation (O(1) formula)
    print("\n4. Testing stint time calculation...")
    stint_time = calculate_stint_time('SOFT', 10, 30.0, 85.0)
    print(f"   ✓ 10-lap SOFT stint: {stint_time:.6f}s")
    
    # Verify against iterative calculation
    iterative_sum = 0.0
    for lap in range(1, 11):
        iterative_sum += calculate_lap_time('SOFT', lap, 30.0, 85.0)
    
    diff = abs(stint_time - iterative_sum)
    assert diff < 1e-9, f"Stint time mismatch: {stint_time} vs {iterative_sum}"
    print(f"   ✓ O(1) formula matches iteration (diff={diff:.2e})")
    
    # Test 5: Temperature effects
    print("\n5. Testing temperature sensitivity...")
    for temp in [20, 25, 30, 35]:
        t = calculate_lap_time('SOFT', 5, float(temp), 85.0)
        print(f"      {temp}°C: {t:.6f}s")
    
    print("\n✅ All tire physics tests passed\n")


def test_driver_model():
    """Test driver and stint management."""
    print("=" * 60)
    print("DRIVER MODEL TESTS")
    print("=" * 60)
    
    # Test 1: Simple strategy (no pit stops)
    print("\n1. Testing no-stop strategy...")
    strategy = {'starting_tire': 'SOFT', 'pit_stops': []}
    driver = Driver('VER', strategy, 30)
    
    assert len(driver.stints) == 1
    assert driver.stints[0]['start_lap'] == 1
    assert driver.stints[0]['end_lap'] == 30
    assert driver.stints[0]['tire'] == 'SOFT'
    print(f"   ✓ Single stint: laps 1-30 on SOFT")
    
    # Test 2: One pit stop
    print("\n2. Testing one-stop strategy...")
    strategy = {
        'starting_tire': 'SOFT',
        'pit_stops': [{'lap': 15, 'to_tire': 'HARD'}]
    }
    driver = Driver('HAM', strategy, 30)
    
    assert len(driver.stints) == 2
    assert driver.stints[0] == {'start_lap': 1, 'end_lap': 14, 'tire': 'SOFT'}
    assert driver.stints[1] == {'start_lap': 15, 'end_lap': 30, 'tire': 'HARD'}
    print(f"   ✓ Two stints: {driver.stints}")
    
    # Test 3: Tire queries
    print("\n3. Testing tire queries...")
    for lap in [1, 10, 15, 20, 30]:
        tire = driver.get_tire_at_lap(lap)
        age = driver.get_tire_age_at_lap(lap)
        print(f"      Lap {lap:2d}: {tire:6s} (age {age})")
    
    # Test 4: Invalid strategy
    print("\n4. Testing validation...")
    try:
        strategy = {'starting_tire': 'INVALID', 'pit_stops': []}
        driver = Driver('TEST', strategy, 30)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"   ✓ Caught invalid tire: {e}")
    
    print("\n✅ All driver model tests passed\n")


def test_race_simulation():
    """Test complete race simulation."""
    print("=" * 60)
    print("RACE SIMULATION TESTS")
    print("=" * 60)
    
    # Create test config
    config = {
        'race_id': 'test_001',
        'base_lap_time': 85.0,
        'total_laps': 30,
        'pit_lane_time': 25.0,
        'track_temp': 30.0
    }
    
    # Create test strategies
    strategies = {}
    for pos in range(1, 21):
        strategies[f'pos{pos}'] = {
            'driver_id': f'D{pos:03d}',
            'starting_tire': 'SOFT' if pos <= 7 else 'MEDIUM',
            'pit_stops': []
        }
    
    # Test 1: Basic simulation
    print("\n1. Testing basic simulation...")
    result = simulate_race_json(config, strategies)
    
    assert 'race_id' in result
    assert 'finishing_positions' in result
    assert len(result['finishing_positions']) == 20
    print(f"   ✓ Race ID: {result['race_id']}")
    print(f"   ✓ Top 3: {result['finishing_positions'][:3]}")
    
    # Test 2: Determinism
    print("\n2. Testing determinism...")
    result2 = simulate_race_json(config, strategies)
    assert result == result2, "Results should be identical"
    print("   ✓ Identical results on repeated runs")
    
    # Test 3: Performance
    print("\n3. Testing performance...")
    start = time.perf_counter()
    num_runs = 100
    for _ in range(num_runs):
        simulate_race_json(config, strategies)
    elapsed = time.perf_counter() - start
    per_run = (elapsed / num_runs) * 1000  # ms
    
    print(f"   ✓ {num_runs} simulations in {elapsed*1000:.2f}ms")
    print(f"   ✓ Average: {per_run:.3f}ms per simulation")
    assert per_run < 10.0, f"Performance regression: {per_run:.3f}ms > 10ms"
    
    print("\n✅ All simulation tests passed\n")


def test_json_interface():
    """Test JSON stdin/stdout interface."""
    print("=" * 60)
    print("JSON INTERFACE TESTS")
    print("=" * 60)
    
    # Test 1: Valid input
    print("\n1. Testing valid input processing...")
    input_data = {
        'race_config': {
            'race_id': 'json_test',
            'base_lap_time': 85.0,
            'total_laps': 20,
            'pit_lane_time': 25.0,
            'track_temp': 30.0
        },
        'strategies': {
            f'pos{i}': {
                'driver_id': f'D{i:03d}',
                'starting_tire': 'SOFT',
                'pit_stops': []
            }
            for i in range(1, 21)
        }
    }
    
    # Parse and validate
    race_config = input_data['race_config']
    strategies = input_data['strategies']
    
    assert len(strategies) == 20
    print("   ✓ Input structure validated")
    
    # Test 2: Output format
    print("\n2. Testing output format...")
    result = simulate_race_json(race_config, strategies)
    
    assert 'race_id' in result
    assert 'finishing_positions' in result
    assert isinstance(result['finishing_positions'], list)
    assert len(result['finishing_positions']) == 20
    
    # Verify JSON serializable
    json_str = json.dumps(result)
    assert len(json_str) > 0
    print(f"   ✓ Output JSON length: {len(json_str)} chars")
    
    print("\n✅ All JSON interface tests passed\n")


def run_all_tests():
    """Run complete test suite."""
    print("\n" + "=" * 60)
    print("CLEAN F1 RACE SIMULATOR - TEST SUITE")
    print("=" * 60)
    
    try:
        test_tire_physics()
        test_driver_model()
        test_race_simulation()
        test_json_interface()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
