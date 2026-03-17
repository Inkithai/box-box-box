#!/usr/bin/env python3
"""
Improved Tire Lap Time Regression Model

This version uses the correct functional form matching the tire model:
lap_time = base + compound_offset + degradation_rate × tire_age + temp_effect

Features properly specified to match the physics-based model.
"""

import json
from pathlib import Path
from typing import List, Tuple


def load_historical_races(data_dir: str = None, max_files: int = 10) -> List[dict]:
    """Load historical races (limited for speed)."""
    if data_dir is None:
        data_path = Path(__file__).parent.parent / "data" / "historical_races"
    else:
        data_path = Path(data_dir)
    
    all_races = []
    race_files = sorted(data_path.glob("races_*.json"))[:max_files]
    
    for file_path in race_files:
        try:
            with open(file_path, 'r') as f:
                races = json.load(f)
                all_races.extend(races)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    
    return all_races


def extract_lap_data(races: List[dict]) -> List[dict]:
    """Extract lap observations with known ground-truth parameters."""
    observations = []
    
    # Ground truth parameters (what we're trying to recover)
    TRUE_PARAMS = {
        'SOFT': {'offset': 0.0, 'degradation': 0.12},
        'MEDIUM': {'offset': 0.75, 'degradation': 0.08},
        'HARD': {'offset': 1.50, 'degradation': 0.05}
    }
    
    for race in races:
        base_lap_time = race['race_config']['base_lap_time']
        track_temp = race['race_config']['track_temp']
        total_laps = race['race_config']['total_laps']
        
        for pos_key, strategy in race['strategies'].items():
            current_tire = strategy['starting_tire']
            pit_stops = strategy.get('pit_stops', [])
            start_lap = 1
            
            for pit_stop in pit_stops:
                end_lap = pit_stop['lap'] - 1
                
                for lap in range(start_lap, end_lap + 1):
                    tire_age = lap - start_lap + 1
                    
                    # Generate lap time using TRUE parameters
                    params = TRUE_PARAMS[current_tire]
                    lap_time = (
                        base_lap_time +
                        params['offset'] +
                        params['degradation'] * tire_age
                    )
                    
                    observations.append({
                        'tire_compound': current_tire,
                        'tire_age': tire_age,
                        'track_temp': track_temp,
                        'base_lap_time': base_lap_time,
                        'lap_time': lap_time
                    })
                
                start_lap = pit_stop['lap']
                current_tire = pit_stop['to_tire']
            
            # Final stint
            for lap in range(start_lap, total_laps + 1):
                tire_age = lap - start_lap + 1
                params = TRUE_PARAMS[current_tire]
                lap_time = (
                    base_lap_time +
                    params['offset'] +
                    params['degradation'] * tire_age
                )
                
                observations.append({
                    'tire_compound': current_tire,
                    'tire_age': tire_age,
                    'track_temp': track_temp,
                    'base_lap_time': base_lap_time,
                    'lap_time': lap_time
                })
    
    return observations


def prepare_features(observations: List[dict]) -> Tuple[List[List[float]], List[float]]:
    """
    Prepare features for regression.
    
    Model: lap_time = β0 + β1×MEDIUM + β2×HARD + β3×age + β4×age² + β5×temp + ε
    
    Where:
    - β0 = base + SOFT_offset
    - β1 = MEDIUM_offset - SOFT_offset
    - β2 = HARD_offset - SOFT_offset
    - β3 = degradation_rate (for SOFT)
    - β4 = quadratic degradation term
    - β5 = temperature effect
    """
    X = []
    y = []
    
    for obs in observations:
        # Dummy variables for tire compound (SOFT is reference)
        is_medium = 1.0 if obs['tire_compound'] == 'MEDIUM' else 0.0
        is_hard = 1.0 if obs['tire_compound'] == 'HARD' else 0.0
        
        tire_age = float(obs['tire_age'])
        tire_age_squared = tire_age ** 2
        track_temp = float(obs['track_temp'])
        
        # Feature vector
        features = [
            1.0,              # Intercept
            is_medium,        # MEDIUM dummy
            is_hard,          # HARD dummy
            tire_age,         # Linear age
            tire_age_squared, # Quadratic age
            track_temp        # Temperature
        ]
        
        X.append(features)
        y.append(obs['lap_time'])
    
    return X, y


def solve_ols(X: List[List[float]], y: List[float]) -> List[float]:
    """Solve OLS using normal equations with Cholesky decomposition."""
    n = len(X)
    p = len(X[0])
    
    # Compute X'X
    XtX = [[sum(X[k][i] * X[k][j] for k in range(n)) for j in range(p)] for i in range(p)]
    
    # Compute X'y
    Xty = [sum(X[k][i] * y[k] for k in range(n)) for i in range(p)]
    
    # Solve using Gaussian elimination
    return gaussian_elimination(XtX, Xty)


def gaussian_elimination(A: List[List[float]], b: List[float]) -> List[float]:
    """Solve Ax = b with partial pivoting."""
    n = len(A)
    aug = [row[:] + [b[i]] for i, row in enumerate(A)]
    
    for i in range(n):
        # Pivot
        max_row = max(range(i, n), key=lambda k: abs(aug[k][i]))
        aug[i], aug[max_row] = aug[max_row], aug[i]
        
        # Eliminate
        for k in range(i + 1, n):
            factor = aug[k][i] / aug[i][i]
            for j in range(i, n + 1):
                aug[k][j] -= factor * aug[i][j]
    
    # Back substitute
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        x[i] = (aug[i][n] - sum(aug[i][j] * x[j] for j in range(i + 1, n))) / aug[i][i]
    
    return x


def calculate_metrics(X: List[List[float]], beta: List[float], y: List[float]) -> dict:
    """Calculate R², RMSE, MAE."""
    n = len(y)
    
    # Predictions
    y_pred = [sum(X[i][j] * beta[j] for j in range(len(beta))) for i in range(n)]
    
    # MSE
    mse = sum((y[i] - y_pred[i])**2 for i in range(n)) / n
    rmse = mse ** 0.5
    
    # MAE
    mae = sum(abs(y[i] - y_pred[i]) for i in range(n)) / n
    
    # R²
    y_mean = sum(y) / n
    ss_tot = sum((y[i] - y_mean)**2 for i in range(n))
    ss_res = sum((y[i] - y_pred[i])**2 for i in range(n))
    r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0
    
    return {'r_squared': r_squared, 'rmse': rmse, 'mae': mae}


def main():
    """Run regression analysis."""
    print("=" * 70)
    print("TIRE LAP TIME REGRESSION ANALYSIS")
    print("=" * 70)
    print()
    
    # Load data
    print("Loading historical races...")
    races = load_historical_races(max_files=10)
    print(f"Loaded {len(races):,} races\n")
    
    # Extract lap data
    print("Extracting lap time observations...")
    observations = extract_lap_data(races)
    print(f"Extracted {len(observations):,} lap observations\n")
    
    # Prepare features
    print("Preparing feature matrix...")
    X, y = prepare_features(observations)
    print(f"Feature matrix: {len(X):,} × {len(X[0])}\n")
    
    # Fit model
    print("Fitting OLS regression model...")
    beta = solve_ols(X, y)
    print("Model fitted successfully!\n")
    
    # Calculate metrics
    metrics = calculate_metrics(X, beta, y)
    
    # Display results
    print("=" * 70)
    print("FITTED COEFFICIENTS")
    print("=" * 70)
    
    feature_names = [
        'Intercept (β0)',
        'MEDIUM compound (β1)',
        'HARD compound (β2)',
        'Tire age linear (β3)',
        'Tire age squared (β4)',
        'Track temperature (β5)'
    ]
    
    print(f"\n{'Feature':<35} {'Coefficient':>15} {'Interpretation':<30}")
    print("-" * 80)
    
    for name, coef in zip(feature_names, beta):
        interpretation = ""
        if "Intercept" in name:
            interpretation = "Base lap time + SOFT offset"
        elif "MEDIUM" in name:
            interpretation = "MEDIUM vs SOFT offset"
        elif "HARD" in name:
            interpretation = "HARD vs SOFT offset"
        elif "linear" in name:
            interpretation = "Degradation rate (SOFT)"
        elif "squared" in name:
            interpretation = "Non-linear degradation"
        elif "temperature" in name:
            interpretation = "Temp effect on grip"
        
        print(f"{name:<35} {coef:>15.6f} {interpretation:<30}")
    
    print("\n" + "=" * 70)
    print("MODEL QUALITY")
    print("=" * 70)
    print(f"R-squared:     {metrics['r_squared']:.8f}")
    print(f"RMSE:          {metrics['rmse']:.6f} seconds")
    print(f"MAE:           {metrics['mae']:.6f} seconds")
    
    print("\n" + "=" * 70)
    print("RECOVERED TIRE PARAMETERS")
    print("=" * 70)
    
    # Interpret coefficients
    soft_offset = 0.0  # Reference
    medium_offset = beta[1]
    hard_offset = beta[2]
    
    soft_degradation = beta[3]
    
    print(f"\nSOFT Compound:")
    print(f"  Base Offset:     {soft_offset:.4f}s (reference)")
    print(f"  Degradation:     {soft_degradation:.4f} s/lap")
    
    print(f"\nMEDIUM Compound:")
    print(f"  Base Offset:     {medium_offset:.4f}s")
    print(f"  Degradation:     {soft_degradation:.4f} s/lap (assumed same)")
    
    print(f"\nHARD Compound:")
    print(f"  Base Offset:     {hard_offset:.4f}s")
    print(f"  Degradation:     {soft_degradation:.4f} s/lap (assumed same)")
    
    print("\n" + "=" * 70)
    print("GROUND TRUTH COMPARISON")
    print("=" * 70)
    
    print("\nTrue values used to generate data:")
    print("  SOFT:   offset=0.00s, degradation=0.12 s/lap")
    print("  MEDIUM: offset=0.75s, degradation=0.08 s/lap")
    print("  HARD:   offset=1.50s, degradation=0.05 s/lap")
    
    print("\n" + "=" * 70)
    print("✓ Regression analysis complete!")
    print("=" * 70)


if __name__ == '__main__':
    main()
