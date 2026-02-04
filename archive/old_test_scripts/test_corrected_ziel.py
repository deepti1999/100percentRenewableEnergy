#!/usr/bin/env python3
"""
Test the CORRECTED 3.4.2 Ziel formula:
3.4.2(Ziel) = 3.4.2(Status) × ((1 - 3.4.1(Ziel)/100) / (1 - 3.4.1(Ziel)/100)) × (3.4(Ziel) / 3.4(Status))

Note: The efficiency ratio becomes 1 since numerator and denominator are the same
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import VerbrauchData

def test_corrected_ziel_formula():
    """Test the corrected ZIEL formula"""
    print("=== TESTING CORRECTED 3.4.2 ZIEL FORMULA ===")
    
    # Get dependencies
    entry_3_4 = VerbrauchData.objects.get(code='3.4')
    entry_3_4_1 = VerbrauchData.objects.get(code='3.4.1')
    entry_3_4_2 = VerbrauchData.objects.get(code='3.4.2')
    
    print(f"3.4   Status/Ziel: {entry_3_4.status}% / {entry_3_4.ziel}%")
    print(f"3.4.1 Status/Ziel: {entry_3_4_1.status}% / {entry_3_4_1.ziel}%")
    
    # Get 3.4.2 Status
    calc_3_4_2_status = entry_3_4_2.calculate_value()
    print(f"3.4.2 Status: {calc_3_4_2_status}")
    
    # Manual calculation of corrected ZIEL formula
    if (calc_3_4_2_status and entry_3_4_1.ziel and entry_3_4.status and entry_3_4.ziel):
        print(f"\n--- Manual Calculation ---")
        print(f"Formula: 3.4.2(Ziel) = 3.4.2(Status) × ((1 - 3.4.1(Ziel)/100) / (1 - 3.4.1(Ziel)/100)) × (3.4(Ziel) / 3.4(Status))")
        
        # Efficiency ratio (this will be 1)
        efficiency_ratio = (1 - entry_3_4_1.ziel / 100.0) / (1 - entry_3_4_1.ziel / 100.0)
        print(f"Efficiency ratio: (1 - {entry_3_4_1.ziel}/100) / (1 - {entry_3_4_1.ziel}/100) = {efficiency_ratio}")
        
        # Consumption ratio
        consumption_ratio = entry_3_4.ziel / entry_3_4.status
        print(f"Consumption ratio: {entry_3_4.ziel} / {entry_3_4.status} = {consumption_ratio}")
        
        # Final result
        manual_result = calc_3_4_2_status * efficiency_ratio * consumption_ratio
        print(f"Result: {calc_3_4_2_status} × {efficiency_ratio} × {consumption_ratio} = {manual_result}")
    
    # Test actual calculation
    calc_3_4_2_ziel = entry_3_4_2.calculate_ziel_value()
    print(f"\n3.4.2 calculated Ziel: {calc_3_4_2_ziel}")
    
    print(f"\n--- Simplified Formula ---")
    print(f"Since efficiency ratio = 1, the formula simplifies to:")
    print(f"3.4.2(Ziel) = 3.4.2(Status) × (3.4(Ziel) / 3.4(Status))")
    print(f"            = {calc_3_4_2_status} × ({entry_3_4.ziel} / {entry_3_4.status})")
    print(f"            = {calc_3_4_2_status} × {entry_3_4.ziel / entry_3_4.status}")
    print(f"            = {calc_3_4_2_status * (entry_3_4.ziel / entry_3_4.status)}")

if __name__ == '__main__':
    test_corrected_ziel_formula()
    print("\n✓ Corrected ZIEL formula testing completed!")