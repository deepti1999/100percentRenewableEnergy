import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData

print('Full check of 9.2.1.3.x entries:')
print('=' * 70)

codes = ['9.2.1.3', '9.2.1.3.1', '9.2.1.3.2']

for code in codes:
    entries = RenewableData.objects.filter(code=code)
    
    print(f'\n{code}: Found {entries.count()} entries')
    
    for entry in entries:
        print(f'  ID: {entry.id}')
        print(f'  Name: {entry.name}')
        print(f'  Category: {entry.category}')
        print(f'  Subcategory: {entry.subcategory}')
        print(f'  Unit: {entry.unit}')
        print(f'  Status: {entry.status_value}')
        print(f'  Target: {entry.target_value}')
        print(f'  Is Fixed: {entry.is_fixed}')
        print(f'  Formula: {entry.formula}')

print('\n\nChecking all entries with code starting with 9.2:')
print('=' * 70)
all_9_2 = RenewableData.objects.filter(code__startswith='9.2').order_by('code')
print(f'Total entries starting with 9.2: {all_9_2.count()}')

for entry in all_9_2:
    print(f'{entry.code}: {entry.name} (Cat: {entry.category}, Sub: {entry.subcategory})')
