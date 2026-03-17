#!/usr/bin/env python3
"""
Reverse Engineer the Race Simulation Rules

This analyzes historical races to discover the EXACT formula used.
"""

import json
from pathlib import Path
import numpy as np
from scipy import stats

def analyze_historical_race(race):
    """Analyze a single historical race to extract patterns"""
    race_config = race['race_config']
    strategies = race['strategies']
    results = race['finishing_positions']
    
    # For each driver, calculate their stint structure
    driver_info = {}
    
    for pos_key, strat in strategies.items():
        driver_id = strat['driver_id']
        
        # Get stints
        stints = []
        current_tire = strat['starting_tire']
        
        pit_stops = sorted(strat.get('pit_stops', []), key=lambda x: x['lap'])
        last_lap = 0
        
        for pit_stop in pit_stops:
            stint_length = pit_stop['lap'] - last_lap
            if stint_length > 0:
                stints.append({
                    'compound': current_tire,
                    'length': stint_length
                })
            current_tire = pit_stop['to_tire']
            last_lap = pit_stop['lap']
        
        # Final stint
        final_laps = race_config['total_laps'] - last_lap
        stints.append({
            'compound': current_tire,
            'length': final_laps
        })
        
        driver_info[driver_id] = {
            'stints': stints,
            'n_pit_stops': len(pit_stops)
        }
    
    return driver_info, results

def find_correlation_patterns(n_races=100):
    """Find patterns that correlate with finishing position"""
    
    print("="*80)
    print("REVERSE ENGINEERING ANALYSIS")
    print("="*80)
    print(f"\nAnalyzing {n_races} historical races...\n")
    
    # Load historical data
    all_races = []
    race_files = sorted(Path("data/historical_races").glob("races_*.json"))
    
    for file in race_files[:10]:
        with open(file, 'r') as f:
            races = json.load(f)
            all_races.extend(races[:10])
        
        if len(all_races) >= n_races:
            break
    
    print(f"Loaded {len(all_races)} races\n")
    
    # Analyze tire compound vs finishing position
    compound_wins = {"SOFT": 0, "MEDIUM": 0, "HARD": 0}
    compound_podiums = {"SOFT": 0, "MEDIUM": 0, "HARD": 0}
    
    starting_tire_wins = {"SOFT": 0, "MEDIUM": 0, "HARD": 0}
    
    for race in all_races:
        driver_info, results = analyze_historical_race(race)
        
        # Check winner's starting tire
        winner = results[0]
        winner_start_tire = None
        
        for pos_key, strat in race['strategies'].items():
            if strat['driver_id'] == winner:
                winner_start_tire = strat['starting_tire']
                break
        
        if winner_start_tire:
            starting_tire_wins[winner_start_tire] += 1
        
        # Check most common compound in top 3
        podium_compounds = []
        for i, driver in enumerate(results[:3]):
            for pos_key, strat in race['strategies'].items():
                if strat['driver_id'] == driver:
                    podium_compounds.append(strat['starting_tire'])
                    break
        
        for compound in podium_compounds:
            compound_podiums[compound] += 1
        
        # Check who wins based on stint length
        for pos_key, strat in race['strategies'].items():
            if strat['driver_id'] == results[0]:
                # Winner's strategy
                pit_stops = strat.get('pit_stops', [])
                if len(pit_stops) == 1:
                    # One-stop strategy
                    pass
    
    print("\nStarting Tire vs Wins:")
    total_wins = sum(starting_tire_wins.values())
    for compound, wins in starting_tire_wins.items():
        pct = wins / total_wins * 100 if total_wins > 0 else 0
        print(f"  {compound}: {wins} wins ({pct:.1f}%)")
    
    print("\nStarting Tire vs Podium Finishes:")
    total_podiums = sum(compound_podiums.values())
    for compound, podiums in compound_podiums.items():
        pct = podiums / total_podiums * 100 if total_podiums > 0 else 0
        print(f"  {compound}: {podiums} podiums ({pct:.1f}%)")
    
    print(f"\n{'='*80}")
    print("KEY INSIGHT:")
    print(f"{'='*80}")
    
    best_start = max(starting_tire_wins, key=starting_tire_wins.get)
    best_podium = max(compound_podiums, key=compound_podiums.get)
    
    print(f"Starting on {best_start} gives highest win rate")
    print(f"{best_podium} tires most common in podium finishes")

if __name__ == "__main__":
    find_correlation_patterns()
