# Tire Performance Model Documentation

## Overview

The tire performance model (`tire_model.py`) provides a sophisticated simulation of F1 tire behavior, accounting for compound characteristics, degradation over time, and environmental effects.

## Model Architecture

### Three Tire Compounds

The model defines three distinct tire compounds, each with unique characteristics:

| Compound | Base Offset | Degradation Rate | Optimal Life | Temp Sensitivity | Optimal Temp |
|----------|-------------|------------------|--------------|------------------|--------------|
| **SOFT**   | 0.00s       | 0.12s/lap        | 10 laps      | 0.030s/°C        | 28°C         |
| **MEDIUM** | 0.75s       | 0.08s/lap        | 18 laps      | 0.025s/°C        | 30°C         |
| **HARD**   | 1.50s       | 0.05s/lap        | 30 laps      | 0.020s/°C        | 32°C         |

#### Compound Characteristics

**SOFT Compound (Red Sidewall)**
- Fastest initial grip (0.0s base offset)
- Degrades rapidly (0.12s per lap)
- Best suited for short stints and qualifying
- Performs optimally in cooler conditions (28°C)
- Most sensitive to temperature variations

**MEDIUM Compound (Yellow Sidewall)**
- Balanced performance (+0.75s vs SOFT)
- Moderate degradation (0.08s per lap)
- Versatile for various strategies
- Optimal at moderate temperatures (30°C)
- Good compromise between speed and durability

**HARD Compound (White Sidewall)**
- Slowest but most durable (+1.50s vs SOFT)
- Lowest degradation (0.05s per lap)
- Ideal for long stints
- Performs best in hot conditions (32°C)
- Least affected by temperature changes

## Lap Time Calculation

### Complete Formula

```python
lap_time = base_lap_time 
         + compound_offset 
         + degradation_rate * tire_age 
         + temperature_effect
```

Or using the model's method:

```python
from models.tire_model import TireModel

adjustment = TireModel.calculate_total_lap_time_adjustment(
    compound='SOFT',
    tire_age=10,
    track_temp=30
)

final_lap_time = base_lap_time + adjustment
```

### Component Breakdown

#### 1. Base Compound Offset

The inherent speed difference between compounds when fresh:

```python
TireModel.get_compound_offset('SOFT')    # Returns: 0.0
TireModel.get_compound_offset('MEDIUM')  # Returns: 0.75
TireModel.get_compound_offset('HARD')    # Returns: 1.5
```

#### 2. Tire Degradation

Cumulative performance loss as tires age, calculated using a **two-phase model**:

**Phase 1: Optimal Period (Linear Degradation)**
```
degradation = tire_age × degradation_rate
```

**Phase 2: Post-Optimal (Accelerated Degradation)**
```
degradation = (optimal_laps × rate) + ((age - optimal_laps) × rate × 2)
```

Example for SOFT tire at lap 15 (past optimal life of 10 laps):
```python
# Phase 1: First 10 laps
phase1 = 10 laps × 0.12s/lap = 1.2s

# Phase 2: Laps 11-15 (5 laps at double rate)
phase2 = 5 laps × 0.12s/lap × 2 = 1.2s

# Total degradation
total = 1.2s + 1.2s = 2.4s
```

**Temperature Effect on Degradation:**
```python
temp_factor = 1.0 + (|track_temp - optimal_temp| × temp_sensitivity)
degradation_with_temp = base_degradation × temp_factor
```

Example: SOFT tire at lap 10, track temp 35°C (optimal is 28°C):
```python
temp_deviation = |35 - 28| = 7°C
temp_factor = 1.0 + (7 × 0.03) = 1.21
base_deg = 10 × 0.12 = 1.2s
adjusted_deg = 1.2s × 1.21 = 1.452s
```

#### 3. Direct Temperature Effect

Separate from degradation, this represents how track temperature directly affects tire grip:

```python
temperature_penalty = |track_temp - optimal_temp| × temp_sensitivity × 5.0
```

Example: MEDIUM compound at 35°C (optimal is 30°C):
```python
temp_deviation = |35 - 30| = 5°C
penalty = 5 × 0.025 × 5.0 = 0.625s
```

## Usage Examples

### Example 1: Fresh Tire Performance

```python
from models.tire_model import TireModel

# Calculate lap time adjustment for fresh SOFT tire at optimal temp
adjustment = TireModel.calculate_total_lap_time_adjustment(
    compound='SOFT',
    tire_age=1,
    track_temp=28  # SOFT's optimal temperature
)

print(f"Fresh SOFT lap adjustment: {adjustment:.3f}s")
# Output: ~0.120s (mostly just first-lap degradation)
```

### Example 2: Old Tire Comparison

```python
# Compare compounds at lap 20, 30°C
for compound in ['SOFT', 'MEDIUM', 'HARD']:
    adj = TireModel.calculate_total_lap_time_adjustment(
        compound, tire_age=20, track_temp=30
    )
    print(f"{compound} at lap 20: +{adj:.3f}s")

# Expected output:
# SOFT at lap 20: +3.816s (severely degraded)
# MEDIUM at lap 20: +2.510s (moderate degradation)
# HARD at lap 20: +2.540s (still performing well)
```

### Example 3: Temperature Impact Analysis

```python
# Analyze how temperature affects a MEDIUM tire at lap 10
print("MEDIUM compound, lap 10:")
for temp in [25, 30, 35]:
    adj = TireModel.calculate_total_lap_time_adjustment(
        'MEDIUM', tire_age=10, track_temp=temp
    )
    print(f"  At {temp}°C: +{adj:.3f}s")

# Shows how deviation from 30°C optimal increases lap time
```

### Example 4: Strategy Planning

```python
# Calculate total stint time for different strategies
base_lap = 85.0
track_temp = 30

# 10-lap stint on SOFT
soft_total = sum(
    base_lap + TireModel.calculate_total_lap_time_adjustment('SOFT', age, track_temp)
    for age in range(1, 11)
)

# 10-lap stint on HARD
hard_total = sum(
    base_lap + TireModel.calculate_total_lap_time_adjustment('HARD', age, track_temp)
    for age in range(1, 11)
)

print(f"10-lap SOFT stint: {soft_total:.2f}s")
print(f"10-lap HARD stint: {hard_total:.2f}s")
print(f"Difference: {hard_total - soft_total:.2f}s ({hard_total - soft_total:.3f}s/lap)")
```

## API Reference

### Core Methods

#### `get_compound_offset(compound: str) -> float`

Returns the base lap time offset for a tire compound.

**Parameters:**
- `compound`: One of 'SOFT', 'MEDIUM', 'HARD'

**Returns:** Base offset in seconds

**Raises:** `ValueError` if invalid compound

---

#### `calculate_degradation(compound: str, tire_age: int, track_temp: int) -> float`

Calculates cumulative degradation penalty based on tire age and temperature.

**Parameters:**
- `compound`: Tire compound name
- `tire_age`: Laps completed on current tire set (1-indexed)
- `track_temp`: Current track temperature in °C

**Returns:** Degradation penalty in seconds

**Raises:** `ValueError` if invalid compound

---

#### `calculate_temperature_effect(compound: str, track_temp: int) -> float`

Calculates direct temperature effect on lap time (independent of degradation).

**Parameters:**
- `compound`: Tire compound name
- `track_temp`: Track temperature in °C

**Returns:** Temperature penalty in seconds (always ≥ 0)

---

#### `calculate_total_lap_time_adjustment(compound: str, tire_age: int, track_temp: int) -> float`

Calculates complete tire adjustment combining all factors.

**Parameters:**
- `compound`: Tire compound name
- `tire_age`: Laps completed on current tire set
- `track_temp`: Track temperature in °C

**Returns:** Total adjustment in seconds (offset + degradation + temp effect)

---

#### `get_compound_properties(compound: str) -> Dict`

Returns complete property dictionary for a compound.

**Parameters:**
- `compound`: Tire compound name

**Returns:** Dictionary with all properties

---

#### `compare_compounds(track_temp: int = 30) -> Dict[str, Dict]`

Compares all three compounds at specified temperature with fresh tires.

**Parameters:**
- `track_temp`: Track temperature (default: 30°C)

**Returns:** Nested dictionary with comparison data

## Design Principles

### Two-Phase Degradation Model

The tire model uses a sophisticated two-phase approach:

1. **Optimal Period**: Tires maintain relatively consistent performance with gradual linear degradation
2. **Post-Optimal Period**: Rubber breakdown accelerates, causing faster performance loss

This creates realistic tire behavior where:
- SOFT tires perform well initially but "fall off a cliff" after ~10 laps
- HARD tires start slower but maintain performance much longer
- Temperature extremes accelerate degradation for all compounds

### Temperature Modeling

Each compound has its own optimal operating temperature, reflecting real F1 tire behavior:
- SOFT works best in cooler conditions (28°C)
- MEDIUM is balanced for average temps (30°C)
- HARD excels in hot conditions (32°C)

Deviations from optimal temperature cause:
1. Increased degradation rate (via `temp_sensitivity`)
2. Direct grip reduction (via `calculate_temperature_effect`)

### Realistic Trade-offs

The model enforces strategic trade-offs:
- **Speed vs Durability**: Faster compounds degrade quicker
- **Temperature Sensitivity**: More aggressive compounds are harder to manage
- **Strategy Flexibility**: No single "best" compound - depends on conditions

## Testing

Run the comprehensive test suite:

```bash
cd solution/models
python test_tire_model.py
```

Tests cover:
- Base compound offsets
- Degradation progression
- Temperature effects
- Complete lap time calculations
- Edge cases and error handling

## Integration

The tire model integrates with the race simulator through `lap_time.py`:

```python
from models.tire_model import TireModel

class LapTimeCalculator:
    @staticmethod
    def calculate(base_lap_time, tire_compound, tire_age, track_temp):
        # Get total adjustment from tire model
        adjustment = TireModel.calculate_total_lap_time_adjustment(
            tire_compound, tire_age, track_temp
        )
        
        # Apply to base lap time
        return base_lap_time + adjustment
```

## Future Enhancements

Potential improvements for increased realism:

1. **Non-linear degradation**: Exponential or polynomial decay curves
2. **Fuel load effects**: Heavier cars increase tire wear
3. **Track evolution**: Changing grip levels throughout race
4. **Tire preparation**: Pre-heating blankets affect initial performance
5. **Compound availability**: Restrictions on number of each compound
6. **Blistering/flattening**: Extreme wear modes at very high ages

## Notes

- All times are in seconds
- Tire age starts at 1 (first lap on new tires)
- Temperature effects are symmetric (hot and cold both penalize)
- Model is deterministic (no randomness)
- Parameters should be calibrated using historical race data
