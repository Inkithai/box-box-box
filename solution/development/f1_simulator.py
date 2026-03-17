#!/usr/bin/env python3
"""
F1 Race Simulator - Clean Architecture Refactoring

This module provides a high-performance, deterministic F1 race simulation engine.

Features:
- Quadratic tire degradation model
- Compound-specific temperature effects  
- Full float precision calculations
- O(1) stint time computation
- Clean JSON stdin/stdout interface
- Comprehensive error handling

Architecture:
┌─────────────────┐
│  run_simulator  │  ← CLI entry point
└────────┬────────┘
         │
┌────────▼────────┐
│  RaceSimulator  │  ← Main simulation engine
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼──┐  ┌───▼────────┐
│Driver│  │TirePhysics │  ← Tire model
└──────┘  └────────────┘
"""

__version__ = '2.0.0'
__author__ = 'F1 Simulator Team'

from .core.simulator import RaceSimulator
from .core.driver import Driver, convert_strategy_to_stints
from .models.tire_model_advanced import (
    TIRE_COMPOUNDS,
    get_compound_properties,
    calculate_lap_time_precise,
    calculate_stint_time_quadratic
)

__all__ = [
    # Main components
    'RaceSimulator',
    'Driver',
    
    # Tire model
    'TIRE_COMPOUNDS',
    'get_compound_properties', 
    'calculate_lap_time_precise',
    'calculate_stint_time_quadratic',
    
    # Utilities
    'convert_strategy_to_stints'
]
