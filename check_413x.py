#!/usr/bin/env python3
"""Check 4.1.3.x values"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData

print('Checking 4.1.3.x values:')
for code in ['4.1.3', '4.1.3.1', '4.1.3.2']:
    try:
        r = RenewableData.objects.get(code=code)
        print(f'  {code}: status={r.status_value}, target={r.target_value}')
    except:
        print(f'  {code}: NOT FOUND')

print()
print('What should 4.3.2 status be?')
print('Tell me the expected formula and I can check.')
