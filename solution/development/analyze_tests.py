#!/usr/bin/env python3
"""
Analyze what makes test cases different from historical races
"""

import json
from pathlib import Path

def analyze_test_cases():
    print("="*80)
    print("TEST CASE ANALYSIS")
    print("="*80)
    
    # Load first test case
    test1 = json.loads(Path("data/test_cases/inputs/test_001.json").read_text())
    expected1 = json.loads(Path("data/test_cases/expected_outputs/test_001.json").read_text())
    
    print(f"\nTest 1 Configuration:")
    print(f"  Track: {test1['race_config']['track']}")
    print(f"  Total Laps: {test1['race_config']['total_laps']}")
    print(f"  Base Lap Time: {test1['race_config']['base_lap_time']}")
    print(f"  Pit Lane Time: {test1['race_config']['pit_lane_time']}")
    print(f"  Track Temp: {test1['race_config']['track_temp']}°C")
    
    print(f"\nExpected Winner: {expected1['finishing_positions'][0]}")
    print(f"Expected Podium: {expected1['finishing_positions'][:3]}")
    
    # Analyze strategies
    print(f"\nStrategy Analysis:")
    strategies = test1['strategies']
    
    for pos_key in ['pos1', 'pos2', 'pos3']:
        strat = strategies[pos_key]
        print(f"\n  {pos_key} ({strat['driver_id']}):")
        print(f"    Starting Tire: {strat['starting_tire']}")
        print(f"    Pit Stops: {len(strat.get('pit_stops', []))}")
        for stop in strat.get('pit_stops', []):
            print(f"      Lap {stop['lap']}: {stop['from_tire']} → {stop['to_tire']}")
    
    # Load a historical race for comparison
    hist_races = json.loads(Path("data/historical_races/races_00000-00999.json").read_text())
    hist_race = hist_races[0]
    
    print(f"\n{'='*80}")
    print(f"HISTORICAL RACE COMPARISON")
    print(f"{'='*80}")
    print(f"\nHistorical Race Configuration:")
    print(f"  Track: {hist_race['race_config']['track']}")
    print(f"  Total Laps: {hist_race['race_config']['total_laps']}")
    print(f"  Base Lap Time: {hist_race['race_config']['base_lap_time']}")
    print(f"  Pit Lane Time: {hist_race['race_config']['pit_lane_time']}")
    print(f"  Track Temp: {hist_race['race_config']['track_temp']}°C")
    
    print(f"\nActual Winner: {hist_race['finishing_positions'][0]}")
    print(f"Actual Podium: {hist_race['finishing_positions'][:3]}")
    
    # Check if there's a pattern
    print(f"\n{'='*80}")
    print(f"PATTERN DETECTION")
    print(f"{'='*80}")
    
    # Count pit stops in test vs historical
    test_pit_counts = []
    hist_pit_counts = []
    
    for pos_key, strat in test1['strategies'].items():
        test_pit_counts.append(len(strat.get('pit_stops', [])))
    
    for pos_key, strat in hist_race['strategies'].items():
        hist_pit_counts.append(len(strat.get('pit_stops', [])))
    
    print(f"\nTest Case Pit Stop Distribution:")
    for i in range(max(test_pit_counts)+1):
        count = test_pit_counts.count(i)
        if count > 0:
            print(f"  {i} stops: {count} drivers")
    
    print(f"\nHistorical Race Pit Stop Distribution:")
    for i in range(max(hist_pit_counts)+1):
        count = hist_pit_counts.count(i)
        if count > 0:
            print(f"  {i} stops: {count} drivers")

if __name__ == "__main__":
    analyze_test_cases()
