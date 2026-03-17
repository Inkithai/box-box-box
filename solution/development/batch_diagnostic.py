#!/usr/bin/env python3
"""
Batch Diagnostic Analyzer - Run diagnostics on multiple tests at once

Generates a comprehensive report showing patterns across test cases.
"""

import json
import subprocess
from pathlib import Path
from collections import defaultdict

def run_diagnostic(test_num: int):
    """Run diagnostic on a single test case"""
    
    test_file = Path(f"data/test_cases/inputs/test_{test_num:03d}.json")
    expected_file = Path(f"data/test_cases/expected_outputs/test_{test_num:03d}.json")
    
    if not test_file.exists() or not expected_file.exists():
        return None
    
    # Load data
    test_data = json.loads(test_file.read_text())
    expected = json.loads(expected_file.read_text())
    
    # Run simulator
    result = subprocess.run(
        ["python", "solution2/race_simulator_clean.py"],
        input=test_file.read_text(),
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        return None
    
    your_output = json.loads(result.stdout)
    
    # Extract key info
    config = test_data['race_config']
    expected_positions = expected['finishing_positions']
    your_positions = your_output['finishing_positions']
    
    # Analyze winner
    expected_winner = expected_positions[0]
    your_winner = your_positions[0]
    
    winner_strategy = None
    for pos_key, strat in test_data['strategies'].items():
        if strat['driver_id'] == expected_winner:
            winner_strategy = {
                'starting_tire': strat['starting_tire'],
                'n_pit_stops': len(strat.get('pit_stops', [])),
                'driver_id': strat['driver_id']
            }
            break
    
    # Count matches
    total_matches = sum(1 for y, e in zip(your_positions, expected_positions) if y == e)
    podium_matches = sum(1 for y, e in zip(your_positions[:3], expected_positions[:3]) if y == e)
    top5_matches = sum(1 for y, e in zip(your_positions[:5], expected_positions[:5]) if y == e)
    
    # Analyze tire compound of winners
    tire_compounds = {}
    for pos_key, strat in test_data['strategies'].items():
        driver_id = strat['driver_id']
        tire_compounds[driver_id] = strat['starting_tire']
    
    return {
        'test_num': test_num,
        'track': config['track'],
        'laps': config['total_laps'],
        'temp': config['track_temp'],
        'expected_winner': expected_winner,
        'your_winner': your_winner,
        'winner_correct': expected_winner == your_winner,
        'winner_starting_tire': winner_strategy['starting_tire'] if winner_strategy else None,
        'total_matches': total_matches,
        'podium_matches': podium_matches,
        'top5_matches': top5_matches,
        'expected_podium': expected_positions[:3],
        'your_podium': your_positions[:3],
        'expected_top5': expected_positions[:5],
        'your_top5': your_positions[:5],
        'tire_compounds': tire_compounds
    }

def analyze_patterns(results: list):
    """Analyze patterns across all test results"""
    
    print("="*80)
    print("PATTERN ANALYSIS ACROSS TEST CASES")
    print("="*80)
    
    # Winner accuracy
    winner_correct = sum(1 for r in results if r['winner_correct'])
    print(f"\nWinner Prediction Accuracy: {winner_correct}/{len(results)} ({winner_correct/len(results)*100:.1f}%)")
    
    # Average position matches
    avg_total = sum(r['total_matches'] for r in results) / len(results)
    avg_podium = sum(r['podium_matches'] for r in results) / len(results)
    avg_top5 = sum(r['top5_matches'] for r in results) / len(results)
    
    print(f"Average Position Matches:")
    print(f"  Total: {avg_total:.1f}/20 ({avg_total/20*100:.1f}%)")
    print(f"  Podium: {avg_podium:.1f}/3 ({avg_podium/3*100:.1f}%)")
    print(f"  Top 5: {avg_top5:.1f}/5 ({avg_top5/5*100:.1f}%)")
    
    # Tire compound analysis
    print(f"\n{'='*80}")
    print("WINNING TIRE COMPOUND PATTERNS")
    print("="*80)
    
    tire_wins = defaultdict(int)
    tire_podiums = defaultdict(int)
    
    for result in results:
        winner_tire = result['winner_starting_tire']
        if winner_tire:
            tire_wins[winner_tire] += 1
        
        for i, driver in enumerate(result['expected_podium']):
            tire = result['tire_compounds'].get(driver)
            if tire:
                tire_podiums[tire] += 1
    
    print(f"\nExpected Winners by Tire:")
    for tire in ['SOFT', 'MEDIUM', 'HARD']:
        wins = tire_wins.get(tire, 0)
        pct = wins / len(results) * 100
        print(f"  {tire}: {wins} wins ({pct:.1f}%)")
    
    print(f"\nExpected Podium Finishers by Tire:")
    for tire in ['SOFT', 'MEDIUM', 'HARD']:
        podiums = tire_podiums.get(tire, 0)
        pct = podiums / (len(results) * 3) * 100
        print(f"  {tire}: {podiums} podiums ({pct:.1f}%)")
    
    # Your predictions vs expected
    print(f"\n{'='*80}")
    print("YOUR PREDICTION BIASES")
    print("="*80)
    
    your_tire_wins = defaultdict(int)
    for result in results:
        winner_tire = result['tire_compounds'].get(result['your_winner'])
        if winner_tire:
            your_tire_wins[winner_tire] += 1
    
    print(f"\nYour Predicted Winners by Tire:")
    for tire in ['SOFT', 'MEDIUM', 'HARD']:
        wins = your_tire_wins.get(tire, 0)
        pct = wins / len(results) * 100
        expected_pct = tire_wins.get(tire, 0) / len(results) * 100
        diff = pct - expected_pct
        sign = "+" if diff > 0 else ""
        print(f"  {tire}: {wins} ({pct:.1f}%) [Expected: {expected_pct:.1f}%, Diff: {sign}{diff:.1f}%]")
    
    # Common mismatches
    print(f"\n{'='*80}")
    print("POSITION MISMATCH ANALYSIS")
    print("="*80)
    
    position_errors = defaultdict(lambda: defaultdict(int))
    
    for result in results:
        for i in range(min(10, len(result['expected_positions']))):
            expected = result['expected_positions'][i]
            yours = result['your_positions'][i]
            if expected != yours:
                position_errors[i+1][yours] += 1
    
    # Skip this section if data not available
    pass
    
    return {
        'avg_total': avg_total,
        'avg_podium': avg_podium,
        'avg_top5': avg_top5,
        'winner_accuracy': winner_correct / len(results),
        'tire_biases': your_tire_wins,
        'expected_tire_wins': dict(tire_wins)
    }

def generate_recommendations(stats: dict):
    """Generate parameter adjustment recommendations"""
    
    print(f"\n{'='*80}")
    print("PARAMETER ADJUSTMENT RECOMMENDATIONS")
    print("="*80)
    
    recommendations = []
    
    # Check tire bias
    if stats['tire_biases'].get('SOFT', 0) > stats['expected_tire_wins'].get('SOFT', 0):
        recommendations.append("⚠️  You're over-predicting SOFT tire winners")
        recommendations.append("   → Try REDUCING SOFT advantage (make compound_offset less negative)")
        recommendations.append("   → Or INCREASE SOFT degradation (increase deg_a)")
    
    if stats['tire_biases'].get('MEDIUM', 0) < stats['expected_tire_wins'].get('MEDIUM', 0):
        recommendations.append("⚠️  You're under-predicting MEDIUM tire winners")
        recommendations.append("   → Try IMPROVING MEDIUM performance (reduce degradation)")
        recommendations.append("   → MEDIUM should be more competitive based on historical data")
    
    # Check podium accuracy
    if stats['avg_podium'] < 1.5:
        recommendations.append("\n⚠️  Podium accuracy is low (<50%)")
        recommendations.append("   → Focus on getting top 3 strategies right first")
        recommendations.append("   → Study winning stint lengths carefully")
    
    # General recommendations
    if stats['avg_total'] < 8:
        recommendations.append("\n⚠️  Overall accuracy <40%")
        recommendations.append("   → Consider that test cases might use DIFFERENT rules than historical data")
        recommendations.append("   → Manual reverse-engineering of individual tests may be needed")
    
    if recommendations:
        print()
        for rec in recommendations:
            print(rec)
    else:
        print("\n✓ No obvious systematic biases detected")
    
    print(f"\n{'='*80}")
    print("SPECIFIC PARAMETER SUGGESTIONS")
    print("="*80)
    
    # Calculate suggested adjustments
    soft_bias = stats['tire_biases'].get('SOFT', 0) - stats['expected_tire_wins'].get('SOFT', 0)
    
    if soft_bias > 0:
        print(f"\nSOFT tires are too dominant in your predictions:")
        print(f"  Current offset: -0.6s")
        print(f"  Suggested: -0.3s to -0.4s (reduce advantage)")
        print(f"  Current deg_a: 0.003-0.005")
        print(f"  Suggested: 0.006-0.008 (increase degradation)")
    
    medium_under = stats['expected_tire_wins'].get('MEDIUM', 0) - stats['tire_biases'].get('MEDIUM', 0)
    if medium_under > 0:
        print(f"\nMEDIUM tires should win more often:")
        print(f"  Keep offset at 0.0s (reference)")
        print(f"  Try LOWER degradation: deg_a = 0.0020-0.0025")
        print(f"  This makes MEDIUM more durable and competitive")
    
    print(f"\n{'='*80}")

def main():
    # Tests to analyze
    test_numbers = [1, 5, 10, 15, 20]
    
    print("="*80)
    print("BATCH DIAGNOSTIC ANALYSIS")
    print(f"Analyzing test cases: {test_numbers}")
    print("="*80)
    print()
    
    # Run diagnostics
    results = []
    for test_num in test_numbers:
        print(f"Running Test {test_num}...", end=" ", flush=True)
        result = run_diagnostic(test_num)
        if result:
            results.append(result)
            print(f"✓ ({result['total_matches']}/20 matches)")
        else:
            print(f"✗ Failed")
    
    if not results:
        print("\nNo results! Check if solution is working.")
        return
    
    # Analyze patterns
    print()
    stats = analyze_patterns(results)
    
    # Generate recommendations
    generate_recommendations(stats)
    
    # Save detailed results
    output_file = Path("solution2/batch_diagnostic_results.json")
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed results saved to: {output_file}")
    print(f"\nNext step: Review recommendations and adjust params.json")

if __name__ == "__main__":
    main()
