#!/usr/bin/env python3
"""Analyze wind structure and its connection to LandUse."""

import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

print('='*70)
print('WIND STRUCTURE ANALYSIS')
print('='*70)

# LU_5 and LU_6 Windparkfläche
print('\nLANDUSE WIND (LU_5, LU_6):')
cursor.execute("SELECT code, name, status_ha, target_ha FROM simulator_landuse WHERE code LIKE 'LU_5%' OR code LIKE 'LU_6%'")
for row in cursor.fetchall():
    print(f'{row[0]}: {row[1]}')
    print(f'   Status: {row[2]:,.2f} ha | Ziel: {row[3]:,.2f} ha')

print('\n' + '='*70)
print('WIND IN RENEWABLE DATA (2.x)')
print('='*70)

cursor.execute("SELECT code, name, target_value, formula FROM simulator_renewabledata WHERE code LIKE '2%' AND code < '3' ORDER BY code LIMIT 25")
for row in cursor.fetchall():
    val = row[2] if row[2] else 0
    formula = row[3][:60] if row[3] else 'Direct'
    has_lu = 'LandUse' in str(row[3]) if row[3] else False
    marker = ' <- USES LANDUSE!' if has_lu else ''
    print(f'{row[0]}: {row[1][:45]} = {val:,.2f}{marker}')

print('\n' + '='*70)
print('KEY WIND VALUES')
print('='*70)

# Wind total
cursor.execute("SELECT code, name, target_value FROM simulator_renewabledata WHERE code = '2.1.1.2.2'")
row = cursor.fetchone()
if row:
    print(f'{row[0]}: {row[1]} = {row[2]:,.2f} GWh/a')

cursor.execute("SELECT code, name, target_value FROM simulator_renewabledata WHERE code = '2.1.1.2.2.2'")
row = cursor.fetchone()
if row:
    print(f'{row[0]}: {row[1]} = {row[2]:,.2f} MW')

print('\n' + '='*70)
print('WS DATA WIND (windstrom row 366)')
print('='*70)

cursor.execute("SELECT tag_im_jahr, windstrom FROM simulator_wsdata WHERE tag_im_jahr = 366")
row = cursor.fetchone()
if row:
    print(f'Day {row[0]}: windstrom = {row[1]:,.2f} GWh/a (yearly total)')

print('\n' + '='*70)
print('WIND FORMULA CHAIN')
print('='*70)

# Check how windstrom is calculated
cursor.execute("SELECT key, expression FROM simulator_formula WHERE key LIKE '%windstrom%' AND category = 'ws_column'")
for row in cursor.fetchall():
    print(f'{row[0]}: {row[1][:80]}')

conn.close()
