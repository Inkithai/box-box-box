#!/usr/bin/env python3
"""
Pattern Hunter - Find hidden patterns in test cases

Maybe there's a deterministic rule we're missing
"""

import json
from pathlib import Path
import statistics

def analyze_all_tests():
    """Look for patterns across all tests"""
    
    print("="*80)
    print("PATTERN HUNTING - Looking for Hidden Rules")
    print("="*80)
    
    test_cases_dir = Path("data/test_cases/inputs")
    expected_dir = Path("data/test_cases/expected_outputs")
    
    # Analyze first 20 tests
    patterns = {
        'winner_starting_positions': [],
        'winner_tires': [],
        'winner_pit_stops': [],
        'driver_number_patterns': []
    }
    
    for i in range(1, 21):
        test_file = test_cases_dir / f"test_{i:03d}.json"
        expected_file = expected_dir / f"test_{i:03d}.json"
        
        if not test_file.exists() or not expected_file.exists():
            continue
        
        test_data = json.loads(test_file.read_text())
        expected = json.loads(expected_file.read_text())
        
        winner = expected['finishing_positions'][0]
        
        # Find winner's strategy
        for pos_key, strat in test_data['strategies'].items():
            if strat['driver_id'] == winner:
                start_pos = int(pos_key.replace('pos', ''))
                patterns['winner_starting_positions'].append(start_pos)
                patterns['winner_tires'].append(strat['starting_tire'])
                patterns['winner_pit_stops'].append(len(strat.get('pit_stops', [])))
                
                # Check driver number
                driver_num = int(winner.replace('D', ''))
                patterns['driver_number_patterns'].append(driver_num)
    
    # Analyze patterns
    print(f"\nAnalysis of First 20 Tests:")
    print(f"\nWinner Starting Positions:")
    print(f"  Values: {patterns['winner_starting_positions']}")
    avg_start = statistics.mean(patterns['winner_starting_positions'])
    print(f"  Average: {avg_start:.1f}")
    print(f"  Most common: {max(set(patterns['winner_starting_positions']), key=patterns['winner_starting_positions'].count)}")
    
    print(f"\nWinner Tires:")
    for tire in ['SOFT', 'MEDIUM', 'HARD']:
        count = patterns['winner_tires'].count(tire)
        pct = count / len(patterns['winner_tires']) * 100
        print(f"  {tire}: {count} ({pct:.1f}%)")
    
    print(f"\nWinner Pit Stops:")
    for stops in range(4):
        count = patterns['winner_pit_stops'].count(stops)
        if count > 0:
            pct = count / len(patterns['winner_pit_stops']) * 100
            print(f"  {stops} stop(s): {count} ({pct:.1f}%)")
    
    print(f"\nDriver Numbers of Winners:")
    print(f"  Values: {patterns['driver_number_patterns']}")
    
    # Check for modulo patterns
    print(f"\n{'='*80}")
    print("MODULO PATTERN CHECK")
    print("="*80)
    
    for mod in [2, 3, 5, 7, 10]:
        remainders = [d % mod for d in patterns['driver_number_patterns']]
        print(f"\nDriver Number % {mod}:")
        print(f"  Remainders: {remainders}")
        
        if len(set(remainders)) < len(remainders) / 2:
            print(f"  ⚠️  Possible pattern: Many winners have same remainder!")
    
    # Check position + driver number correlation
    print(f"\n{'='*80}")
    print("POSITION + DRIVER NUMBER CORRELATION")
    print("="*80)
    
    correlations = []
    for i in range(1, 21):
        test_file = test_cases_dir / f"test_{i:03d}.json"
        expected_file = expected_dir / f"test_{i:03d}.json"
        
        if not test_file.exists() or not expected_file.exists():
            continue
        
        test_data = json.loads(test_file.read_text())
        expected = json.loads(expected_file.read_text())
        
        winner = expected['finishing_positions'][0]
        driver_num = int(winner.replace('D', ''))
        
        for pos_key, strat in test_data['strategies'].items():
            if strat['driver_id'] == winner:
                start_pos = int(pos_key.replace('pos', ''))
                
                # Try different formulas
                formula1 = (start_pos + driver_num) % 20
                formula2 = (start_pos * driver_num) % 20
                formula3 = driver_num % start_pos
                
                correlations.append({
                    'test': i,
                    'start': start_pos,
                    'driver': driver_num,
                    'f1': formula1,
                    'f2': formula2,
                    'f3': formula3
                })
    
    print("\nChecking if (start_pos + driver_num) predicts anything...")
    f1_values = [c['f1'] for c in correlations]
    print(f"  (start + driver) % 20 = {f1_values}")
    
    print("\nChecking if (driver_num % start_pos) predicts anything...")
    f3_values = [c['f3'] for c in correlations]
    print(f"  driver % start = {f3_values}")
    
    print(f"\n{'='*80}")
    print("HYPOTHESIS")
    print("="*80)
    
    # Check if lower driver numbers win more
    avg_winner_num = statistics.mean(patterns['driver_number_patterns'])
    print(f"\nAverage winner driver number: {avg_winner_num:.1f}")
    
    if avg_winner_num < 10:
        print(f"💡 Lower-numbered drivers tend to win")
    elif avg_winner_num > 15:
        print(f"💡 Higher-numbered drivers tend to win")
    else:
        print(f"💡 No clear driver number bias")
    
    print(f"\n{'='*80}")
    print("CONCLUSION")
    print("="*80)
    print(f"\nThe pattern might be:")
    print(f"1. Tire strategy matters (we already know this)")
    print(f"2. Driver number might have hidden influence")
    print(f"3. Starting position + driver interaction")
    print(f"\nNext step: Build a ML model to learn the actual rule from data!")

if __name__ == "__main__":
    analyze_all_tests()
