#!/usr/bin/env python3
"""Update 9.3.1 and 9.3.4 to be fixed and get values from WS 365"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData
from simulator.ws_365_service import get_ws_365_data

# Set 9.3.1 and 9.3.4 as fixed (values come from ws_365_service, not formulas)
for code in ['9.3.1', '9.3.4']:
    try:
        r = RenewableData.objects.get(code=code)
        r.is_fixed = True
        r.formula = None  # Clear any special formula
        r.save(update_fields=['is_fixed', 'formula'])
        print(f'✅ {code}: is_fixed=True, target_value={r.target_value}')
    except Exception as e:
        print(f'❌ {code}: {e}')

# Trigger WS 365 calculation which will update database values
print()
print('Triggering WS 365 calculation to update database...')
ws_data = get_ws_365_data(run_goal_seek=False)

print()
print('WS 365 calculated values:')
print(f'  einspeich_sum: {ws_data["current"]["einspeich_sum"]:.2f} GWh')
print(f'  9.3.1 ziel = einspeich/0.65: {ws_data["current"]["einspeich_sum"]/0.65:.2f} GWh')
print(f'  9.3.4 ziel = abregelung_sum: {ws_data["current"]["abregelung_sum"]:.2f} GWh')

# Verify database values
print()
print('Database values after update:')
r931 = RenewableData.objects.get(code='9.3.1')
r934 = RenewableData.objects.get(code='9.3.4')
print(f'  9.3.1 target_value: {r931.target_value:.2f} GWh')
print(f'  9.3.4 target_value: {r934.target_value:.2f} GWh')

# Verify dependent formulas will get correct values
print()
print('Testing dependent formula 9.3.1.2_target:')
from simulator.models import Formula
f = Formula.objects.filter(key='9.3.1.2_target').first()
if f:
    print(f'  Formula: {f.expression}')
    print(f'  References Renewable_9_3_1_zeil which should now be {r931.target_value:.2f} GWh')
