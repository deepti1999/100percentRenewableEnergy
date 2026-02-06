#!/usr/bin/env python3
"""Check 4.3.3 formula values"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData, Formula

# Get 4.3.3 data
r = RenewableData.objects.get(code='4.3.3')
print(f'4.3.3: status={r.status_value}, target={r.target_value}')

# Get formula
f = Formula.objects.filter(key='4.3.3').first()
if f:
    print(f'\nStatus Formula: {f.expression}')
    print(f'Variables:')
    for v in f.variables.all():
        try:
            rv = RenewableData.objects.get(code=v.source_key)
            if 'status' in v.source_type:
                val = rv.status_value
            else:
                val = rv.target_value
            print(f'  {v.variable_name} = {v.source_type} / {v.source_key} → {val}')
        except:
            print(f'  {v.variable_name} = {v.source_type} / {v.source_key} → NOT FOUND')

# Get target formula
f2 = Formula.objects.filter(key__in=['4.3.3_target', '4.3.3_ziel_target']).first()
if f2:
    print(f'\nTarget Formula: {f2.expression}')
    for v in f2.variables.all():
        try:
            rv = RenewableData.objects.get(code=v.source_key)
            if 'target' in v.source_type:
                val = rv.target_value
            else:
                val = rv.status_value
            print(f'  {v.variable_name} = {v.source_type} / {v.source_key} → {val}')
        except:
            print(f'  {v.variable_name} = {v.source_type} / {v.source_key} → NOT FOUND')
