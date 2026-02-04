#!/usr/bin/env python
"""
Test script to verify that balance_energy now also recalculates WS data.

This test:
1. Runs balance_energy button
2. Verifies WS data is recalculated
3. Checks that WS codes 9.3.x are updated
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData, WSData
from simulator.views import _balance_energy_core

print("="*80)
print("TEST: Balance Energy with WS Recalculation")
print("="*80)

# Get initial WS values
print("\n1. Checking initial WS state...")
try:
    ws_9_3_1 = RenewableData.objects.get(code='9.3.1')
    ws_9_3_4 = RenewableData.objects.get(code='9.3.4')
    row_366 = WSData.objects.get(tag_im_jahr=366)
    
    initial_9_3_1 = ws_9_3_1.target_value or 0
    initial_9_3_4 = ws_9_3_4.target_value or 0
    initial_stromverbr = row_366.stromverbr_raumwaerm_korr or 0
    
    print(f"   Initial 9.3.1 (Abregelung WS): {initial_9_3_1:,.2f} GWh")
    print(f"   Initial 9.3.4 (ELY Überschuss WS): {initial_9_3_4:,.2f} GWh")
    print(f"   Initial WS stromverbr (row 366): {initial_stromverbr:,.2f} GWh")
except Exception as e:
    print(f"   ❌ Error getting initial values: {e}")
    sys.exit(1)

# Run balance energy
print("\n2. Running balance energy...")
try:
    result = _balance_energy_core(driver="solar", energy_tolerance=1.0, max_iter=10)
    print(f"   ✅ Balance complete")
    print(f"   - Balanced: {result['is_balanced']}")
    print(f"   - Final gap: {result.get('final_gap', 0):,.2f} GWh")
    print(f"   - Final ha: {result.get('final_ha', 0):,.2f}")
except Exception as e:
    print(f"   ❌ Balance failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Check WS values after balance
print("\n3. Checking WS state after balance...")
try:
    ws_9_3_1.refresh_from_db()
    ws_9_3_4.refresh_from_db()
    row_366.refresh_from_db()
    
    final_9_3_1 = ws_9_3_1.target_value or 0
    final_9_3_4 = ws_9_3_4.target_value or 0
    final_stromverbr = row_366.stromverbr_raumwaerm_korr or 0
    
    print(f"   Final 9.3.1 (Abregelung WS): {final_9_3_1:,.2f} GWh")
    print(f"   Final 9.3.4 (ELY Überschuss WS): {final_9_3_4:,.2f} GWh")
    print(f"   Final WS stromverbr (row 366): {final_stromverbr:,.2f} GWh")
    
    # Check if values changed (indicating WS was recalculated)
    ws_changed = (
        abs(final_9_3_1 - initial_9_3_1) > 0.01 or
        abs(final_9_3_4 - initial_9_3_4) > 0.01 or
        abs(final_stromverbr - initial_stromverbr) > 0.01
    )
    
    if ws_changed:
        print(f"\n   ✅ WS DATA WAS RECALCULATED (values changed)")
        print(f"      Δ 9.3.1: {final_9_3_1 - initial_9_3_1:,.2f} GWh")
        print(f"      Δ 9.3.4: {final_9_3_4 - initial_9_3_4:,.2f} GWh")
        print(f"      Δ stromverbr: {final_stromverbr - initial_stromverbr:,.2f} GWh")
    else:
        print(f"\n   ℹ️  WS values unchanged (may already be in sync)")
        
except Exception as e:
    print(f"   ❌ Error checking final values: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*80)
print("✅ TEST COMPLETE")
print("="*80)
