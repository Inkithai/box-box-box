"""
Driver class to represent a single driver's state during the race.
"""

from typing import Dict, List, Optional


def convert_strategy_to_stints(strategy: dict, total_laps: int) -> List[dict]:
    """
    Convert a driver's pit stop strategy into tire stints.
    
    Each stint represents a continuous period on the same tire compound,
    defined by start lap, end lap, and tire compound.
    
    Args:
        strategy: Driver strategy with starting_tire and pit_stops
        total_laps: Total number of laps in the race
        
    Returns:
        List of stint dictionaries, each containing:
        - start_lap: First lap of the stint (1-indexed)
        - end_lap: Last lap of the stint (inclusive)
        - tire: Tire compound used during this stint
        
    Raises:
        ValueError: If strategy is invalid (bad tire compounds, out-of-range laps, etc.)
        
    Example:
        >>> strategy = {
        ...     'starting_tire': 'SOFT',
        ...     'pit_stops': [
        ...         {'lap': 18, 'to_tire': 'MEDIUM'},
        ...         {'lap': 38, 'to_tire': 'HARD'}
        ...     ]
        ... }
        >>> convert_strategy_to_stints(strategy, total_laps=50)
        [
            {'start_lap': 1, 'end_lap': 17, 'tire': 'SOFT'},
            {'start_lap': 18, 'end_lap': 37, 'tire': 'MEDIUM'},
            {'start_lap': 38, 'end_lap': 50, 'tire': 'HARD'}
        ]
    """
    valid_compounds = ['SOFT', 'MEDIUM', 'HARD']
    
    # Validate starting tire
    starting_tire = strategy.get('starting_tire')
    if not starting_tire:
        raise ValueError("Strategy must include 'starting_tire'")
    if starting_tire not in valid_compounds:
        raise ValueError(
            f"Invalid starting tire '{starting_tire}'. Must be one of: {valid_compounds}"
        )
    
    # Get and validate pit stops
    pit_stops = strategy.get('pit_stops', [])
    
    # Sort pit stops by lap number
    sorted_pit_stops = sorted(pit_stops, key=lambda x: x['lap'])
    
    # Validate pit stops
    for i, pit_stop in enumerate(sorted_pit_stops):
        # Check lap is present
        if 'lap' not in pit_stop:
            raise ValueError(f"Pit stop {i} missing 'lap' field")
        
        pit_lap = pit_stop['lap']
        
        # Validate lap range
        if pit_lap < 1 or pit_lap > total_laps:
            raise ValueError(
                f"Pit stop lap {pit_lap} is out of range. Must be between 1 and {total_laps}"
            )
        
        # Validate tire compound
        to_tire = pit_stop.get('to_tire')
        if not to_tire:
            raise ValueError(f"Pit stop {i} missing 'to_tire' field")
        if to_tire not in valid_compounds:
            raise ValueError(
                f"Invalid tire '{to_tire}' in pit stop {i}. Must be one of: {valid_compounds}"
            )
    
    # Build stints
    stints = []
    previous_tire = starting_tire
    stint_start = 1  # First stint starts at lap 1
    
    for pit_stop in sorted_pit_stops:
        pit_lap = pit_stop['lap']
        to_tire = pit_stop['to_tire']
        
        # Create stint from start to lap BEFORE the pit stop
        # The pit lap itself is on the NEW tire
        stint_end = pit_lap - 1
        
        # Only add stint if it has at least one lap
        if stint_start <= stint_end:
            stints.append({
                'start_lap': stint_start,
                'end_lap': stint_end,
                'tire': previous_tire
            })
        
        # Start new stint from the pit lap
        stint_start = pit_lap
        previous_tire = to_tire
    
    # Add final stint from last pit stop to end of race
    final_stint_end = total_laps
    
    # Final stint should always exist
    if stint_start > final_stint_end:
        raise ValueError(
            f"Final stint would have no laps. Last pit stop at lap {stint_start} "
            f"in a {total_laps}-lap race."
        )
    
    stints.append({
        'start_lap': stint_start,
        'end_lap': final_stint_end,
        'tire': previous_tire
    })
    
    return stints


class Driver:
    """Represents an F1 driver with their strategy and race state."""
    
    def __init__(self, driver_id: str, strategy: dict, total_laps: int):
        """
        Initialize a driver with their strategy.
        
        Args:
            driver_id: Unique driver identifier (e.g., "D001")
            strategy: Driver's strategy including starting tire and pit stops
            total_laps: Total number of laps in the race
        """
        self.driver_id = driver_id
        self.total_laps = total_laps
        
        # Convert strategy to stints
        self.stints = convert_strategy_to_stints(strategy, total_laps)
        
        # Store original strategy for reference
        self.starting_tire = strategy['starting_tire']
        self.pit_stops = strategy.get('pit_stops', [])
        
        # Current race state
        self.current_tire = self.starting_tire
        self.tire_age = 0  # Laps completed on current tire set
        self.total_race_time = 0.0
        
        # Track current stint index
        self.current_stint_index = 0
    
    def get_current_tire(self, lap: int = None) -> str:
        """
        Get the current tire compound for a given lap.
        
        Uses the stint list to determine which tire compound the driver
        is using during the specified lap.
        
        Args:
            lap: Lap number to check (1-indexed). If None, uses current lap.
            
        Returns:
            Current tire compound (SOFT, MEDIUM, or HARD)
        """
        if lap is None:
            # Use current stint index
            if self.current_stint_index < len(self.stints):
                return self.stints[self.current_stint_index]['tire']
            return self.current_tire
        
        # Find the stint that contains this lap
        for stint in self.stints:
            if stint['start_lap'] <= lap <= stint['end_lap']:
                return stint['tire']
        
        # Fallback (shouldn't happen with valid data)
        return self.current_tire
    
    def get_tire_age(self, lap: int = None) -> int:
        """
        Get the age of current tires in laps.
        
        Tire age is calculated as the number of laps completed on the
        current tire set within the current stint.
        
        Args:
            lap: Lap number to check (1-indexed). If None, uses current state.
            
        Returns:
            Tire age in laps (1-indexed: first lap on new tires = age 1)
        """
        if lap is None:
            return self.tire_age
        
        # Find the current stint for this lap
        for i, stint in enumerate(self.stints):
            if stint['start_lap'] <= lap <= stint['end_lap']:
                # Tire age is how many laps into this stint we are
                return lap - stint['start_lap'] + 1
        
        return self.tire_age
    
    def increment_tire_age(self) -> None:
        """Increment tire age by one lap."""
        self.tire_age += 1
    
    def update_current_stint(self, lap: int) -> None:
        """
        Update the current stint index based on the current lap.
        
        This should be called at the start of each lap to ensure
        the driver is tracking the correct stint.
        
        Args:
            lap: Current lap number (1-indexed)
        """
        for i, stint in enumerate(self.stints):
            if stint['start_lap'] <= lap <= stint['end_lap']:
                self.current_stint_index = i
                self.current_tire = stint['tire']
                # Calculate tire age for this lap
                self.tire_age = lap - stint['start_lap'] + 1
                break
    
    def should_pit_this_lap(self, current_lap: int) -> bool:
        """
        Check if the driver should pit at the end of this lap.
        
        This method checks if the current lap marks the end of a stint,
        which means a pit stop is needed.
        
        Args:
            current_lap: The current lap number (1-indexed)
            
        Returns:
            True if driver should pit after completing this lap
        """
        # Check if this lap is the last lap of the current stint
        if self.current_stint_index < len(self.stints):
            current_stint = self.stints[self.current_stint_index]
            return current_lap == current_stint['end_lap']
        return False
    
    def get_pit_stop_info(self, lap: int) -> Optional[Dict[str, str]]:
        """
        Get pit stop information for a specific lap.
        
        Args:
            lap: The lap number to check
            
        Returns:
            Dictionary with 'from_tire' and 'to_tire' if pitting, None otherwise
        """
        # Check if this lap ends a stint (except the final stint)
        if self.current_stint_index < len(self.stints) - 1:
            current_stint = self.stints[self.current_stint_index]
            next_stint = self.stints[self.current_stint_index + 1]
            
            if lap == current_stint['end_lap']:
                return {
                    'from_tire': current_stint['tire'],
                    'to_tire': next_stint['tire']
                }
        return None
    
    def execute_pit_stop(self, pit_lane_time: float) -> None:
        """
        Execute a pit stop and apply time penalty.
        
        Advances to the next stint and applies the pit lane time penalty.
        
        Args:
            pit_lane_time: Time penalty for the pit stop in seconds
        """
        # Only pit if there's a next stint
        if self.current_stint_index < len(self.stints) - 1:
            # Move to next stint
            self.current_stint_index += 1
            next_stint = self.stints[self.current_stint_index]
            
            # Update tire compound
            self.current_tire = next_stint['tire']
            
            # Reset tire age (will be set to 1 on next lap)
            self.tire_age = 0
            
            # Add pit lane time penalty
            self.total_race_time += pit_lane_time
    
    def add_lap_time(self, lap_time: float) -> None:
        """
        Add a lap time to the driver's total race time.
        
        Args:
            lap_time: Time taken to complete the lap in seconds
        """
        self.total_race_time += lap_time
    
    def get_total_time(self) -> float:
        """
        Get the driver's total race time.
        
        Returns:
            Total race time in seconds
        """
        return self.total_race_time
    
    def reset_state(self) -> None:
        """Reset driver state to start of race (for re-simulation)."""
        self.current_tire = self.starting_tire
        self.tire_age = 0
        self.total_race_time = 0.0
        self.current_stint_index = 0
