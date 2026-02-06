#!/usr/bin/env python3
"""Check which heat sources are connected to LandUse."""

import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

print('='*80)
print('CHECKING WHICH HEAT SOURCES ARE CONNECTED TO LANDUSE')
print('='*80)
print()

# Check formulas that reference LandUse
heat_sources = [
    ('1.1.1.1.2', 'Solarthermie Dach'),
    ('4.4.2', 'Solarthermie Freifläche GW'),
    ('7.1.2.3', 'Wärmepumpe Luft'),
    ('7.1.4.3', 'Wärmepumpe Erdreich'),
    ('8.2', 'Tiefengeothermie'),
    ('9.3.2.1', 'Sonstige Wärme'),
]

for code, desc in heat_sources:
    cursor.execute('SELECT code, name, formula, target_value FROM simulator_renewabledata WHERE code = ?', (code,))
    row = cursor.fetchone()
    if row:
        formula = row[2] if row[2] else 'NO FORMULA (direct input)'
        target = row[3] if row[3] else 0
        has_landuse = 'LandUse' in str(formula) or 'LU_' in str(formula)
        print(f'{code}: {desc}')
        print(f'   Target: {target:,.2f} GWh/a')
        print(f'   Formula: {formula[:80]}')
        print(f'   Connected to LandUse: {"YES" if has_landuse else "NO - Direct Input"}')
        print()

print('='*80)
print('SOLARTHERMIE SECTION (1.1.1 and 4.x)')
print('='*80)

# Check Solarthermie Dach connection
cursor.execute("SELECT code, name, formula, target_value FROM simulator_renewabledata WHERE code LIKE '1.1.1%' ORDER BY code")
print('\nSOLARTHERMIE DACH (1.1.1.x):')
for row in cursor.fetchall():
    formula = row[2][:60] if row[2] else 'Direct'
    target = row[3] if row[3] else 0
    print(f'  {row[0]}: {row[1][:35]} = {target:,.2f}')
    if 'LandUse' in str(row[2]):
        print(f'      -> Uses LandUse!')

# Check Solarthermie Freifläche
cursor.execute("SELECT code, name, formula, target_value FROM simulator_renewabledata WHERE code LIKE '4.1%' OR code LIKE '4.4%' ORDER BY code")
print('\nSOLARTHERMIE FREIFLÄCHE (4.x):')
for row in cursor.fetchall()[:20]:
    formula = row[2][:60] if row[2] else 'Direct'
    target = row[3] if row[3] else 0
    has_lu = 'LandUse' in str(row[2]) if row[2] else False
    marker = ' <- USES LANDUSE!' if has_lu else ''
    print(f'  {row[0]}: {row[1][:40]} = {target:,.2f}{marker}')

print()
print('='*80)
print('LANDUSE ENTRIES FOR SOLARTHERMIE')
print('='*80)

cursor.execute("SELECT code, name, status_ha, target_ha FROM simulator_landuse WHERE name LIKE '%Solar%' OR name LIKE '%Thermie%' ORDER BY code")
for row in cursor.fetchall():
    print(f'{row[0]}: {row[1]}')
    print(f'   Status: {row[2]:,.0f} ha  |  Ziel: {row[3]:,.0f} ha')

conn.close()
