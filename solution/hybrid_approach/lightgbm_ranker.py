#!/usr/bin/env python3
"""
LightGBM Ranker - Optimized for F1 Race Prediction

Uses pairwise ranking objective (LambdaRank) instead of regression.
This matches the true nature of the problem: predicting driver ORDER, not positions.
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    print("⚠️  LightGBM not installed. Install with: pip install lightgbm")
    LIGHTGBM_AVAILABLE = False


class F1RankerPredictor:
    """LightGBM LambdaRank predictor for F1 race outcomes."""
    
    def __init__(self):
        if not LIGHTGBM_AVAILABLE:
            raise ImportError("LightGBM is required for this predictor")
        
        self.model = lgb.LGBMRanker(
            objective="lambdarank",
            metric="ndcg",
            n_estimators=300,
            learning_rate=0.05,
            max_depth=8,
            num_leaves=50,
            min_child_samples=20,
            random_state=42,
            n_jobs=-1
        )
        self.is_trained = False
        self.feature_names = []
        
    def extract_features(self, test_data: Dict) -> Tuple[np.ndarray, List[Dict]]:
        """Extract features for each driver in a race."""
        
        config = test_data['race_config']
        strategies = test_data['strategies']
        
        features_list = []
        driver_info = []
        
        for pos_key, strat in strategies.items():
            start_pos = int(pos_key.replace('pos', ''))
            driver_id = strat['driver_id']
            driver_num = int(driver_id.replace('D', ''))
            
            # Core features (same as before)
            features = {
                'start_pos': start_pos,
                'driver_num': driver_num,
                'starting_tire_soft': 1 if strat['starting_tire'] == 'SOFT' else 0,
                'starting_tire_medium': 1 if strat['starting_tire'] == 'MEDIUM' else 0,
                'starting_tire_hard': 1 if strat['starting_tire'] == 'HARD' else 0,
                'n_pit_stops': len(strat.get('pit_stops', [])),
                'total_laps': config['total_laps'],
                'base_lap_time': config['base_lap_time'],
                'pit_lane_time': config['pit_lane_time'],
                'track_temp': config['track_temp'],
                'driver_per_start': driver_num / start_pos if start_pos > 0 else 0,
                'driver_mod_start': driver_num % start_pos if start_pos > 0 else 0,
                'laps_per_stop': config['total_laps'] / (len(strat.get('pit_stops', [])) + 1),
            }
            
            # Stint features
            pit_stops = strat.get('pit_stops', [])
            if pit_stops:
                features['first_stint_length'] = pit_stops[0]['lap']
                features['last_stint_length'] = config['total_laps'] - pit_stops[-1]['lap']
                
                stint_lengths = []
                last_lap = 0
                tire_changes = []
                for stop in pit_stops:
                    stint_lengths.append(stop['lap'] - last_lap)
                    tire_changes.append(stop['from_tire'] + '_' + stop['to_tire'])
                    last_lap = stop['lap']
                stint_lengths.append(config['total_laps'] - last_lap)
                
                features['avg_stint_length'] = np.mean(stint_lengths)
                features['stint_variance'] = np.std(stint_lengths)
                features['stint_consistency'] = np.std(stint_lengths) / np.mean(stint_lengths) if np.mean(stint_lengths) > 0 else 0
                
                # Tire change patterns
                features['soft_to_medium'] = 1 if 'SOFT_MEDIUM' in tire_changes else 0
                features['soft_to_hard'] = 1 if 'SOFT_HARD' in tire_changes else 0
                features['medium_to_hard'] = 1 if 'MEDIUM_HARD' in tire_changes else 0
                features['hard_to_medium'] = 1 if 'HARD_MEDIUM' in tire_changes else 0
                features['medium_to_soft'] = 1 if 'MEDIUM_SOFT' in tire_changes else 0
                features['hard_to_soft'] = 1 if 'HARD_SOFT' in tire_changes else 0
                
                # Pit stop timing features
                features['early_pit'] = 1 if pit_stops[0]['lap'] < config['total_laps'] * 0.3 else 0
                features['late_pit'] = 1 if pit_stops[-1]['lap'] > config['total_laps'] * 0.7 else 0
                features['pit_window_center'] = np.mean([stop['lap'] for stop in pit_stops]) / config['total_laps']
            else:
                features['first_stint_length'] = config['total_laps']
                features['last_stint_length'] = config['total_laps']
                features['avg_stint_length'] = config['total_laps']
                features['stint_variance'] = 0
                features['stint_consistency'] = 0
                features['soft_to_medium'] = 0
                features['soft_to_hard'] = 0
                features['medium_to_hard'] = 0
                features['hard_to_medium'] = 0
                features['medium_to_soft'] = 0
                features['hard_to_soft'] = 0
                features['early_pit'] = 0
                features['late_pit'] = 0
                features['pit_window_center'] = 0.5
            
            features_list.append(features)
            driver_info.append({
                'driver_id': driver_id,
                'start_pos': start_pos
            })
        
        if not self.feature_names:
            self.feature_names = list(features_list[0].keys())
        
        feature_matrix = np.array([[f[name] for name in self.feature_names] 
                                   for f in features_list])
        
        return feature_matrix, driver_info
    
    def train_on_historical(self, n_races: int = 30000):
        """Train ranking model on historical data."""
        
        print("="*80)
        print("TRAINING LIGHTRANK MODEL ON HISTORICAL DATA")
        print("="*80)
        
        historical_dir = Path("data/historical_races")
        race_files = sorted(historical_dir.glob("races_*.json"))
        
        X_train = []
        y_train = []
        groups = []
        
        print(f"\nLoading {n_races} historical races...")
        
        races_loaded = 0
        for file in race_files:
            if races_loaded >= n_races:
                break
            
            with open(file, 'r') as f:
                races = json.load(f)
            
            for race in races:
                if races_loaded >= n_races:
                    break
                
                try:
                    strategies = race['strategies']
                    results = race['finishing_positions']
                    
                    X_race, driver_info = self.extract_features(race)
                    
                    # Create target: finishing position (lower is better)
                    for i, info in enumerate(driver_info):
                        driver_id = info['driver_id']
                        finish_pos = results.index(driver_id) + 1
                        
                        # INVERT: Lower position number (1st) → Higher value for ranking
                        inverted_score = 21 - finish_pos  # Position 1 → Score 20, Position 20 → Score 1
                        
                        X_train.append(X_race[i])
                        y_train.append(inverted_score)
                    
                    groups.append(len(driver_info))  # 20 drivers per race
                    races_loaded += 1
                    
                    if races_loaded % 1000 == 0:
                        print(f"  Loaded {races_loaded} races...")
                        
                except Exception as e:
                    continue
        
        print(f"\nTotal samples: {len(X_train)}")
        print(f"Total groups (races): {len(groups)}")
        
        X_train = np.array(X_train)
        y_train = np.array(y_train)
        groups = np.array(groups)
        
        # Train ranking model
        print("\nTraining LightGBM Ranker (LambdaRank)...")
        print(f"  Features: {len(self.feature_names)}")
        print(f"  Samples: {len(y_train)}")
        print(f"  Groups: {len(groups)}")
        
        self.model.fit(
            X_train, 
            y_train, 
            group=groups,
            eval_set=[(X_train, y_train)],
            eval_group=[groups],
            eval_metric='ndcg'
        )
        
        self.is_trained = True
        
        # Feature importance
        print(f"\nTop 10 Most Important Features:")
        importances = self.model.feature_importances_
        indices = np.argsort(importances)[::-1][:10]
        
        for idx in indices:
            print(f"  {self.feature_names[idx]:<30} {importances[idx]:.4f}")
        
        print(f"\n✓ LightGBM Ranker trained successfully!")
        print(f"   Model ready for ranking predictions!")
        
        return len(y_train)
    
    def predict(self, test_data: Dict) -> List[str]:
        """Predict finishing order using ranking scores."""
        
        if not self.is_trained:
            raise ValueError("Model not trained yet!")
        
        X, driver_info = self.extract_features(test_data)
        
        # Get ranking scores (higher score = better position)
        scores = self.model.predict(X)
        
        # Sort drivers by score (descending - higher is better)
        driver_scores = []
        for i, score in enumerate(scores):
            driver_scores.append({
                'driver_id': driver_info[i]['driver_id'],
                'score': score
            })
        
        # Sort by score descending
        driver_scores.sort(key=lambda x: -x['score'])
        
        return [d['driver_id'] for d in driver_scores]
    
    def predict_with_scores(self, test_data: Dict) -> List[tuple]:
        """
        Predict finishing order WITH raw ranking scores.
        
        Returns:
            List of (driver_id, score) tuples
            Higher score = better rank
        """
        
        if not self.is_trained:
            raise ValueError("Model not trained yet!")
        
        X, driver_info = self.extract_features(test_data)
        
        # Get raw ranking scores (LambdaRank output)
        raw_scores = self.model.predict(X)
        
        # Pair drivers with their scores
        driver_scores = []
        for i, score in enumerate(raw_scores):
            driver_scores.append((
                driver_info[i]['driver_id'],
                float(score)  # Convert numpy to Python float
            ))
        
        # Sort descending (higher score = better position)
        driver_scores.sort(key=lambda x: -x[1])
        
        return driver_scores
    
    def get_score_map(self, test_data: Dict) -> Dict[str, float]:
        """
        Get score mapping for all drivers.
        
        Returns:
            Dict mapping driver_id → ranking score
        """
        preds = self.predict_with_scores(test_data)
        return {driver: score for driver, score in preds}
    
    def save_model(self, filepath: str):
        """Save trained model."""
        model_data = {
            'model': self.model,
            'feature_names': self.feature_names,
            'is_trained': self.is_trained
        }
        
        import pickle
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"✓ Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load trained model."""
        import pickle
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.feature_names = model_data['feature_names']
        self.is_trained = model_data['is_trained']


def main():
    """Train the ranking model."""
    
    if not LIGHTGBM_AVAILABLE:
        print("\n❌ LightGBM is not installed.")
        print("Install it with: pip install lightgbm")
        print("\nAlternatively, the Gradient Boosting model in ml_predictor.py works well too!")
        return
    
    ranker = F1RankerPredictor()
    
    # Train on historical data
    n_samples = ranker.train_on_historical(n_races=30000)
    
    # Save model
    ranker.save_model("solution2/lightgbm_ranker.pkl")
    
    print(f"\n{'='*80}")
    print("TRAINING COMPLETE")
    print("="*80)
    print(f"\nTrained on {n_samples} driver-race samples")
    print(f"Ranking model ready for predictions!")
    print(f"\nNext: python solution2/test_lightgbm_ranker.py")


if __name__ == "__main__":
    main()
