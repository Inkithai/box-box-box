"""
JSON I/O Utilities - Handle input parsing and output formatting.
"""

import json
from typing import Dict, List, Tuple


def load_race_input(input_data: dict) -> Tuple[str, dict, dict]:
    """
    Load and validate race input from JSON.
    
    Args:
        input_data: Raw JSON input data
        
    Returns:
        Tuple of (race_id, race_config, strategies)
        
    Raises:
        ValueError: If input is invalid
    """
    # Validate required fields
    if 'race_id' not in input_data:
        raise ValueError("Missing 'race_id' in input")
    
    if 'race_config' not in input_data:
        raise ValueError("Missing 'race_config' in input")
    
    if 'strategies' not in input_data:
        raise ValueError("Missing 'strategies' in input")
    
    race_id = input_data['race_id']
    race_config = input_data['race_config']
    strategies = input_data['strategies']
    
    # Validate race config
    _validate_race_config(race_config)
    
    # Validate strategies
    validate_strategies(strategies)
    
    return race_id, race_config, strategies


def _validate_race_config(race_config: dict) -> None:
    """
    Validate race configuration parameters.
    
    Args:
        race_config: Race configuration dictionary
        
    Raises:
        ValueError: If any required field is missing
    """
    required_fields = [
        'track',
        'total_laps',
        'base_lap_time',
        'pit_lane_time',
        'track_temp'
    ]
    
    for field in required_fields:
        if field not in race_config:
            raise ValueError(f"Missing required race config field: {field}")
    
    # Validate types
    if not isinstance(race_config['total_laps'], int):
        raise ValueError("'total_laps' must be an integer")
    
    if not isinstance(race_config['base_lap_time'], (int, float)):
        raise ValueError("'base_lap_time' must be a number")
    
    if not isinstance(race_config['pit_lane_time'], (int, float)):
        raise ValueError("'pit_lane_time' must be a number")
    
    if not isinstance(race_config['track_temp'], int):
        raise ValueError("'track_temp' must be an integer")


def validate_strategies(strategies: dict) -> bool:
    """
    Validate driver strategies.
    
    Args:
        strategies: Dictionary of driver strategies
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If strategies are invalid
    """
    # Check all 20 positions are present
    for position in range(1, 21):
        position_key = f'pos{position}'
        
        if position_key not in strategies:
            raise ValueError(f"Missing strategy for position {position} ({position_key})")
        
        strategy = strategies[position_key]
        
        # Validate strategy structure
        if 'driver_id' not in strategy:
            raise ValueError(f"Missing 'driver_id' in {position_key}")
        
        if 'starting_tire' not in strategy:
            raise ValueError(f"Missing 'starting_tire' in {position_key}")
        
        # Validate tire compound
        valid_compounds = ['SOFT', 'MEDIUM', 'HARD']
        if strategy['starting_tire'] not in valid_compounds:
            raise ValueError(
                f"Invalid starting tire '{strategy['starting_tire']}' in {position_key}. "
                f"Must be one of {valid_compounds}"
            )
        
        # Validate pit stops if present
        pit_stops = strategy.get('pit_stops', [])
        for i, pit_stop in enumerate(pit_stops):
            if 'lap' not in pit_stop:
                raise ValueError(f"Missing 'lap' in pit stop {i} of {position_key}")
            
            if 'from_tire' not in pit_stop or 'to_tire' not in pit_stop:
                raise ValueError(
                    f"Pit stop {i} in {position_key} must have 'from_tire' and 'to_tire'"
                )
            
            # Validate tire compounds in pit stop
            if pit_stop['from_tire'] not in valid_compounds:
                raise ValueError(
                    f"Invalid 'from_tire' '{pit_stop['from_tire']}' in pit stop {i} of {position_key}"
                )
            
            if pit_stop['to_tire'] not in valid_compounds:
                raise ValueError(
                    f"Invalid 'to_tire' '{pit_stop['to_tire']}' in pit stop {i} of {position_key}"
                )
    
    return True


def format_output(race_id: str, finishing_positions: List[str]) -> dict:
    """
    Format the simulation output as JSON-serializable dictionary.
    
    Args:
        race_id: Race identifier
        finishing_positions: List of driver IDs in finishing order
        
    Returns:
        Dictionary ready for JSON serialization
    """
    # Validate we have exactly 20 drivers
    if len(finishing_positions) != 20:
        raise ValueError(
            f"Expected 20 finishing positions, got {len(finishing_positions)}"
        )
    
    # Validate no duplicates
    if len(set(finishing_positions)) != 20:
        raise ValueError("Duplicate driver IDs in finishing positions")
    
    return {
        'race_id': race_id,
        'finishing_positions': finishing_positions
    }
