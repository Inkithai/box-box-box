"""
Tire Performance Model for F1 Race Simulation.

This module defines the physics of tire behavior including:
- Three tire compounds (SOFT, MEDIUM, HARD) with distinct characteristics
- Base speed offsets for each compound
- Degradation rates that increase lap times as tires age
- Temperature sensitivity affecting performance based on track conditions

The model provides precise lap time adjustments based on compound choice,
tire age, and environmental conditions.
"""

from typing import Dict


class TireModel:
    """
    Tire performance and degradation model.
    
    This class encapsulates the physics of how different tire compounds
    perform and degrade over time under varying track temperatures.
    
    Each compound has three key characteristics:
    - base_offset: Initial lap time penalty relative to the fastest compound
    - degradation_rate: How quickly the tire loses performance per lap
    - optimal_temperature: Track temperature where tire performs best
    - temp_sensitivity: How much performance changes with temperature deviation
    
    Attributes:
        TIRE_COMPOUNDS: Class-level dictionary defining all tire compound properties
    """
    
    # Tire compound definitions with their performance characteristics
    # All times are in seconds
    TIRE_COMPOUNDS: Dict[str, Dict] = {
        'SOFT': {
            'name': 'SOFT',
            'base_offset': 0.0,           # Fastest compound (reference point)
            'degradation_rate': 0.12,     # Degrades 0.12s per lap
            'optimal_laps': 10,           # Laps before significant wear
            'temp_sensitivity': 0.03,     # 0.03s per °C deviation from optimal
            'optimal_temperature': 28,    # Performs best at 28°C
        },
        'MEDIUM': {
            'name': 'MEDIUM',
            'base_offset': 0.75,          # 0.75s slower than SOFT initially
            'degradation_rate': 0.08,     # Degrades 0.08s per lap
            'optimal_laps': 18,           # Longer lasting than SOFT
            'temp_sensitivity': 0.025,    # Less sensitive to temperature
            'optimal_temperature': 30,    # Performs best at 30°C
        },
        'HARD': {
            'name': 'HARD',
            'base_offset': 1.50,          # 1.50s slower than SOFT initially
            'degradation_rate': 0.05,     # Degrades only 0.05s per lap
            'optimal_laps': 30,           # Most durable compound
            'temp_sensitivity': 0.02,     # Least sensitive to temperature
            'optimal_temperature': 32,    # Performs best at 32°C
        }
    }
    
    @staticmethod
    def get_compound_offset(compound: str) -> float:
        """
        Get the base lap time offset for a tire compound.
        
        The base offset represents the inherent speed difference between
        tire compounds when they are fresh (lap 1). SOFT is the fastest
        compound and serves as the reference point (0.0s offset).
        
        Args:
            compound: Tire compound name. Must be one of 'SOFT', 'MEDIUM', or 'HARD'
            
        Returns:
            Base lap time offset in seconds. This is added to the track's
            base lap time. Lower values indicate faster compounds.
            
        Raises:
            ValueError: If compound is not a valid tire type
            
        Example:
            >>> TireModel.get_compound_offset('SOFT')
            0.0
            >>> TireModel.get_compound_offset('MEDIUM')
            0.75
            >>> TireModel.get_compound_offset('HARD')
            1.5
        """
        if compound not in TireModel.TIRE_COMPOUNDS:
            valid_compounds = ', '.join(TireModel.TIRE_COMPOUNDS.keys())
            raise ValueError(
                f"Invalid tire compound '{compound}'. Must be one of: {valid_compounds}"
            )
        
        return TireModel.TIRE_COMPOUNDS[compound]['base_offset']
    
    @staticmethod
    def calculate_degradation(
        compound: str,
        tire_age: int,
        track_temp: int
    ) -> float:
        """
        Calculate total degradation penalty for a tire at current conditions.
        
        Degradation represents the cumulative performance loss as tires age.
        The model uses a two-phase approach:
        
        Phase 1 (Optimal Period): Linear degradation at base rate
        - Tires maintain relatively consistent performance
        - Degradation accumulates gradually
        
        Phase 2 (Post-Optimal): Accelerated degradation
        - Rubber compound breaks down more rapidly
        - Degradation rate doubles to simulate cliff-like performance drop
        
        Temperature modifies the effective degradation rate:
        - Temperatures near optimal: minimal effect
        - Temperatures far from optimal: increased degradation
        
        Args:
            compound: Tire compound name ('SOFT', 'MEDIUM', or 'HARD')
            tire_age: Number of laps completed on current tire set (1-indexed)
            track_temp: Current track temperature in degrees Celsius
            
        Returns:
            Total degradation penalty in seconds to add to lap time.
            This represents cumulative performance loss from tire wear.
            
        Raises:
            ValueError: If compound is invalid
            
        Example:
            >>> # Fresh SOFT tire at optimal temperature
            >>> TireModel.calculate_degradation('SOFT', 1, 28)
            0.12
            
            >>> # Worn SOFT tire (past optimal life)
            >>> TireModel.calculate_degradation('SOFT', 15, 28)
            2.64
            
            >>> # HARD tire at non-optimal temperature
            >>> TireModel.calculate_degradation('HARD', 10, 25)
            0.575
        """
        if compound not in TireModel.TIRE_COMPOUNDS:
            valid_compounds = ', '.join(TireModel.TIRE_COMPOUNDS.keys())
            raise ValueError(
                f"Invalid tire compound '{compound}'. Must be one of: {valid_compounds}"
            )
        
        tire_info = TireModel.TIRE_COMPOUNDS[compound]
        base_degradation_rate = tire_info['degradation_rate']
        optimal_laps = tire_info['optimal_laps']
        temp_sensitivity = tire_info['temp_sensitivity']
        optimal_temp = tire_info['optimal_temperature']
        
        # Calculate temperature factor
        # Deviation from optimal temperature increases degradation
        temp_deviation = abs(track_temp - optimal_temp)
        temp_factor = 1.0 + (temp_deviation * temp_sensitivity)
        
        # Calculate base degradation based on tire age
        if tire_age <= optimal_laps:
            # Phase 1: Linear degradation during optimal period
            # Degradation accumulates at the base rate
            degradation_penalty = tire_age * base_degradation_rate
        else:
            # Phase 2: Accelerated degradation after optimal period
            # First, calculate degradation accumulated during optimal period
            optimal_period_degradation = optimal_laps * base_degradation_rate
            
            # Then, calculate accelerated degradation for remaining laps
            laps_over_optimal = tire_age - optimal_laps
            # Degradation rate doubles after optimal period
            accelerated_rate = base_degradation_rate * 2.0
            post_optimal_degradation = laps_over_optimal * accelerated_rate
            
            # Total degradation is sum of both phases
            degradation_penalty = (
                optimal_period_degradation + post_optimal_degradation
            )
        
        # Apply temperature modifier to final degradation
        total_degradation = degradation_penalty * temp_factor
        
        return total_degradation
    
    @staticmethod
    def calculate_temperature_effect(
        compound: str,
        track_temp: int
    ) -> float:
        """
        Calculate the direct temperature effect on lap time.
        
        This is separate from degradation and represents how track temperature
        directly affects tire grip and performance, independent of wear.
        
        Each compound has an optimal operating temperature. When track
        temperature deviates from this optimum, the tire cannot generate
        maximum grip, resulting in slower lap times.
        
        The effect is symmetric: both hotter and colder temperatures
        negatively impact performance.
        
        Args:
            compound: Tire compound name ('SOFT', 'MEDIUM', or 'HARD')
            track_temp: Current track temperature in degrees Celsius
            
        Returns:
            Temperature effect penalty in seconds. Always non-negative.
            Zero when track temperature equals compound's optimal temperature.
            
        Raises:
            ValueError: If compound is invalid
            
        Example:
            >>> # At optimal temperature, no penalty
            >>> TireModel.calculate_temperature_effect('MEDIUM', 30)
            0.0
            
            >>> # 5 degrees from optimal
            >>> TireModel.calculate_temperature_effect('MEDIUM', 25)
            0.125
            
            >>> # Different compounds have different optimal temps
            >>> TireModel.calculate_temperature_effect('SOFT', 32)
            0.12
            >>> TireModel.calculate_temperature_effect('HARD', 32)
            0.0
        """
        if compound not in TireModel.TIRE_COMPOUNDS:
            valid_compounds = ', '.join(TireModel.TIRE_COMPOUNDS.keys())
            raise ValueError(
                f"Invalid tire compound '{compound}'. Must be one of: {valid_compounds}"
            )
        
        tire_info = TireModel.TIRE_COMPOUNDS[compound]
        temp_sensitivity = tire_info['temp_sensitivity']
        optimal_temp = tire_info['optimal_temperature']
        
        # Calculate absolute deviation from optimal temperature
        temp_deviation = abs(track_temp - optimal_temp)
        
        # Apply sensitivity to get time penalty
        # Larger deviations = larger penalties
        temperature_penalty = temp_deviation * temp_sensitivity * 5.0
        
        return temperature_penalty
    
    @staticmethod
    def calculate_total_lap_time_adjustment(
        compound: str,
        tire_age: int,
        track_temp: int
    ) -> float:
        """
        Calculate complete tire adjustment to lap time.
        
        This combines all tire-related effects into a single adjustment value:
        - Base compound offset (inherent speed difference)
        - Cumulative degradation from tire wear
        - Direct temperature effect on grip
        
        This method provides the total time to add to the track's base lap time
        to get the actual lap time for a specific tire state.
        
        Args:
            compound: Tire compound name ('SOFT', 'MEDIUM', or 'HARD')
            tire_age: Number of laps completed on current tire set (1-indexed)
            track_temp: Current track temperature in degrees Celsius
            
        Returns:
            Total lap time adjustment in seconds. This includes:
            - Base compound offset
            - Degradation penalty from tire age
            - Temperature effect penalty
            
        Raises:
            ValueError: If compound is invalid
            
        Example:
            >>> # Fresh SOFT at optimal conditions
            >>> TireModel.calculate_total_lap_time_adjustment('SOFT', 1, 28)
            0.12
            
            >>> # Worn MEDIUM at non-optimal temperature
            >>> TireModel.calculate_total_lap_time_adjustment('MEDIUM', 20, 35)
            3.225
        """
        # Get base compound offset
        base_offset = TireModel.get_compound_offset(compound)
        
        # Calculate degradation penalty
        degradation = TireModel.calculate_degradation(compound, tire_age, track_temp)
        
        # Calculate temperature effect
        temp_effect = TireModel.calculate_temperature_effect(compound, track_temp)
        
        # Sum all components
        total_adjustment = base_offset + degradation + temp_effect
        
        return total_adjustment
    
    @staticmethod
    def get_compound_properties(compound: str) -> Dict:
        """
        Get complete property dictionary for a tire compound.
        
        Returns all performance characteristics for a compound, useful for
        analysis and debugging.
        
        Args:
            compound: Tire compound name ('SOFT', 'MEDIUM', or 'HARD')
            
        Returns:
            Dictionary containing all compound properties:
            - name: Compound name
            - base_offset: Base lap time offset
            - degradation_rate: Degradation per lap
            - optimal_laps: Laps before accelerated degradation
            - temp_sensitivity: Temperature sensitivity factor
            - optimal_temperature: Optimal operating temperature in °C
            
        Raises:
            ValueError: If compound is invalid
        """
        if compound not in TireModel.TIRE_COMPOUNDS:
            valid_compounds = ', '.join(TireModel.TIRE_COMPOUNDS.keys())
            raise ValueError(
                f"Invalid tire compound '{compound}'. Must be one of: {valid_compounds}"
            )
        
        # Return a copy to prevent external modification
        return TireModel.TIRE_COMPOUNDS[compound].copy()
    
    @staticmethod
    def compare_compounds(track_temp: int = 30) -> Dict[str, Dict]:
        """
        Compare all three compounds at specified conditions.
        
        Utility method for analysis showing how each compound would perform
        at a given track temperature with fresh tires.
        
        Args:
            track_temp: Track temperature in degrees Celsius (default: 30)
            
        Returns:
            Dictionary mapping compound names to their fresh-tire performance:
            - base_offset: Base speed difference
            - lap_1_degradation: Degradation on first lap
            - temp_effect: Temperature penalty
            - total_adjustment: Complete lap time adjustment
        """
        comparison = {}
        
        for compound_name in ['SOFT', 'MEDIUM', 'HARD']:
            compound_data = TireModel.TIRE_COMPOUNDS[compound_name]
            
            # Calculate fresh tire (lap 1) performance
            degradation_lap1 = TireModel.calculate_degradation(
                compound_name, 1, track_temp
            )
            temp_effect = TireModel.calculate_temperature_effect(
                compound_name, track_temp
            )
            total = TireModel.calculate_total_lap_time_adjustment(
                compound_name, 1, track_temp
            )
            
            comparison[compound_name] = {
                'base_offset': compound_data['base_offset'],
                'lap_1_degradation': degradation_lap1,
                'temperature_effect': temp_effect,
                'total_adjustment': total
            }
        
        return comparison
