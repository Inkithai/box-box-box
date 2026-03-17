"""
Test script to verify the race simulator works correctly.
Run this from the solution directory.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from core.simulator import RaceSimulator
from core.driver import Driver
from models.lap_time import LapTimeCalculator
from models.tire import TireModel


def test_tire_model():
    """Test tire compound calculations."""
    print("Testing Tire Model...")
    
    # Test compound offsets
    soft_offset = TireModel.get_compound_offset('SOFT')
    medium_offset = TireModel.get_compound_offset('MEDIUM')
    hard_offset = TireModel.get_compound_offset('HARD')
    
    print(f"  SOFT offset: {soft_offset}s (should be fastest)")
    print(f"  MEDIUM offset: {medium_offset}s (should be +{medium_offset - soft_offset}s)")
    print(f"  HARD offset: {hard_offset}s (should be slowest, +{hard_offset - soft_offset}s)")
    
    # Test degradation
    soft_degradation_lap1 = TireModel.calculate_degradation('SOFT', 1, 30)
    soft_degradation_lap10 = TireModel.calculate_degradation('SOFT', 10, 30)
    
    print(f"  SOFT degradation at lap 1: +{soft_degradation_lap1:.3f}s")
    print(f"  SOFT degradation at lap 10: +{soft_degradation_lap10:.3f}s")
    
    # Test temperature effect
    degradation_cool = TireModel.calculate_degradation('SOFT', 5, 20)
    degradation_hot = TireModel.calculate_degradation('SOFT', 5, 40)
    
    print(f"  SOFT degradation at 20°C (lap 5): +{degradation_cool:.3f}s")
    print(f"  SOFT degradation at 40°C (lap 5): +{degradation_hot:.3f}s")
    print()


def test_lap_time_calculator():
    """Test lap time calculations."""
    print("Testing Lap Time Calculator...")
    
    base_time = 85.0
    track_temp = 30
    
    # Fresh tires (age 1)
    lap_soft = LapTimeCalculator.calculate(base_time, 'SOFT', 1, track_temp)
    lap_medium = LapTimeCalculator.calculate(base_time, 'MEDIUM', 1, track_temp)
    lap_hard = LapTimeCalculator.calculate(base_time, 'HARD', 1, track_temp)
    
    print(f"  Lap 1 with fresh tires (base: {base_time}s):")
    print(f"    SOFT: {lap_soft:.3f}s")
    print(f"    MEDIUM: {lap_medium:.3f}s (+{lap_medium - lap_soft:.3f}s)")
    print(f"    HARD: {lap_hard:.3f}s (+{lap_hard - lap_soft:.3f}s)")
    
    # Old tires (age 20)
    lap_soft_old = LapTimeCalculator.calculate(base_time, 'SOFT', 20, track_temp)
    lap_hard_old = LapTimeCalculator.calculate(base_time, 'HARD', 20, track_temp)
    
    print(f"  Lap 20 with old tires:")
    print(f"    SOFT: {lap_soft_old:.3f}s (degraded by +{lap_soft_old - lap_soft:.3f}s)")
    print(f"    HARD: {lap_hard_old:.3f}s (degraded by +{lap_hard_old - lap_hard:.3f}s)")
    print()


def test_driver():
    """Test driver state management."""
    print("Testing Driver State Management...")
    
    strategy = {
        'driver_id': 'D001',
        'starting_tire': 'MEDIUM',
        'pit_stops': [
            {'lap': 10, 'to_tire': 'SOFT'},
            {'lap': 20, 'to_tire': 'HARD'}
        ]
    }
    
    total_laps = 30
    driver = Driver('D001', strategy, total_laps)
    
    print(f"  Driver: {driver.driver_id}")
    print(f"  Starting tire: {driver.starting_tire}")
    print(f"  Planned pit stops: {len(driver.pit_stops)}")
    
    # Simulate first few laps using the new stint-based approach
    for lap in range(1, 12):
        # Update stint for this lap
        driver.update_current_stint(lap)
        
        # Get tire and age for this lap
        tire = driver.get_current_tire(lap)
        age = driver.get_tire_age(lap)
        
        print(f"  Lap {lap}: Tire={tire}, Age={age}")
        
        # Check if pitting at end of this lap
        if driver.should_pit_this_lap(lap):
            pit_info = driver.get_pit_stop_info(lap)
            if pit_info:
                print(f"           Pitting! {pit_info['from_tire']} -> {pit_info['to_tire']}")
                driver.execute_pit_stop(22.0)  # 22s pit lane time
    
    print(f"  Total race time so far: {driver.get_total_time():.3f}s")
    print()


def test_full_simulation():
    """Test a complete race simulation with sample data."""
    print("Testing Full Race Simulation...")
    
    race_config = {
        'track': 'Test Track',
        'total_laps': 30,
        'base_lap_time': 85.0,
        'pit_lane_time': 22.0,
        'track_temp': 32
    }
    
    # Create simple strategies for 3 drivers (simplified test)
    strategies = {
        f'pos{i}': {
            'driver_id': f'D{i:03d}',
            'starting_tire': 'MEDIUM' if i % 2 == 0 else 'SOFT',
            'pit_stops': [
                {'lap': 15, 'from_tire': 'MEDIUM' if i % 2 == 0 else 'SOFT', 'to_tire': 'HARD'}
            ] if i <= 6 else []  # Some drivers pit, some don't
        }
        for i in range(1, 21)
    }
    
    simulator = RaceSimulator(race_config, strategies)
    finishing_order = simulator.simulate_race()
    
    print(f"  Race: {race_config['total_laps']} laps at {race_config['track']}")
    print(f"  Track temperature: {race_config['track_temp']}°C")
    print(f"  Finishing order (Top 5):")
    for i, driver_id in enumerate(finishing_order[:5], 1):
        print(f"    {i}. {driver_id}")
    print(f"  ... ({len(finishing_order)} total drivers)")
    print()


def main():
    """Run all tests."""
    print("=" * 60)
    print("Race Simulator Component Tests")
    print("=" * 60)
    print()
    
    test_tire_model()
    test_lap_time_calculator()
    test_driver()
    test_full_simulation()
    
    print("=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == '__main__':
    main()
