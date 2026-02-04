#!/usr/bin/env python3
"""
Verify 3.4.2 calculations step by step
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import VerbrauchData

def verify_calculations():
    print("=== STEP-BY-STEP VERIFICATION ===")
    
    # Get values
    val_3_4_0_status = 334903.185
    val_3_4_0_ziel = 132752.5900773
    val_3_4_1_status = 86.0
    val_3_4_1_ziel = 88.0
    
    print(f"Input values:")
    print(f"  3.4.0 Status: {val_3_4_0_status}")
    print(f"  3.4.0 Ziel:   {val_3_4_0_ziel}")
    print(f"  3.4.1 Status: {val_3_4_1_status}%")
    print(f"  3.4.1 Ziel:   {val_3_4_1_ziel}%")
    print()
    
    # Formula 1: 3.4.2 (Status) = 3.4.0(Status) × (1 - 3.4.1(Status)/100)
    status_calc = val_3_4_0_status * (1 - val_3_4_1_status/100)
    print(f"Formula 1: 3.4.2 (Status) = 3.4.0(Status) × (1 - 3.4.1(Status)/100)")
    print(f"         = {val_3_4_0_status} × (1 - {val_3_4_1_status}/100)")
    print(f"         = {val_3_4_0_status} × {1 - val_3_4_1_status/100}")
    print(f"         = {status_calc}")
    print()
    
    # Formula 2 components
    efficiency_ratio = (1 - val_3_4_1_ziel/100) / (1 - val_3_4_1_status/100)
    consumption_ratio = val_3_4_0_ziel / val_3_4_0_status
    
    print(f"Formula 2: 3.4.2(Ziel) = 3.4.2(Status) × efficiency_ratio × consumption_ratio")
    print(f"Efficiency ratio = (1 - 3.4.1(Ziel)/100) / (1 - 3.4.1(Status)/100)")
    print(f"                 = (1 - {val_3_4_1_ziel}/100) / (1 - {val_3_4_1_status}/100)")
    print(f"                 = {1 - val_3_4_1_ziel/100:.6f} / {1 - val_3_4_1_status/100:.6f}")
    print(f"                 = {efficiency_ratio:.6f}")
    print()
    print(f"Consumption ratio = 3.4.0(Ziel) / 3.4.0(Status)")
    print(f"                  = {val_3_4_0_ziel} / {val_3_4_0_status}")
    print(f"                  = {consumption_ratio:.6f}")
    print()
    
    ziel_calc = status_calc * efficiency_ratio * consumption_ratio
    print(f"3.4.2(Ziel) = {status_calc} × {efficiency_ratio:.6f} × {consumption_ratio:.6f}")
    print(f"            = {ziel_calc:.6f}")
    print()
    
    # Compare with actual calculations
    entry_3_4_2 = VerbrauchData.objects.get(code='3.4.2')
    actual_status = entry_3_4_2.calculate_value()
    actual_ziel = entry_3_4_2.calculate_ziel_value()
    
    print(f"VERIFICATION:")
    print(f"Manual Status calc: {status_calc}")
    print(f"Actual Status calc: {actual_status}")
    print(f"Match: {abs(status_calc - actual_status) < 0.001}")
    print()
    print(f"Manual Ziel calc:   {ziel_calc:.6f}")
    print(f"Actual Ziel calc:   {actual_ziel}")
    print(f"Match: {abs(ziel_calc - actual_ziel) < 0.001}")

if __name__ == '__main__':
    verify_calculations()
    print("\n✓ Verification completed!")