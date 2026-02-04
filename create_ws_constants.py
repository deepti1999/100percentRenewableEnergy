"""
Create WS Constants in the Formula model
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
import django
django.setup()

from simulator.models import Formula
from django.db import transaction

print("=" * 70)
print("CREATING WS CONSTANTS")
print("=" * 70)

with transaction.atomic():
    # Standard WS constants values
    ws_constants = [
        {'key': 'WS_ETA_STROM_GAS', 'expression': '0.65', 'description': 'Efficiency: Electricity to Gas (Elektrolyzer)', 'category': 'ws_constant'},
        {'key': 'WS_ETA_GAS_STROM', 'expression': '0.585', 'description': 'Efficiency: Gas to Electricity (CCGT)', 'category': 'ws_constant'},
        {'key': 'WS_STORAGE_CAPACITY', 'expression': '1000000', 'description': 'Maximum storage capacity in MWh', 'category': 'ws_constant'},
        {'key': 'WS_ABREGELUNG_THRESHOLD', 'expression': '0.65', 'description': 'Curtailment threshold factor', 'category': 'ws_constant'},
    ]
    
    for const in ws_constants:
        obj, created = Formula.objects.update_or_create(
            key=const['key'],
            defaults={
                'expression': const['expression'],
                'description': const['description'],
                'category': const['category'],
                'is_active': True,
            }
        )
        status = 'CREATED' if created else 'UPDATED'
        print(f'{status}: {const["key"]} = {const["expression"]}')

print()
print("✅ WS Constants ready!")
