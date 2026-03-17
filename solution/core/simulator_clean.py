#!/usr/bin/env python3
"""
F1 Race Simulator - Main Simulation Engine

Clean, high-performance implementation with:
- Quadratic tire degradation physics
- Compound-specific temperature effects  
- Full float precision throughout
- O(1) stint time calculations using arithmetic series
- Deterministic results (no randomness)
"""

from typing import Dict, List

from models.tire_physics import calculate_stint_time
from core.driver_clean import Driver, create_drivers_from_strategies


class RaceSimulator:
    """Main F1 race simulation engine.
    
    Simulates complete F1 races using physics-based tire model with
    quadratic degradation and compound-specific temperature effects.
    
    Attributes:
        race_id: Unique race identifier
        total_laps: Total race laps
        base_lap_time: Base lap time for the track
        pit_lane_time: Time lost during pit stops
        track_temp: Track temperature in °C
        drivers: List of Driver objects
    """
    
    def __init__(
        self,
        race_config: Dict,
        strategies: Dict[str, Dict]
    ):
        """Initialize race simulator.
        
        Args:
            race_config: Race configuration dict with:
                - race_id: Unique identifier
                - base_lap_time: Base lap time (seconds)
                - total_laps: Number of laps
                - pit_lane_time: Pit lane loss time (seconds)
                - track_temp: Track temperature (°C)
            strategies: Dict mapping positions to driver strategies
            
        Raises:
            ValueError: If configuration is invalid
        """
        # Extract and validate race config
        self.race_id = race_config.get('race_id', 'unknown')
        self.total_laps = int(race_config['total_laps'])
        self.base_lap_time = float(race_config['base_lap_time'])
        self.pit_lane_time = float(race_config['pit_lane_time'])
        self.track_temp = float(race_config['track_temp'])
        
        # Validate
        if self.total_laps < 1:
            raise ValueError(f"Invalid total_laps: {self.total_laps}")
        if len(strategies) != 20:
            raise ValueError(f"Expected 20 strategies, got {len(strategies)}")
        
        # Create drivers
        self.drivers = create_drivers_from_strategies(strategies, self.total_laps)
    
    def simulate_driver_race(self, driver: Driver) -> float:
        """Calculate total race time for a driver.
        
        For each stint:
        1. Calculate stint time using O(1) formula
        2. Add pit stop penalty (except first stint)
        3. Sum all contributions
        
        Uses quadratic degradation model:
            stint_time = n×(base+offset+temp)
                       + linear × sum(ages)
                       + quadratic × sum(age²)
        
        Args:
            driver: Driver object with stints to simulate
            
        Returns:
            Total race time in seconds
        """
        total_time = 0.0
        
        for stint_idx, stint in enumerate(driver.stints):
            num_laps = stint['end_lap'] - stint['start_lap'] + 1
            compound = stint['tire']
            
            # Calculate stint time with physics model
            stint_time = calculate_stint_time(
                compound=compound,
                num_laps=num_laps,
                track_temp=self.track_temp,
                base_lap_time=self.base_lap_time,
                start_age=1  # Fresh tire at stint start
            )
            
            # Add pit stop penalty (not for first stint)
            if stint_idx > 0:
                stint_time += self.pit_lane_time
            
            total_time += stint_time
        
        return total_time
    
    def simulate_race(self) -> List[str]:
        """Run complete race simulation.
        
        Simulates all drivers independently and ranks by total time.
        
        Returns:
            List of driver IDs in finishing order (fastest to slowest)
        """
        # Calculate race times for all drivers
        driver_times: List[tuple] = []
        
        for driver in self.drivers:
            total_time = self.simulate_driver_race(driver)
            driver_times.append((driver, total_time))
        
        # Sort by total time (ascending = fastest first)
        driver_times.sort(key=lambda x: x[1])
        
        # Extract finishing order
        finishing_order = [driver.driver_id for driver, _ in driver_times]
        
        return finishing_order
    
    def get_detailed_results(self) -> Dict:
        """Get detailed race results with times.
        
        Returns:
            Dict with:
                - race_id: Race identifier
                - finishing_positions: List of driver IDs
                - driver_times: Dict mapping driver_id to total_time
        """
        # Calculate all times
        driver_times = {}
        for driver in self.drivers:
            time = self.simulate_driver_race(driver)
            driver_times[driver.driver_id] = time
        
        # Get finishing order
        finishing_order = sorted(driver_times.keys(), key=lambda x: driver_times[x])
        
        return {
            'race_id': self.race_id,
            'finishing_positions': finishing_order,
            'driver_times': driver_times
        }


def simulate_race_json(race_config: Dict, strategies: Dict) -> Dict:
    """Convenience function for JSON-based simulation.
    
    Args:
        race_config: Race configuration dict
        strategies: Strategies dict
        
    Returns:
        Results dict with race_id and finishing_positions
    """
    simulator = RaceSimulator(race_config, strategies)
    finishing_order = simulator.simulate_race()
    
    return {
        'race_id': race_config.get('race_id', 'unknown'),
        'finishing_positions': finishing_order
    }


if __name__ == '__main__':
    # Quick test
    test_config = {
        'race_id': 'test_001',
        'base_lap_time': 85.0,
        'total_laps': 30,
        'pit_lane_time': 25.0,
        'track_temp': 30.0
    }
    
    # Create minimal test strategies (just show structure)
    test_strategies = {}
    for pos in range(1, 21):
        test_strategies[f'pos{pos}'] = {
            'driver_id': f'D{pos:03d}',
            'starting_tire': 'SOFT' if pos <= 7 else 'MEDIUM',
            'pit_stops': []
        }
    
    result = simulate_race_json(test_config, test_strategies)
    print(f"Race: {result['race_id']}")
    print(f"Top 3: {result['finishing_positions'][:3]}")
