#!/usr/bin/env python3
"""
F1 Race Simulator - Production CLI Interface

Clean JSON stdin/stdout interface with comprehensive error handling.
No debug output - only valid JSON results.

Usage:
    echo '{"race_config": {...}, "strategies": {...}}' | python run_simulator_clean.py
    cat input.json | python run_simulator_clean.py
"""

import sys
import json
from typing import Dict, Any

# Add solution directory to path
from pathlib import Path
solution_dir = Path(__file__).parent
sys.path.insert(0, str(solution_dir))

from core.simulator_clean import simulate_race_json


def read_input() -> Dict[str, Any]:
    """Read and parse JSON from stdin.
    
    Returns:
        Parsed input dict with race_config and strategies
        
    Raises:
        ValueError: If input is invalid
    """
    try:
        input_text = sys.stdin.read().strip()
        
        if not input_text:
            raise ValueError("Empty input")
        
        return json.loads(input_text)
    
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {str(e)}")


def validate_input(data: Dict) -> tuple:
    """Validate input structure.
    
    Args:
        data: Parsed input dict
        
    Returns:
        Tuple of (race_config, strategies)
        
    Raises:
        ValueError: If validation fails
    """
    # Check required fields
    if 'race_config' not in data:
        raise ValueError("Missing 'race_config' field")
    if 'strategies' not in data:
        raise ValueError("Missing 'strategies' field")
    
    race_config = data['race_config']
    strategies = data['strategies']
    
    # Validate race config
    required_config = ['base_lap_time', 'total_laps', 'pit_lane_time', 'track_temp']
    for field in required_config:
        if field not in race_config:
            raise ValueError(f"Missing race_config.{field}")
    
    # Validate strategies count
    if not isinstance(strategies, dict):
        raise ValueError("'strategies' must be a dictionary")
    
    if len(strategies) != 20:
        raise ValueError(f"Expected 20 strategies, got {len(strategies)}")
    
    # Validate each strategy has required fields
    for pos_key, strategy in strategies.items():
        if 'starting_tire' not in strategy:
            raise ValueError(f"Missing 'starting_tire' in {pos_key}")
    
    return race_config, strategies


def create_error_response(error_type: str, message: str) -> Dict:
    """Create standardized error response.
    
    Args:
        error_type: Type of error (e.g., 'ValidationError')
        message: Human-readable error message
        
    Returns:
        Error response dict
    """
    return {
        'error': error_type,
        'message': message
    }


def main():
    """Main entry point."""
    try:
        # Read input
        data = read_input()
        
        # Validate
        race_config, strategies = validate_input(data)
        
        # Run simulation
        result = simulate_race_json(race_config, strategies)
        
        # Output result (compact JSON, no extra whitespace)
        output_json = json.dumps(result, separators=(',', ':'))
        print(output_json)
        
    except ValueError as e:
        # Validation/input errors
        error_response = create_error_response('ValidationError', str(e))
        output_json = json.dumps(error_response, separators=(',', ':'))
        print(output_json)
        sys.exit(1)
        
    except Exception as e:
        # Unexpected errors
        error_response = create_error_response('InternalError', str(e))
        output_json = json.dumps(error_response, separators=(',', ':'))
        print(output_json)
        sys.exit(1)


if __name__ == '__main__':
    main()
