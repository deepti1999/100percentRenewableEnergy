"""
Fix 10.1 calculation by properly calculating 10.3, 10.4, 10.5, 10.6 from their formulas
and then calculating 10.1 as the sum of these four sections.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData

print('='*80)
print('FIXING SECTION 10.1 CALCULATION')
print('='*80)
print()

# Step 1: Ensure all formulas are correct
print('Step 1: Verify formulas')
print('-'*80)

formulas = {
    '10.1': '10.3 + 10.4 + 10.5 + 10.6',
    '10.3': '10.3.1',
    '10.4': '10.4.1 + 10.4.3 + 10.4.2',
    '10.5': '10.5.1 + 10.5.3 + 10.5.2',
    '10.6': '10.6.1 + 10.6.2',
}

for code, expected_formula in formulas.items():
    try:
        item = RenewableData.objects.get(code=code)
        current_formula = item.formula or ''
        # Normalize formulas by removing spaces
        current_normalized = current_formula.replace(' ', '')
        expected_normalized = expected_formula.replace(' ', '')
        
        if current_normalized != expected_normalized:
            print(f'  {code}: Updating formula')
            print(f'    Old: {current_formula}')
            print(f'    New: {expected_formula}')
            item.formula = expected_formula
            item.is_fixed = False
            item.save()
        else:
            print(f'  {code}: Formula correct ✓')
    except Exception as e:
        print(f'  {code}: ERROR - {e}')

print()
print('='*80)
print('Step 2: Calculate subsections (10.3, 10.4, 10.5, 10.6)')
print('='*80)

subsection_values = {}

for code in ['10.3', '10.4', '10.5', '10.6']:
    try:
        item = RenewableData.objects.get(code=code)
        print(f'\n{code}: {item.name}')
        print(f'  Formula: {item.formula}')
        
        # Get calculated values
        calc_status, calc_target = item.get_calculated_values()
        
        # If None, fall back to stored values
        if calc_status is None:
            calc_status = item.status_value or 0
            print(f'  ⚠️  Calculation returned None, using stored status: {calc_status}')
        
        if calc_target is None:
            calc_target = item.target_value or 0
            print(f'  ⚠️  Calculation returned None, using stored target: {calc_target}')
        
        print(f'  Status: {calc_status}')
        print(f'  Target: {calc_target}')
        
        # Store values
        subsection_values[code] = {
            'status': calc_status,
            'target': calc_target
        }
        
        # Update in database
        if item.status_value != calc_status or item.target_value != calc_target:
            item.status_value = calc_status
            item.target_value = calc_target
            item.save()
            print(f'  ✓ Updated in database')
        else:
            print(f'  ✓ Already up to date')
            
    except Exception as e:
        print(f'{code}: ERROR - {e}')
        subsection_values[code] = {'status': 0, 'target': 0}

print()
print('='*80)
print('Step 3: Calculate 10.1 (sum of 10.3 + 10.4 + 10.5 + 10.6)')
print('='*80)

total_status = sum(v['status'] for v in subsection_values.values())
total_target = sum(v['target'] for v in subsection_values.values())

print(f'\n10.3 Status: {subsection_values["10.3"]["status"]:>15.3f} GWh')
print(f'10.4 Status: {subsection_values["10.4"]["status"]:>15.3f} GWh')
print(f'10.5 Status: {subsection_values["10.5"]["status"]:>15.3f} GWh')
print(f'10.6 Status: {subsection_values["10.6"]["status"]:>15.3f} GWh')
print('-'*50)
print(f'TOTAL Status: {total_status:>13.3f} GWh')
print()
print(f'10.3 Target: {subsection_values["10.3"]["target"]:>15.3f} GWh')
print(f'10.4 Target: {subsection_values["10.4"]["target"]:>15.3f} GWh')
print(f'10.5 Target: {subsection_values["10.5"]["target"]:>15.3f} GWh')
print(f'10.6 Target: {subsection_values["10.6"]["target"]:>15.3f} GWh')
print('-'*50)
print(f'TOTAL Target: {total_target:>13.3f} GWh')

# Update 10.1
try:
    item_10_1 = RenewableData.objects.get(code='10.1')
    item_10_1.status_value = total_status
    item_10_1.target_value = total_target
    item_10_1.save()
    print()
    print(f'✓ Updated 10.1 in database')
    print(f'  Status: {total_status:.3f} GWh')
    print(f'  Target: {total_target:.3f} GWh')
except Exception as e:
    print(f'ERROR updating 10.1: {e}')

print()
print('='*80)
print('DONE!')
print('='*80)
