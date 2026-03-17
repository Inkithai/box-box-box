"""
Global constants and configuration for the race simulator.
"""

# Tire compound names
TIRE_COMPOUND_SOFT = "SOFT"
TIRE_COMPOUND_MEDIUM = "MEDIUM"
TIRE_COMPOUND_HARD = "HARD"

# Valid tire compounds list
VALID_TIRE_COMPOUNDS = [TIRE_COMPOUND_SOFT, TIRE_COMPOUND_MEDIUM, TIRE_COMPOUND_HARD]

# Simulation parameters
NUM_DRIVERS = 20
DEFAULT_OPTIMAL_TEMP = 30  # Celsius

# Lap time calculation defaults
DEFAULT_DEGRADATION_RATE = 0.10
DEFAULT_TEMPERATURE_SENSITIVITY = 0.05
