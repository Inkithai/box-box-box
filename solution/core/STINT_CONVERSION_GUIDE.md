# Tire Stint Conversion Guide

## Overview

The race simulator now uses a **stint-based approach** to manage tire strategies. Instead of tracking individual pit stops during the simulation, each driver's strategy is pre-converted into tire stints - continuous periods on the same tire compound.

This refactoring simplifies lap-time calculations, improves code clarity, and reduces the complexity of pit stop handling during the race simulation.

---

## What is a Tire Stint?

A **stint** represents a contiguous sequence of laps where the driver uses the same tire compound. Each stint is defined by:

- **start_lap**: The first lap number (1-indexed) when this tire is fitted
- **end_lap**: The last lap number (inclusive) before changing tires
- **tire**: The tire compound used (SOFT, MEDIUM, or HARD)

### Example

**Input Strategy:**
```json
{
  "starting_tire": "SOFT",
  "pit_stops": [
    {"lap": 18, "to_tire": "MEDIUM"},
    {"lap": 38, "to_tire": "HARD"}
  ]
}
```

**Converted to Stints:**
```python
[
  {"start_lap": 1, "end_lap": 17, "tire": "SOFT"},
  {"start_lap": 18, "end_lap": 37, "tire": "MEDIUM"},
  {"start_lap": 38, "end_lap": 50, "tire": "HARD"}  # Assuming 50-lap race
]
```

---

## Key Benefits

### 1. **Simplified Lap-Time Calculation**

Before (pit stop checking):
```python
if driver.should_pit_this_lap(lap):
    driver.change_tire(new_compound)
    driver.reset_tire_age()
```

After (direct stint lookup):
```python
driver.update_current_stint(lap)
tire = driver.get_current_tire(lap)
age = driver.get_tire_age(lap)
```

### 2. **Clearer Code Structure**

Stints make it explicit which tire compound is used for each lap, eliminating ambiguity about when tire changes occur.

### 3. **Better Validation**

Strategies are validated upfront during conversion, catching errors early:
- Invalid tire compounds
- Out-of-range pit stop laps
- Missing required fields

### 4. **Easier Testing**

Stints can be tested independently from the race simulation logic.

---

## Implementation Details

### Function Signature

```python
def convert_strategy_to_stints(strategy: dict, total_laps: int) -> list[dict]:
    """
    Convert a driver's pit stop strategy into tire stints.
    
    Args:
        strategy: Driver strategy with starting_tire and pit_stops
        total_laps: Total number of laps in the race
        
    Returns:
        List of stint dictionaries with start_lap, end_lap, and tire
        
    Raises:
        ValueError: If strategy is invalid
    """
```

### Conversion Algorithm

1. **Validate starting tire** - Must be SOFT, MEDIUM, or HARD
2. **Sort pit stops** by lap number (ascending)
3. **Validate each pit stop**:
   - Lap must be within range [1, total_laps]
   - `to_tire` must be valid compound
4. **Build stints iteratively**:
   - First stint: Lap 1 to (first pit lap - 1)
   - Middle stints: Between consecutive pit stops
   - Final stint: Last pit lap to total_laps
5. **Return** list of stints

### Edge Cases Handled

- **No pit stops**: Single stint covering all laps
- **Pit on lap 1**: First stint skipped, starts directly on new tire
- **Unsorted pit stops**: Automatically sorted by lap number
- **Invalid inputs**: Clear ValueError messages

---

## Usage Examples

### Example 1: Basic Two-Stop Strategy

```python
from core.driver import convert_strategy_to_stints

strategy = {
    'starting_tire': 'MEDIUM',
    'pit_stops': [
        {'lap': 20, 'to_tire': 'SOFT'},
        {'lap': 35, 'to_tire': 'HARD'}
    ]
}

total_laps = 50
stints = convert_strategy_to_stints(strategy, total_laps)

# Result:
# [
#     {'start_lap': 1, 'end_lap': 19, 'tire': 'MEDIUM'},
#     {'start_lap': 20, 'end_lap': 34, 'tire': 'SOFT'},
#     {'start_lap': 35, 'end_lap': 50, 'tire': 'HARD'}
# ]
```

### Example 2: No Pit Stops

```python
strategy = {
    'starting_tire': 'HARD',
    'pit_stops': []
}

stints = convert_strategy_to_stints(strategy, total_laps=30)

# Result: Single stint
# [{'start_lap': 1, 'end_lap': 30, 'tire': 'HARD'}]
```

### Example 3: Early Pit Stop

```python
strategy = {
    'starting_tire': 'SOFT',
    'pit_stops': [
        {'lap': 5, 'to_tire': 'MEDIUM'}
    ]
}

stints = convert_strategy_to_stints(strategy, total_laps=40)

# Result:
# [
#     {'start_lap': 1, 'end_lap': 4, 'tire': 'SOFT'},
#     {'start_lap': 5, 'end_lap': 40, 'tire': 'MEDIUM'}
# ]
```

---

## Driver Class Integration

The `Driver` class now stores stints instead of raw pit stops:

### Constructor

```python
driver = Driver(driver_id='D001', strategy=strategy_dict, total_laps=50)
```

The constructor automatically converts the strategy to stints.

### Key Methods

#### Get Tire for Specific Lap

```python
tire = driver.get_current_tire(lap=25)
# Returns: Tire compound for lap 25
```

#### Get Tire Age for Specific Lap

```python
age = driver.get_tire_age(lap=25)
# Returns: How many laps completed on current tire set at lap 25
```

#### Update Current Stint

```python
driver.update_current_stint(lap_number)
# Updates internal state to correct stint for this lap
```

#### Check if Pitting This Lap

```python
if driver.should_pit_this_lap(current_lap):
    driver.execute_pit_stop(pit_lane_time)
```

---

## Simulator Integration

The race simulator now uses stints for cleaner lap-by-lap simulation:

### Updated Simulation Loop

```python
def _simulate_lap(self, lap_number: int) -> None:
    for driver in self.drivers:
        # Step 1: Update to correct stint for this lap
        driver.update_current_stint(lap_number)
        
        # Step 2: Get tire and age from stints
        tire = driver.get_current_tire(lap_number)
        age = driver.get_tire_age(lap_number)
        
        # Step 3: Calculate lap time
        lap_time = calculator.calculate(base_time, tire, age, track_temp)
        
        # Step 4: Add to total race time
        driver.add_lap_time(lap_time)
        
        # Step 5: Handle pit stop if this lap ends a stint
        if driver.should_pit_this_lap(lap_number):
            driver.execute_pit_stop(pit_lane_time)
```

---

## Validation Rules

The conversion function enforces these rules:

### 1. Valid Tire Compounds

```python
# ✓ Valid
{'starting_tire': 'SOFT'}
{'to_tire': 'MEDIUM'}

# ✗ Invalid - raises ValueError
{'starting_tire': 'ULTRASOFT'}
{'to_tire': 'INTERMEDIATE'}
```

### 2. Valid Lap Range

```python
# ✓ Valid (in 50-lap race)
{'lap': 1}
{'lap': 25}
{'lap': 50}

# ✗ Invalid - raises ValueError
{'lap': 0}      # Before race start
{'lap': 51}     # After race end
```

### 3. Complete Coverage

All laps from 1 to total_laps must be covered exactly once:

```python
# ✓ Correct - no gaps, no overlaps
Stint 1: Laps 1-17
Stint 2: Laps 18-37
Stint 3: Laps 38-50

# ✗ Incorrect - gap at lap 18
Stint 1: Laps 1-17
Stint 2: Laps 19-50  # Missing lap 18!
```

---

## Testing

Comprehensive tests ensure correctness:

### Run Test Suite

```bash
cd solution/core
python test_stints.py
```

### Tests Cover

1. ✓ Basic stint conversion
2. ✓ No pit stops (single stint)
3. ✓ One pit stop (two stints)
4. ✓ Multiple pit stops
5. ✓ Unsorted pit stops (auto-sort)
6. ✓ Invalid tire compounds
7. ✓ Invalid pit stop laps
8. ✓ Driver class integration
9. ✓ Complete lap coverage
10. ✓ Edge case: Pit on first lap

---

## Migration Notes

If you have existing code using the old pit stop approach:

### Old Approach (Deprecated)

```python
driver = Driver('D001', strategy)  # No total_laps
driver.change_tire('MEDIUM')       # Manual tire changes
```

### New Approach (Required)

```python
driver = Driver('D001', strategy, total_laps=50)  # Pass total_laps
driver.update_current_stint(lap)                   # Use stint-based methods
```

### Breaking Changes

- `Driver.__init__()` now requires `total_laps` parameter
- `change_tire()` method deprecated (use stints instead)
- Tire age automatically calculated from stints

---

## Performance Considerations

### Time Complexity

- **Conversion**: O(n log n) where n = number of pit stops (for sorting)
- **Stint lookup**: O(s) where s = number of stints (typically 1-4)
- **Per-lap operations**: O(1) amortized (stint index cached)

### Memory Overhead

Minimal: Each stint adds ~100 bytes. Typical 3-stint strategy = ~300 bytes per driver.

---

## Future Enhancements

Potential improvements:

1. **Stint visualization**: Graphical timeline showing tire usage
2. **Strategy optimization**: Find optimal stint lengths
3. **Fuel load modeling**: Affect tire degradation per stint
4. **Track evolution**: Changing grip levels across stints

---

## Summary

The stint-based approach provides:

✅ **Cleaner code** - No complex pit stop tracking during simulation  
✅ **Better validation** - Catch strategy errors upfront  
✅ **Easier testing** - Isolated stint conversion logic  
✅ **Improved performance** - Faster lap-by-simulation  
✅ **Enhanced clarity** - Explicit tire usage per lap  

This refactoring lays the foundation for more advanced strategy analysis and optimization features.
