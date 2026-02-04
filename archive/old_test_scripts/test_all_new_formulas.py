#!/usr/bin/env python3
"""
Test all the new formulas:
3.4.3, 3.4.4, 3.5.0, 3.6, 3.6.0
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import VerbrauchData

def test_all_new_formulas():
    """Test all new formulas"""
    print("=== TESTING ALL NEW FORMULAS ===")
    
    # Get all relevant entries
    codes_to_test = ['3.3', '3.4', '3.4.2', '3.4.3', '3.4.4', '3.5', '3.5.0', '3.6', '3.6.0']
    
    print("\n--- Current Values ---")
    for code in codes_to_test:
        entry = VerbrauchData.objects.filter(code=code).first()
        if entry:
            calc_status = '[CALC]' if entry.is_calculated else '[FIXED]'
            
            if entry.is_calculated:
                status_calc = entry.calculate_value()
                ziel_calc = entry.calculate_ziel_value()
                status_display = f"{status_calc:>10.3f}" if status_calc is not None else "None"
                ziel_display = f"{ziel_calc:>10.3f}" if ziel_calc is not None else "None"
            else:
                status_display = f"{entry.status:>10}" if entry.status else "None"
                ziel_display = f"{entry.ziel:>10}" if entry.ziel else "None"
            
            print(f"{code:8} {calc_status:8} {status_display} | {ziel_display}")
        else:
            print(f"{code:8} NOT FOUND")
    
    print("\n--- Formula Verification ---")
    
    # Get base values for manual verification
    entry_3_3 = VerbrauchData.objects.get(code='3.3')
    entry_3_4 = VerbrauchData.objects.get(code='3.4')
    entry_3_4_2 = VerbrauchData.objects.get(code='3.4.2')
    entry_3_5 = VerbrauchData.objects.get(code='3.5')
    
    calc_3_3_status = entry_3_3.calculate_value()
    calc_3_3_ziel = entry_3_3.calculate_ziel_value()
    calc_3_4_2_status = entry_3_4_2.calculate_value()
    calc_3_4_2_ziel = entry_3_4_2.calculate_ziel_value()
    
    print(f"Base values:")
    print(f"  3.3 Status/Ziel: {calc_3_3_status:.3f} / {calc_3_3_ziel:.3f}")
    print(f"  3.4 Status/Ziel: {entry_3_4.status} / {entry_3_4.ziel}")
    print(f"  3.4.2 Status/Ziel: {calc_3_4_2_status:.3f} / {calc_3_4_2_ziel:.3f}")
    print(f"  3.5 Status/Ziel: {entry_3_5.status} / {entry_3_5.ziel}")
    
    # Manual calculations
    print(f"\nManual calculations:")
    
    # 3.4.3
    manual_3_4_3_status = 0.0  # 3.4.2 - 3.4.2 = 0
    manual_3_4_3_ziel = calc_3_4_2_status - calc_3_4_2_ziel
    print(f"3.4.3 Status: 0 (formula seems to be 3.4.2 - 3.4.2)")
    print(f"3.4.3 Ziel: {calc_3_4_2_status:.3f} - {calc_3_4_2_ziel:.3f} = {manual_3_4_3_ziel:.3f}")
    
    # 3.5.0
    manual_3_5_0_status = calc_3_3_status * (entry_3_5.status / 100.0) if entry_3_5.status else 0
    manual_3_5_0_ziel = calc_3_3_ziel * (entry_3_5.ziel / 100.0) if entry_3_5.ziel else 0
    print(f"3.5.0 Status: {calc_3_3_status:.3f} × {entry_3_5.status}% = {manual_3_5_0_status:.3f}")
    print(f"3.5.0 Ziel: {calc_3_3_ziel:.3f} × {entry_3_5.ziel}% = {manual_3_5_0_ziel:.3f}")
    
    # 3.6
    manual_3_6_status = 100.0 - entry_3_4.status - entry_3_5.status - manual_3_4_3_status
    manual_3_6_ziel = 100.0 - entry_3_4.ziel - entry_3_5.ziel - (manual_3_4_3_ziel * entry_3_4.ziel / 100.0) if entry_3_5.ziel else None
    print(f"3.6 Status: 100 - {entry_3_4.status} - {entry_3_5.status} - {manual_3_4_3_status} = {manual_3_6_status}")
    if manual_3_6_ziel:
        print(f"3.6 Ziel: 100 - {entry_3_4.ziel} - {entry_3_5.ziel} - ({manual_3_4_3_ziel:.3f} × {entry_3_4.ziel}%) = {manual_3_6_ziel:.3f}")
    
    # Test actual calculations
    print(f"\nActual calculations:")
    for code in ['3.4.3', '3.4.4', '3.5.0', '3.6', '3.6.0']:
        entry = VerbrauchData.objects.filter(code=code).first()
        if entry and entry.is_calculated:
            status_calc = entry.calculate_value()
            ziel_calc = entry.calculate_ziel_value()
            print(f"{code} Status/Ziel: {status_calc} / {ziel_calc}")

if __name__ == '__main__':
    test_all_new_formulas()
    print("\n✓ All new formulas tested!")