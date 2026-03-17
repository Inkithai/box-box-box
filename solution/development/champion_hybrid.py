#!/usr/bin/env python3
"""
CHAMPION HYBRID - Competition-Winning Strategy

Regression base (full order) + Ranking override (top 3 only)
Target: 90%+ winner, 85%+ podium, 70%+ overall accuracy
"""

import json
from pathlib import Path
import sys

# Add solution directory to path for model imports
solution_dir = Path(__file__).parent
sys.path.insert(0, str(solution_dir))

try:
    from lightgbm_ranker import F1RankerPredictor
    from enhanced_gb_predictor import EnhancedGBPredictor
except ImportError as e:
    print(f"⚠️  Import error: {e}", file=sys.stderr)
    sys.exit(1)


class ChampionHybrid:
    """Production hybrid: Regression base + Ranking top-3 override."""
    
    def __init__(self):
        self.rank_predictor = F1RankerPredictor()
        self.reg_predictor = EnhancedGBPredictor()
        self.models_loaded = False
        
    def load_models(self):
        """Load both trained models."""
        try:
            model_dir = Path(__file__).parent
            self.rank_predictor.load_model(str(model_dir / "lightgbm_ranker.pkl"))
            self.reg_predictor.load_model(str(model_dir / "enhanced_gb_predictor.pkl"))
            self.models_loaded = True
        except FileNotFoundError as e:
            print(f"❌ Model file not found: {e}", file=sys.stderr)
            self.models_loaded = False
    
    def predict(self, test_data: dict) -> list:
        """
        Smart hybrid prediction:
        
        1. Get regression predictions (full order baseline)
        2. Get ranking predictions (top-3 specialist)
        3. Override top 3 with ranking predictions
        4. Keep positions 4-20 from regression
        """
        
        if not self.models_loaded:
            print("⚠️  Models not loaded! Using regression only...")
            return self.reg_predictor.predict(test_data)
        
        # Get both predictions
        reg_order = self.reg_predictor.predict(test_data)  # Full order
        rank_order = self.rank_predictor.predict(test_data)  # Top-3 specialist
        
        # Take top 3 from ranking model (its strength!)
        top3_from_rank = rank_order[:3]
        
        # Filter out these drivers from regression order
        remaining_from_reg = [d for d in reg_order if d not in top3_from_rank]
        
        # Combine: ranking top 3 + regression rest
        final_order = top3_from_rank + remaining_from_reg
        
        return final_order


def test_champion():
    """Test champion hybrid on all available test cases."""
    
    print("="*80)
    print("CHAMPION HYBRID TEST (Regression Base + Ranking Top-3)")
    print("="*80)
    
    hybrid = ChampionHybrid()
    hybrid.load_models()
    
    test_cases_dir = Path("data/test_cases/inputs")
    expected_outputs_dir = Path("data/test_cases/expected_outputs")
    
    results = []
    
    # Test on first 20 cases
    for i in range(1, 21):
        test_file = test_cases_dir / f"test_{i:03d}.json"
        expected_file = expected_outputs_dir / f"test_{i:03d}.json"
        
        if not test_file.exists() or not expected_file.exists():
            continue
        
        test_data = json.loads(test_file.read_text())
        expected = json.loads(expected_file.read_text())
        
        predicted = hybrid.predict(test_data)
        expected_order = expected['finishing_positions']
        
        winner_correct = predicted[0] == expected_order[0]
        podium_matches = sum(1 for p, e in zip(predicted[:3], expected_order[:3]) if p == e)
        total_matches = sum(1 for p, e in zip(predicted, expected_order) if p == e)
        
        results.append({
            'test_num': i,
            'winner_correct': winner_correct,
            'podium_matches': podium_matches,
            'total_matches': total_matches
        })
    
    # Aggregate results
    winners_correct = sum(1 for r in results if r['winner_correct'])
    avg_podium = sum(r['podium_matches'] for r in results) / len(results)
    avg_total = sum(r['total_matches'] for r in results) / len(results)
    
    print(f"\n{'='*80}")
    print(f"CHAMPION HYBRID RESULTS (First 20 Tests)")
    print("="*80)
    
    print(f"\n🏆 Winner Accuracy: {winners_correct}/20 ({winners_correct/20*100:.1f}%)")
    print(f"🥈 Podium Accuracy: {avg_podium:.1f}/3 ({avg_podium/3*100:.1f}%)")
    print(f"📊 Overall Position: {avg_total:.1f}/20 ({avg_total*5:.1f}%)")
    
    # Compare baselines
    print(f"\n{'='*80}")
    print("PERFORMANCE COMPARISON")
    print("="*80)
    print(f"Physics-Only:          ~25%")
    print(f"GradientBoosting:      64.5%")
    print(f"LightGBM Ranker:       45.0% (but 95% winner)")
    print(f"**CHAMPION HYBRID:     {avg_total*5:.1f}%**")
    
    # Assessment
    print(f"\n{'='*80}")
    print("COMPETITION READINESS ASSESSMENT")
    print("="*80)
    
    checks = []
    checks.append(("Winner >90%", winners_correct >= 18))
    checks.append(("Podium >85%", avg_podium >= 2.55))
    checks.append(("Overall >70%", avg_total >= 14))
    
    for check_name, passed in checks:
        status = "✅" if passed else "⚠️"
        print(f"{status} {check_name}")
    
    if all(c[1] for c in checks):
        print(f"\n🎉 ALL CHECKS PASSED! READY TO WIN!")
    elif checks[0] and checks[1]:
        print(f"\n✓ Strong contender! Winner & podium excellent.")
    else:
        print(f"\n⚠️  Needs tuning")
    
    # Detailed examples
    print(f"\n{'='*80}")
    print("DETAILED EXAMPLES")
    print("="*80)
    
    for result in results[:10]:
        status = "✓" if result['winner_correct'] else "✗"
        print(f"\n{status} Test {result['test_num']}:")
        print(f"   Winner: {'Correct ✓' if result['winner_correct'] else 'Wrong ✗'}")
        print(f"   Podium: {result['podium_matches']}/3 correct")
        print(f"   Total: {result['total_matches']}/20 correct")


if __name__ == "__main__":
    test_champion()
