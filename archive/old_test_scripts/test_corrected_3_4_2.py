#!/usr/bin/env python3
"""
Test the CORRECTED 3.4.2 formulas:
3.4.2 (Status) = 3.4(Status) × (1 - 3.4.1(Status)/100)  [CHANGED from 3.4.0 to 3.4]
3.4.2(Ziel) = 3.4.2(Status) × ((1 - 3.4.1(Ziel)/100) / (1 - 3.4.1(Status)/100)) × (3.4.0(Ziel) / 3.4.0(Status))  [FIXED PARENTHESES]
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import VerbrauchData

def test_corrected_formulas():
    """Test the corrected 3.4.2 formulas"""
    print("=== TESTING CORRECTED 3.4.2 FORMULAS ===")
    
    # Get all dependencies
    entry_3_4 = VerbrauchData.objects.get(code='3.4')
    entry_3_4_0 = VerbrauchData.objects.get(code='3.4.0')
    entry_3_4_1 = VerbrauchData.objects.get(code='3.4.1')
    entry_3_4_2 = VerbrauchData.objects.get(code='3.4.2')
    
    print("\n--- Dependencies ---")
    print(f"3.4   Status/Ziel: {entry_3_4.status} / {entry_3_4.ziel}")
    print(f"3.4.0 Status/Ziel: {entry_3_4_0.calculate_value()} / {entry_3_4_0.calculate_ziel_value()}")
    print(f"3.4.1 Status/Ziel: {entry_3_4_1.status} / {entry_3_4_1.ziel}")
    
    # Manual calculation for CORRECTED 3.4.2 Status (now using 3.4 instead of 3.4.0)
    if entry_3_4.status and entry_3_4_1.status:
        manual_3_4_2_status = entry_3_4.status * (1 - entry_3_4_1.status / 100.0)
        print(f"\n--- Manual CORRECTED 3.4.2 Status Calculation ---")
        print(f"OLD: 3.4.2 Status = 3.4.0(Status) × (1 - 3.4.1(Status)/100)")
        print(f"NEW: 3.4.2 Status = 3.4(Status) × (1 - 3.4.1(Status)/100)")
        print(f"     3.4.2 Status = {entry_3_4.status} × (1 - {entry_3_4_1.status}/100)")
        print(f"                   = {entry_3_4.status} × (1 - {entry_3_4_1.status/100.0})")
        print(f"                   = {entry_3_4.status} × {1 - entry_3_4_1.status/100.0}")
        print(f"                   = {manual_3_4_2_status}")
    
    # Test 3.4.2 Status calculation
    calc_3_4_2_status = entry_3_4_2.calculate_value()
    print(f"\n3.4.2 calculated Status: {calc_3_4_2_status}")
    
    # Compare old vs new
    calc_3_4_0_status = entry_3_4_0.calculate_value()
    if calc_3_4_0_status:
        old_result = calc_3_4_0_status * (1 - entry_3_4_1.status / 100.0)
        print(f"\nComparison:")
        print(f"OLD method (3.4.0): {old_result}")
        print(f"NEW method (3.4):   {calc_3_4_2_status}")
        print(f"Difference: {abs(old_result - calc_3_4_2_status)}")
    
    # Test ZIEL calculation with corrected parentheses
    calc_3_4_2_ziel = entry_3_4_2.calculate_ziel_value()
    print(f"\n3.4.2 calculated Ziel: {calc_3_4_2_ziel}")
    
    print(f"\n--- Formula Summary ---")
    print(f"STATUS: 3.4.2 = {entry_3_4.status} × (1 - {entry_3_4_1.status}/100) = {calc_3_4_2_status}")
    print(f"ZIEL:   3.4.2 = {calc_3_4_2_status} × efficiency_ratio × consumption_ratio = {calc_3_4_2_ziel}")

def show_all_3_4_values():
    """Show all 3.4.x values for comparison"""
    print("\n\n=== ALL 3.4.x VALUES ===")
    entries_3_4 = VerbrauchData.objects.filter(code__startswith='3.4').order_by('code')
    
    for entry in entries_3_4:
        calc_status = '[CALC]' if entry.is_calculated else '[FIXED]'
        
        if entry.is_calculated:
            status_calc = entry.calculate_value()
            ziel_calc = entry.calculate_ziel_value()
            status_display = f"{status_calc:>12.3f}" if status_calc else "None"
            ziel_display = f"{ziel_calc:>12.3f}" if ziel_calc else "None"
        else:
            status_display = f"{entry.status:>12}" if entry.status else "None"
            ziel_display = f"{entry.ziel:>12}" if entry.ziel else "None"
        
        print(f"{entry.code:8} {calc_status:8} {status_display} | {ziel_display}")

if __name__ == '__main__':
    test_corrected_formulas()
    show_all_3_4_values()
    print("\n✓ Corrected formula testing completed!")