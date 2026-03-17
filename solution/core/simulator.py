"""
Race Simulator - Main simulation engine with high-precision tire physics.

Improved version features:
- Quadratic degradation per lap (non-linear tire wear)
- Compound-specific temperature sensitivity
- Full float precision throughout calculations
- Minimal rounding errors via careful arithmetic
"""

import json
from pathlib import Path
import sys
from typing import Dict, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.driver import Driver
from models.tire_model_advanced import (
    calculate_stint_time_quadratic,
    get_compound_properties,
    TIRE_COMPOUNDS
)


class RaceSimulator:
    """Main race simulation engine with regression-based stint calculations."""
    
    def __init__(self, race_config: dict, strategies: dict, model_file: str = None, use_advanced_model: bool = True):
        """
        Initialize the race simulator with improved tire physics.
        
        Args:
            race_config: Race configuration parameters
            strategies: Dictionary of driver strategies (pos1-pos20)
            model_file: Path to regression model JSON file (optional, ignored if use_advanced_model=True)
            use_advanced_model: If True, use quadratic degradation model; if False, use regression model
        """
        self.race_config = race_config
        self.strategies = strategies
        
        # Extract race parameters with explicit float conversion for precision
        self.total_laps = int(race_config['total_laps'])
        self.base_lap_time = float(race_config['base_lap_time'])
        self.pit_lane_time = float(race_config['pit_lane_time'])
        self.track_temp = float(race_config['track_temp'])
        
        # Model selection
        self.use_advanced_model = use_advanced_model
        
        if use_advanced_model:
            # Use advanced quadratic degradation model (silent mode)
            self.coefficients = None  # Not used in advanced model
            self.temp_deviation = None  # Not used in advanced model
        else:
            # Fall back to regression model
            self.coefficients = self._load_regression_model(model_file, verbose=False)
            # Precompute temperature effects for regression model
            self.temp_deviation = self.track_temp - 30.0  # Reference temp = 30°C
        
        # Create driver objects for all 20 positions
        self.drivers = self._create_drivers()
    
    def _load_regression_model(self, model_file: str = None, verbose: bool = True) -> dict:
        """
        Load regression model coefficients from JSON file.
        
        Args:
            model_file: Path to model file. If None, uses default location.
            verbose: If True, print loading messages; if False, stay silent
            
        Returns:
            Dictionary of regression coefficients
        """
        if model_file is None:
            # Default to solution directory
            model_path = Path(__file__).parent / "regression_model.json"
        else:
            model_path = Path(model_file)
        
        try:
            with open(model_path, 'r') as f:
                model_data = json.load(f)
                coefficients = model_data['coefficients']
                
            if verbose:
                print(f"Loaded regression model from {model_path}")
                print(f"  R² = {model_data['metrics']['r_squared']:.4f}")
                print(f"  RMSE = {model_data['metrics']['rmse']:.3f}s")
            
            return coefficients
            
        except FileNotFoundError:
            if verbose:
                print(f"Warning: Regression model not found at {model_path}")
                print("Using fallback parameters...")
            
            # Return sensible defaults if model not found
            return {
                'intercept': 85.0,
                'medium_offset': 0.75,
                'hard_offset': 1.50,
                'degradation_linear': 0.10,
                'degradation_quadratic': 0.0,
                'temperature_main': 0.03,
                'medium_temp_interaction': 0.0,
                'hard_temp_interaction': 0.0
            }
    
    def _get_compound_offset(self, tire_compound: str) -> float:
        """
        Get compound offset from regression coefficients.
        
        Args:
            tire_compound: Tire compound (SOFT, MEDIUM, HARD)
            
        Returns:
            Offset in seconds relative to SOFT compound
        """
        if tire_compound == 'SOFT':
            return 0.0  # Reference compound
        elif tire_compound == 'MEDIUM':
            return self.coefficients['medium_offset']
        elif tire_compound == 'HARD':
            return self.coefficients['hard_offset']
        else:
            raise ValueError(f"Unknown tire compound: {tire_compound}")
    
    def _get_degradation_rate(self, tire_compound: str) -> float:
        """
        Get effective degradation rate for a compound.
        
        Uses the linear degradation coefficient from regression.
        For more accuracy, could include compound-specific interactions.
        
        Args:
            tire_compound: Tire compound (SOFT, MEDIUM, HARD)
            
        Returns:
            Degradation rate in seconds per lap
        """
        # Base degradation rate (same for all compounds in simple model)
        base_deg = self.coefficients['degradation_linear']
        
        # Optional: Add compound-specific adjustments
        # This would come from interaction terms in the regression
        if tire_compound == 'MEDIUM':
            # MEDIUM typically degrades slower than SOFT
            return base_deg * 0.85
        elif tire_compound == 'HARD':
            # HARD degrades slowest
            return base_deg * 0.65
        else:
            # SOFT degrades fastest
            return base_deg
    
    def _get_temperature_effect(self, tire_compound: str) -> float:
        """
        Calculate temperature effect on lap time for a compound.
        
        Formula: temp_effect = (temp_main + compound_interaction) × temp_deviation
        
        Args:
            tire_compound: Tire compound (SOFT, MEDIUM, HARD)
            
        Returns:
            Temperature effect in seconds (added to each lap)
        """
        temp_main = self.coefficients['temperature_main']
        
        # Add compound-specific temperature sensitivity
        if tire_compound == 'MEDIUM':
            temp_interaction = self.coefficients['medium_temp_interaction']
        elif tire_compound == 'HARD':
            temp_interaction = self.coefficients['hard_temp_interaction']
        else:  # SOFT
            temp_interaction = 0.0
        
        # Total temperature effect per lap
        temp_effect_per_lap = (temp_main + temp_interaction) * self.temp_deviation
        
        return temp_effect_per_lap
    
    def _create_drivers(self) -> List[Driver]:
        """
        Create Driver objects from strategies.
        
        Returns:
            List of Driver objects
        """
        drivers = []
        
        # Strategies are keyed by position (pos1, pos2, ..., pos20)
        for position in range(1, 21):
            position_key = f'pos{position}'
            if position_key not in self.strategies:
                raise ValueError(f"Missing strategy for {position_key}")
            
            strategy = self.strategies[position_key]
            # Pass total_laps to Driver constructor for stint conversion
            driver = Driver(strategy['driver_id'], strategy, self.total_laps)
            drivers.append(driver)
        
        return drivers
    
    def simulate_race(self) -> List[str]:
        """
        Run the complete race simulation using optimized stint-based calculations.
        
        Instead of simulating each lap individually, we compute the total time
        for each stint using mathematical formulas:
        
        For a stint of n laps:
        - Base time contribution: n * base_lap_time
        - Compound offset contribution: n * compound_offset
        - Degradation contribution: degradation_rate * sum(1..n)
          where sum(1..n) = n*(n+1)/2
        
        Returns:
            List of driver IDs in finishing order (1st to 20th)
        """
        for driver in self.drivers:
            self._simulate_driver_stints(driver)
        
        # Calculate finishing order based on total race times
        finishing_order = self._calculate_finishing_order()
        
        return finishing_order
    
    def _simulate_driver_stints(self, driver: Driver) -> None:
        """
        Calculate total race time using improved tire physics model.
        
        For each stint, computes with full float precision:
        - Base time: laps × base_lap_time
        - Compound offset: laps × compound_offset  
        - Linear degradation: linear_coeff × sum(ages)
        - Quadratic degradation: quadratic_coeff × sum(age²)
        - Temperature effect: compound-specific sensitivity × temp_deviation
        - Pit stop penalty (if not first stint)
        
        Uses closed-form formulas for O(1) calculation with minimal rounding errors.
        
        Args:
            driver: Driver object with stints to simulate
        """
        total_race_time = 0.0
        
        for stint_idx, stint in enumerate(driver.stints):
            start_lap = stint['start_lap']
            end_lap = stint['end_lap']
            tire_compound = stint['tire']
            
            # Calculate number of laps in this stint
            num_laps = end_lap - start_lap + 1
            
            if self.use_advanced_model:
                # Use advanced quadratic degradation model
                stint_time = self._calculate_advanced_stint_time(
                    tire_compound=tire_compound,
                    num_laps=num_laps
                )
            else:
                # Use legacy regression model
                stint_time = self._calculate_regression_stint_time(
                    tire_compound=tire_compound,
                    num_laps=num_laps
                )
            
            # Add stint time to total with full precision
            total_race_time += stint_time
            
            # Add pit lane time penalty if this isn't the first stint
            if stint_idx > 0:
                total_race_time += self.pit_lane_time
        
        # Set the driver's total race time with explicit float
        driver.total_race_time = float(total_race_time)
    
    def _calculate_advanced_stint_time(
        self,
        tire_compound: str,
        num_laps: int
    ) -> float:
        """
        Calculate stint time using advanced quadratic degradation model.
        
        Implements the complete physics-based formula:
        
        For a stint of n laps starting at age 1:
        stint_time = n×(base + offset + temp)
                   + linear × n×(a+b)/2
                   + quadratic × n×(a²+ab+b²)/3
        
        Where a=1 (start age), b=n (end age)
        
        This captures:
        - Linear degradation (first-order wear)
        - Quadratic degradation (accelerated wear in later life)
        - Compound-specific temperature sensitivity
        - Full float precision throughout
        
        Args:
            tire_compound: Tire compound (SOFT, MEDIUM, HARD)
            num_laps: Number of laps in the stint
            
        Returns:
            Total stint time in seconds (full float precision)
        """
        # Delegate to advanced tire model function
        stint_time = calculate_stint_time_quadratic(
            compound=tire_compound,
            num_laps=num_laps,
            track_temp=self.track_temp,
            base_lap_time=self.base_lap_time,
            start_age=1  # Fresh tires start at age 1
        )
        
        return stint_time
    
    def _calculate_regression_stint_time(
        self,
        tire_compound: str,
        num_laps: int
    ) -> float:
        """
        Legacy method for backward compatibility with regression model.
        
        Uses simple linear degradation formula:
        stint_time = n×base + n×offset + deg×n×(n+1)/2 + n×temp
        
        Args:
            tire_compound: Tire compound (SOFT, MEDIUM, HARD)
            num_laps: Number of laps in the stint
            
        Returns:
            Total stint time in seconds
        """
        # Get regression-based parameters
        compound_offset = self._get_compound_offset(tire_compound)
        degradation_rate = self._get_degradation_rate(tire_compound)
        temp_effect_per_lap = self._get_temperature_effect(tire_compound)
        
        # Calculate components using arithmetic series
        n = float(num_laps)
        
        # 1. Base time: n × base_lap_time
        base_time = n * self.base_lap_time
        
        # 2. Compound offset: n × compound_offset
        offset_time = n * compound_offset
        
        # 3. Degradation: degradation_rate × sum(1..n)
        age_sum = n * (n + 1.0) / 2.0  # Use float division for precision
        degradation_time = degradation_rate * age_sum
        
        # 4. Temperature effect: n × temp_effect_per_lap
        temp_time = n * temp_effect_per_lap
        
        # Total stint time
        stint_time = base_time + offset_time + degradation_time + temp_time
        
        return stint_time
    
    def _calculate_finishing_order(self) -> List[str]:
        """
        Sort drivers by total race time to determine finishing order.
        
        Returns:
            List of driver IDs from fastest (1st) to slowest (20th)
        """
        # Sort drivers by total race time (ascending - fastest first)
        sorted_drivers = sorted(
            self.drivers,
            key=lambda d: d.get_total_time()
        )
        
        # Extract driver IDs in finishing order
        finishing_order = [driver.driver_id for driver in sorted_drivers]
        
        return finishing_order
