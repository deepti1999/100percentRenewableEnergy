#!/usr/bin/env python
"""
Check all pages for missing formulas in database
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData, VerbrauchData, LandUse, WSData, Formula

print('=' * 70)
print('DATABASE FORMULA COVERAGE CHECK - ALL PAGES')
print('=' * 70)

# 1. RENEWABLE DATA
print('\n1. RENEWABLE ENERGY PAGE')
print('-' * 70)
renewable_calculated = RenewableData.objects.filter(is_calculated=True).order_by('code')
renewable_missing = []
for entry in renewable_calculated:
    formula = Formula.objects.filter(category='renewable', key=entry.code).first()
    if not formula:
        renewable_missing.append(entry.code)

print(f'Total calculated entries: {renewable_calculated.count()}')
print(f'Total formulas in DB: {Formula.objects.filter(category="renewable").count()}')
if renewable_missing:
    print(f'❌ Missing {len(renewable_missing)} formulas:')
    for code in renewable_missing[:10]:
        print(f'   - {code}')
    if len(renewable_missing) > 10:
        print(f'   ... and {len(renewable_missing) - 10} more')
else:
    print('✅ All renewable calculated entries have formulas')

# 2. VERBRAUCH DATA
print('\n2. VERBRAUCH (CONSUMPTION) PAGE')
print('-' * 70)
verbrauch_calculated = VerbrauchData.objects.filter(is_calculated=True).order_by('code')
verbrauch_missing = []
for entry in verbrauch_calculated:
    formula_keys = [f'V_{entry.code}', f'VERBRAUCH_{entry.code.replace(".", "_")}']
    formula = Formula.objects.filter(category='verbrauch', key__in=formula_keys).first()
    if not formula:
        verbrauch_missing.append(entry.code)

print(f'Total calculated entries: {verbrauch_calculated.count()}')
print(f'Total formulas in DB: {Formula.objects.filter(category="verbrauch").count()}')
if verbrauch_missing:
    print(f'❌ Missing {len(verbrauch_missing)} formulas:')
    for code in verbrauch_missing[:10]:
        print(f'   - {code}')
    if len(verbrauch_missing) > 10:
        print(f'   ... and {len(verbrauch_missing) - 10} more')
else:
    print('✅ All verbrauch calculated entries have formulas')

# 3. LANDUSE DATA
print('\n3. LANDUSE PAGE')
print('-' * 70)
landuse_calculated = LandUse.objects.filter(is_calculated=True).order_by('code')
landuse_missing = []
for entry in landuse_calculated:
    formula = Formula.objects.filter(category='landuse', key=entry.code).first()
    if not formula:
        landuse_missing.append(entry.code)

print(f'Total calculated entries: {landuse_calculated.count()}')
print(f'Total formulas in DB: {Formula.objects.filter(category="landuse").count()}')
if landuse_missing:
    print(f'❌ Missing {len(landuse_missing)} formulas:')
    for code in landuse_missing[:10]:
        print(f'   - {code}')
    if len(landuse_missing) > 10:
        print(f'   ... and {len(landuse_missing) - 10} more')
else:
    print('✅ All landuse calculated entries have formulas')

# 4. WS (ENERGY STORAGE) DATA
print('\n4. WS (ENERGY STORAGE) PAGE')
print('-' * 70)
ws_entries = WSData.objects.filter(row_number__in=[366, 367]).order_by('row_number')
ws_formulas = Formula.objects.filter(category='ws')
print(f'WS special rows (366, 367): {ws_entries.count()}')
print(f'Total WS formulas in DB: {ws_formulas.count()}')
if ws_formulas.count() > 0:
    print('✅ WS formulas exist in database')
    print(f'   Formula keys: {[f.key for f in ws_formulas[:5]]}...')
else:
    print('❌ No WS formulas in database')

# SUMMARY
print('\n' + '=' * 70)
print('SUMMARY')
print('=' * 70)
total_missing = len(renewable_missing) + len(verbrauch_missing) + len(landuse_missing)
if total_missing == 0 and ws_formulas.count() > 0:
    print('✅ ALL PAGES: Complete formula coverage in database')
else:
    print(f'❌ TOTAL MISSING: {total_missing} formulas across all pages')
    if renewable_missing:
        print(f'   - Renewable: {len(renewable_missing)} missing')
    if verbrauch_missing:
        print(f'   - Verbrauch: {len(verbrauch_missing)} missing')
    if landuse_missing:
        print(f'   - LandUse: {len(landuse_missing)} missing')
    if ws_formulas.count() == 0:
        print(f'   - WS: No formulas')

print(f'\nTotal formulas in database: {Formula.objects.count()}')
print('\n' + '=' * 70)
print('CHECKING MANAGEMENT COMMANDS FOR PERMANENT IMPORT')
print('=' * 70)

import os
cmd_dir = 'simulator/management/commands'
if os.path.exists(cmd_dir):
    commands = [f for f in os.listdir(cmd_dir) if f.startswith('import_') and f.endswith('.py')]
    print(f'\nFound {len(commands)} import commands:')
    for cmd in sorted(commands):
        print(f'   ✓ {cmd}')
    print('\n✅ Formulas can be re-imported using these management commands')
else:
    print('❌ Management commands directory not found')
