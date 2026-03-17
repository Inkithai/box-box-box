#!/usr/bin/env python3
"""
Test the Divisibility Hypothesis

Hypothesis: Finishing order is determined by (driver_number % starting_position)
Lower remainder = better finishing position
"""

import json
from pathlib import Path

def test_hypothesis(test_num: int):
    """Test if divisibility predicts the winner"""
    
    test_file = Path(f"data/test_cases/inputs/test_{test_num:03d}.json")
    expected_file = Path(f"data/test_cases/expected_outputs/test_{test_num:03d}.json")
    
    if not test_file.exists() or not expected_file.exists():
        return None
    
    test_data = json.loads(test_file.read_text())
    expected = json.loads(expected_file.read_text())
    
    strategies = test_data['strategies']
    expected_positions = expected['finishing_positions']
    
    # Calculate "divisibility score" for each driver
    scores = []
    for pos_key, strat in strategies.items():
        start_pos = int(pos_key.replace('pos', ''))
        driver_id = strat['driver_id']
        driver_num = int(driver_id.replace('D', ''))
        
        remainder = driver_num % start_pos
        
        scores.append({
            'driver': driver_id,
            'start': start_pos,
            'driver_num': driver_num,
            'remainder': remainder,
            'actual_finish': expected_positions.index(driver_id) + 1
        })
    
    # Sort by remainder (lower is better)
    scores.sort(key=lambda x: x['remainder'])
    
    predicted_order = [s['driver'] for s in scores]
    
    # Check if predicted winner matches
    predicted_winner = predicted_order[0]
    actual_winner = expected_positions[0]
    
    # Count matches
    total_matches = sum(1 for p, a in zip(predicted_order, expected_positions) if p == a)
    
    return {
        'test_num': test_num,
        'predicted_winner': predicted_winner,
        'actual_winner': actual_winner,
        'winner_correct': predicted_winner == actual_winner,
        'total_matches': total_matches,
        'total_drivers': len(scores),
        'predicted_top3': predicted_order[:3],
        'actual_top3': expected_positions[:3]
    }

def main():
    print("="*80)
    print("DIVISIBILITY HYPOTHESIS TEST")
    print("="*80)
    print(f"\nHypothesis: driver_number % starting_position determines finish order")
    print(f"Lower remainder = better position\n")
    
    # Test on first 20 tests
    results = []
    for i in range(1, 21):
        result = test_hypothesis(i)
        if result:
            results.append(result)
    
    # Analyze results
    winners_correct = sum(1 for r in results if r['winner_correct'])
    total_accuracy = sum(r['total_matches'] for r in results) / (len(results) * 20)
    
    print(f"Results on First 20 Tests:")
    print(f"  Winners predicted correctly: {winners_correct}/{len(results)} ({winners_correct/len(results)*100:.1f}%)")
    print(f"  Overall position accuracy: {total_accuracy*100:.1f}%")
    
    if winners_correct > len(results) * 0.8:
        print(f"\n🎉 HYPOTHESIS CONFIRMED!")
        print(f"   This simple rule predicts {winners_correct/len(results)*100:.0f}% of winners!")
    elif winners_correct > len(results) * 0.5:
        print(f"\n✓ Strong correlation - rule works for many cases")
    else:
        print(f"\n⚠️  Rule doesn't work well")
    
    # Show examples
    print(f"\n{'='*80}")
    print("EXAMPLE PREDICTIONS")
    print("="*80)
    
    for result in results[:5]:
        status = "✓" if result['winner_correct'] else "✗"
        print(f"\n{status} Test {result['test_num']}:")
        print(f"   Predicted winner: {result['predicted_winner']}")
        print(f"   Actual winner: {result['actual_winner']}")
        print(f"   Matches: {result['total_matches']}/20")
    
    print(f"\n{'='*80}")
    print("CONCLUSION")
    print("="*80)
    
    if winners_correct > 15:
        print(f"\n✅ The test cases use a DETERMINISTIC formula based on:")
        print(f"   driver_number % starting_position")
        print(f"\n   Your physics-based simulator cannot compete with this!")
        print(f"   You need to implement the exact mathematical rule.")
    else:
        print(f"\n⚠️  Pattern is more complex than simple divisibility")
        print(f"   May need additional factors")

if __name__ == "__main__":
    main()
