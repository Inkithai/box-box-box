#!/usr/bin/env python3
"""
Validate Phase 2 Fix - Test previously failing races

Tests Tests 5, 10, 20 which were at 0/20 before the fix
"""

import subprocess
from pathlib import Path

def test_race(test_num: int):
    """Test a single race and return results"""
    
    test_file = Path(f"data/test_cases/inputs/test_{test_num:03d}.json")
    expected_file = Path(f"data/test_cases/expected_outputs/test_{test_num:03d}.json")
    
    # Run simulator
    result = subprocess.run(
        ["python", "solution2/race_simulator_clean.py"],
        input=test_file.read_text(),
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        return None
    
    import json
    your_output = json.loads(result.stdout)
    expected = json.loads(expected_file.read_text())
    
    your_positions = your_output['finishing_positions']
    expected_positions = expected['finishing_positions']
    
    total_matches = sum(1 for y, e in zip(your_positions, expected_positions) if y == e)
    podium_matches = sum(1 for y, e in zip(your_positions[:3], expected_positions[:3]) if y == e)
    winner_correct = your_positions[0] == expected_positions[0]
    
    return {
        'test_num': test_num,
        'total_matches': total_matches,
        'podium_matches': podium_matches,
        'winner_correct': winner_correct,
        'your_winner': your_positions[0],
        'expected_winner': expected_positions[0]
    }

def main():
    print("="*80)
    print("PHASE 2 VALIDATION - Testing Previously Failing Races")
    print("="*80)
    
    tests_to_check = [5, 10, 20]
    
    print(f"\nBefore fix:")
    print(f"  Test 5:  0/20 (0%)")
    print(f"  Test 10: 0/20 (0%)")
    print(f"  Test 20: 1/20 (5%)")
    print(f"\nApplying HARD tire & multi-stop optimizations...\n")
    
    results = []
    for test_num in tests_to_check:
        print(f"Testing {test_num}...", end=" ", flush=True)
        result = test_race(test_num)
        
        if result:
            results.append(result)
            improvement = result['total_matches']
            status = "✓ IMPROVED" if improvement > (0 if test_num != 20 else 1) else "⚠️ same"
            print(f"{result['total_matches']}/20 ({result['total_matches']/20*100:.0f}%) - {status}")
            
            if result['winner_correct']:
                print(f"   ✓ Winner correct: {result['your_winner']}")
            else:
                print(f"   ✗ Wrong winner: Expected {result['expected_winner']}, got {result['your_winner']}")
            
            if result['podium_matches'] > 0:
                print(f"   ✓ Podium matches: {result['podium_matches']}/3")
        else:
            print(f"✗ FAILED")
    
    print(f"\n{'='*80}")
    print("SUMMARY")
    print("="*80)
    
    if results:
        total_improvement = sum(r['total_matches'] for r in results)
        print(f"\nTotal positions correct: {total_improvement}/{len(tests_to_check)*20}")
        print(f"Average accuracy: {total_improvement/len(tests_to_check)/20*100:.1f}%")
        
        winners_correct = sum(1 for r in results if r['winner_correct'])
        print(f"Winners predicted: {winners_correct}/{len(tests_to_check)}")
        
        if total_improvement > (1 if 20 in tests_to_check else 0):
            print(f"\n✅ PHASE 2 FIX SUCCESSFUL!")
            print(f"   HARD tires now competitive")
            print(f"   Multi-stop strategies working better")
        else:
            print(f"\n⚠️  Limited improvement - may need different approach")
    
    print(f"\n{'='*80}")
    print("NEXT STEPS")
    print("="*80)
    
    if results and all(r['winner_correct'] for r in results):
        print(f"\n🎉 All winners correct! Ready for full batch analysis.")
        print(f"   Run: python solution2\\batch_diagnostic.py")
    elif results and sum(r['total_matches'] for r in results) > len(tests_to_check) * 5:
        print(f"\n✓ Good improvement! Continue fine-tuning.")
        print(f"   Check midfield positions with deep_diagnostic.py")
    else:
        print(f"\n⚠️  Still struggling. Consider:")
        print(f"   - Track-specific parameters")
        print(f"   - Driver-specific offsets")
        print(f"   - Different degradation model")
    
    print()

if __name__ == "__main__":
    main()
