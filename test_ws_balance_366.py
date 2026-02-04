#!/usr/bin/env python
"""
Test to verify that row 366 ladezustand_netto is balanced to ~0 after balance_energy
"""

import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import WSData
from simulator.views import _balance_energy_core

print("="*80)
print("TEST: WS Row 366 ladezustand_netto Balance")
print("="*80)

# Check initial state
print("\n1. Initial state of row 366...")
row_366 = WSData.objects.get(tag_im_jahr=366)
initial_ladezustand = row_366.ladezustand_netto or 0
initial_stromverbr = row_366.stromverbr_raumwaerm_korr or 0
print(f"   Ladezustand Netto (row 366): {initial_ladezustand:,.2f} GWh")
print(f"   Stromverbr (row 366): {initial_stromverbr:,.2f} GWh")

# Run balance energy
print("\n2. Running balance_energy...")
print("   (This may take 30-60 seconds...)")
result = _balance_energy_core(driver="solar", energy_tolerance=1.0, max_iter=5)
print(f"\n   Result keys: {list(result.keys())}")
print(f"   ✅ Energy balanced: {result.get('is_balanced')}")
print(f"   Energy gap: {result.get('final_gap', 0):,.2f} GWh")
if 'ws_balanced' in result:
    print(f"   ✅ WS balanced: {result.get('ws_balanced')}")
    print(f"   WS balance value: {result.get('ws_balance_value', 0):,.2f} GWh")
else:
    print(f"   ⚠️  NO WS BALANCE INFO IN RESULT")

# Check final state
print("\n3. Final state of row 366...")
row_366.refresh_from_db()
final_ladezustand = row_366.ladezustand_netto or 0
final_stromverbr = row_366.stromverbr_raumwaerm_korr or 0
print(f"   Ladezustand Netto (row 366): {final_ladezustand:,.2f} GWh")
print(f"   Stromverbr (row 366): {final_stromverbr:,.2f} GWh")

# Check if balanced
print("\n4. Verification...")
is_balanced = abs(final_ladezustand) < 10.0  # Within 10 GWh tolerance
print(f"   Change in ladezustand: {final_ladezustand - initial_ladezustand:,.2f} GWh")
print(f"   Change in stromverbr: {final_stromverbr - initial_stromverbr:,.2f} GWh")

if is_balanced:
    print(f"\n   ✅ WS IS BALANCED! Ladezustand netto = {final_ladezustand:,.2f} GWh (< 10 GWh)")
else:
    print(f"\n   ❌ WS NOT BALANCED! Ladezustand netto = {final_ladezustand:,.2f} GWh (> 10 GWh)")

print("\n" + "="*80)
