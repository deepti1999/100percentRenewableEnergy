#!/usr/bin/env python3
"""Iteratively balance Gebäudewärme by adjusting Tiefengeothermie (8.2) until gap is ~0."""

import sqlite3
import subprocess
import os

os.chdir('/Users/deeptimaheedharan/Desktop/pypsa implementation')

def get_gap_and_82():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    cursor.execute("SELECT ziel FROM simulator_verbrauchdata WHERE code = '2.10'")
    demand = cursor.fetchone()[0]
    
    cursor.execute("SELECT target_value FROM simulator_renewabledata WHERE code = '10.4'")
    supply = cursor.fetchone()[0]
    
    cursor.execute("SELECT target_value FROM simulator_renewabledata WHERE code = '8.2'")
    current_82 = cursor.fetchone()[0]
    
    conn.close()
    return demand, supply, current_82

def update_82(new_value):
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute("UPDATE simulator_renewabledata SET target_value = ? WHERE code = '8.2'", (new_value,))
    conn.commit()
    conn.close()

def recalculate():
    result = subprocess.run([
        'python3', 'manage.py', 'shell', '-c',
        'from simulator.recalc_service import full_chain_recalc; full_chain_recalc(verbose=False)'
    ], capture_output=True, text=True)
    return result.returncode == 0

# Iteratively balance
print('='*60)
print('ITERATIVE HEAT BALANCE')
print('='*60)

max_iterations = 10
tolerance = 10  # GWh/a

for i in range(max_iterations):
    demand, supply, current_82 = get_gap_and_82()
    gap = demand - supply
    
    print(f'\nIteration {i+1}:')
    print(f'  Demand: {demand:,.2f} GWh/a')
    print(f'  Supply: {supply:,.2f} GWh/a')
    print(f'  Gap: {gap:,.2f} GWh/a')
    print(f'  8.2: {current_82:,.2f} GWh/a')
    
    if abs(gap) <= tolerance:
        print(f'\n✅ BALANCED! Gap is within tolerance ({tolerance} GWh/a)')
        break
    
    # Adjust 8.2
    new_82 = current_82 + gap
    if new_82 < 0:
        new_82 = 0
        print('  Warning: 8.2 would be negative, setting to 0')
    
    update_82(new_82)
    print(f'  Updated 8.2 to: {new_82:,.2f} GWh/a')
    
    # Recalculate
    print('  Recalculating...')
    recalculate()

# Final check
demand, supply, current_82 = get_gap_and_82()
gap = demand - supply

print('\n' + '='*60)
print('FINAL RESULT')
print('='*60)
print(f'Demand: {demand:,.2f} GWh/a')
print(f'Supply: {supply:,.2f} GWh/a')
print(f'Gap: {gap:,.2f} GWh/a ({gap/demand*100:.4f}%)')
print(f'8.2 Tiefengeothermie: {current_82:,.2f} GWh/a')
