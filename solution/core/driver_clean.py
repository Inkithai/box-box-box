#!/usr/bin/env python3
"""
F1 Race Simulator - Driver Model

Represents F1 drivers with tire stint management and strategy validation.
"""

from typing import Dict, List, Optional


class Driver:
    """Represents an F1 driver with tire strategy.
    
    Attributes:
        driver_id: Unique driver identifier
        total_laps: Total race laps
        stints: List of tire stints (start_lap, end_lap, compound)
        current_stint_index: Current stint being executed
    """
    
    def __init__(self, driver_id: str, strategy: Dict, total_laps: int):
        """Initialize driver with strategy.
        
        Args:
            driver_id: Driver identifier (e.g., 'VER', 'HAM')
            strategy: Driver strategy dict with starting_tire and pit_stops
            total_laps: Total race laps
            
        Raises:
            ValueError: If strategy is invalid
        """
        self.driver_id = driver_id
        self.total_laps = total_laps
        
        # Convert strategy to stints
        self.stints = self._convert_to_stints(strategy, total_laps)
        
        if not self.stints:
            raise ValueError(f"Driver {driver_id}: No valid stints created")
        
        self.current_stint_index = 0
    
    def _convert_to_stints(self, strategy: Dict, total_laps: int) -> List[Dict]:
        """Convert pit stop strategy to tire stints.
        
        Validates and converts:
            {'starting_tire': 'SOFT', 'pit_stops': [{'lap': 20, 'to_tire': 'HARD'}]}
        To:
            [{'start_lap': 1, 'end_lap': 19, 'tire': 'SOFT'},
             {'start_lap': 20, 'end_lap': 52, 'tire': 'HARD'}]
        
        Args:
            strategy: Strategy dict with starting_tire and pit_stops
            total_laps: Total race laps
            
        Returns:
            List of stint dicts
            
        Raises:
            ValueError: If strategy validation fails
        """
        valid_compounds = {'SOFT', 'MEDIUM', 'HARD'}
        
        # Validate starting tire
        starting_tire = strategy.get('starting_tire')
        if starting_tire not in valid_compounds:
            raise ValueError(
                f"Driver {self.driver_id}: Invalid starting tire '{starting_tire}'. "
                f"Must be one of {valid_compounds}"
            )
        
        # Get pit stops
        pit_stops = strategy.get('pit_stops', [])
        
        # Sort by lap number
        sorted_pit_stops = sorted(pit_stops, key=lambda x: x['lap'])
        
        # Build stints
        stints = []
        stint_start = 1
        previous_tire = starting_tire
        
        for pit_stop in sorted_pit_stops:
            pit_lap = pit_stop['lap']
            
            # Validate pit lap
            if pit_lap < 1 or pit_lap > total_laps:
                raise ValueError(
                    f"Driver {self.driver_id}: Invalid pit lap {pit_lap}. "
                    f"Must be between 1 and {total_laps}"
                )
            
            # Validate new tire compound
            new_tire = pit_stop.get('to_tire')
            if new_tire not in valid_compounds:
                raise ValueError(
                    f"Driver {self.driver_id}: Invalid tire '{new_tire}' at lap {pit_lap}"
                )
            
            # Create stint ending before pit
            if stint_start <= pit_lap - 1:
                stints.append({
                    'start_lap': stint_start,
                    'end_lap': pit_lap - 1,
                    'tire': previous_tire
                })
            
            # Start new stint at pit lap
            stint_start = pit_lap
            previous_tire = new_tire
        
        # Add final stint
        if stint_start <= total_laps:
            stints.append({
                'start_lap': stint_start,
                'end_lap': total_laps,
                'tire': previous_tire
            })
        
        return stints
    
    def get_stint_for_lap(self, lap: int) -> Optional[Dict]:
        """Get the stint active during a specific lap.
        
        Args:
            lap: Lap number (1-indexed)
            
        Returns:
            Stint dict or None if lap is outside range
        """
        for stint in self.stints:
            if stint['start_lap'] <= lap <= stint['end_lap']:
                return stint
        return None
    
    def get_tire_at_lap(self, lap: int) -> Optional[str]:
        """Get tire compound used at specific lap.
        
        Args:
            lap: Lap number (1-indexed)
            
        Returns:
            Tire compound or None if lap is outside range
        """
        stint = self.get_stint_for_lap(lap)
        return stint['tire'] if stint else None
    
    def get_tire_age_at_lap(self, lap: int) -> Optional[int]:
        """Get tire age at specific lap.
        
        Args:
            lap: Lap number (1-indexed)
            
        Returns:
            Tire age in laps or None if lap is outside range
        """
        stint = self.get_stint_for_lap(lap)
        if stint:
            return lap - stint['start_lap'] + 1
        return None
    
    @property
    def num_stints(self) -> int:
        """Get number of stints."""
        return len(self.stints)
    
    def __repr__(self) -> str:
        return f"Driver(id={self.driver_id}, stints={self.num_stints})"


def create_drivers_from_strategies(
    strategies: Dict[str, Dict],
    total_laps: int
) -> List[Driver]:
    """Create driver objects from strategy dictionary.
    
    Args:
        strategies: Dict mapping position keys (pos1, pos2, ...) to strategies
        total_laps: Total race laps
        
    Returns:
        List of Driver objects sorted by position
        
    Raises:
        ValueError: If any strategy is invalid or positions missing
    """
    drivers = []
    
    # Validate all 20 positions exist
    for pos in range(1, 21):
        pos_key = f'pos{pos}'
        if pos_key not in strategies:
            raise ValueError(f"Missing strategy for position {pos} ({pos_key})")
        
        strategy = strategies[pos_key]
        
        # Extract driver ID
        driver_id = strategy.get('driver_id', f'D{pos:03d}')
        
        # Create driver object
        driver = Driver(driver_id=driver_id, strategy=strategy, total_laps=total_laps)
        drivers.append(driver)
    
    return drivers


if __name__ == '__main__':
    # Test driver creation
    test_strategy = {
        'starting_tire': 'SOFT',
        'pit_stops': [
            {'lap': 15, 'to_tire': 'HARD'},
            {'lap': 30, 'to_tire': 'MEDIUM'}
        ]
    }
    
    driver = Driver('VER', test_strategy, 52)
    print(f"Created: {driver}")
    print(f"Stints: {driver.stints}")
    
    # Test tire queries
    for lap in [1, 10, 15, 20, 30, 40]:
        tire = driver.get_tire_at_lap(lap)
        age = driver.get_tire_age_at_lap(lap)
        print(f"Lap {lap}: {tire} (age {age})")
