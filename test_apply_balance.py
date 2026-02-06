#!/usr/bin/env python3
"""Test the apply_balanced_landuse function"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.ws_365_service import (
    apply_balanced_landuse, 
    calculate_required_landuse, 
    get_ws_base_data, 
    get_fixed_values, 
    goal_seek_optimal_solar
)
from simulator.models import LandUse, RenewableData

# Check current state
lu21 = LandUse.objects.get(code='LU_2.1')
r912 = RenewableData.objects.get(code='9.1.2')
print('Current state:')
print(f'  LU_2.1 target_ha: {lu21.target_ha:.0f} ha')
print(f'  9.1.2 target: {r912.target_value:.0f} GWh')

# Test Goal Seek
ws_data = get_ws_base_data()
fixed_values = get_fixed_values()
gs = goal_seek_optimal_solar(ws_data, fixed_values)
print()
print('Goal Seek result:')
print(f'  Optimal Solar: {gs["optimal_solar"]:.0f} GWh')
print(f'  Storage drift: {gs["result"]["storage_drift"]:.2f} GWh')

# Test LandUse calculation
lu_result = calculate_required_landuse(gs['optimal_solar'])
print()
print('Required LandUse:')
print(f'  Required LU_2.1: {lu_result["required_landuse"]:.0f} ha')
print(f'  Current LU_2.1: {lu_result["current_landuse"]:.0f} ha')
print(f'  Change: {lu_result["landuse_change"]:.0f} ha')
