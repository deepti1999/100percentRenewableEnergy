#!/usr/bin/env python
"""
Check how 10.4.2 target value is calculated
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData

# Get 10.4.2 current values and formula
r1042 = RenewableData.objects.filter(code='10.4.2').first()
if r1042:
    print('=== 10.4.2 in RenewableData ===')
    print(f'Code: {r1042.code}')
    print(f'Name: {r1042.name}')
    print(f'Status Value: {r1042.status_value}')
    print(f'Target Value: {r1042.target_value}')
    print(f'Formula: {r1042.formula}')
    print()

# The formula is:
# renewable_1_1_1_1_2_target + renewable_7_1_2_3_target + renewable_7_1_4_3_target + 
# renewable_5_4_2_4_target + renewable_6_1_3_2_4_target + renewable_8_2_target + 
# renewable_4_4_2_target + renewable_9_3_2_1_target

# Get values for all the components in the 10.4.2 formula
codes = ['1.1.1.1.2', '7.1.2.3', '7.1.4.3', '5.4.2.4', '6.1.3.2.4', '8.2', '4.4.2', '9.3.2.1']

print('=== Components of 10.4.2 Formula ===')
print()

total = 0
for code in codes:
    r = RenewableData.objects.filter(code=code).first()
    if r:
        target_val = r.target_value if r.target_value else 0
        print(f'{code:15} target={target_val:12.2f}  name={r.name[:50]}')
        total += float(target_val)
    else:
        print(f'{code:15} NOT FOUND')

print()
print(f'SUM of components: {total:.2f}')
print(f'Current 10.4.2 target: {r1042.target_value if r1042 else "N/A"}')
print()

if r1042 and r1042.target_value:
    diff = abs(float(r1042.target_value) - total)
    print(f'Difference: {diff:.4f}')
    if diff < 0.01:
        print('✓ Values match!')
    else:
        print('✗ Values do NOT match!')
