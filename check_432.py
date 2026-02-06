#!/usr/bin/env python3
"""Check 4.3.2 formula values"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData, Formula

# Get 4.3.2 data
r = RenewableData.objects.get(code='4.3.2')
print(f'4.3.2: status={r.status_value}, target={r.target_value}')

# Get formula
f = Formula.objects.filter(key='4.3.2').first()
if f:
    print(f'\nFormula: {f.expression}')
    print(f'Variables:')
    for v in f.variables.all():
        print(f'  {v.variable_name} = {v.source_type} / {v.source_key}')
        # Get actual value
        try:
            rv = RenewableData.objects.get(code=v.source_key)
            if 'status' in v.source_type:
                print(f'    → value = {rv.status_value}')
            else:
                print(f'    → value = {rv.target_value}')
        except:
            print(f'    → NOT FOUND')

# Get target formula
f2 = Formula.objects.filter(key__in=['4.3.2_target', '4.3.2_ziel_target']).first()
if f2:
    print(f'\nTarget Formula: {f2.expression}')
    for v in f2.variables.all():
        print(f'  {v.variable_name} = {v.source_type} / {v.source_key}')
        try:
            rv = RenewableData.objects.get(code=v.source_key)
            if 'target' in v.source_type:
                print(f'    → value = {rv.target_value}')
            else:
                print(f'    → value = {rv.status_value}')
        except:
            print(f'    → NOT FOUND')
