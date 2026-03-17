#!/usr/bin/env python3
"""
Automated Parameter Tuner - Grid Search Approach

Systematically tests parameter combinations to find optimal values.
"""

import json
import subprocess
from pathlib import Path
from itertools import product
import time
from typing import Dict, List, Tuple

class ParameterTuner:
    """Automated parameter tuning using grid search."""
    
    def __init__(self):
        self.test_cases_dir = Path("data/test_cases/inputs")
        self.expected_outputs_dir = Path("data/test_cases/expected_outputs")
        self.params_file = Path("solution2/params.json")
        
        # Parameter ranges to search
        self.param_ranges = {
            'compound_offset': {
                'SOFT': [-0.6, -0.5, -0.4, -0.3],
                'MEDIUM': [0.0],  # Keep as reference
                'HARD': [0.4, 0.5, 0.6, 0.7]
            },
            'deg_a': {
                'SOFT': [0.003, 0.004, 0.005, 0.006],
                'MEDIUM': [0.0015, 0.0022, 0.003, 0.004],
                'HARD': [0.001, 0.0014, 0.002, 0.003]
            },
            'deg_b': {
                'SOFT': [0.012, 0.015, 0.018, 0.022],
                'MEDIUM': [0.008, 0.0105, 0.013, 0.016],
                'HARD': [0.005, 0.0075, 0.01, 0.013]
            }
        }
        
        self.best_score = 0
        self.best_params = None
        self.results_history = []
    
    def load_base_params(self) -> Dict:
        """Load current params.json as base"""
        try:
            with open(self.params_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return self._get_default_params()
    
    def _get_default_params(self) -> Dict:
        """Default parameters if file not found"""
        return {
            "compound_offset": {"SOFT": -0.6, "MEDIUM": 0.0, "HARD": 0.55},
            "warmup_laps": {"SOFT": 2, "MEDIUM": 2, "HARD": 2},
            "deg_a": {"SOFT": 0.004, "MEDIUM": 0.0022, "HARD": 0.0014},
            "deg_b": {"SOFT": 0.018, "MEDIUM": 0.0105, "HARD": 0.0075},
            "temp_ref": 30.0,
            "temp_k": {"SOFT": -0.01, "MEDIUM": -0.006, "HARD": -0.004}
        }
    
    def save_params(self, params: Dict):
        """Save parameters to file"""
        with open(self.params_file, 'w') as f:
            json.dump(params, f, indent=2)
    
    def run_test_batch(self, test_range: Tuple[int, int]) -> float:
        """Run tests and return accuracy"""
        passed = 0
        total = test_range[1] - test_range[0]
        
        solution_cmd = "python solution2/race_simulator_clean.py"
        
        for i in range(test_range[0], test_range[1]):
            test_file = self.test_cases_dir / f"test_{i:03d}.json"
            expected_file = self.expected_outputs_dir / f"test_{i:03d}.json"
            
            if not test_file.exists() or not expected_file.exists():
                continue
            
            try:
                # Run solution
                result = subprocess.run(
                    solution_cmd,
                    shell=True,
                    input=test_file.read_text(),
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode != 0:
                    continue
                
                output = json.loads(result.stdout)
                predicted = output.get("finishing_positions", [])
                
                expected = json.loads(expected_file.read_text())
                expected_positions = expected.get("finishing_positions", [])
                
                if predicted == expected_positions:
                    passed += 1
                    
            except Exception as e:
                continue
        
        return passed / total if total > 0 else 0
    
    def generate_param_combinations(self) -> List[Dict]:
        """Generate all parameter combinations to test"""
        combinations = []
        
        # Get all possible values for each parameter
        soft_offsets = self.param_ranges['compound_offset']['SOFT']
        hard_offsets = self.param_ranges['compound_offset']['HARD']
        
        soft_deg_a = self.param_ranges['deg_a']['SOFT']
        medium_deg_a = self.param_ranges['deg_a']['MEDIUM']
        hard_deg_a = self.param_ranges['deg_a']['HARD']
        
        soft_deg_b = self.param_ranges['deg_b']['SOFT']
        medium_deg_b = self.param_ranges['deg_b']['MEDIUM']
        hard_deg_b = self.param_ranges['deg_b']['HARD']
        
        # Generate combinations
        for combo in product(soft_offsets, hard_offsets, 
                           soft_deg_a, medium_deg_a, hard_deg_a,
                           soft_deg_b, medium_deg_b, hard_deg_b):
            
            params = self._get_default_params()
            params['compound_offset']['SOFT'] = combo[0]
            params['compound_offset']['HARD'] = combo[1]
            params['deg_a']['SOFT'] = combo[2]
            params['deg_a']['MEDIUM'] = combo[3]
            params['deg_a']['HARD'] = combo[4]
            params['deg_b']['SOFT'] = combo[5]
            params['deg_b']['MEDIUM'] = combo[6]
            params['deg_b']['HARD'] = combo[7]
            
            combinations.append(params)
        
        return combinations
    
    def tune(self, test_range: Tuple[int, int] = (1, 11), max_combinations: int = None):
        """Run grid search optimization"""
        
        print("="*80)
        print("AUTOMATED PARAMETER TUNING - GRID SEARCH")
        print("="*80)
        print(f"\nTesting on test cases {test_range[0]} to {test_range[1]-1}")
        print(f"Parameter ranges:")
        for param, compounds in self.param_ranges.items():
            print(f"  {param}:")
            for compound, values in compounds.items():
                if len(values) > 1:
                    print(f"    {compound}: {values}")
        print()
        
        combinations = self.generate_param_combinations()
        
        if max_combinations:
            combinations = combinations[:max_combinations]
        
        print(f"Total combinations to test: {len(combinations)}\n")
        
        start_time = time.time()
        
        for i, params in enumerate(combinations, 1):
            # Save params
            self.save_params(params)
            
            # Test
            score = self.run_test_batch(test_range)
            
            # Track results
            self.results_history.append({
                'iteration': i,
                'params': params,
                'score': score
            })
            
            # Check if best
            if score > self.best_score:
                self.best_score = score
                self.best_params = params.copy()
                print(f"[{i}/{len(combinations)}] 🎯 New best: {score*100:.1f}%")
                print(f"   SOFT offset: {params['compound_offset']['SOFT']:.2f}, HARD offset: {params['compound_offset']['HARD']:.2f}")
                print(f"   SOFT deg_a: {params['deg_a']['SOFT']:.4f}, MEDIUM deg_a: {params['deg_a']['MEDIUM']:.4f}")
            elif i % 10 == 0:
                print(f"[{i}/{len(combinations)}] Current best: {self.best_score*100:.1f}%")
        
        elapsed = time.time() - start_time
        
        print(f"\n{'='*80}")
        print(f"GRID SEARCH COMPLETE")
        print(f"{'='*80}")
        print(f"Time elapsed: {elapsed:.1f}s ({elapsed/60:.1f} minutes)")
        print(f"Best score: {self.best_score*100:.1f}%")
        print(f"Combinations tested: {len(combinations)}")
        
        if self.best_params:
            print(f"\nBEST PARAMETERS FOUND:")
            print(f"  compound_offset:")
            print(f"    SOFT: {self.best_params['compound_offset']['SOFT']:.2f}")
            print(f"    MEDIUM: {self.best_params['compound_offset']['MEDIUM']:.2f}")
            print(f"    HARD: {self.best_params['compound_offset']['HARD']:.2f}")
            print(f"  deg_a:")
            print(f"    SOFT: {self.best_params['deg_a']['SOFT']:.4f}")
            print(f"    MEDIUM: {self.best_params['deg_a']['MEDIUM']:.4f}")
            print(f"    HARD: {self.best_params['deg_a']['HARD']:.4f}")
            print(f"  deg_b:")
            print(f"    SOFT: {self.best_params['deg_b']['SOFT']:.4f}")
            print(f"    MEDIUM: {self.best_params['deg_b']['MEDIUM']:.4f}")
            print(f"    HARD: {self.best_params['deg_b']['HARD']:.4f}")
            
            # Save best params
            self.save_params(self.best_params)
            print(f"\n✓ Best parameters saved to {self.params_file}")
        
        return self.best_params, self.best_score

def main():
    """Main entry point"""
    tuner = ParameterTuner()
    
    # Run grid search on first 10 tests
    best_params, best_score = tuner.tune(
        test_range=(1, 11),  # Tests 1-10
        max_combinations=50  # Limit to 50 combinations for speed
    )
    
    if best_score > 0:
        print(f"\n🎉 Success! Found parameters with {best_score*100:.1f}% accuracy")
        print(f"\nNext steps:")
        print(f"1. Review the best parameters above")
        print(f"2. Run full test suite: python solution2/quick_test.py")
        print(f"3. If satisfied, submit!")
    else:
        print(f"\n⚠️ No improvement found. Try:")
        print(f"1. Expanding parameter ranges")
        print(f"2. Using finer granularity")
        print(f"3. Manual parameter adjustment")

if __name__ == "__main__":
    main()
