#!/usr/bin/env python3
"""Check what the correct LandUse should be for balancing BOTH storage and electricity."""

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
import django
django.setup()

from simulator.ws_365_service import calculate_365_days, get_ws_base_data, get_fixed_values, goal_seek_for_balance
from simulator.models import VerbrauchData, RenewableData

ws_data = get_ws_base_data()
fixed_values = get_fixed_values()

# Current Solar
current_solar = fixed_values['ziel_912']
result = calculate_365_days(current_solar, ws_data, fixed_values)

print('=== CURRENT STATE ===')
print(f'Current Solar (9.1.2): {current_solar:,.0f}')
print(f'Annual Demand: {result["annual_demand"]:,.2f}')
print(f'Annual Electricity: {result["annual_electricity"]:,.2f}')
print(f'Electricity Gap: {result["annual_demand"] - result["annual_electricity"]:,.2f}')
print(f'Storage Drift: {result["storage_drift"]:,.2f}')
print()

# Test goal seek
print('=== GOAL SEEK RESULT ===')
goal_result = goal_seek_for_balance(ws_data, fixed_values)
print(f'Found Solar: {goal_result["optimal_solar"]:,.0f}')
print(f'Balance Solar: {goal_result["balanced_solar"]:,.2f}')
print(f'Storage Drift: {goal_result["storage_drift"]:,.2f}')

# Now calculate with goal seek Solar
balanced_result = calculate_365_days(goal_result["optimal_solar"], ws_data, fixed_values)
print()
print('=== WITH BALANCED SOLAR ===')
print(f'Annual Demand: {balanced_result["annual_demand"]:,.2f}')
print(f'Annual Electricity: {balanced_result["annual_electricity"]:,.2f}')
print(f'Electricity Gap: {balanced_result["annual_demand"] - balanced_result["annual_electricity"]:,.2f}')
print(f'Storage Drift: {balanced_result["storage_drift"]:,.2f}')

# Check what electricity gap looks like at different Solar values
print()
print('=== EXPLORING SOLAR VALUES ===')
print(f'{"Solar":>12} | {"Demand":>14} | {"Electricity":>14} | {"Elec Gap":>12} | {"Stg Drift":>10}')
print('-' * 80)

for solar_offset in [-100000, -50000, -20000, 0, 20000, 50000, 100000]:
    test_solar = current_solar + solar_offset
    r = calculate_365_days(test_solar, ws_data, fixed_values)
    elec_gap = r["annual_demand"] - r["annual_electricity"]
    print(f'{test_solar:>12,.0f} | {r["annual_demand"]:>14,.2f} | {r["annual_electricity"]:>14,.2f} | {elec_gap:>12,.2f} | {r["storage_drift"]:>10,.2f}')

# Check: is demand fixed or does it depend on Solar?
print()
print('=== WHAT DETERMINES DEMAND? ===')
# Demand should be fixed based on Verbrauch
v7 = VerbrauchData.objects.get(formel_id='7')
print(f'Verbrauch 7 ziel: {v7.ziel:,.2f}')
