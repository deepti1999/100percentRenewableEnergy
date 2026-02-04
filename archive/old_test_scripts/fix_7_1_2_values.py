import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import VerbrauchData

# Update 7.1.2 to be fixed (not calculated)
item = VerbrauchData.objects.filter(code='7.1.2').first()

if item:
    print(f'Updating 7.1.2: {item.category}')
    print(f'  Old values:')
    print(f'    Status: {item.status}')
    print(f'    Ziel: {item.ziel}')
    print(f'    Is Calculated: {item.is_calculated}')
    
    item.status = 197841
    item.ziel = 104855
    item.is_calculated = False
    item.status_calculated = False
    item.ziel_calculated = False
    item.save()
    
    print(f'  New values:')
    print(f'    Status: {item.status}')
    print(f'    Ziel: {item.ziel}')
    print(f'    Is Calculated: {item.is_calculated}')
    print(f'\n✓ Updated 7.1.2 to fixed values (not calculated)')

# Verify all Grundstoff values
print('\n\nVerifying all Grundstoff-Synthetisierung values:')
print('=' * 70)

codes = ['7.1', '7.1.1', '7.1.2', '7.1.3', '7.1.4']
for code in codes:
    item = VerbrauchData.objects.filter(code=code).first()
    if item:
        print(f'\n{code}: {item.category}')
        print(f'  Status: {item.status} | Ziel: {item.ziel}')
        print(f'  Is Calculated: {item.is_calculated}')
