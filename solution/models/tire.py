"""
Tire Model - Defines tire compounds and degradation behavior.

This module contains the physics of how tires perform and degrade over time.
The exact values should be determined through analysis of historical data.

Note: This module now delegates to tire_model.py for actual calculations.
This file is kept for backward compatibility with existing code.
"""

from typing import Dict
from .tire_model import TireModel as NewTireModel


# Keep old interface for backward compatibility
class TireModel:
    """
    Backward-compatible wrapper for the new tire model.
    
    This class maintains the old API while using the new tire_model.py
    implementation underneath.
    """
    
    @staticmethod
    def get_compound_offset(compound: str) -> float:
        """
        Get the base lap time offset for a tire compound.
        
        Args:
            compound: Tire compound name (SOFT, MEDIUM, HARD)
            
        Returns:
            Base lap time offset in seconds (added to base lap time)
        """
        return NewTireModel.get_compound_offset(compound)
    
    @staticmethod
    def calculate_degradation(compound: str, age: int, temperature: int) -> float:
        """
        Calculate tire degradation penalty based on age and temperature.
        
        Args:
            compound: Tire compound name
            age: Tire age in laps (how many laps completed on this set)
            temperature: Track temperature in Celsius
            
        Returns:
            Degradation penalty in seconds to add to lap time
        """
        return NewTireModel.calculate_degradation(compound, age, temperature)
    
    @staticmethod
    def get_base_performance(compound: str) -> Dict:
        """
        Get complete performance characteristics for a tire compound.
        
        Args:
            compound: Tire compound name
            
        Returns:
            Dictionary with all performance parameters
        """
        return NewTireModel.get_compound_properties(compound)
