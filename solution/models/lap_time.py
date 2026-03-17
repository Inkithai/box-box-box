"""
Lap Time Calculator - Combines all factors to calculate final lap time.
"""

from models.tire import TireModel


class LapTimeCalculator:
    """
    Calculates lap time based on multiple factors:
    - Base lap time (track characteristic)
    - Tire compound performance
    - Tire degradation
    - Track temperature effects
    """
    
    @staticmethod
    def calculate(
        base_lap_time: float,
        tire_compound: str,
        tire_age: int,
        track_temp: int
    ) -> float:
        """
        Calculate the total lap time for a driver.
        
        Args:
            base_lap_time: Track's baseline lap time in seconds
            tire_compound: Current tire compound (SOFT, MEDIUM, HARD)
            tire_age: Number of laps completed on current tires
            track_temp: Track temperature in Celsius
            
        Returns:
            Total lap time in seconds
        """
        # Start with base lap time
        lap_time = base_lap_time
        
        # Apply tire compound effect
        lap_time = LapTimeCalculator._apply_tire_effect(
            lap_time, tire_compound
        )
        
        # Apply tire degradation
        lap_time = LapTimeCalculator._apply_degradation(
            lap_time, tire_compound, tire_age, track_temp
        )
        
        # Apply temperature effect (additional adjustments)
        lap_time = LapTimeCalculator._apply_temperature_effect(
            lap_time, track_temp
        )
        
        return lap_time
    
    @staticmethod
    def _apply_tire_effect(base_time: float, compound: str) -> float:
        """
        Apply tire compound offset to lap time.
        
        Args:
            base_time: Base lap time
            compound: Tire compound
            
        Returns:
            Lap time with tire compound offset applied
        """
        compound_offset = TireModel.get_compound_offset(compound)
        return base_time + compound_offset
    
    @staticmethod
    def _apply_degradation(
        time: float,
        compound: str,
        age: int,
        track_temp: int
    ) -> float:
        """
        Apply tire degradation penalty to lap time.
        
        Args:
            time: Current lap time
            compound: Tire compound
            age: Tire age in laps
            track_temp: Track temperature
            
        Returns:
            Lap time with degradation penalty added
        """
        degradation = TireModel.calculate_degradation(compound, age, track_temp)
        return time + degradation
    
    @staticmethod
    def _apply_temperature_effect(time: float, track_temp: int) -> float:
        """
        Apply additional temperature effects on lap time.
        
        This accounts for how track temperature affects overall grip levels,
        independent of tire degradation.
        
        Args:
            time: Current lap time
            track_temp: Track temperature in Celsius
            
        Returns:
            Lap time with temperature adjustment
        """
        # Simple model: optimal temperature around 30°C
        # Deviations from optimal add small penalty
        optimal_temp = 30
        temp_deviation = abs(track_temp - optimal_temp)
        
        # Small penalty for temperature deviation (0.05s per degree)
        temp_penalty = temp_deviation * 0.05
        
        return time + temp_penalty
