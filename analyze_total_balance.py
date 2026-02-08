#!/usr/bin/env python3
"""
Analyze total energy balance and adjust solar to match demand exactly.
This adjusts LandUse solar area to balance total energy.
"""

import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

print('='*70)
print('TOTAL ENERGY BALANCE ANALYSIS')
print('='*70)

# Get total energy demand from Verbrauch (code 8)
cursor.execute("SELECT code, category, ziel FROM simulator_verbrauchdata WHERE code = '8'")
row = cursor.fetchone()
total_demand = row[2] if row else 0
print(f'Total Energy Demand (code 8): {total_demand:,.2f} GWh/a')

# Get total renewable supply (10.1)
cursor.execute("SELECT code, name, target_value FROM simulator_renewabledata WHERE code = '10.1'")
row = cursor.fetchone()
total_renewable = row[2] if row else 0
print(f'Total Renewable Supply (10.1): {total_renewable:,.2f} GWh/a')

print()
print('='*70)
print('DEMAND BY SECTOR')
print('='*70)

sectors = [('1.4', 'KLIK (Kraft/Licht)'), ('2.10', 'Gebäudewärme'), ('3.7', 'Prozesswärme'), ('6.0', 'Mobile')]
total_d = 0
for code, name in sectors:
    cursor.execute('SELECT ziel FROM simulator_verbrauchdata WHERE code = ?', (code,))
    row = cursor.fetchone()
    val = row[0] if row else 0
    total_d += val
    print(f'{name}: {val:,.2f} GWh/a')
print(f'TOTAL: {total_d:,.2f} GWh/a')

print()
print('='*70)
print('SUPPLY BY SECTOR (Renewable 10.x)')
print('='*70)

sectors_supply = [('10.3', 'KLIK'), ('10.4', 'Gebäudewärme'), ('10.5', 'Prozesswärme'), ('10.6', 'Mobile')]
total_s = 0
for code, name in sectors_supply:
    cursor.execute('SELECT target_value FROM simulator_renewabledata WHERE code = ?', (code,))
    row = cursor.fetchone()
    val = row[0] if row else 0
    total_s += val
    print(f'{name} ({code}): {val:,.2f} GWh/a')
print(f'TOTAL: {total_s:,.2f} GWh/a')

print()
print('='*70)
print('SOLAR CONTRIBUTION')
print('='*70)

# Get current solar values
cursor.execute("SELECT code, name, target_value FROM simulator_renewabledata WHERE code IN ('1.1.2.1.2', '1.2.1.2') ORDER BY code")
for row in cursor.fetchall():
    print(f'{row[0]}: {row[1][:40]} = {row[2]:,.2f} GWh/a')

# Total solar
cursor.execute("SELECT target_value FROM simulator_renewabledata WHERE code = '1.1.2.1.2'")
solar_roof = cursor.fetchone()[0] or 0
cursor.execute("SELECT target_value FROM simulator_renewabledata WHERE code = '1.2.1.2'")
solar_field = cursor.fetchone()[0] or 0
total_solar = solar_roof + solar_field
print(f'TOTAL SOLAR: {total_solar:,.2f} GWh/a')

print()
print('='*70)
print('LANDUSE SOLAR AREAS')
print('='*70)

cursor.execute("SELECT code, name, target_ha FROM simulator_landuse WHERE code IN ('LU_1.1', 'LU_2.1') ORDER BY code")
for row in cursor.fetchall():
    print(f'{row[0]}: {row[1]} = {row[2]:,.2f} ha')

# Get current LU_2.1 (Solare Freiflächen)
cursor.execute("SELECT target_ha FROM simulator_landuse WHERE code = 'LU_2.1'")
lu_21_ha = cursor.fetchone()[0] or 0

print()
gap = total_d - total_s
print(f'='*70)
print(f'TOTAL GAP (Demand - Supply): {gap:,.2f} GWh/a')
print(f'='*70)

# Calculate how much to adjust solar field (LU_2.1)
# Solar field energy yield: 1.2.1.1 = 1235.33 MWh/ha/a
cursor.execute("SELECT target_value FROM simulator_renewabledata WHERE code = '1.2.1.1'")
solar_yield = cursor.fetchone()[0] or 1235.33  # MWh/ha/a

# To close gap, we need to add: gap GWh = gap * 1000 MWh
# ha_needed = (gap * 1000) / solar_yield
if gap != 0:
    ha_adjustment = (gap * 1000) / solar_yield
    new_lu_21 = lu_21_ha + ha_adjustment
    
    print()
    print(f'To close gap of {gap:,.2f} GWh:')
    print(f'  Solar yield: {solar_yield:,.2f} MWh/ha/a')
    print(f'  Need to adjust LU_2.1 by: {ha_adjustment:,.2f} ha')
    print(f'  Current LU_2.1: {lu_21_ha:,.2f} ha')
    print(f'  New LU_2.1: {new_lu_21:,.2f} ha')
else:
    print('Gap is zero - already balanced!')

conn.close()
