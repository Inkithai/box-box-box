#!/usr/bin/env python3
"""
Smart Parameter Estimation from Historical Data

This analyzes historical races to extract the ACTUAL tire model parameters
that match the simulation results.
"""

import json
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from typing import Dict, List, Tuple

def load_historical_sample(n_races=100):
    """Load a sample of historical races"""
    all_races = []
    race_files = sorted(Path("data/historical_races").glob("races_*.json"))
    
    for file in race_files[:5]:  # First 5 files
        with open(file, 'r') as f:
            races = json.load(f)
            all_races.extend(races[:20])  # 20 races per file
        
        if len(all_races) >= n_races:
            break
    
    return all_races[:n_races]

def calculate_driver_times(driver_strategy, race_config):
    """Calculate total race time for a driver based on their strategy"""
    total_laps = race_config['total_laps']
    base_lap_time = race_config['base_lap_time']
    track_temp = race_config['track_temp']
    pit_lane_time = race_config['pit_lane_time']
    
    # Get stints
    stints = []
    current_tire = driver_strategy['starting_tire']
    current_age = 1
    
    pit_stops = sorted(driver_strategy.get('pit_stops', []), key=lambda x: x['lap'])
    
    last_lap = 0
    for pit_stop in pit_stops:
        stint_length = pit_stop['lap'] - last_lap
        if stint_length > 0:
            stints.append({
                'compound': current_tire,
                'laps': stint_length,
                'start_age': current_age
            })
        current_tire = pit_stop['to_tire']
        current_age = 1
        last_lap = pit_stop['lap']
    
    # Final stint
    final_laps = total_laps - last_lap
    if final_laps > 0:
        stints.append({
            'compound': current_tire,
            'laps': final_laps,
            'start_age': current_age
        })
    
    # Calculate total time
    total_time = 0.0
    pit_time_total = 0.0
    
    for stint in stints:
        compound = stint['compound']
        laps = stint['laps']
        
        # Sum lap times for this stint
        for lap_age in range(1, laps + 1):
            lap_time = calculate_lap_time(compound, lap_age, track_temp, base_lap_time)
            total_time += lap_time
        
        # Add pit stop (except for last stint)
        if stint != stints[-1]:
            pit_time_total += pit_lane_time
    
    return total_time + pit_time_total

def calculate_lap_time(compound, age, track_temp, base_lap_time):
    """Simple lap time model - to be optimized"""
    # This will be replaced with the actual model during optimization
    return base_lap_time

def objective_function(params, races):
    """Objective: minimize prediction error"""
    soft_base, medium_base, hard_base = params[:3]
    soft_lin, medium_lin, hard_lin = params[3:6]
    soft_quad, medium_quad, hard_quad = params[6:9]
    
    # Build compound properties
    compounds = {
        'SOFT': {'base': soft_base, 'lin': soft_lin, 'quad': soft_quad},
        'MEDIUM': {'base': medium_base, 'lin': medium_lin, 'quad': medium_quad},
        'HARD': {'base': hard_base, 'lin': hard_lin, 'quad': hard_quad},
    }
    
    correct_predictions = 0
    total_drivers = 0
    
    for race in races[:50]:  # Use first 50 races for speed
        race_config = race['race_config']
        strategies = race['strategies']
        actual_results = race['finishing_positions']
        
        # Calculate times for all drivers
        driver_times = []
        for pos_key, strategy in strategies.items():
            driver_id = strategy['driver_id']
            
            # Calculate total time using current parameters
            total_time = calculate_driver_time_with_params(
                strategy, race_config, compounds
            )
            
            driver_times.append((total_time, driver_id))
        
        # Sort by time
        driver_times.sort(key=lambda x: x[0])
        predicted_order = [d[1] for d in driver_times]
        
        # Count correct positions
        for pred, actual in zip(predicted_order, actual_results):
            total_drivers += 1
            if pred == actual:
                correct_predictions += 1
    
    # Return negative accuracy (we want to minimize)
    accuracy = correct_predictions / total_drivers if total_drivers > 0 else 0
    return -accuracy

def calculate_driver_time_with_params(strategy, race_config, compounds):
    """Calculate driver total time with given parameters"""
    total_laps = race_config['total_laps']
    base_lap_time = race_config['base_lap_time']
    track_temp = race_config['track_temp']
    pit_lane_time = race_config['pit_lane_time']
    
    # Get stints
    stints = []
    current_tire = strategy['starting_tire']
    
    pit_stops = sorted(strategy.get('pit_stops', []), key=lambda x: x['lap'])
    
    last_lap = 0
    for pit_stop in pit_stops:
        stint_length = pit_stop['lap'] - last_lap
        if stint_length > 0:
            stints.append({
                'compound': current_tire,
                'laps': stint_length,
            })
        current_tire = pit_stop['to_tire']
        last_lap = pit_stop['lap']
    
    # Final stint
    final_laps = total_laps - last_lap
    if final_laps > 0:
        stints.append({
            'compound': current_tire,
            'laps': final_laps,
        })
    
    # Calculate total time
    total_time = 0.0
    
    for stint in stints:
        compound = stint['compound']
        laps = stint['laps']
        comp_params = compounds[compound]
        
        # Sum lap times for this stint
        for lap_age in range(1, laps + 1):
            lap_time = (
                base_lap_time + 
                comp_params['base'] +
                comp_params['lin'] * lap_age +
                comp_params['quad'] * (lap_age ** 2)
            )
            total_time += lap_time
        
        # Add pit stop (except for last stint)
        if stint != stints[-1]:
            total_time += pit_lane_time
    
    return total_time

def main():
    print("="*80)
    print("SMART PARAMETER ESTIMATION")
    print("="*80)
    print("\nLoading historical data...")
    
    races = load_historical_sample(100)
    print(f"Loaded {len(races)} historical races")
    
    print("\nOptimizing parameters...")
    print("This may take a few minutes...\n")
    
    # Initial guess based on friend's solution
    x0 = [
        -0.6, 0.0, 0.55,    # base offsets (SOFT, MEDIUM, HARD)
        0.018, 0.0105, 0.0075,  # linear degradation
        0.004, 0.0022, 0.0014   # quadratic degradation
    ]
    
    # Bounds for parameters
    bounds = [
        (-1.0, 0.0),    # SOFT base
        (-0.5, 1.0),    # MEDIUM base
        (0.0, 2.0),     # HARD base
        (0.001, 0.05),  # SOFT linear
        (0.001, 0.05),  # MEDIUM linear
        (0.001, 0.05),  # HARD linear
        (0.0001, 0.02), # SOFT quadratic
        (0.0001, 0.02), # MEDIUM quadratic
        (0.0001, 0.02), # HARD quadratic
    ]
    
    try:
        result = minimize(
            objective_function,
            x0,
            args=(races,),
            method='L-BFGS-B',
            bounds=bounds,
            options={'maxiter': 50, 'disp': True}
        )
        
        print(f"\n{'='*80}")
        print("OPTIMIZED PARAMETERS:")
        print(f"{'='*80}")
        
        opt_params = result.x
        print(f"\nBase Offsets:")
        print(f"  SOFT:   {opt_params[0]:.4f}")
        print(f"  MEDIUM: {opt_params[1]:.4f}")
        print(f"  HARD:   {opt_params[2]:.4f}")
        
        print(f"\nLinear Degradation:")
        print(f"  SOFT:   {opt_params[3]:.6f}")
        print(f"  MEDIUM: {opt_params[4]:.6f}")
        print(f"  HARD:   {opt_params[5]:.6f}")
        
        print(f"\nQuadratic Degradation:")
        print(f"  SOFT:   {opt_params[6]:.6f}")
        print(f"  MEDIUM: {opt_params[7]:.6f}")
        print(f"  HARD:   {opt_params[8]:.6f}")
        
        print(f"\nAccuracy achieved: {-result.fun * 100:.1f}%")
        print(f"{'='*80}\n")
        
        # Save to file
        output = {
            "optimized_parameters": {
                "soft_base": opt_params[0],
                "medium_base": opt_params[1],
                "hard_base": opt_params[2],
                "soft_linear": opt_params[3],
                "medium_linear": opt_params[4],
                "hard_linear": opt_params[5],
                "soft_quadratic": opt_params[6],
                "medium_quadratic": opt_params[7],
                "hard_quadratic": opt_params[8],
            },
            "accuracy": -result.fun
        }
        
        with open("solution2/estimated_parameters.json", 'w') as f:
            json.dump(output, f, indent=2)
        
        print("✓ Parameters saved to solution2/estimated_parameters.json")
        
    except Exception as e:
        print(f"Optimization failed: {e}")
        print("\nUsing manual tuning instead...")

if __name__ == "__main__":
    main()
