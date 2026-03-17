#!/usr/bin/env python3
"""
Test ML Predictor on competition test cases

Compares ML predictions against expected outcomes
"""

import json
from pathlib import Path
import sys
sys.path.append('solution2')

from ml_predictor import MLPredictor

def test_ml_predictor():
    """Test trained model on first 20 test cases."""
    
    print("="*80)
    print("ML PREDICTOR VALIDATION")
    print("="*80)
    
    # Load trained model
    predictor = MLPredictor()
    
    try:
        predictor.load_model("solution2/ml_predictor.pkl")
        print("\n✓ Loaded pre-trained model")
    except FileNotFoundError:
        print("\n⚠️  No trained model found!")
        print(f"First run: python solution2\\ml_predictor.py")
        return
    
    # Test on competition test cases
    test_cases_dir = Path("data/test_cases/inputs")
    expected_outputs_dir = Path("data/test_cases/expected_outputs")
    
    results = []
    
    for i in range(1, 21):
        test_file = test_cases_dir / f"test_{i:03d}.json"
        expected_file = expected_outputs_dir / f"test_{i:03d}.json"
        
        if not test_file.exists() or not expected_file.exists():
            continue
        
        test_data = json.loads(test_file.read_text())
        expected = json.loads(expected_file.read_text())
        
        # Get ML prediction
        predicted_order = predictor.predict(test_data)
        expected_order = expected['finishing_positions']
        
        # Calculate metrics
        winner_correct = predicted_order[0] == expected_order[0]
        podium_matches = sum(1 for p, e in zip(predicted_order[:3], expected_order[:3]) if p == e)
        total_matches = sum(1 for p, e in zip(predicted_order, expected_order) if p == e)
        
        results.append({
            'test_num': i,
            'winner_correct': winner_correct,
            'podium_matches': podium_matches,
            'total_matches': total_matches,
            'predicted_winner': predicted_order[0],
            'expected_winner': expected_order[0]
        })
    
    # Aggregate results
    winners_correct = sum(1 for r in results if r['winner_correct'])
    avg_podium = sum(r['podium_matches'] for r in results) / len(results)
    avg_total = sum(r['total_matches'] for r in results) / len(results)
    
    print(f"\n{'='*80}")
    print(f"RESULTS ON FIRST 20 TEST CASES")
    print("="*80)
    
    print(f"\nWinner Prediction:")
    print(f"  Correct: {winners_correct}/{len(results)} ({winners_correct/len(results)*100:.1f}%)")
    
    print(f"\nPodium Accuracy:")
    print(f"  Average matches: {avg_podium:.1f}/3 ({avg_podium/3*100:.1f}%)")
    
    print(f"\nOverall Position Accuracy:")
    print(f"  Average matches: {avg_total:.1f}/20 ({avg_total/20*100:.1f}%)")
    
    # Show examples
    print(f"\n{'='*80}")
    print("DETAILED RESULTS")
    print("="*80)
    
    for result in results[:10]:
        status = "✓" if result['winner_correct'] else "✗"
        print(f"\n{status} Test {result['test_num']}:")
        print(f"   Winner: Predicted {result['predicted_winner']}, Expected {result['expected_winner']}")
        print(f"   Podium: {result['podium_matches']}/3 correct")
        print(f"   Total: {result['total_matches']}/20 correct")
    
    # Performance assessment
    print(f"\n{'='*80}")
    print("PERFORMANCE ASSESSMENT")
    print("="*80)
    
    if avg_total >= 16:
        print(f"\n🎉 EXCELLENT! ML model achieves {avg_total/20*100:.1f}% accuracy")
        print(f"   Ready for competition submission!")
    elif avg_total >= 12:
        print(f"\n✓ GOOD! ML model at {avg_total/20*100:.1f}% accuracy")
        print(f"   Consider hybrid approach for final improvements")
    elif avg_total >= 8:
        print(f"\n⚠️  MODERATE - {avg_total/20*100:.1f}% accuracy")
        print(f"   May need more training data or feature engineering")
    else:
        print(f"\n❌ LOW ACCURACY - {avg_total/20*100:.1f}%")
        print(f"   Model needs significant improvement")
    
    print()


if __name__ == "__main__":
    test_ml_predictor()
