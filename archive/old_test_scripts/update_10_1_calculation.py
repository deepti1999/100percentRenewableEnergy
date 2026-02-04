"""
Update 10.1 calculation by properly calculating from subsections
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData

print('='*80)
print('RECALCULATING AND UPDATING 10.1')
print('='*80)

# Get calculated values for each subsection
print('\nStep 1: Get calculated values for subsections')
print('-'*80)

subsections = {}
for code in ['10.3', '10.4', '10.5', '10.6']:
    item = RenewableData.objects.get(code=code)
    calc_status, calc_target = item.get_calculated_values()
    
    # Use calculated values if available, otherwise use stored
    status = calc_status if calc_status is not None else (item.status_value or 0)
    target = calc_target if calc_target is not None else (item.target_value or 0)
    
    subsections[code] = {'status': status, 'target': target}
    print(f'{code}: Status={status:,.3f}, Target={target:,.3f}')

# Calculate 10.1
print('\nStep 2: Calculate 10.1 = 10.3 + 10.4 + 10.5 + 10.6')
print('-'*80)

total_status = sum(v['status'] for v in subsections.values())
total_target = sum(v['target'] for v in subsections.values())

print(f'Total Status: {total_status:,.3f}')
print(f'Total Target: {total_target:,.3f}')

# Update 10.1
print('\nStep 3: Update 10.1 in database')
print('-'*80)

item_10_1 = RenewableData.objects.get(code='10.1')
print(f'Old Status: {item_10_1.status_value:,.3f}')
print(f'Old Target: {item_10_1.target_value:,.3f}')

item_10_1.status_value = total_status
item_10_1.target_value = total_target
item_10_1.save()

print(f'New Status: {item_10_1.status_value:,.3f}')
print(f'New Target: {item_10_1.target_value:,.3f}')
print('\n✓ Updated successfully!')

# Verify by recalculating
print('\nStep 4: Verify calculation')
print('-'*80)
calc_status, calc_target = item_10_1.get_calculated_values()
print(f'Calculated Status from formula: {calc_status:,.3f}' if calc_status else 'Calculated Status: None')
print(f'Calculated Target from formula: {calc_target:,.3f}' if calc_target else 'Calculated Target: None')

print('\n' + '='*80)
print('SUMMARY')
print('='*80)
print(f'10.1 (Endenergie aus Erneuerbaren Q. gesamt):')
print(f'  Status: {total_status:,.3f} GWh')
print(f'  Target: {total_target:,.3f} GWh')
print(f'  Formula: 10.3 + 10.4 + 10.5 + 10.6')
print('\nThis is the sum of:')
for code in ['10.3', '10.4', '10.5', '10.6']:
    item = RenewableData.objects.get(code=code)
    print(f'  {code} ({item.name}):')
    print(f'    Status: {subsections[code]["status"]:,.3f} GWh')
    print(f'    Target: {subsections[code]["target"]:,.3f} GWh')
