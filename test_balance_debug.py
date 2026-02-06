#!/usr/bin/env python3
"""Debug the apply_balanced_landuse function"""

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')

import django
django.setup()

from simulator.ws_365_service import apply_balanced_landuse, get_ws_365_data
from simulator.models import RenewableData, LandUse
from calculation_engine.bilanz_engine import calculate_bilanz_data, get_renewable_value

# Reset LU_2.1 to unbalanced state
lu = LandUse.objects.get(code='LU_2.1')
lu.target_ha = 700000
lu._skip_cascade = True
lu.save(update_fields=['target_ha'])
print('Reset LU_2.1 to 700000 ha')

# Check state before
print()
print('=== BEFORE BALANCE ===')
data = get_ws_365_data(run_goal_seek=True)
bilanz = calculate_bilanz_data()
demand = bilanz.get('verbrauch_gesamt', {}).get('ziel', {}).get('gesamt', 0) or 0
renewable = get_renewable_value('10.1', use_target=True, fail_fast=False) or 0

print('Solar:', f'{data["current"]["solar"]:,.0f}', 'GWh')
print('Storage Drift:', f'{data["current"]["storage_drift"]:,.2f}', 'GWh')
print('Demand:', f'{demand:,.0f}', 'GWh')
print('Production (10.1):', f'{renewable:,.0f}', 'GWh')
print('Electricity Gap:', f'{demand - renewable:,.0f}', 'GWh')

# Apply balance
print()
print('=== APPLYING BALANCE ===')
result = apply_balanced_landuse()

# Check state after
print()
print('=== AFTER BALANCE ===')
data = get_ws_365_data(run_goal_seek=False)
bilanz = calculate_bilanz_data()
demand = bilanz.get('verbrauch_gesamt', {}).get('ziel', {}).get('gesamt', 0) or 0
renewable = get_renewable_value('10.1', use_target=True, fail_fast=False) or 0

print('Solar:', f'{data["current"]["solar"]:,.0f}', 'GWh')
print('Storage Drift:', f'{data["current"]["storage_drift"]:,.2f}', 'GWh')
print('Demand:', f'{demand:,.0f}', 'GWh')
print('Production (10.1):', f'{renewable:,.0f}', 'GWh')  
print('Electricity Gap:', f'{demand - renewable:,.0f}', 'GWh')
print()
print('Storage balanced?', abs(data["current"]["storage_drift"]) < 10)
print('Electricity balanced?', abs(demand - renewable) < 10)
