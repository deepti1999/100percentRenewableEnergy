import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData

print('Checking renewable energy entries for 9.2.1.3.x:')
print('=' * 70)

codes = ['9.2.1.3', '9.2.1.3.1', '9.2.1.3.2']

for code in codes:
    entries = RenewableData.objects.filter(code=code)
    count = entries.count()
    
    print(f'\n{code}: Found {count} entries')
    
    if count > 0:
        for entry in entries:
            print(f'  ID: {entry.id}')
            print(f'  Name: {entry.name}')
            print(f'  Category: {entry.category}')
            print(f'  Subcategory: {entry.subcategory}')
            print(f'  Unit: {entry.unit}')
            print(f'  Status: {entry.status_value}')
            print(f'  Target: {entry.target_value}')
            print(f'  Formula: {entry.formula}')
            print(f'  Is Fixed: {entry.is_fixed}')
    else:
        print(f'  ⚠ NO ENTRIES FOUND - Need to create them!')

print('\n' + '=' * 70)
print('Check complete!')
