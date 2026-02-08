#!/usr/bin/env python3
"""
Balance total energy by adjusting solar LandUse (LU_2.1).
Iteratively adjusts until total supply = total demand.
"""

import sqlite3
import subprocess
import os

os.chdir('/Users/deeptimaheedharan/Desktop/pypsa implementation')

def get_balance():
    """Get current total demand and supply."""
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    # Total demand by sector
    sectors = ['1.4', '2.10', '3.7', '6.0']
    total_demand = 0
    for code in sectors:
        cursor.execute('SELECT ziel FROM simulator_verbrauchdata WHERE code = ?', (code,))
        row = cursor.fetchone()
        if row and row[0]:
            total_demand += row[0]
    
    # Total supply by sector
    sectors_supply = ['10.3', '10.4', '10.5', '10.6']
    total_supply = 0
    for code in sectors_supply:
        cursor.execute('SELECT target_value FROM simulator_renewabledata WHERE code = ?', (code,))
        row = cursor.fetchone()
        if row and row[0]:
            total_supply += row[0]
    
    # Get LU_2.1
    cursor.execute("SELECT target_ha FROM simulator_landuse WHERE code = 'LU_2.1'")
    lu_21 = cursor.fetchone()[0] or 0
    
    # Get solar yield
    cursor.execute("SELECT target_value FROM simulator_renewabledata WHERE code = '1.2.1.1'")
    solar_yield = cursor.fetchone()[0] or 1235.33
    
    conn.close()
    return total_demand, total_supply, lu_21, solar_yield

def update_lu_21(new_value):
    """Update LU_2.1 solar area."""
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute("UPDATE simulator_landuse SET target_ha = ? WHERE code = 'LU_2.1'", (new_value,))
    conn.commit()
    conn.close()

def recalculate():
    """Run full chain recalc."""
    result = subprocess.run([
        'python3', 'manage.py', 'shell', '-c',
        'from simulator.recalc_service import full_chain_recalc; full_chain_recalc(verbose=False)'
    ], capture_output=True, text=True)
    return result.returncode == 0

print('='*60)
print('TOTAL ENERGY BALANCE VIA SOLAR ADJUSTMENT')
print('='*60)

max_iterations = 10
tolerance = 50  # GWh/a

for i in range(max_iterations):
    demand, supply, lu_21, solar_yield = get_balance()
    gap = demand - supply
    
    print(f'\nIteration {i+1}:')
    print(f'  Demand: {demand:,.2f} GWh/a')
    print(f'  Supply: {supply:,.2f} GWh/a')
    print(f'  Gap: {gap:,.2f} GWh/a')
    print(f'  LU_2.1: {lu_21:,.2f} ha')
    
    if abs(gap) <= tolerance:
        print(f'\n✅ BALANCED! Gap is within tolerance ({tolerance} GWh/a)')
        break
    
    # Calculate adjustment needed
    # gap > 0 means undersupply, need more solar
    # gap < 0 means oversupply, need less solar
    ha_adjustment = (gap * 1000) / solar_yield
    new_lu_21 = lu_21 + ha_adjustment
    
    if new_lu_21 < 0:
        new_lu_21 = 0
        print('  Warning: LU_2.1 would be negative, setting to 0')
    
    update_lu_21(new_lu_21)
    print(f'  Updated LU_2.1 to: {new_lu_21:,.2f} ha (delta: {ha_adjustment:,.2f} ha)')
    
    # Recalculate
    print('  Recalculating...')
    recalculate()

# Final check
demand, supply, lu_21, solar_yield = get_balance()
gap = demand - supply

print('\n' + '='*60)
print('FINAL RESULT')
print('='*60)
print(f'Demand: {demand:,.2f} GWh/a')
print(f'Supply: {supply:,.2f} GWh/a')
print(f'Gap: {gap:,.2f} GWh/a ({abs(gap)/demand*100:.4f}%)')
print(f'LU_2.1 Solare Freiflächen: {lu_21:,.2f} ha')
