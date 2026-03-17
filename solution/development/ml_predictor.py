#!/usr/bin/env python3
"""
ML-Based F1 Race Outcome Predictor

Uses gradient boosting to learn race outcome patterns from historical data.
Combines driver features, strategy features, and tire performance.
"""

import json
import numpy as np
from pathlib import Path
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
import pickle
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

class MLPredictor:
    """Machine Learning predictor for F1 race outcomes."""
    
    def __init__(self):
        self.model = GradientBoostingRegressor(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            min_samples_split=10,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_names = []
        
    def extract_features(self, test_data: Dict) -> Tuple[np.ndarray, List[Dict]]:
        """Extract features from race data for each driver."""
        
        config = test_data['race_config']
        strategies = test_data['strategies']
        
        features_list = []
        driver_info = []
        
        for pos_key, strat in strategies.items():
            start_pos = int(pos_key.replace('pos', ''))
            driver_id = strat['driver_id']
            driver_num = int(driver_id.replace('D', ''))
            
            # Driver features
            features = {
                'start_pos': start_pos,
                'driver_num': driver_num,
                
                # Tire features
                'starting_tire_soft': 1 if strat['starting_tire'] == 'SOFT' else 0,
                'starting_tire_medium': 1 if strat['starting_tire'] == 'MEDIUM' else 0,
                'starting_tire_hard': 1 if strat['starting_tire'] == 'HARD' else 0,
                
                # Strategy features
                'n_pit_stops': len(strat.get('pit_stops', [])),
                
                # Race configuration
                'total_laps': config['total_laps'],
                'base_lap_time': config['base_lap_time'],
                'pit_lane_time': config['pit_lane_time'],
                'track_temp': config['track_temp'],
                
                # Derived features
                'driver_per_start': driver_num / start_pos if start_pos > 0 else 0,
                'driver_mod_start': driver_num % start_pos if start_pos > 0 else 0,
                'laps_per_stop': config['total_laps'] / (len(strat.get('pit_stops', [])) + 1),
            }
            
            # Tire stint features
            pit_stops = strat.get('pit_stops', [])
            if pit_stops:
                # First stint length
                features['first_stint_length'] = pit_stops[0]['lap']
                
                # Last stint length
                features['last_stint_length'] = config['total_laps'] - pit_stops[-1]['lap']
                
                # Average stint length
                stint_lengths = []
                last_lap = 0
                for stop in pit_stops:
                    stint_lengths.append(stop['lap'] - last_lap)
                    last_lap = stop['lap']
                stint_lengths.append(config['total_laps'] - last_lap)
                features['avg_stint_length'] = np.mean(stint_lengths)
                features['stint_variance'] = np.std(stint_lengths)
                
                # Tire compound changes
                tire_changes = [stop['from_tire'] + '_' + stop['to_tire'] for stop in pit_stops]
                features['soft_to_medium'] = 1 if 'SOFT_MEDIUM' in tire_changes else 0
                features['soft_to_hard'] = 1 if 'SOFT_HARD' in tire_changes else 0
                features['medium_to_hard'] = 1 if 'MEDIUM_HARD' in tire_changes else 0
                features['hard_to_medium'] = 1 if 'HARD_MEDIUM' in tire_changes else 0
                features['medium_to_soft'] = 1 if 'MEDIUM_SOFT' in tire_changes else 0
                features['hard_to_soft'] = 1 if 'HARD_SOFT' in tire_changes else 0
            else:
                features['first_stint_length'] = config['total_laps']
                features['last_stint_length'] = config['total_laps']
                features['avg_stint_length'] = config['total_laps']
                features['stint_variance'] = 0
                features['soft_to_medium'] = 0
                features['soft_to_hard'] = 0
                features['medium_to_hard'] = 0
                features['hard_to_medium'] = 0
                features['medium_to_soft'] = 0
                features['hard_to_soft'] = 0
            
            features_list.append(features)
            driver_info.append({
                'driver_id': driver_id,
                'start_pos': start_pos
            })
        
        # Convert to array
        if not self.feature_names:
            self.feature_names = list(features_list[0].keys())
        
        feature_matrix = np.array([[f[name] for name in self.feature_names] 
                                   for f in features_list])
        
        return feature_matrix, driver_info
    
    def train_on_historical(self, n_races: int = 5000):
        """Train model on historical race data."""
        
        print("="*80)
        print("TRAINING ML MODEL ON HISTORICAL DATA")
        print("="*80)
        
        historical_dir = Path("data/historical_races")
        race_files = sorted(historical_dir.glob("races_*.json"))
        
        X_train = []
        y_train = []
        
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
                    # Extract features and labels
                    strategies = race['strategies']
                    results = race['finishing_positions']
                    
                    # Get features for this race
                    X_race, driver_info = self.extract_features(race)
                    
                    # Create target variable: finishing position for each driver
                    for i, info in enumerate(driver_info):
                        driver_id = info['driver_id']
                        finish_pos = results.index(driver_id) + 1
                        
                        X_train.append(X_race[i])
                        y_train.append(finish_pos)
                    
                    races_loaded += 1
                    
                    if races_loaded % 1000 == 0:
                        print(f"  Loaded {races_loaded} races...")
                        
                except Exception as e:
                    continue
        
        print(f"\nTotal samples: {len(X_train)}")
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        
        # Train model
        print("\nTraining Gradient Boosting model...")
        print(f"  Features: {len(self.feature_names)}")
        print(f"  Samples: {len(y_train)}")
        
        self.model.fit(X_train_scaled, y_train)
        self.is_trained = True
        
        # Feature importance
        print(f"\nTop 10 Most Important Features:")
        importances = self.model.feature_importances_
        indices = np.argsort(importances)[::-1][:10]
        
        for idx in indices:
            print(f"  {self.feature_names[idx]:<25} {importances[idx]:.4f}")
        
        # Training accuracy
        train_score = self.model.score(X_train_scaled, y_train)
        print(f"\nTraining R² score: {train_score:.4f}")
        print(f"\n✓ Model trained successfully!")
        
        return len(y_train)
    
    def predict(self, test_data: Dict) -> List[str]:
        """Predict finishing order for a race."""
        
        if not self.is_trained:
            raise ValueError("Model not trained yet!")
        
        # Extract features
        X, driver_info = self.extract_features(test_data)
        X_scaled = self.scaler.transform(X)
        
        # Predict finishing positions
        predictions = self.model.predict(X_scaled)
        
        # Sort drivers by predicted position
        driver_predictions = []
        for i, pred in enumerate(predictions):
            driver_predictions.append({
                'driver_id': driver_info[i]['driver_id'],
                'predicted_pos': pred
            })
        
        # Sort by predicted position (lower is better)
        driver_predictions.sort(key=lambda x: x['predicted_pos'])
        
        # Return finishing order
        return [d['driver_id'] for d in driver_predictions]
    
    def save_model(self, filepath: str):
        """Save trained model to file."""
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'is_trained': self.is_trained
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"✓ Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load trained model from file."""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.feature_names = model_data['feature_names']
        self.is_trained = model_data['is_trained']
        
        print(f"✓ Model loaded from {filepath}")


def main():
    """Main training script."""
    
    predictor = MLPredictor()
    
    # Train on historical data
    n_samples = predictor.train_on_historical(n_races=30000)
    
    # Save model
    predictor.save_model("solution2/ml_predictor.pkl")
    
    print(f"\n{'='*80}")
    print("TRAINING COMPLETE")
    print("="*80)
    print(f"\nTrained on {n_samples} driver-race samples")
    print(f"Model ready for predictions!")
    print(f"\nNext steps:")
    print(f"1. Test model: python solution2/test_ml_predictor.py")
    print(f"2. Integrate with simulator")
    print(f"3. Run full validation")


if __name__ == "__main__":
    main()
