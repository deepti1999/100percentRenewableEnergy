#!/usr/bin/env python3
"""Analyze the Gebäudewärme (building heat) gap between demand and supply."""

import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

print('='*80)
print('ENERGY BALANCE ANALYSIS - GEBÄUDEWÄRME GAP')
print('='*80)

# Get Gebäudewärme demand (2.10 or 2.6)
cursor.execute("SELECT code, category, ziel FROM simulator_verbrauchdata WHERE code = '2.10'")
row = cursor.fetchone()
gw_demand = row[2] if row else 0
print(f'\nGebäudewärme Demand (2.10): {gw_demand:.2f} GWh/a')

# Get Gebäudewärme supply from renewable (10.4)
cursor.execute("SELECT code, name, target_value FROM simulator_renewabledata WHERE code = '10.4'")
row = cursor.fetchone()
gw_supply = row[2] if row else 0
print(f'Gebäudewärme Supply (10.4): {gw_supply:.2f} GWh/a')

gap = gw_demand - gw_supply
print(f'\n*** Gebäudewärme GAP: {gap:.2f} GWh/a ***')
print(f'Gap percentage: {(gap/gw_demand)*100:.1f}%')

print('\n' + '='*80)
print('HEAT SUPPLY BREAKDOWN (10.4.x)')
print('='*80)

cursor.execute("SELECT code, name, target_value FROM simulator_renewabledata WHERE code LIKE '10.4%' ORDER BY code")
for row in cursor.fetchall():
    val = row[2] if row[2] else 0
    print(f'{row[0]}: {row[1][:50]} = {val:.2f}')

print('\n' + '='*80)
print('ALL HEAT PRODUCTION SOURCES')
print('='*80)

# Solarthermie
cursor.execute("SELECT code, name, target_value FROM simulator_renewabledata WHERE code = '1.1.1.1.2'")
row = cursor.fetchone()
solarthermie = row[2] if row else 0
print(f'\n1. Solarthermie Dach (1.1.1.1.2): {solarthermie:.2f} GWh/a')

# Check for Solarthermie Freiflächen (4.x)
cursor.execute("SELECT code, name, target_value FROM simulator_renewabledata WHERE code LIKE '4.1%' AND (name LIKE '%Thermie%' OR name LIKE '%Wärme%') ORDER BY code")
rows = cursor.fetchall()
print('\n2. Solarthermie Freiflächen:')
for row in rows[:5]:
    val = row[2] if row[2] else 0
    print(f'   {row[0]}: {row[1][:40]} = {val:.2f}')

# Geothermie
cursor.execute("SELECT code, name, target_value FROM simulator_renewabledata WHERE code LIKE '7%' ORDER BY code")
rows = cursor.fetchall()
print('\n3. Geothermie:')
for row in rows[:10]:
    val = row[2] if row[2] else 0
    print(f'   {row[0]}: {row[1][:40]} = {val:.2f}')

# Abwärme
cursor.execute("SELECT code, name, target_value FROM simulator_renewabledata WHERE code LIKE '8%' ORDER BY code")
rows = cursor.fetchall()
print('\n4. Abwärme (Waste Heat):')
for row in rows[:10]:
    val = row[2] if row[2] else 0
    print(f'   {row[0]}: {row[1][:40]} = {val:.2f}')

# Wärmepumpen (heat pumps - from electricity)
cursor.execute("SELECT code, category, ziel FROM simulator_verbrauchdata WHERE code = '2.9.0'")
row = cursor.fetchone()
wp_strom = row[2] if row else 0
print(f'\n5. Wärmepumpen Stromverbrauch (2.9.0): {wp_strom:.2f} GWh/a')
print(f'   (With typical COP of 3.5, this provides ~{wp_strom * 3.5:.2f} GWh/a heat)')

# Biomass for Gebäudewärme
cursor.execute("SELECT code, name, target_value FROM simulator_renewabledata WHERE code LIKE '4.3%' ORDER BY code")
rows = cursor.fetchall()
print('\n6. Biomasse für Gebäudewärme:')
for row in rows[:5]:
    val = row[2] if row[2] else 0
    print(f'   {row[0]}: {row[1][:40]} = {val:.2f}')

print('\n' + '='*80)
print('POTENTIAL SOLUTIONS TO CLOSE THE GAP')
print('='*80)

print(f'''
Current Gap: {gap:.2f} GWh/a ({(gap/gw_demand)*100:.1f}% of demand)

Options to balance Gebäudewärme:

1. INCREASE SOLARTHERMIE
   - Increase solar thermal roof area (1.1.1.1)
   - Current: {solarthermie:.2f} GWh/a
   
2. INCREASE WÄRMEPUMPEN (Heat Pumps)
   - Increase the share of heat pumps for Gebäudewärme
   - Current electricity for WP: {wp_strom:.2f} GWh/a
   - This requires more electricity production!
   
3. INCREASE GEOTHERMIE
   - Increase deep geothermal (Tiefengeothermie)
   - Increase shallow geothermal (Oberflächennahe Geothermie)
   
4. INCREASE ABWÄRME (Waste Heat)
   - Utilize industrial waste heat
   - Utilize data center waste heat
   
5. REDUCE DEMAND
   - Improve building insulation (Sanierungsrate)
   - Reduce specific heat demand per m²
   
6. INCREASE BIOMASS
   - More biomass for heating (with sustainability limits)
''')

conn.close()
