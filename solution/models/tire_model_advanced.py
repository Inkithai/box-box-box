#!/usr/bin/env python3
"""
Advanced Tire Performance Model

Implements high-precision tire physics with:
- Quadratic degradation per lap (non-linear wear)
- Compound-specific temperature sensitivity
- Full float precision throughout calculations
- Minimal rounding errors

This model captures realistic F1 tire behavior including:
- Initial performance drop-off
- Accelerated degradation in later life
- Temperature-dependent grip levels
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class TireCompoundProperties:
    """Physical properties for each tire compound."""
    name: str
    base_offset: float  # Speed offset relative to SOFT (seconds)
    linear_degradation: float  # Linear degradation coefficient (s/lap)
    quadratic_degradation: float  # Quadratic degradation coefficient (s/lap²)
    optimal_temperature: float  # Temperature at which tire performs best (°C)
    temp_sensitivity: float  # Grip loss per °C deviation from optimal (s/°C)
    heat_capacity: float  # How quickly tire heats up (affects temp sensitivity)


# Tire compound definitions with physically realistic parameters
TIRE_COMPOUNDS: Dict[str, TireCompoundProperties] = {
    'SOFT': TireCompoundProperties(
        name='SOFT',
        base_offset=0.0,           # Reference compound (fastest)
        linear_degradation=0.12,   # High initial degradation
        quadratic_degradation=0.008,  # Accelerates quickly
        optimal_temperature=28.0,  # Works best at lower temps
        temp_sensitivity=0.035,    # Very sensitive to temperature
        heat_capacity=1.0          # Heats up quickly
    ),
    'MEDIUM': TireCompoundProperties(
        name='MEDIUM',
        base_offset=0.75,          # +0.75s vs SOFT
        linear_degradation=0.08,   # Moderate degradation
        quadratic_degradation=0.004,  # More progressive wear
        optimal_temperature=30.0,  # Middle range
        temp_sensitivity=0.025,    # Less sensitive than SOFT
        heat_capacity=0.95         # Slightly slower to heat
    ),
    'HARD': TireCompoundProperties(
        name='HARD',
        base_offset=1.50,          # +1.50s vs SOFT
        linear_degradation=0.05,   # Low degradation
        quadratic_degradation=0.002,  # Very progressive, durable
        optimal_temperature=32.0,  # Needs higher temps
        temp_sensitivity=0.018,    # Least sensitive
        heat_capacity=0.90         # Slowest to heat up
    )
}


def get_compound_properties(compound: str) -> TireCompoundProperties:
    """
    Get tire compound properties with validation.
    
    Args:
        compound: Tire compound name ('SOFT', 'MEDIUM', 'HARD')
        
    Returns:
        TireCompoundProperties object
        
    Raises:
        ValueError: If compound is not recognized
    """
    if compound not in TIRE_COMPOUNDS:
        raise ValueError(
            f"Unknown tire compound '{compound}'. "
            f"Valid options: {', '.join(TIRE_COMPOUNDS.keys())}"
        )
    
    return TIRE_COMPOUNDS[compound]


def calculate_lap_time_precise(
    compound: str,
    tire_age: int,
    track_temp: float,
    base_lap_time: float
) -> float:
    """
    Calculate precise lap time with full float precision.
    
    Uses the complete quadratic degradation model:
    lap_time = base + compound_offset 
             + (linear_deg × age) 
             + (quadratic_deg × age²)
             + temp_effect
    
    Args:
        compound: Tire compound ('SOFT', 'MEDIUM', 'HARD')
        tire_age: Current tire age in laps (1-indexed)
        track_temp: Track temperature in °C
        base_lap_time: Base lap time for the track (seconds)
        
    Returns:
        Precise lap time in seconds (full float precision)
    """
    props = get_compound_properties(compound)
    
    # Component 1: Base lap time
    lap_time = base_lap_time
    
    # Component 2: Compound speed offset
    lap_time += props.base_offset
    
    # Component 3: Linear degradation
    lap_time += props.linear_degradation * tire_age
    
    # Component 4: Quadratic degradation (accelerated wear)
    lap_time += props.quadratic_degradation * (tire_age ** 2)
    
    # Component 5: Temperature effect
    temp_deviation = track_temp - props.optimal_temperature
    temp_penalty = abs(temp_deviation) * props.temp_sensitivity
    
    # Apply heat capacity factor (tires perform worse when cold)
    if track_temp < props.optimal_temperature:
        # Cold tires: additional penalty
        temp_penalty *= (1.0 + (1.0 - props.heat_capacity))
    
    lap_time += temp_penalty
    
    return lap_time


def calculate_stint_time_quadratic(
    compound: str,
    num_laps: int,
    track_temp: float,
    base_lap_time: float,
    start_age: int = 1
) -> float:
    """
    Calculate total stint time using quadratic degradation formula.
    
    For a stint of n laps starting at age `start_age`:
    
    stint_time = Σ[lap_time(age) for age in start_age..(start_age+n-1)]
    
    Using the quadratic model:
    lap_time(age) = base + offset + linear×age + quadratic×age² + temp
    
    Summing over n laps:
    stint_time = n×(base + offset + temp)
               + linear × Σ[age] 
               + quadratic × Σ[age²]
    
    Where:
    - Σ[age] = n×(2×start_age + n - 1)/2  (arithmetic series)
    - Σ[age²] = n×(start_age² + (start_age+n-1)² + start_age×(start_age+n-1))/3
              = n×(a² + ab + b²)/3 where a=start_age, b=start_age+n-1
    
    Args:
        compound: Tire compound ('SOFT', 'MEDIUM', 'HARD')
        num_laps: Number of laps in the stint
        track_temp: Track temperature in °C
        base_lap_time: Base lap time for the track
        start_age: Starting tire age (default: 1 for fresh tires)
        
    Returns:
        Total stint time in seconds (full float precision)
    """
    props = get_compound_properties(compound)
    
    # Convert to float for precision
    n = float(num_laps)
    a = float(start_age)
    b = float(start_age + num_laps - 1)  # Final tire age
    
    # Temperature effect (constant per lap)
    temp_deviation = track_temp - props.optimal_temperature
    temp_penalty_per_lap = abs(temp_deviation) * props.temp_sensitivity
    
    if track_temp < props.optimal_temperature:
        temp_penalty_per_lap *= (1.0 + (1.0 - props.heat_capacity))
    
    # Component 1: Constant terms (base + offset + temp)
    constant_contribution = n * (base_lap_time + props.base_offset + temp_penalty_per_lap)
    
    # Component 2: Linear degradation sum
    # Sum of arithmetic series: a + (a+1) + ... + b
    # Formula: n × (a + b) / 2
    age_sum = n * (a + b) / 2.0
    linear_contribution = props.linear_degradation * age_sum
    
    # Component 3: Quadratic degradation sum
    # Sum of squares: a² + (a+1)² + ... + b²
    # Correct formula: n×(n-1)×(2n-1)/6 for sum from 1 to n-1, adjusted for start_age
    # Better approach: use closed form for sum of squares from a to b
    # Σ[i²] from i=a to b = (b×(b+1)×(2b+1) - (a-1)×a×(2a-1)) / 6
    
    sum_squares_b = b * (b + 1.0) * (2.0*b + 1.0) / 6.0
    sum_squares_a_minus_1 = (a - 1.0) * a * (2.0*a - 1.0) / 6.0
    sum_of_squares = sum_squares_b - sum_squares_a_minus_1
    
    quadratic_contribution = props.quadratic_degradation * sum_of_squares
    
    # Total stint time
    total_time = (
        constant_contribution +
        linear_contribution +
        quadratic_contribution
    )
    
    return total_time


def calculate_degradation_acceleration(
    compound: str,
    tire_age: int
) -> float:
    """
    Calculate how much faster degradation is accelerating at a given age.
    
    The second derivative of the degradation function shows acceleration:
    d²(lap_time)/d(age)² = 2 × quadratic_coefficient
    
    This is constant, but the impact grows with age because:
    degradation_rate(age) = linear + 2×quadratic×age
    
    Args:
        compound: Tire compound name
        tire_age: Current tire age
        
    Returns:
        Degradation acceleration (increase in degradation rate per lap)
    """
    props = get_compound_properties(compound)
    
    # Rate of change of degradation (first derivative)
    current_degradation_rate = (
        props.linear_degradation + 
        2.0 * props.quadratic_degradation * tire_age
    )
    
    return current_degradation_rate


def find_optimal_stint_length(
    compound: str,
    track_temp: float,
    base_lap_time: float,
    pit_lane_time: float,
    target_avg_lap: float = None
) -> int:
    """
    Find the optimal stint length that minimizes average lap time.
    
    Accounts for:
    - Increasing degradation with tire age
    - Pit lane time penalty
    - Compound-specific characteristics
    
    Uses numerical optimization to find the minimum.
    
    Args:
        compound: Tire compound to analyze
        track_temp: Track temperature
        base_lap_time: Base lap time for track
        pit_lane_time: Time lost during pit stop
        target_avg_lap: Optional target average lap time
        
    Returns:
        Optimal stint length in laps
    """
    props = get_compound_properties(compound)
    
    # Try different stint lengths and find minimum
    best_laps = 1
    best_avg_time = float('inf')
    
    for stint_laps in range(1, 51):  # Test 1-50 laps
        stint_time = calculate_stint_time_quadratic(
            compound=compound,
            num_laps=stint_laps,
            track_temp=track_temp,
            base_lap_time=base_lap_time,
            start_age=1
        )
        
        # Average lap time including pit stop
        avg_lap_time = (stint_time + pit_lane_time) / stint_laps
        
        if avg_lap_time < best_avg_time:
            best_avg_time = avg_lap_time
            best_laps = stint_laps
        
        # Early exit if we've passed the minimum
        if avg_lap_time > best_avg_time * 1.05 and stint_laps > 10:
            break
    
    return best_laps


def compare_compound_performance(
    track_temp: float,
    base_lap_time: float,
    stint_length: int
) -> Dict[str, Dict[str, float]]:
    """
    Compare all three compounds over a given stint length.
    
    Args:
        track_temp: Track temperature
        base_lap_time: Base lap time
        stint_length: Stint length to compare
        
    Returns:
        Dictionary with performance metrics for each compound
    """
    results = {}
    
    for compound in ['SOFT', 'MEDIUM', 'HARD']:
        props = get_compound_properties(compound)
        
        # Calculate stint time
        stint_time = calculate_stint_time_quadratic(
            compound=compound,
            num_laps=stint_length,
            track_temp=track_temp,
            base_lap_time=base_lap_time
        )
        
        # Calculate average lap time
        avg_lap = stint_time / stint_length
        
        # Calculate degradation over stint
        first_lap = calculate_lap_time_precise(
            compound=compound,
            tire_age=1,
            track_temp=track_temp,
            base_lap_time=base_lap_time
        )
        last_lap = calculate_lap_time_precise(
            compound=compound,
            tire_age=stint_length,
            track_temp=track_temp,
            base_lap_time=base_lap_time
        )
        degradation = last_lap - first_lap
        
        results[compound] = {
            'stint_time': stint_time,
            'average_lap': avg_lap,
            'total_degradation': degradation,
            'degradation_per_lap': degradation / stint_length,
            'base_offset': props.base_offset,
            'linear_deg': props.linear_degradation,
            'quadratic_deg': props.quadratic_degradation
        }
    
    return results


def validate_model_parameters() -> bool:
    """
    Validate that tire model parameters are physically realistic.
    
    Checks:
    - All offsets are non-negative
    - Degradation rates are positive
    - Temperature sensitivities are reasonable
    - Quadratic term doesn't dominate linear term
    
    Returns:
        True if all validations pass
    """
    all_valid = True
    
    for compound, props in TIRE_COMPOUNDS.items():
        errors = []
        
        # Check base offset
        if props.base_offset < 0:
            errors.append(f"Negative base offset: {props.base_offset}")
        
        # Check degradation rates
        if props.linear_degradation <= 0:
            errors.append(f"Non-positive linear degradation: {props.linear_degradation}")
        
        if props.quadratic_degradation < 0:
            errors.append(f"Negative quadratic degradation: {props.quadratic_degradation}")
        
        # Check quadratic doesn't dominate at typical ages
        # At age 10, quadratic should contribute less than linear
        age_10_linear = props.linear_degradation * 10
        age_10_quadratic = props.quadratic_degradation * 100
        if age_10_quadratic > age_10_linear:
            errors.append(
                f"Quadratic dominates at age 10: {age_10_quadratic:.4f} > {age_10_linear:.4f}"
            )
        
        # Check temperature sensitivity
        if props.temp_sensitivity < 0 or props.temp_sensitivity > 0.1:
            errors.append(
                f"Unrealistic temp sensitivity: {props.temp_sensitivity}"
            )
        
        # Check optimal temperature range
        if props.optimal_temperature < 20 or props.optimal_temperature > 40:
            errors.append(
                f"Optimal temp outside realistic range: {props.optimal_temperature}"
            )
        
        if errors:
            print(f"Validation errors for {compound}:")
            for error in errors:
                print(f"  - {error}")
            all_valid = False
    
    return all_valid


if __name__ == '__main__':
    """Test the advanced tire model."""
    print("="*70)
    print("ADVANCED TIRE MODEL VALIDATION")
    print("="*70)
    
    # Validate parameters
    print("\nValidating model parameters...")
    if validate_model_parameters():
        print("✓ All parameters valid")
    else:
        print("✗ Parameter validation failed")
    
    # Test lap time calculation
    print("\nLap time examples (30°C track, 85s base):")
    print("-"*70)
    
    for compound in ['SOFT', 'MEDIUM', 'HARD']:
        for age in [1, 5, 10, 15, 20]:
            lap_time = calculate_lap_time_precise(
                compound=compound,
                tire_age=age,
                track_temp=30.0,
                base_lap_time=85.0
            )
            print(f"{compound:6} age {age:2d}: {lap_time:>8.6f}s")
    
    # Test stint time calculation
    print("\nStint time comparison (15 laps, 30°C):")
    print("-"*70)
    
    for compound in ['SOFT', 'MEDIUM', 'HARD']:
        stint_time = calculate_stint_time_quadratic(
            compound=compound,
            num_laps=15,
            track_temp=30.0,
            base_lap_time=85.0
        )
        avg_lap = stint_time / 15
        print(f"{compound:6}: {stint_time:>10.6f}s total, {avg_lap:>10.6f}s avg lap")
    
    # Show compound comparison
    print("\nDetailed compound analysis:")
    print("-"*70)
    
    comparison = compare_compound_performance(
        track_temp=30.0,
        base_lap_time=85.0,
        stint_length=15
    )
    
    for compound, metrics in comparison.items():
        print(f"\n{compound}:")
        print(f"  Stint time:      {metrics['stint_time']:.6f}s")
        print(f"  Average lap:     {metrics['average_lap']:.6f}s")
        print(f"  Total deg:       {metrics['total_degradation']:.6f}s")
        print(f"  Deg per lap:     {metrics['degradation_per_lap']:.6f}s")
        print(f"  Base offset:     {metrics['base_offset']:.3f}s")
        print(f"  Linear deg:      {metrics['linear_deg']:.4f} s/lap")
        print(f"  Quadratic deg:   {metrics['quadratic_deg']:.5f} s/lap²")
    
    print("\n" + "="*70)
    print("Model validation complete")
    print("="*70)
