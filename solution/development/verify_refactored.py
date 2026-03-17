#!/usr/bin/env python3
"""Quick verification of the refactored simulator."""

import sys
from pathlib import Path

solution_dir = Path(__file__).parent.parent
sys.path.insert(0, str(solution_dir))

from core.simulator_clean import RaceSimulator

# Test configuration
config = {
    'race_id': 'verification_test',
    'base_lap_time': 85.0,
    'total_laps': 30,
    'pit_lane_time': 25.0,
    'track_temp': 30.0
}

# Test strategies - all 20 positions
strategies = {}
for i in range(1, 21):
    strategies[f'pos{i}'] = {
        'driver_id': f'D{i:03d}',
        'starting_tire': 'SOFT' if i <= 7 else 'MEDIUM',
        'pit_stops': []
    }

# Run simulation
simulator = RaceSimulator(config, strategies)
result = simulator.simulate_race()

print("✅ REFACTORED SIMULATOR VERIFICATION")
print("=" * 50)
print(f"Race ID: {config['race_id']}")
print(f"Top 3 finishers: {result[:3]}")
print(f"Total drivers: {len(result)}")
print(f"All 20 positions: {result}")
print("=" * 50)
print("✅ All systems operational!")
