#!/usr/bin/env python3
"""
F1 Race Simulator - Core Physics Engine

High-performance tire physics with quadratic degradation and compound-specific temperature effects.
All calculations use full float precision for deterministic results.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class TireCompound:
    """Physical properties for each tire compound."""
    name: str
    base_offset: float  # Speed offset vs SOFT (seconds)
    linear_degradation: float  # Linear degradation coefficient (s/lap)
    quadratic_degradation: float  # Quadratic degradation coefficient (s/lap²)
    optimal_temperature: float  # Optimal temp (°C)
    temp_sensitivity: float  # Grip loss per °C deviation


# Tire compound definitions - calibrated from historical data
TIRE_COMPOUNDS: Dict[str, TireCompound] = {
    'SOFT': TireCompound(
        name='SOFT',
        base_offset=0.0,
        linear_degradation=0.14,
        quadratic_degradation=0.0048,
        optimal_temperature=28.0,
        temp_sensitivity=0.035
    ),
    'MEDIUM': TireCompound(
        name='MEDIUM',
        base_offset=0.75,
        linear_degradation=0.09,
        quadratic_degradation=0.0032,
        optimal_temperature=30.0,
        temp_sensitivity=0.025
    ),
    'HARD': TireCompound(
        name='HARD',
        base_offset=1.50,
        linear_degradation=0.06,
        quadratic_degradation=0.0020,
        optimal_temperature=32.0,
        temp_sensitivity=0.018
    )
}


def get_compound(compound: str) -> TireCompound:
    """Get tire compound properties.
    
    Args:
        compound: Tire compound name (SOFT, MEDIUM, HARD)
        
    Returns:
        TireCompound dataclass with physical properties
        
    Raises:
        ValueError: If compound is not valid
    """
    if compound not in TIRE_COMPOUNDS:
        raise ValueError(f"Invalid tire compound: {compound}")
    return TIRE_COMPOUNDS[compound]


def calculate_lap_time(
    compound: str,
    tire_age: int,
    track_temp: float,
    base_lap_time: float
) -> float:
    """Calculate lap time with full float precision.
    
    Lap time model:
        lap_time = base + compound_offset 
                 + linear_deg × age + quad_deg × age²
                 + temp_sensitivity × |track_temp - optimal_temp|
    
    Args:
        compound: Tire compound (SOFT, MEDIUM, HARD)
        tire_age: Current tire age in laps (1-indexed)
        track_temp: Track temperature in °C
        base_lap_time: Base lap time for the track
        
    Returns:
        Lap time in seconds with full float precision
    """
    tire = get_compound(compound)
    
    # Component 1: Base + compound offset
    base_component = base_lap_time + tire.base_offset
    
    # Component 2: Linear degradation
    linear_component = tire.linear_degradation * tire_age
    
    # Component 3: Quadratic degradation (accelerated wear)
    quadratic_component = tire.quadratic_degradation * (tire_age ** 2)
    
    # Component 4: Temperature effect
    temp_deviation = abs(track_temp - tire.optimal_temperature)
    temp_component = tire.temp_sensitivity * temp_deviation
    
    # Sum all components (full float precision)
    return base_component + linear_component + quadratic_component + temp_component


def calculate_stint_time(
    compound: str,
    num_laps: int,
    track_temp: float,
    base_lap_time: float,
    start_age: int = 1
) -> float:
    """Calculate total stint time using O(1) closed-form formulas.
    
    Uses arithmetic series formulas to compute sum of lap times without iteration:
        sum(age) = n×(a+b)/2     where a=start_age, b=start_age+n-1
        sum(age²) = [b×(b+1)×(2b+1) - (a-1)×a×(2a-1)] / 6
    
    For a stint of n laps:
        stint_time = n×(base + offset + temp)
                   + linear × sum(ages)
                   + quadratic × sum(age²)
    
    Args:
        compound: Tire compound (SOFT, MEDIUM, HARD)
        num_laps: Number of laps in the stint
        track_temp: Track temperature in °C
        base_lap_time: Base lap time for the track
        start_age: Starting tire age (default=1 for fresh tires)
        
    Returns:
        Total stint time in seconds
    """
    tire = get_compound(compound)
    
    # Age range: [start_age, start_age + num_laps - 1]
    a = float(start_age)
    b = float(start_age + num_laps - 1)
    n = float(num_laps)
    
    # Component 1: Constant terms (base + offset + temp)
    temp_deviation = abs(track_temp - tire.optimal_temperature)
    temp_effect = tire.temp_sensitivity * temp_deviation
    constant_per_lap = base_lap_time + tire.base_offset + temp_effect
    constant_contribution = n * constant_per_lap
    
    # Component 2: Sum of ages (linear degradation)
    # Formula: sum = n × (a + b) / 2
    age_sum = n * (a + b) / 2.0
    linear_contribution = tire.linear_degradation * age_sum
    
    # Component 3: Sum of age squares (quadratic degradation)
    # Formula: sum[i²] from i=a to b = [b(b+1)(2b+1) - (a-1)a(2a-1)] / 6
    sum_sq_b = b * (b + 1.0) * (2.0 * b + 1.0) / 6.0
    sum_sq_a_minus_1 = (a - 1.0) * a * (2.0 * a - 1.0) / 6.0
    age_squared_sum = sum_sq_b - sum_sq_a_minus_1
    quadratic_contribution = tire.quadratic_degradation * age_squared_sum
    
    # Total stint time
    return constant_contribution + linear_contribution + quadratic_contribution


def compare_compounds(num_laps: int, track_temp: float) -> Dict[str, float]:
    """Compare performance of different compounds over a stint.
    
    Args:
        num_laps: Stint length in laps
        track_temp: Track temperature in °C
        
    Returns:
        Dictionary mapping compound names to total stint times
    """
    results = {}
    for compound in ['SOFT', 'MEDIUM', 'HARD']:
        results[compound] = calculate_stint_time(
            compound=compound,
            num_laps=num_laps,
            track_temp=track_temp,
            base_lap_time=85.0
        )
    return results


if __name__ == '__main__':
    # Quick validation
    print("Testing tire physics...")
    
    # Test lap time calculation
    lap_time = calculate_lap_time('SOFT', 5, 30.0, 85.0)
    print(f"SOFT at age 5: {lap_time:.6f}s")
    
    # Test stint calculation
    stint_time = calculate_stint_time('SOFT', 10, 30.0, 85.0)
    print(f"SOFT stint (10 laps): {stint_time:.6f}s")
    
    # Compare compounds
    comparison = compare_compounds(15, 30.0)
    print("\nCompound comparison (15-lap stint):")
    for compound, time in sorted(comparison.items(), key=lambda x: x[1]):
        print(f"  {compound}: {time:.3f}s")
