#!/usr/bin/env python3
"""
Deep Analysis - Why are Tests 5, 10, 20 impossible to predict?

Let's look at the ACTUAL starting positions vs finishing positions
to understand if there's a pattern we're missing.
"""

import json
from pathlib import Path

def analyze_test_deep(test_num: int):
    """Deep analysis of a single test"""
    
    test_file = Path(f"data/test_cases/inputs/test_{test_num:03d}.json")
    expected_file = Path(f"data/test_cases/expected_outputs/test_{test_num:03d}.json")
    
    test_data = json.loads(test_file.read_text())
    expected = json.loads(expected_file.read_text())
    
    print("="*80)
    print(f"DEEP PATTERN ANALYSIS - TEST {test_num}")
    print("="*80)
    
    config = test_data['race_config']
    strategies = test_data['strategies']
    expected_positions = expected['finishing_positions']
    
    print(f"\nRace: {config['track']} - {config['total_laps']} laps")
    print(f"Track Temp: {config['track_temp']}°C")
    print(f"Base Lap Time: {config['base_lap_time']}s")
    print(f"Pit Lane Time: {config['pit_lane_time']}s")
    
    # Analyze winner
    winner = expected_positions[0]
    print(f"\n{'='*80}")
    print(f"WINNER ANALYSIS: {winner}")
    print("="*80)
    
    for pos_key, strat in strategies.items():
        if strat['driver_id'] == winner:
            print(f"\nStarting Grid Position: {pos_key}")
            print(f"Strategy:")
            print(f"  Starting Tire: {strat['starting_tire']}")
            print(f"  Pit Stops: {len(strat.get('pit_stops', []))}")
            
            if strat.get('pit_stops'):
                for stop in strat['pit_stops']:
                    print(f"    Lap {stop['lap']}: {stop['from_tire']} → {stop['to_tire']}")
            
            # Calculate total stint on each compound
            stint_lengths = {}
            if strat.get('pit_stops'):
                last_lap = 0
                tires_used = [strat['starting_tire']]
                for stop in strat['pit_stops']:
                    stint_length = stop['lap'] - last_lap
                    tire = strat['starting_tire'] if last_lap == 0 else strat['pit_stops'][strat['pit_stops'].index(stop)-1]['to_tire']
                    stint_lengths[tire] = stint_lengths.get(tire, 0) + stint_length
                    last_lap = stop['lap']
                    tires_used.append(stop['to_tire'])
                
                # Final stint
                final_stint = config['total_laps'] - last_lap
                final_tire = strat['pit_stops'][-1]['to_tire']
                stint_lengths[final_tire] = stint_lengths.get(final_tire, 0) + final_stint
                
                print(f"\nTire Usage:")
                for tire, laps in stint_lengths.items():
                    pct = laps / config['total_laps'] * 100
                    print(f"  {tire}: {laps} laps ({pct:.1f}%)")
    
    # Analyze podium finishers
    print(f"\n{'='*80}")
    print("PODIUM FINISHERS - STARTING POSITIONS")
    print("="*80)
    
    for i, driver in enumerate(expected_positions[:3]):
        for pos_key, strat in strategies.items():
            if strat['driver_id'] == driver:
                print(f"\n{i+1}. {driver} (started {pos_key})")
                print(f"   Strategy: {strat['starting_tire']}, {len(strat.get('pit_stops', []))} stops")
                
                # Check if starting position correlates with finishing
                start_pos = int(pos_key.replace('pos', ''))
                finish_pos = i + 1
                position_change = start_pos - finish_pos
                
                if position_change > 0:
                    print(f"   Gained {position_change} positions")
                elif position_change < 0:
                    print(f"   Lost {abs(position_change)} positions")
                else:
                    print(f"   Maintained position")
    
    # Check correlation between starting and finishing
    print(f"\n{'='*80}")
    print("STARTING VS FINISHING CORRELATION")
    print("="*80)
    
    correlations = []
    for pos_key, strat in strategies.items():
        start_pos = int(pos_key.replace('pos', ''))
        driver_id = strat['driver_id']
        
        try:
            finish_pos = expected_positions.index(driver_id) + 1
            correlation = abs(start_pos - finish_pos)
            correlations.append({
                'driver': driver_id,
                'start': start_pos,
                'finish': finish_pos,
                'diff': correlation,
                'tire': strat['starting_tire'],
                'stops': len(strat.get('pit_stops', []))
            })
        except ValueError:
            pass
    
    # Sort by position change
    correlations.sort(key=lambda x: x['diff'])
    
    print(f"\nTop 5 (smallest position change):")
    for corr in correlations[:5]:
        print(f"  {corr['driver']}: Started {corr['start']}, Finished {corr['finish']} (Δ{corr['diff']}) - {corr['tire']}, {corr['stops']} stops")
    
    print(f"\nBottom 5 (largest position change):")
    for corr in correlations[-5:]:
        print(f"  {corr['driver']}: Started {corr['start']}, Finished {corr['finish']} (Δ{corr['diff']}) - {corr['tire']}, {corr['stops']} stops")
    
    # Key insight
    avg_change = sum(c['diff'] for c in correlations) / len(correlations)
    print(f"\nAverage position change: {avg_change:.1f} positions")
    
    if avg_change < 3:
        print(f"\n💡 INSIGHT: Starting position strongly predicts finishing position")
        print(f"   → Track position is CRITICAL")
        print(f"   → Overtaking is difficult on this track")
    elif avg_change < 6:
        print(f"\n💡 INSIGHT: Moderate overtaking")
        print(f"   → Strategy matters but starting position still important")
    else:
        print(f"\n💡 INSIGHT: High overtaking track")
        print(f"   → Strategy dominates starting position")
        print(f"   → Tire performance is likely key factor")

def main():
    print("Which test should we analyze deeply?")
    print("Enter test number (or press Enter for test 5): ")
    
    try:
        user_input = input().strip()
        if user_input:
            test_num = int(user_input)
        else:
            test_num = 5
    except ValueError:
        test_num = 5
    
    analyze_test_deep(test_num)
    
    print(f"\n{'='*80}")
    print(f"KEY QUESTION:")
    print(f"Is your simulator capturing the right balance between:")
    print(f"  1. Starting grid position")
    print(f"  2. Tire strategy")
    print(f"  3. Pit stop timing")
    print(f"  4. Tire degradation")
    print(f"\nIf winners come from unexpected starting positions,")
    print(f"your tire model MUST be extremely precise!")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
