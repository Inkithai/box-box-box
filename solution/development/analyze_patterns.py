#!/usr/bin/env python3
"""
Test Case Pattern Analyzer

Reverse-engineers the hidden test case generation model by analyzing patterns.

Analyzes:
1. Correlation between starting position and finishing position
2. Pit stop impact on final position
3. Tire compound advantages
4. Lap time patterns (if detectable)

Goal: Discover heuristic rules to improve pass rate.
"""

import json
from pathlib import Path
from typing import Dict, List
from collections import defaultdict


def analyze_test_case(test_input: dict, test_output: dict) -> dict:
    """Extract patterns from a single test case."""
    
    strategies = test_input['strategies']
    finishing_order = test_output['finishing_positions']
    
    patterns = {
        'starting_vs_finishing': [],
        'pit_stop_impact': [],
        'tire_compound_distribution': defaultdict(list),
        'position_gainers': [],
        'position_losers': []
    }
    
    # Analyze each driver
    for finish_pos, driver_id in enumerate(finishing_order, 1):
        # Find this driver's strategy
        for pos_key, strategy in strategies.items():
            if strategy['driver_id'] == driver_id:
                start_pos = int(pos_key.replace('pos', ''))
                num_pit_stops = len(strategy.get('pit_stops', []))
                starting_tire = strategy['starting_tire']
                
                position_change = start_pos - finish_pos  # Positive = gained positions
                
                patterns['starting_vs_finishing'].append({
                    'driver': driver_id,
                    'start': start_pos,
                    'finish': finish_pos,
                    'change': position_change
                })
                
                patterns['pit_stop_impact'].append({
                    'driver': driver_id,
                    'pit_stops': num_pit_stops,
                    'finish': finish_pos
                })
                
                patterns['tire_compound_distribution'][starting_tire].append(finish_pos)
                
                if position_change > 0:
                    patterns['position_gainers'].append({
                        'driver': driver_id,
                        'gained': position_change,
                        'start': start_pos,
                        'finish': finish_pos,
                        'pit_stops': num_pit_stops,
                        'tire': starting_tire
                    })
                elif position_change < 0:
                    patterns['position_losers'].append({
                        'driver': driver_id,
                        'lost': abs(position_change),
                        'start': start_pos,
                        'finish': finish_pos,
                        'pit_stops': num_pit_stops,
                        'tire': starting_tire
                    })
                
                break
    
    return patterns


def aggregate_patterns(all_patterns: list) -> dict:
    """Aggregate patterns across multiple test cases."""
    
    aggregated = {
        'correlation_start_finish': 0.0,
        'optimal_pit_stops': 0,
        'tire_advantage': {},
        'typical_position_changes': {}
    }
    
    # Calculate correlations and averages
    total_gain_by_pit_stops = defaultdict(list)
    tire_finish_positions = defaultdict(list)
    
    for patterns in all_patterns:
        # Tire compound analysis
        for tire, positions in patterns['tire_compound_distribution'].items():
            tire_finish_positions[tire].extend(positions)
        
        # Pit stop analysis
        for item in patterns['position_gainers']:
            total_gain_by_pit_stops[item['pit_stops']].append(item['gained'])
    
    # Calculate average finish position by tire
    for tire, positions in tire_finish_positions.items():
        avg_finish = sum(positions) / len(positions)
        aggregated['tire_advantage'][tire] = {
            'avg_finish': avg_finish,
            'count': len(positions)
        }
    
    # Find optimal pit stop count
    best_avg_gain = 0
    for pit_count, gains in total_gain_by_pit_stops.items():
        avg_gain = sum(gains) / len(gains)
        if avg_gain > best_avg_gain:
            best_avg_gain = avg_gain
            aggregated['optimal_pit_stops'] = pit_count
    
    return aggregated


def main():
    print("="*60)
    print("TEST CASE PATTERN ANALYZER")
    print("="*60)
    
    # Load test cases
    input_dir = Path("data/test_cases/inputs")
    output_dir = Path("data/test_cases/expected_outputs")
    
    input_files = sorted(input_dir.glob("test_*.json"))
    
    print(f"\nAnalyzing {len(input_files)} test cases...")
    
    all_patterns = []
    
    for i, input_file in enumerate(input_files[:20], 1):  # First 20 tests
        output_file = output_dir / f"{input_file.stem}.json"
        
        if not output_file.exists():
            continue
        
        with open(input_file, 'r') as f:
            input_data = json.load(f)
        
        with open(output_file, 'r') as f:
            output_data = json.load(f)
        
        patterns = analyze_test_case(input_data, output_data)
        all_patterns.append(patterns)
        
        if i % 5 == 0:
            print(f"Analyzed {i}/{min(20, len(input_files))} test cases...")
    
    print("\n" + "="*60)
    print("AGGREGATE PATTERNS")
    print("="*60)
    
    aggregated = aggregate_patterns(all_patterns)
    
    print("\n1. TIRE COMPOUND ADVANTAGE:")
    for tire, stats in sorted(aggregated['tire_advantage'].items(), 
                              key=lambda x: x[1]['avg_finish']):
        print(f"   {tire}: Avg Finish = {stats['avg_finish']:.1f} "
              f"(appeared in {stats['count']} races)")
    
    print(f"\n2. OPTIMAL PIT STOPS:")
    print(f"   Best: {aggregated['optimal_pit_stops']} pit stops")
    
    print("\n3. POSITION CHANGE PATTERNS:")
    gainers_count = sum(len(p['position_gainers']) for p in all_patterns)
    losers_count = sum(len(p['position_losers']) for p in all_patterns)
    print(f"   Position Gainers: {gainers_count}")
    print(f"   Position Losers: {losers_count}")
    print(f"   Ratio: {gainers_count / (gainers_count + losers_count) * 100:.1f}% gained")
    
    # Generate heuristic recommendations
    print("\n" + "="*60)
    print("HEURISTIC RECOMMENDATIONS")
    print("="*60)
    
    # Find best tire
    best_tire = min(aggregated['tire_advantage'].items(), 
                   key=lambda x: x[1]['avg_finish'])[0]
    print(f"\n1. Favor {best_tire} compound in heuristic model")
    print(f"   (Average finish: {aggregated['tire_advantage'][best_tire]['avg_finish']:.1f})")
    
    print(f"\n2. Optimal pit strategy: {aggregated['optimal_pit_stops']} stops")
    
    # Calculate starting position correlation
    if gainers_count > losers_count:
        print("\n3. Apply negative starting position bias")
        print("   (Drivers starting further back tend to gain positions)")
    else:
        print("\n3. Apply positive starting position bias")
        print("   (Front runners tend to maintain positions)")
    
    print("\n" + "="*60)
    print("Analysis complete!")
    print("="*60)


if __name__ == '__main__':
    main()
