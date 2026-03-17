#!/usr/bin/env python3
"""Check pit stop patterns across ALL test cases"""

import json
from pathlib import Path

test_files = sorted(Path("data/test_cases/inputs").glob("test_*.json"))

print(f"Analyzing {len(test_files)} test cases...\n")

all_one_stop = True
pit_stop_distribution = {}

for test_file in test_files:
    test_data = json.loads(test_file.read_text())
    
    for pos_key, strat in test_data['strategies'].items():
        n_stops = len(strat.get('pit_stops', []))
        
        if n_stops not in pit_stop_distribution:
            pit_stop_distribution[n_stops] = 0
        pit_stop_distribution[n_stops] += 1
        
        if n_stops != 1:
            all_one_stop = False

print("Pit Stop Distribution Across ALL Test Cases:")
for n_stops in sorted(pit_stop_distribution.keys()):
    count = pit_stop_distribution[n_stops]
    print(f"  {n_stops} stops: {count} drivers")

print(f"\n{'='*80}")
if all_one_stop:
    print("🎯 BREAKTHROUGH: ALL test case drivers have EXACTLY 1 pit stop!")
    print("This is DIFFERENT from historical data!")
else:
    print("Test cases have mixed pit stop strategies")
print(f"{'='*80}\n")

# Check if there's a correlation with starting position
print("Checking starting tire preferences...")
tire_counts = {"SOFT": 0, "MEDIUM": 0, "HARD": 0}

for test_file in test_files[:10]:  # First 10 tests
    test_data = json.loads(test_file.read_text())
    for pos_key, strat in test_data['strategies'].items():
        tire_counts[strat['starting_tire']] += 1

print(f"\nStarting Tire Distribution (first 10 tests):")
for tire, count in tire_counts.items():
    print(f"  {tire}: {count} drivers ({count/200*100:.1f}%)")
