#!/usr/bin/env python3
"""Analyze Gebäudewärme supply structure and how to close the gap."""

import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

print('='*80)
print('GEBÄUDEWÄRME SUPPLY STRUCTURE')
print('='*80)
print()
print('Formula: 10.4 = 10.4.1 (Brennstoffe) + 10.4.2 (Wärme) + 10.4.3 (Strom)')
print()

# 10.4 and its components
for code in ['10.4', '10.4.1', '10.4.2', '10.4.3']:
    cursor.execute('SELECT code, name, target_value, formula FROM simulator_renewabledata WHERE code = ?', (code,))
    row = cursor.fetchone()
    if row:
        val = row[2] if row[2] else 0
        formula = row[3][:80] if row[3] else 'No formula'
        print(f'{row[0]}: {row[1][:50]} = {val:,.2f} GWh/a')
        print(f'   Formula: {formula}')
        print()

print()
print('='*80)
print('10.4.2 (Wärme) - HEAT SOURCES FOR GEBÄUDEWÄRME')
print('='*80)
cursor.execute("SELECT code, name, target_value, formula FROM simulator_renewabledata WHERE code = '10.4.2'")
row = cursor.fetchone()
if row:
    print(f'Full Formula: {row[3]}')
    print()

# Check each source mentioned in the formula
print('Individual Heat Sources:')
print('-'*80)
sources = [
    ('1.1.1.1.2', 'Solarthermie Dach'),
    ('7.1.2.3', 'Wärmepumpe Luft - Wärmegewinn'),
    ('7.1.4.3', 'Wärmepumpe Erdreich - Wärmegewinn'),
    ('5.4.2.4', 'Biogas Wärme'),
    ('6.1.3.2.4', 'Biomasse Wärme'),
    ('8.2', 'Tiefengeothermie Wärme'),
    ('4.4.2', 'Solarthermie Freifläche für GW'),
    ('9.3.2.1', 'Sonstige Wärme'),
]

total = 0
for code, desc in sources:
    cursor.execute('SELECT code, name, target_value FROM simulator_renewabledata WHERE code = ?', (code,))
    row = cursor.fetchone()
    if row:
        val = row[2] if row[2] else 0
        total += val
        print(f'{code}: {row[1][:45]:<45} = {val:>12,.2f} GWh/a')
    else:
        print(f'{code}: NOT FOUND')

print('-'*80)
print(f'{"TOTAL":<52} = {total:>12,.2f} GWh/a')

# Check current gap
cursor.execute("SELECT ziel FROM simulator_verbrauchdata WHERE code = '2.10'")
demand = cursor.fetchone()[0]
cursor.execute("SELECT target_value FROM simulator_renewabledata WHERE code = '10.4'")
supply = cursor.fetchone()[0]
gap = demand - supply

print()
print('='*80)
print('GAP ANALYSIS')
print('='*80)
print(f'Gebäudewärme Demand (2.10):  {demand:>15,.2f} GWh/a')
print(f'Gebäudewärme Supply (10.4):  {supply:>15,.2f} GWh/a')
print(f'GAP:                         {gap:>15,.2f} GWh/a')
print()

print('='*80)
print('OPTIONS TO CLOSE THE GAP')
print('='*80)

# Check 8.2 Tiefengeothermie
cursor.execute("SELECT code, name, target_value FROM simulator_renewabledata WHERE code = '8.2'")
row = cursor.fetchone()
tiefengeo = row[2] if row else 0

# Check 4.4.2 Solarthermie Freifläche
cursor.execute("SELECT code, name, target_value FROM simulator_renewabledata WHERE code = '4.4.2'")
row = cursor.fetchone()
solar_ff = row[2] if row else 0

print()
print(f'Option 1: Increase Tiefengeothermie (8.2)')
print(f'   Current: {tiefengeo:,.2f} GWh/a')
print(f'   Needed:  {tiefengeo + gap:,.2f} GWh/a  (increase by {gap:,.2f})')
print()
print(f'Option 2: Increase Solarthermie Freifläche für GW (4.4.2)')
print(f'   Current: {solar_ff:,.2f} GWh/a')
print(f'   Needed:  {solar_ff + gap:,.2f} GWh/a  (increase by {gap:,.2f})')
print()

# Check 9.3.2.1
cursor.execute("SELECT code, name, target_value FROM simulator_renewabledata WHERE code = '9.3.2.1'")
row = cursor.fetchone()
sonstige = row[2] if row else 0
print(f'Option 3: Increase Sonstige Wärme (9.3.2.1)')
print(f'   Current: {sonstige:,.2f} GWh/a')
print(f'   Needed:  {sonstige + gap:,.2f} GWh/a  (increase by {gap:,.2f})')

conn.close()
