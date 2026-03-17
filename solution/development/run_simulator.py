#!/usr/bin/env python3
"""
F1 Race Simulator - Command Line Interface

Reads race configuration from stdin, runs simulation, outputs JSON result.

Usage:
    echo '{"race_config": {...}, "strategies": {...}}' | python run_simulator.py
    cat input.json | python run_simulator.py
    python run_simulator.py < input.json

Input format:
{
    "race_config": {
        "race_id": "race_001",
        "base_lap_time": 85.0,
        "total_laps": 52,
        "pit_lane_time": 25.0,
        "track_temp": 30.0
    },
    "strategies": {
        "pos1": {"driver_id": "D001", "starting_tire": "SOFT", "pit_stops": [...]},
        ...
    }
}

Output format:
{
    "race_id": "race_001",
    "finishing_positions": ["D006", "D018", ..., "D005"]
}
"""

import sys
import json

# Add solution directory to path
from pathlib import Path
solution_dir = Path(__file__).parent
sys.path.insert(0, str(solution_dir))

from core.simulator import RaceSimulator


def main():
    """Read input from stdin, run simulation, output JSON to stdout."""
    
    # Suppress all warnings and info messages
    import warnings
    warnings.filterwarnings('ignore')
    
    try:
        # Read all input from stdin
        input_data = sys.stdin.read()
        
        if not input_data.strip():
            error_response = {
                "error": "No input provided",
                "message": "Please provide JSON input via stdin"
            }
            print(json.dumps(error_response, indent=2))
            sys.exit(1)
        
        # Parse input JSON
        try:
            data = json.loads(input_data)
        except json.JSONDecodeError as e:
            error_response = {
                "error": "Invalid JSON",
                "message": str(e)
            }
            print(json.dumps(error_response, indent=2))
            sys.exit(1)
        
        # Extract required fields
        if 'race_config' not in data:
            error_response = {
                "error": "Missing race_config",
                "message": "Input must contain 'race_config' object"
            }
            print(json.dumps(error_response, indent=2))
            sys.exit(1)
        
        if 'strategies' not in data:
            error_response = {
                "error": "Missing strategies",
                "message": "Input must contain 'strategies' object"
            }
            print(json.dumps(error_response, indent=2))
            sys.exit(1)
        
        race_config = data['race_config']
        strategies = data['strategies']
        
        # Validate we have all 20 positions
        for i in range(1, 21):
            pos_key = f'pos{i}'
            if pos_key not in strategies:
                error_response = {
                    "error": "Missing strategy",
                    "message": f"Missing strategy for position {pos_key}"
                }
                print(json.dumps(error_response, indent=2))
                sys.exit(1)
        
        # Run simulation (use advanced model by default)
        simulator = RaceSimulator(race_config, strategies, use_advanced_model=True)
        finishing_order = simulator.simulate_race()
        
        # Verify exactly 20 drivers
        if len(finishing_order) != 20:
            error_response = {
                "error": "Invalid simulation result",
                "message": f"Expected 20 drivers, got {len(finishing_order)}"
            }
            print(json.dumps(error_response, indent=2))
            sys.exit(1)
        
        # Build output JSON
        race_id = race_config.get('race_id', 'unknown')
        
        output = {
            "race_id": race_id,
            "finishing_positions": finishing_order
        }
        
        # Output JSON to stdout (no extra whitespace)
        print(json.dumps(output))
        
        sys.exit(0)
        
    except Exception as e:
        error_response = {
            "error": "Simulation failed",
            "message": str(e),
            "type": type(e).__name__
        }
        print(json.dumps(error_response, indent=2))
        sys.exit(1)


if __name__ == '__main__':
    main()
