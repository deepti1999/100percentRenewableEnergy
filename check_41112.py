#!/usr/bin/env python3
"""Check 4.1.1.1.1.2 formula values"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData

# Get all values in the formula chain
codes = ['4.1.1.1', '4.1.1.1.1', '4.1.1.1.1.1', '4.1.1.1.1.2']
for code in codes:
    r = RenewableData.objects.get(code=code)
    print(f'{code}: status={r.status_value}, target={r.target_value}')

# Calculate expected value
r4111 = RenewableData.objects.get(code='4.1.1.1')
r41111 = RenewableData.objects.get(code='4.1.1.1.1')
r411111 = RenewableData.objects.get(code='4.1.1.1.1.1')

expected_status = r4111.status_value * r41111.status_value / 100 * r411111.status_value / 1000
expected_target = r4111.target_value * r41111.target_value / 100 * r411111.target_value / 1000

print()
print(f'Formula: 4.1.1.1 * 4.1.1.1.1 / 100 * 4.1.1.1.1.1 / 1000')
print()
print(f'Expected status = {r4111.status_value} * {r41111.status_value} / 100 * {r411111.status_value} / 1000')
print(f'Expected status = {expected_status}')
print()
print(f'Expected target = {r4111.target_value} * {r41111.target_value} / 100 * {r411111.target_value} / 1000')
print(f'Expected target = {expected_target}')

# Compare
r41112 = RenewableData.objects.get(code='4.1.1.1.1.2')
print()
print(f'Actual 4.1.1.1.1.2 status = {r41112.status_value}')
print(f'Actual 4.1.1.1.1.2 target = {r41112.target_value}')
print()
if abs(expected_status - r41112.status_value) < 1:
    print('✅ Status matches!')
else:
    print(f'❌ Status mismatch! Diff = {expected_status - r41112.status_value}')
    
if abs(expected_target - r41112.target_value) < 1:
    print('✅ Target matches!')
else:
    print(f'❌ Target mismatch! Diff = {expected_target - r41112.target_value}')
