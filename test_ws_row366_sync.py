#!/usr/bin/env python
"""
Test to verify that row 366 stromverbr and stromverbr_raumwaerm_korr are synced
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
print("TEST: Row 366 Column Synchronization")
print("="*80)

# Check initial state
print("\n1. Initial state of row 366...")
row_366 = WSData.objects.get(tag_im_jahr=366)
initial_stromverbr = row_366.stromverbr or 0
initial_stromverbr_korr = row_366.stromverbr_raumwaerm_korr or 0
initial_ladezustand = row_366.ladezustand_netto or 0
print(f"   stromverbr: {initial_stromverbr:,.2f} GWh")
print(f"   stromverbr_raumwaerm_korr: {initial_stromverbr_korr:,.2f} GWh")
print(f"   Difference: {abs(initial_stromverbr - initial_stromverbr_korr):,.2f} GWh")
print(f"   ladezustand_netto: {initial_ladezustand:,.2f} GWh")

# Run balance energy
print("\n2. Running balance_energy...")
result = _balance_energy_core(driver="solar", energy_tolerance=1.0, max_iter=5)
print(f"   ✅ Complete")

# Check final state
print("\n3. Final state of row 366...")
row_366.refresh_from_db()
final_stromverbr = row_366.stromverbr or 0
final_stromverbr_korr = row_366.stromverbr_raumwaerm_korr or 0
final_ladezustand = row_366.ladezustand_netto or 0
print(f"   stromverbr: {final_stromverbr:,.2f} GWh")
print(f"   stromverbr_raumwaerm_korr: {final_stromverbr_korr:,.2f} GWh")
print(f"   Difference: {abs(final_stromverbr - final_stromverbr_korr):,.2f} GWh")
print(f"   ladezustand_netto: {final_ladezustand:,.2f} GWh")

# Verification
print("\n4. Verification...")
columns_synced = abs(final_stromverbr - final_stromverbr_korr) < 1.0
ws_balanced = abs(final_ladezustand) < 10.0

if columns_synced and ws_balanced:
    print(f"   ✅ ALL CHECKS PASSED!")
    print(f"      - Row 366 columns synced (diff < 1 GWh)")
    print(f"      - WS balanced (ladezustand < 10 GWh)")
elif columns_synced:
    print(f"   ⚠️  Columns synced but WS not balanced")
    print(f"      - ladezustand: {final_ladezustand:,.2f} GWh")
elif ws_balanced:
    print(f"   ⚠️  WS balanced but columns NOT synced!")
    print(f"      - Column difference: {abs(final_stromverbr - final_stromverbr_korr):,.2f} GWh")
else:
    print(f"   ❌ BOTH CHECKS FAILED")
    print(f"      - Column difference: {abs(final_stromverbr - final_stromverbr_korr):,.2f} GWh")
    print(f"      - ladezustand: {final_ladezustand:,.2f} GWh")

print("\n" + "="*80)
