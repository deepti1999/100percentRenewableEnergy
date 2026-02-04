#!/usr/bin/env python3
"""
Test the FINAL CORRECT 3.4.2 Ziel formula matching Excel:
3.4.2(Ziel) = 3.4.2(Status) × (1 - 3.4.1(Ziel)/100) / (1 - 3.4.1(Status)/100) × (3.4(Ziel) / 3.4(Status))
Should result in 3.2
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import VerbrauchData

def test_final_correct_formula():
    """Test the final correct formula that should give 3.2"""
    print("=== TESTING FINAL CORRECT 3.4.2 ZIEL FORMULA ===")
    
    # Get values matching Excel
    entry_3_4 = VerbrauchData.objects.get(code='3.4')
    entry_3_4_1 = VerbrauchData.objects.get(code='3.4.1')
    entry_3_4_2 = VerbrauchData.objects.get(code='3.4.2')
    
    print(f"Values from database:")
    print(f"3.4   Status: {entry_3_4.status}%   Ziel: {entry_3_4.ziel}%")
    print(f"3.4.1 Status: {entry_3_4_1.status}%   Ziel: {entry_3_4_1.ziel}%")
    
    calc_3_4_2_status = entry_3_4_2.calculate_value()
    print(f"3.4.2 Status: {calc_3_4_2_status}")
    
    # Manual calculation using Excel formula
    print(f"\n--- Manual Calculation (Excel Formula) ---")
    print(f"Formula: =L111*(1-M110%)/(1-L110%)*M108/L108")
    print(f"Where:")
    print(f"  L111 = 3.4.2(Status) = {calc_3_4_2_status}")
    print(f"  M110 = 3.4.1(Ziel) = {entry_3_4_1.ziel}%")
    print(f"  L110 = 3.4.1(Status) = {entry_3_4_1.status}%")
    print(f"  M108 = 3.4(Ziel) = {entry_3_4.ziel}%")
    print(f"  L108 = 3.4(Status) = {entry_3_4.status}%")
    
    # Step by step calculation
    efficiency_numerator = 1 - entry_3_4_1.ziel / 100.0
    efficiency_denominator = 1 - entry_3_4_1.status / 100.0
    efficiency_ratio = efficiency_numerator / efficiency_denominator
    
    consumption_ratio = entry_3_4.ziel / entry_3_4.status
    
    manual_result = calc_3_4_2_status * efficiency_ratio * consumption_ratio
    
    print(f"\nStep by step:")
    print(f"1. Efficiency numerator:   (1 - {entry_3_4_1.ziel}/100) = {efficiency_numerator}")
    print(f"2. Efficiency denominator: (1 - {entry_3_4_1.status}/100) = {efficiency_denominator}")
    print(f"3. Efficiency ratio: {efficiency_numerator} / {efficiency_denominator} = {efficiency_ratio}")
    print(f"4. Consumption ratio: {entry_3_4.ziel} / {entry_3_4.status} = {consumption_ratio}")
    print(f"5. Final: {calc_3_4_2_status} × {efficiency_ratio} × {consumption_ratio} = {manual_result}")
    
    # Test our implementation
    calc_3_4_2_ziel = entry_3_4_2.calculate_ziel_value()
    print(f"\nOur calculation result: {calc_3_4_2_ziel}")
    print(f"Expected (from Excel): 3.2")
    print(f"Match: {abs(calc_3_4_2_ziel - 3.2) < 0.1}")

if __name__ == '__main__':
    test_final_correct_formula()
    print("\n✓ Final formula verification completed!")