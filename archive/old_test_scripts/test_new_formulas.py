#!/usr/bin/env python3
"""
Test the new formulas:
3.3 (Status) = 3.2.3(Status) + 3.1.2(Status)
3.3 (Ziel)   = 3.2.3(Ziel) + 3.1.2(Ziel)
3.4.0 (Status) = 3.3(Status) × (3.4%(Status))
3.4.0 (Ziel)   = 3.3(Ziel) × (3.4%(Ziel))
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import VerbrauchData

def test_new_formulas():
    """Test the new 3.3 and 3.4.0 formulas"""
    print("=== TESTING NEW FORMULAS ===")
    
    # Test dependencies first
    print("\n--- Dependencies ---")
    deps = ['3.1.2', '3.2.3', '3.3', '3.4', '3.4.0']
    
    for code in deps:
        entry = VerbrauchData.objects.filter(code=code).first()
        if entry:
            if entry.is_calculated:
                status_calc = entry.calculate_value()
                ziel_calc = entry.calculate_ziel_value()
                print(f"{code:8} [CALC] Status: {status_calc:>12} | Ziel: {ziel_calc:>12}")
            else:
                print(f"{code:8} [FIXED] Status: {entry.status:>11} | Ziel: {entry.ziel:>11}")
        else:
            print(f"{code:8} NOT FOUND")
    
    print("\n--- Manual Formula Verification ---")
    
    # Manual calculation for 3.3
    entry_3_1_2 = VerbrauchData.objects.get(code='3.1.2')
    entry_3_2_3 = VerbrauchData.objects.get(code='3.2.3')
    
    calc_3_1_2_status = entry_3_1_2.calculate_value()
    calc_3_1_2_ziel = entry_3_1_2.calculate_ziel_value()
    calc_3_2_3_status = entry_3_2_3.calculate_value()
    calc_3_2_3_ziel = entry_3_2_3.calculate_ziel_value()
    
    if calc_3_1_2_status and calc_3_2_3_status:
        manual_3_3_status = calc_3_1_2_status + calc_3_2_3_status
        print(f"3.3 Status: {calc_3_2_3_status} + {calc_3_1_2_status} = {manual_3_3_status}")
    
    if calc_3_1_2_ziel and calc_3_2_3_ziel:
        manual_3_3_ziel = calc_3_1_2_ziel + calc_3_2_3_ziel
        print(f"3.3 Ziel:   {calc_3_2_3_ziel} + {calc_3_1_2_ziel} = {manual_3_3_ziel}")
    
    # Test 3.3 calculation
    entry_3_3 = VerbrauchData.objects.get(code='3.3')
    calc_3_3_status = entry_3_3.calculate_value()
    calc_3_3_ziel = entry_3_3.calculate_ziel_value()
    
    print(f"\n3.3 calculated Status: {calc_3_3_status}")
    print(f"3.3 calculated Ziel:   {calc_3_3_ziel}")
    
    # Manual calculation for 3.4.0
    entry_3_4 = VerbrauchData.objects.get(code='3.4')
    
    if calc_3_3_status and entry_3_4.status:
        manual_3_4_0_status = calc_3_3_status * (entry_3_4.status / 100.0)
        print(f"\n3.4.0 Status: {calc_3_3_status} × {entry_3_4.status}% = {manual_3_4_0_status}")
    
    if calc_3_3_ziel and entry_3_4.ziel:
        manual_3_4_0_ziel = calc_3_3_ziel * (entry_3_4.ziel / 100.0)
        print(f"3.4.0 Ziel:   {calc_3_3_ziel} × {entry_3_4.ziel}% = {manual_3_4_0_ziel}")
    
    # Test 3.4.0 calculation
    entry_3_4_0 = VerbrauchData.objects.get(code='3.4.0')
    calc_3_4_0_status = entry_3_4_0.calculate_value()
    calc_3_4_0_ziel = entry_3_4_0.calculate_ziel_value()
    
    print(f"\n3.4.0 calculated Status: {calc_3_4_0_status}")
    print(f"3.4.0 calculated Ziel:   {calc_3_4_0_ziel}")

if __name__ == '__main__':
    test_new_formulas()
    print("\n✓ Formula testing completed!")