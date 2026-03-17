#!/usr/bin/env python3
"""
Historical Data Analyzer - Extract Key Patterns

Analyzes historical races to understand tire degradation, pit stop strategies,
and winning patterns.
"""

import json
from pathlib import Path
from collections import defaultdict
import statistics

class HistoricalAnalyzer:
    """Analyze historical F1 race data for patterns."""
    
    def __init__(self):
        self.historical_dir = Path("data/historical_races")
        self.races = []
    
    def load_races(self, n_races: int = 100):
        """Load sample of historical races"""
        print(f"Loading historical races...")
        
        race_files = sorted(self.historical_dir.glob("races_*.json"))
        
        for file in race_files[:10]:  # First 10 files
            with open(file, 'r') as f:
                races = json.load(f)
                self.races.extend(races[:10])  # 10 races per file
            
            if len(self.races) >= n_races:
                break
        
        print(f"Loaded {len(self.races)} races\n")
    
    def analyze_tire_degradation(self):
        """Analyze how tire compounds perform"""
        print("="*80)
        print("TIRE DEGRADATION ANALYSIS")
        print("="*80)
        
        compound_stats = defaultdict(lambda: {
            'wins': 0,
            'podiums': 0,
            'top5': 0,
            'starts': 0,
            'stint_lengths': []
        })
        
        for race in self.races:
            strategies = race['strategies']
            results = race['finishing_positions']
            
            # Track starting tires
            for pos_key, strat in strategies.items():
                compound = strat['starting_tire']
                driver_id = strat['driver_id']
                
                compound_stats[compound]['starts'] += 1
                
                # Check finishing position
                try:
                    finish_pos = results.index(driver_id) + 1
                    
                    if finish_pos == 1:
                        compound_stats[compound]['wins'] += 1
                    elif finish_pos <= 3:
                        compound_stats[compound]['podiums'] += 1
                    elif finish_pos <= 5:
                        compound_stats[compound]['top5'] += 1
                
                except ValueError:
                    pass
                
                # Analyze stint lengths
                pit_stops = strat.get('pit_stops', [])
                if pit_stops:
                    for i, stop in enumerate(pit_stops):
                        if i == 0:
                            stint_length = stop['lap']
                        else:
                            stint_length = stop['lap'] - pit_stops[i-1]['lap']
                        compound_stats[compound]['stint_lengths'].append(stint_length)
                else:
                    # No pit stops - full race stint
                    stint_length = race['race_config']['total_laps']
                    compound_stats[compound]['stint_lengths'].append(stint_length)
        
        # Print results
        for compound in ['SOFT', 'MEDIUM', 'HARD']:
            stats = compound_stats[compound]
            total_starts = stats['starts']
            
            if total_starts > 0:
                win_rate = (stats['wins'] / total_starts) * 100
                podium_rate = (stats['podiums'] / total_starts) * 100
                top5_rate = (stats['top5'] / total_starts) * 100
                
                avg_stint = statistics.mean(stats['stint_lengths']) if stats['stint_lengths'] else 0
                
                print(f"\n{compound}:")
                print(f"  Starts: {total_starts}")
                print(f"  Wins: {stats['wins']} ({win_rate:.1f}%)")
                print(f"  Podiums: {stats['podiums']} ({podium_rate:.1f}%)")
                print(f"  Top 5: {stats['top5']} ({top5_rate:.1f}%)")
                print(f"  Avg Stint Length: {avg_stint:.1f} laps")
        
        print()
    
    def analyze_pit_strategies(self):
        """Analyze pit stop strategies"""
        print("="*80)
        print("PIT STOP STRATEGY ANALYSIS")
        print("="*80)
        
        strategy_counts = defaultdict(int)
        winner_strategies = defaultdict(int)
        
        for race in self.races:
            strategies = race['strategies']
            results = race['finishing_positions']
            winner = results[0]
            
            for pos_key, strat in strategies.items():
                driver_id = strat['driver_id']
                n_stops = len(strat.get('pit_stops', []))
                
                strategy_key = f"{n_stops}-stop"
                strategy_counts[strategy_key] += 1
                
                if driver_id == winner:
                    winner_strategies[strategy_key] += 1
        
        total_races = len(self.races)
        
        print(f"\nStrategy Distribution:")
        for strategy, count in sorted(strategy_counts.items()):
            pct = (count / (total_races * 20)) * 100
            wins = winner_strategies.get(strategy, 0)
            win_pct = (wins / total_races) * 100 if total_races > 0 else 0
            print(f"  {strategy}: {count} drivers ({pct:.1f}%), {wins} wins ({win_pct:.1f}%)")
        
        print()
    
    def analyze_track_temperature_effects(self):
        """Analyze how temperature affects tire performance"""
        print("="*80)
        print("TEMPERATURE EFFECTS ANALYSIS")
        print("="*80)
        
        temp_ranges = [
            (0, 25, "Cool"),
            (26, 30, "Moderate"),
            (31, 35, "Warm"),
            (36, 50, "Hot")
        ]
        
        for temp_min, temp_max, label in temp_ranges:
            temp_races = [r for r in self.races 
                         if temp_min <= r['race_config']['track_temp'] <= temp_max]
            
            if not temp_races:
                continue
            
            compound_wins = defaultdict(int)
            
            for race in temp_races:
                winner = race['finishing_positions'][0]
                for pos_key, strat in race['strategies'].items():
                    if strat['driver_id'] == winner:
                        compound_wins[strat['starting_tire']] += 1
            
            total = sum(compound_wins.values())
            
            print(f"\n{label} ({temp_min}-{temp_max}°C) - {len(temp_races)} races:")
            for compound in ['SOFT', 'MEDIUM', 'HARD']:
                wins = compound_wins.get(compound, 0)
                pct = (wins / total) * 100 if total > 0 else 0
                print(f"  {compound}: {wins} wins ({pct:.1f}%)")
        
        print()
    
    def get_recommended_params(self) -> dict:
        """Generate recommended parameters based on analysis"""
        print("="*80)
        print("RECOMMENDED PARAMETERS")
        print("="*80)
        
        # Analyze which compounds work best
        compound_performance = defaultdict(lambda: {'wins': 0, 'podiums': 0})
        
        for race in self.races:
            results = race['finishing_positions']
            strategies = race['strategies']
            
            for pos_key, strat in strategies.items():
                driver_id = strat['driver_id']
                compound = strat['starting_tire']
                
                try:
                    finish_pos = results.index(driver_id) + 1
                    if finish_pos == 1:
                        compound_performance[compound]['wins'] += 1
                    elif finish_pos <= 3:
                        compound_performance[compound]['podiums'] += 1
                except ValueError:
                    pass
        
        # Determine relative performance
        max_wins = max(cp['wins'] for cp in compound_performance.values())
        
        if max_wins > 0:
            # MEDIUM should be competitive based on historical data
            soft_offset = -0.4  # Reduced from -0.6
            medium_offset = 0.0
            hard_offset = 0.5   # Reduced from 0.55
            
            # Adjust degradation based on stint analysis
            soft_deg_a = 0.005  # Higher degradation
            medium_deg_a = 0.0025
            hard_deg_a = 0.0015
            
            print(f"\nBased on historical analysis:")
            print(f"  SOFT compound offset: {soft_offset}s")
            print(f"  MEDIUM compound offset: {medium_offset}s (reference)")
            print(f"  HARD compound offset: {hard_offset}s")
            print(f"\n  SOFT degradation (deg_a): {soft_deg_a}")
            print(f"  MEDIUM degradation (deg_a): {medium_deg_a}")
            print(f"  HARD degradation (deg_a): {hard_deg_a}")
            
            return {
                "compound_offset": {"SOFT": soft_offset, "MEDIUM": medium_offset, "HARD": hard_offset},
                "deg_a": {"SOFT": soft_deg_a, "MEDIUM": medium_deg_a, "HARD": hard_deg_a}
            }
        else:
            print("Insufficient data for recommendations")
            return None

def main():
    analyzer = HistoricalAnalyzer()
    analyzer.load_races(100)
    
    analyzer.analyze_tire_degradation()
    analyzer.analyze_pit_strategies()
    analyzer.analyze_track_temperature_effects()
    
    recommendations = analyzer.get_recommended_params()
    
    if recommendations:
        print(f"\n💡 Recommendation:")
        print(f"Update solution2/params.json with the values above")
        print(f"Then run: python solution2/auto_tuner_grid.py for fine-tuning")

if __name__ == "__main__":
    main()
