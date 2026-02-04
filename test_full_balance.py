#!/usr/bin/env python3
"""Test full balance (energy + WS)"""
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.views import _balance_energy_core, _balance_ws_storage_core
from simulator.models import WSData, LandUse

print('=== Before Balance ===')
ws_366 = WSData.objects.get(tag_im_jahr=366)
lu_21 = LandUse.objects.get(code='LU_2.1')
print(f'LU_2.1 (Solar) target_ha = {lu_21.target_ha:,.2f}')
print(f'stromverbr_raumwaerm_korr = {ws_366.stromverbr_raumwaerm_korr:,.2f}')
print(f'ladezustand_netto = {ws_366.ladezustand_netto:,.2f}')

print()
print('=== Step 1: Balance Energy ===')
energy_result = _balance_energy_core(driver='solar', energy_tolerance=1.0)
print(f'  is_balanced: {energy_result.get("is_balanced")}')
print(f'  final_ha: {energy_result.get("final_ha"):,.2f}')
print(f'  final_gap: {energy_result.get("final_gap"):.2f}')

print()
print('=== Step 2: Balance WS Storage ===')
ws_result = _balance_ws_storage_core(ws_tolerance=10.0, max_iter=20, num_passes=1)
print(f'  is_balanced: {ws_result["is_balanced"]}')
print(f'  final_stromverbr: {ws_result["final_stromverbr"]:,.2f}')
print(f'  final_balance: {ws_result["final_balance"]:.2f}')

print()
print('=== After Balance ===')
ws_366 = WSData.objects.get(tag_im_jahr=366)
lu_21 = LandUse.objects.get(code='LU_2.1')
print(f'LU_2.1 (Solar) target_ha = {lu_21.target_ha:,.2f}')
print(f'stromverbr_raumwaerm_korr = {ws_366.stromverbr_raumwaerm_korr:,.2f}')
print(f'ladezustand_netto = {ws_366.ladezustand_netto:,.2f}')

if energy_result.get("is_balanced") and ws_result["is_balanced"]:
    print()
    print('✅ FULL BALANCE SUCCESS!')
else:
    print()
    print('❌ Balance incomplete')
    if not energy_result.get("is_balanced"):
        print('   - Energy not balanced')
    if not ws_result["is_balanced"]:
        print('   - WS storage not balanced')
