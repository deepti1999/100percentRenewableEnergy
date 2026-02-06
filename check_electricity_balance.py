#!/usr/bin/env python3
"""Check electricity balance values"""

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')

import django
django.setup()

from simulator.models import VerbrauchData, RenewableData
from simulator.ws_365_service import calculate_365_days, get_ws_base_data, get_fixed_values

# Get WS 365 values
ws_data = get_ws_base_data()
fixed_values = get_fixed_values()
result = calculate_365_days(fixed_values['ziel_912'], ws_data, fixed_values)

# Check Verbrauch
v7 = VerbrauchData.objects.get(code='7')
print('=== VERBRAUCH ===')
print(f'Verbrauch 7 ziel: {v7.ziel:,.2f}')

# Check renewable values
r_91 = RenewableData.objects.get(code='9.1')
r_101 = RenewableData.objects.get(code='10.1')
r_103 = RenewableData.objects.get(code='10.3')

print()
print('=== RENEWABLE (DATABASE) ===')
print(f'9.1 (electricity from renewables): {r_91.target_value:,.2f}')
print(f'10.1 (total energy): {r_101.target_value:,.2f}')
print(f'10.3 (electricity sector): {r_103.target_value:,.2f}')

print()
print('=== WS 365 CALCULATION ===')
print(f'Annual Demand (with grid loss): {result["annual_demand"]:,.2f}')
print(f'Annual Electricity: {result["annual_electricity"]:,.2f}')
print(f'Electricity Gap: {result["annual_demand"] - result["annual_electricity"]:,.2f}')
print(f'Storage Drift: {result["storage_drift"]:,.2f}')

print()
print('=== COMPARING DEMAND vs PRODUCTION ===')
print(f'Demand (Verbrauch 7): {v7.ziel:,.2f}')
print(f'Production (10.3 electricity): {r_103.target_value:,.2f}')
print(f'Gap: {v7.ziel - r_103.target_value:,.2f}')
