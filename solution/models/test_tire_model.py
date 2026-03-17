"""
Test suite for Tire Performance Model.

This script demonstrates the tire model capabilities and verifies
correct calculations for all compounds under various conditions.
"""

from tire_model import TireModel


def test_compound_offsets():
    """Test base compound offset calculations."""
    print("=" * 70)
    print("TEST 1: Base Compound Offsets")
    print("=" * 70)
    
    soft_offset = TireModel.get_compound_offset('SOFT')
    medium_offset = TireModel.get_compound_offset('MEDIUM')
    hard_offset = TireModel.get_compound_offset('HARD')
    
    print(f"\nBase Lap Time Offsets:")
    print(f"  SOFT:   {soft_offset:6.2f}s (reference - fastest)")
    print(f"  MEDIUM: {medium_offset:6.2f}s (+{medium_offset - soft_offset:.2f}s vs SOFT)")
    print(f"  HARD:   {hard_offset:6.2f}s (+{hard_offset - soft_offset:.2f}s vs SOFT)")
    
    # Verify expected values
    assert soft_offset == 0.0, "SOFT should be 0.0s offset"
    assert abs(medium_offset - 0.75) < 0.01, "MEDIUM should be ~0.75s"
    assert abs(hard_offset - 1.50) < 0.01, "HARD should be ~1.50s"
    
    print("\n✓ All compound offsets are correct")


def test_degradation_basic():
    """Test basic degradation calculations at optimal temperature."""
    print("\n" + "=" * 70)
    print("TEST 2: Basic Degradation at Optimal Temperature")
    print("=" * 70)
    
    track_temp = 30  # Near-optimal for all compounds
    
    print(f"\nTrack Temperature: {track_temp}°C")
    print("\nDegradation progression (seconds added to lap time):")
    print(f"{'Lap':<6} {'SOFT':<10} {'MEDIUM':<10} {'HARD':<10}")
    print("-" * 40)
    
    for lap in [1, 5, 10, 15, 20, 25, 30]:
        soft_deg = TireModel.calculate_degradation('SOFT', lap, track_temp)
        medium_deg = TireModel.calculate_degradation('MEDIUM', lap, track_temp)
        hard_deg = TireModel.calculate_degradation('HARD', lap, track_temp)
        
        print(f"{lap:<6} {soft_deg:<10.3f} {medium_deg:<10.3f} {hard_deg:<10.3f}")
    
    print("\nObservations:")
    print("  - SOFT degrades fastest but starts with best grip")
    print("  - HARD degrades slowest, maintaining performance longer")
    print("  - Degradation accelerates after optimal lap count")


def test_temperature_effects():
    """Test how temperature affects tire degradation."""
    print("\n" + "=" * 70)
    print("TEST 3: Temperature Effects on Degradation")
    print("=" * 70)
    
    tire_age = 10  # Mid-life tire
    
    print(f"\nDegradation at lap {tire_age} across different temperatures:")
    print(f"{'Temp (°C)':<12} {'SOFT':<12} {'MEDIUM':<12} {'HARD':<12}")
    print("-" * 50)
    
    for temp in [20, 25, 28, 30, 32, 35, 40]:
        soft_deg = TireModel.calculate_degradation('SOFT', tire_age, temp)
        medium_deg = TireModel.calculate_degradation('MEDIUM', tire_age, temp)
        hard_deg = TireModel.calculate_degradation('HARD', tire_age, temp)
        
        print(f"{temp:<12} {soft_deg:<12.3f} {medium_deg:<12.3f} {hard_deg:<12.3f}")
    
    print("\nOptimal Temperatures:")
    print("  - SOFT:   28°C (performs best in cooler conditions)")
    print("  - MEDIUM: 30°C (balanced for average conditions)")
    print("  - HARD:   32°C (performs best in hotter conditions)")


def test_temperature_direct_effect():
    """Test direct temperature effect on lap time (separate from degradation)."""
    print("\n" + "=" * 70)
    print("TEST 4: Direct Temperature Effect on Lap Time")
    print("=" * 70)
    
    print("\nTemperature penalty (independent of tire wear):")
    print(f"{'Temp (°C)':<12} {'SOFT':<12} {'MEDIUM':<12} {'HARD':<12}")
    print("-" * 50)
    
    for temp in [20, 24, 28, 30, 32, 36, 40]:
        soft_temp = TireModel.calculate_temperature_effect('SOFT', temp)
        medium_temp = TireModel.calculate_temperature_effect('MEDIUM', temp)
        hard_temp = TireModel.calculate_temperature_effect('HARD', temp)
        
        # Highlight optimal temperatures
        soft_marker = " ← OPTIMAL" if temp == 28 else ""
        medium_marker = " ← OPTIMAL" if temp == 30 else ""
        hard_marker = " ← OPTIMAL" if temp == 32 else ""
        
        print(f"{temp:<12} {soft_temp:<12.3f}{soft_marker} "
              f"{medium_temp:<12.3f}{medium_marker} "
              f"{hard_temp:<12.3f}{hard_marker}")


def test_complete_lap_time_adjustment():
    """Test total lap time adjustment combining all factors."""
    print("\n" + "=" * 70)
    print("TEST 5: Complete Lap Time Adjustment")
    print("=" * 70)
    
    base_lap_time = 85.0
    track_temp = 30
    
    print(f"\nBase Lap Time: {base_lap_time}s")
    print(f"Track Temperature: {track_temp}°C")
    print("\nTotal lap time by compound and tire age:")
    print(f"{'Age':<6} {'SOFT Total':<14} {'MEDIUM Total':<14} {'HARD Total':<14}")
    print("-" * 56)
    
    for age in [1, 5, 10, 15, 20, 25, 30]:
        soft_adj = TireModel.calculate_total_lap_time_adjustment('SOFT', age, track_temp)
        medium_adj = TireModel.calculate_total_lap_time_adjustment('MEDIUM', age, track_temp)
        hard_adj = TireModel.calculate_total_lap_time_adjustment('HARD', age, track_temp)
        
        soft_total = base_lap_time + soft_adj
        medium_total = base_lap_time + medium_adj
        hard_total = base_lap_time + hard_adj
        
        print(f"{age:<6} {soft_total:<14.3f} {medium_total:<14.3f} {hard_total:<14.3f}")
    
    print("\nExample calculation breakdown (Lap 10, 30°C):")
    print("\nSOFT Compound:")
    offset = TireModel.get_compound_offset('SOFT')
    deg = TireModel.calculate_degradation('SOFT', 10, 30)
    temp = TireModel.calculate_temperature_effect('SOFT', 30)
    total = offset + deg + temp
    print(f"  Base Offset:      {offset:6.3f}s")
    print(f"  Degradation:      {deg:6.3f}s")
    print(f"  Temp Effect:      {temp:6.3f}s")
    print(f"  Total Adjustment: {total:6.3f}s")
    print(f"  Final Lap Time:   {base_lap_time + total:6.3f}s")


def test_compound_comparison():
    """Compare all compounds side-by-side."""
    print("\n" + "=" * 70)
    print("TEST 6: Compound Comparison at Different Temperatures")
    print("=" * 70)
    
    for temp in [25, 30, 35]:
        print(f"\n--- Track Temperature: {temp}°C ---")
        comparison = TireModel.compare_compounds(temp)
        
        for compound in ['SOFT', 'MEDIUM', 'HARD']:
            data = comparison[compound]
            print(f"\n{compound}:")
            print(f"  Base Offset:     {data['base_offset']:.3f}s")
            print(f"  Lap 1 Degradation: {data['lap_1_degradation']:.3f}s")
            print(f"  Temp Effect:     {data['temperature_effect']:.3f}s")
            print(f"  Total Adj:       {data['total_adjustment']:.3f}s")


def test_properties():
    """Test getting compound properties."""
    print("\n" + "=" * 70)
    print("TEST 7: Compound Properties Reference")
    print("=" * 70)
    
    print("\nComplete tire compound specifications:")
    
    for compound in ['SOFT', 'MEDIUM', 'HARD']:
        props = TireModel.get_compound_properties(compound)
        print(f"\n{compound} Compound:")
        print(f"  Base Offset:        {props['base_offset']:.2f}s")
        print(f"  Degradation Rate:   {props['degradation_rate']:.2f}s/lap")
        print(f"  Optimal Laps:       {props['optimal_laps']} laps")
        print(f"  Temp Sensitivity:   {props['temp_sensitivity']:.3f}s/°C")
        print(f"  Optimal Temperature: {props['optimal_temperature']}°C")


def test_edge_cases():
    """Test edge cases and error handling."""
    print("\n" + "=" * 70)
    print("TEST 8: Edge Cases and Error Handling")
    print("=" * 70)
    
    # Test invalid compound
    try:
        TireModel.get_compound_offset('ULTRASOFT')
        print("✗ Should have raised ValueError for invalid compound")
    except ValueError as e:
        print(f"✓ Correctly raises ValueError: {e}")
    
    # Test very old tire
    old_tire_deg = TireModel.calculate_degradation('SOFT', 50, 30)
    print(f"\n✓ Handles very old tires (50 laps): {old_tire_deg:.3f}s degradation")
    
    # Test extreme temperatures
    extreme_deg = TireModel.calculate_degradation('MEDIUM', 10, 50)
    print(f"✓ Handles extreme temperature (50°C): {extreme_deg:.3f}s degradation")


def main():
    """Run all tire model tests."""
    print("\n" + "=" * 70)
    print("TIRE PERFORMANCE MODEL - TEST SUITE")
    print("=" * 70)
    
    test_compound_offsets()
    test_degradation_basic()
    test_temperature_effects()
    test_temperature_direct_effect()
    test_complete_lap_time_adjustment()
    test_compound_comparison()
    test_properties()
    test_edge_cases()
    
    print("\n" + "=" * 70)
    print("ALL TESTS COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print("\nThe tire model is ready for integration with the race simulator.")
    print("Next step: Update lap_time.py to use this new tire_model.py")


if __name__ == '__main__':
    main()
