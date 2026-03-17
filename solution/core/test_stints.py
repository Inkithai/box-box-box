"""
Test suite for tire stint conversion functionality.

Tests the convert_strategy_to_stints function and Driver class integration.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.driver import convert_strategy_to_stints, Driver


def test_basic_stint_conversion():
    """Test basic stint conversion with multiple pit stops."""
    print("=" * 70)
    print("TEST 1: Basic Stint Conversion")
    print("=" * 70)
    
    strategy = {
        'starting_tire': 'SOFT',
        'pit_stops': [
            {'lap': 18, 'to_tire': 'MEDIUM'},
            {'lap': 38, 'to_tire': 'HARD'}
        ]
    }
    
    total_laps = 50
    stints = convert_strategy_to_stints(strategy, total_laps)
    
    print(f"\nStrategy: Start on SOFT, pit at 18 (MEDIUM), pit at 38 (HARD)")
    print(f"Total laps: {total_laps}")
    print(f"\nConverted stints:")
    for i, stint in enumerate(stints):
        print(f"  Stint {i+1}: Laps {stint['start_lap']}-{stint['end_lap']} on {stint['tire']}")
    
    # Validate results
    assert len(stints) == 3, f"Expected 3 stints, got {len(stints)}"
    
    assert stints[0]['start_lap'] == 1, "First stint should start at lap 1"
    assert stints[0]['end_lap'] == 17, "First stint should end at lap 17"
    assert stints[0]['tire'] == 'SOFT', "First stint should be on SOFT"
    
    assert stints[1]['start_lap'] == 18, "Second stint should start at lap 18"
    assert stints[1]['end_lap'] == 37, "Second stint should end at lap 37"
    assert stints[1]['tire'] == 'MEDIUM', "Second stint should be on MEDIUM"
    
    assert stints[2]['start_lap'] == 38, "Third stint should start at lap 38"
    assert stints[2]['end_lap'] == 50, "Third stint should end at lap 50"
    assert stints[2]['tire'] == 'HARD', "Third stint should be on HARD"
    
    print("\n✓ All assertions passed")


def test_no_pit_stops():
    """Test strategy with no pit stops (single stint)."""
    print("\n" + "=" * 70)
    print("TEST 2: No Pit Stops (Single Stint)")
    print("=" * 70)
    
    strategy = {
        'starting_tire': 'HARD',
        'pit_stops': []
    }
    
    total_laps = 30
    stints = convert_strategy_to_stints(strategy, total_laps)
    
    print(f"\nStrategy: Start on HARD, no pit stops")
    print(f"Total laps: {total_laps}")
    print(f"\nConverted stints:")
    for i, stint in enumerate(stints):
        print(f"  Stint {i+1}: Laps {stint['start_lap']}-{stint['end_lap']} on {stint['tire']}")
    
    assert len(stints) == 1, f"Expected 1 stint, got {len(stints)}"
    assert stints[0]['start_lap'] == 1
    assert stints[0]['end_lap'] == 30
    assert stints[0]['tire'] == 'HARD'
    
    print("\n✓ Single stint correctly created")


def test_one_pit_stop():
    """Test strategy with one pit stop (two stints)."""
    print("\n" + "=" * 70)
    print("TEST 3: One Pit Stop (Two Stints)")
    print("=" * 70)
    
    strategy = {
        'starting_tire': 'MEDIUM',
        'pit_stops': [
            {'lap': 20, 'to_tire': 'SOFT'}
        ]
    }
    
    total_laps = 40
    stints = convert_strategy_to_stints(strategy, total_laps)
    
    print(f"\nStrategy: Start on MEDIUM, pit at 20 (SOFT)")
    print(f"Total laps: {total_laps}")
    print(f"\nConverted stints:")
    for i, stint in enumerate(stints):
        print(f"  Stint {i+1}: Laps {stint['start_lap']}-{stint['end_lap']} on {stint['tire']}")
    
    assert len(stints) == 2, f"Expected 2 stints, got {len(stints)}"
    assert stints[0]['start_lap'] == 1
    assert stints[0]['end_lap'] == 19
    assert stints[0]['tire'] == 'MEDIUM'
    assert stints[1]['start_lap'] == 20
    assert stints[1]['end_lap'] == 40
    assert stints[1]['tire'] == 'SOFT'
    
    print("\n✓ Two stints correctly created")


def test_unsorted_pit_stops():
    """Test that pit stops are automatically sorted by lap."""
    print("\n" + "=" * 70)
    print("TEST 4: Unsorted Pit Stops (Auto-Sort)")
    print("=" * 70)
    
    strategy = {
        'starting_tire': 'SOFT',
        'pit_stops': [
            {'lap': 35, 'to_tire': 'HARD'},
            {'lap': 15, 'to_tire': 'MEDIUM'},
            {'lap': 25, 'to_tire': 'SOFT'}
        ]
    }
    
    total_laps = 50
    stints = convert_strategy_to_stints(strategy, total_laps)
    
    print(f"\nStrategy: Start on SOFT, pits at 35, 15, 25 (unsorted)")
    print(f"Total laps: {total_laps}")
    print(f"\nConverted stints (should be sorted):")
    for i, stint in enumerate(stints):
        print(f"  Stint {i+1}: Laps {stint['start_lap']}-{stint['end_lap']} on {stint['tire']}")
    
    assert len(stints) == 4, f"Expected 4 stints, got {len(stints)}"
    
    # Verify they're in correct order despite unsorted input
    assert stints[0]['tire'] == 'SOFT'
    assert stints[1]['tire'] == 'MEDIUM'
    assert stints[2]['tire'] == 'SOFT'
    assert stints[3]['tire'] == 'HARD'
    
    print("\n✓ Pit stops correctly sorted")


def test_invalid_tire_compound():
    """Test that invalid tire compounds raise ValueError."""
    print("\n" + "=" * 70)
    print("TEST 5: Invalid Tire Compound")
    print("=" * 70)
    
    strategy = {
        'starting_tire': 'ULTRASOFT',  # Invalid
        'pit_stops': []
    }
    
    try:
        convert_strategy_to_stints(strategy, total_laps=30)
        print("✗ Should have raised ValueError for invalid tire")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {e}")


def test_invalid_pit_stop_lap():
    """Test that out-of-range pit stop laps raise ValueError."""
    print("\n" + "=" * 70)
    print("TEST 6: Invalid Pit Stop Lap")
    print("=" * 70)
    
    # Test lap 0
    strategy = {
        'starting_tire': 'SOFT',
        'pit_stops': [
            {'lap': 0, 'to_tire': 'MEDIUM'}  # Invalid: lap 0
        ]
    }
    
    try:
        convert_strategy_to_stints(strategy, total_laps=30)
        print("✗ Should have raised ValueError for lap 0")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"✓ Correctly raised ValueError for lap 0: {e}")
    
    # Test lap > total_laps
    strategy = {
        'starting_tire': 'SOFT',
        'pit_stops': [
            {'lap': 31, 'to_tire': 'MEDIUM'}  # Invalid: lap 31 in 30-lap race
        ]
    }
    
    try:
        convert_strategy_to_stints(strategy, total_laps=30)
        print("✗ Should have raised ValueError for lap > total_laps")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"✓ Correctly raised ValueError for lap > total_laps: {e}")


def test_invalid_pit_stop_tire():
    """Test that invalid tire in pit stop raises ValueError."""
    print("\n" + "=" * 70)
    print("TEST 7: Invalid Pit Stop Tire")
    print("=" * 70)
    
    strategy = {
        'starting_tire': 'SOFT',
        'pit_stops': [
            {'lap': 15, 'to_tire': 'INTERMEDIATE'}  # Invalid tire
        ]
    }
    
    try:
        convert_strategy_to_stints(strategy, total_laps=30)
        print("✗ Should have raised ValueError for invalid pit stop tire")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {e}")


def test_driver_integration():
    """Test Driver class integration with stints."""
    print("\n" + "=" * 70)
    print("TEST 8: Driver Class Integration")
    print("=" * 70)
    
    strategy = {
        'driver_id': 'D001',
        'starting_tire': 'MEDIUM',
        'pit_stops': [
            {'lap': 15, 'to_tire': 'SOFT'},
            {'lap': 30, 'to_tire': 'HARD'}
        ]
    }
    
    total_laps = 45
    
    driver = Driver('D001', strategy, total_laps)
    
    print(f"\nDriver: {driver.driver_id}")
    print(f"Total laps: {total_laps}")
    print(f"Number of stints: {len(driver.stints)}")
    print(f"\nStints:")
    for i, stint in enumerate(driver.stints):
        print(f"  Stint {i+1}: Laps {stint['start_lap']}-{stint['end_lap']} on {stint['tire']}")
    
    # Test get_current_tire for various laps
    print(f"\nTire compounds by lap:")
    test_laps = [1, 10, 15, 20, 30, 40, 45]
    for lap in test_laps:
        tire = driver.get_current_tire(lap)
        age = driver.get_tire_age(lap)
        print(f"  Lap {lap:2d}: {tire:6s} (age: {age} laps)")
    
    # Validate stint storage
    assert len(driver.stints) == 3, f"Expected 3 stints, got {len(driver.stints)}"
    assert driver.stints[0]['tire'] == 'MEDIUM'
    assert driver.stints[1]['tire'] == 'SOFT'
    assert driver.stints[2]['tire'] == 'HARD'
    
    print("\n✓ Driver integration successful")


def test_stint_coverage():
    """Test that stints cover all laps exactly once."""
    print("\n" + "=" * 70)
    print("TEST 9: Complete Lap Coverage")
    print("=" * 70)
    
    strategy = {
        'starting_tire': 'SOFT',
        'pit_stops': [
            {'lap': 10, 'to_tire': 'MEDIUM'},
            {'lap': 20, 'to_tire': 'HARD'},
            {'lap': 30, 'to_tire': 'SOFT'}
        ]
    }
    
    total_laps = 40
    stints = convert_strategy_to_stints(strategy, total_laps)
    
    print(f"\nStrategy: 4 stints over {total_laps} laps")
    print(f"Stints: {len(stints)}")
    
    # Build set of all laps covered
    covered_laps = set()
    for stint in stints:
        for lap in range(stint['start_lap'], stint['end_lap'] + 1):
            if lap in covered_laps:
                print(f"✗ Lap {lap} covered multiple times!")
                assert False, f"Lap {lap} covered multiple times"
            covered_laps.add(lap)
    
    # Check all laps 1..total_laps are covered
    expected_laps = set(range(1, total_laps + 1))
    missing_laps = expected_laps - covered_laps
    extra_laps = covered_laps - expected_laps
    
    if missing_laps:
        print(f"✗ Missing laps: {missing_laps}")
        assert False, f"Missing laps: {missing_laps}"
    
    if extra_laps:
        print(f"✗ Extra laps: {extra_laps}")
        assert False, f"Extra laps: {extra_laps}"
    
    print(f"✓ All laps 1-{total_laps} covered exactly once")


def test_edge_case_first_lap_pit():
    """Test edge case: pit stop on first lap."""
    print("\n" + "=" * 70)
    print("TEST 10: Edge Case - Pit on First Lap")
    print("=" * 70)
    
    strategy = {
        'starting_tire': 'SOFT',
        'pit_stops': [
            {'lap': 1, 'to_tire': 'MEDIUM'}  # Pit immediately
        ]
    }
    
    total_laps = 30
    stints = convert_strategy_to_stints(strategy, total_laps)
    
    print(f"\nStrategy: Start on SOFT, pit at lap 1 (MEDIUM)")
    print(f"Total laps: {total_laps}")
    print(f"\nConverted stints:")
    for i, stint in enumerate(stints):
        print(f"  Stint {i+1}: Laps {stint['start_lap']}-{stint['end_lap']} on {stint['tire']}")
    
    # First stint should be empty (laps 1-0 is invalid, so skipped)
    # Second stint should be laps 1-30 on MEDIUM
    assert len(stints) == 1, f"Expected 1 stint (first is empty), got {len(stints)}"
    assert stints[0]['start_lap'] == 1
    assert stints[0]['end_lap'] == 30
    assert stints[0]['tire'] == 'MEDIUM'
    
    print("\n✓ First-lap pit handled correctly (first stint skipped)")


def main():
    """Run all stint conversion tests."""
    print("\n" + "=" * 70)
    print("TIRE STINT CONVERSION - TEST SUITE")
    print("=" * 70)
    
    test_basic_stint_conversion()
    test_no_pit_stops()
    test_one_pit_stop()
    test_unsorted_pit_stops()
    test_invalid_tire_compound()
    test_invalid_pit_stop_lap()
    test_invalid_pit_stop_tire()
    test_driver_integration()
    test_stint_coverage()
    test_edge_case_first_lap_pit()
    
    print("\n" + "=" * 70)
    print("ALL TESTS COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print("\nThe stint conversion system is working correctly!")
    print("Next step: Update the simulator to use stints instead of pit stops.")


if __name__ == '__main__':
    main()
