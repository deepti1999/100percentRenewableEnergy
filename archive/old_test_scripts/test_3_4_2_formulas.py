#!/usr/bin/env python3
"""
Test the new 3.4.2 formulas:
3.4.2 (Status) = 3.4.0(Status) × (1 - 3.4.1(Status)/100)
3.4.2(Ziel) = 3.4.2(Status) × ((1 - 3.4.1(Ziel)/100) / (1 - 3.4.1(Status)/100)) × (3.4.0(Ziel) / 3.4.0(Status))
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import VerbrauchData

def test_3_4_2_formulas():
    """Test the new 3.4.2 formulas"""
    print("=== TESTING 3.4.2 FORMULAS ===")
    
    # Get all dependencies
    entry_3_4_0 = VerbrauchData.objects.get(code='3.4.0')
    entry_3_4_1 = VerbrauchData.objects.get(code='3.4.1')
    entry_3_4_2 = VerbrauchData.objects.get(code='3.4.2')
    
    print("\n--- Dependencies ---")
    print(f"3.4.0 Status/Ziel: {entry_3_4_0.calculate_value()} / {entry_3_4_0.calculate_ziel_value()}")
    print(f"3.4.1 Status/Ziel: {entry_3_4_1.status} / {entry_3_4_1.ziel}")
    
    # Manual calculation for 3.4.2 Status
    calc_3_4_0_status = entry_3_4_0.calculate_value()
    if calc_3_4_0_status and entry_3_4_1.status:
        manual_3_4_2_status = calc_3_4_0_status * (1 - entry_3_4_1.status / 100.0)
        print(f"\n--- Manual 3.4.2 Status Calculation ---")
        print(f"3.4.2 Status = {calc_3_4_0_status} × (1 - {entry_3_4_1.status}/100)")
        print(f"             = {calc_3_4_0_status} × (1 - {entry_3_4_1.status/100.0})")
        print(f"             = {calc_3_4_0_status} × {1 - entry_3_4_1.status/100.0}")
        print(f"             = {manual_3_4_2_status}")
    
    # Test 3.4.2 Status calculation
    calc_3_4_2_status = entry_3_4_2.calculate_value()
    print(f"\n3.4.2 calculated Status: {calc_3_4_2_status}")
    
    # Manual calculation for 3.4.2 Ziel (complex formula)
    calc_3_4_0_ziel = entry_3_4_0.calculate_ziel_value()
    if (calc_3_4_2_status and calc_3_4_0_status and calc_3_4_0_ziel and 
        entry_3_4_1.status and entry_3_4_1.ziel and 
        entry_3_4_1.status != 100 and calc_3_4_0_status != 0):
        
        print(f"\n--- Manual 3.4.2 Ziel Calculation ---")
        print(f"3.4.2 Ziel = 3.4.2(Status) × ((1 - 3.4.1(Ziel)/100) / (1 - 3.4.1(Status)/100)) × (3.4.0(Ziel) / 3.4.0(Status))")
        
        efficiency_ratio = (1 - entry_3_4_1.ziel / 100.0) / (1 - entry_3_4_1.status / 100.0)
        consumption_ratio = calc_3_4_0_ziel / calc_3_4_0_status
        manual_3_4_2_ziel = calc_3_4_2_status * efficiency_ratio * consumption_ratio
        
        print(f"Efficiency ratio:  (1 - {entry_3_4_1.ziel}/100) / (1 - {entry_3_4_1.status}/100) = {efficiency_ratio:.6f}")
        print(f"Consumption ratio: {calc_3_4_0_ziel} / {calc_3_4_0_status} = {consumption_ratio:.6f}")
        print(f"Final calculation: {calc_3_4_2_status} × {efficiency_ratio:.6f} × {consumption_ratio:.6f} = {manual_3_4_2_ziel}")
    
    # Test 3.4.2 Ziel calculation
    calc_3_4_2_ziel = entry_3_4_2.calculate_ziel_value()
    print(f"\n3.4.2 calculated Ziel: {calc_3_4_2_ziel}")

def show_3_4_complete():
    """Show complete 3.4.x structure"""
    print("\n\n=== COMPLETE 3.4.x STRUCTURE ===")
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
        
        print(f"{entry.code:8} {entry.category:50} {calc_status:8} {status_display} | {ziel_display}")

if __name__ == '__main__':
    test_3_4_2_formulas()
    show_3_4_complete()
    print("\n✓ 3.4.2 formula testing completed!")