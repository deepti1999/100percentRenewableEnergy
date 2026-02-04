import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData

print('=' * 100)
print('FIXING ALL SECTION 10 FORMULAS')
print('=' * 100)
print()

# Define all the correct formulas
formulas = {
    # 10.2.x formulas
    '10.2.1': 'VerbrauchData_6',
    '10.2.2': '10.2 * 10.2.1 / 100',
    '10.2': '9.4.3.3',
    
    # 10.3.x formulas
    '10.3.1': 'VerbrauchData_1.4 * 10.2.2 / 100',
    '10.3': '10.3.1',
    
    # 10.4.x formulas
    '10.4.1.3': '4.3.1',
    '10.4.1.1': '4.3.4.2',
    '10.4.1.2': '4.3.4.2',
    '10.4.1': '10.4.1.3 + 10.4.1.1 + 10.4.1.2',
    '10.4.3': 'VerbrauchData_2.9.0 * 10.2.2 / 100',
    '10.4': '10.4.1 + 10.4.3 + 10.4.2',
    
    # 10.5.x formulas
    '10.5.1.1': '5.4.1.1',
    '10.5.1.2': '4.3.4.2',
    '10.5.1.3': '4.3.4.2',
    '10.5.1.4': '4.3.2',
    '10.5.1': '10.5.1.1 + 10.5.1.2 + 10.5.1.3 + 10.5.1.4',
    '10.5.2': '4.3.4.2',
    '10.5.3': 'VerbrauchData_3.6.0 * 10.2.2 / 100',
    '10.5': '10.5.1 + 10.5.3 + 10.5.2',
    
    # 10.6.x formulas
    '10.6.1.2': '5.4.3.2',
    '10.6.1.3': '6.1.3.1.1 + 6.2.3 + 9.2.1.3',
    '10.6.1': '10.6.1.1 + 10.6.1.2 + 10.6.1.3',
    '10.6.2': 'VerbrauchData_4.3.6 * 10.2.2 / 100',
    '10.6': '10.6.1 + 10.6.2',
    
    # 10.7.x formulas
    '10.7.1': '4.3.4.2',
    '10.7.2': '5.4.3.2 + 5.4.1.1',
    '10.7.3': '10.6.1.3',
    '10.7.4': '4.3.1 + 4.3.2',
    '10.7': '10.7.1 + 10.7.2 + 10.7.3 + 10.7.4',
    
    # 10.8 formula
    '10.8': '9.2.1.4',
    
    # 10.9.x formulas
    '10.9.1.1': '5.1.2 + 5.2 + 5.3',
    '10.9.1.2': '6.1.1.2 + 6.1.2 + 6.2.2 + 6.2.1.2',
    '10.9.1.3': '4.3 + 4.4',
    '10.9.1': '10.9.1.1 + 10.9.1.2 + 10.9.1.3',
}

updated = 0
errors = 0

for code, formula in formulas.items():
    try:
        item = RenewableData.objects.get(code=code)
        old_formula = item.formula
        
        if old_formula != formula:
            print(f'✏️  {code}: {item.name}')
            print(f'   Old: {old_formula}')
            print(f'   New: {formula}')
            
            item.formula = formula
            item.save()
            updated += 1
            print(f'   ✅ Updated')
        else:
            print(f'✅ {code}: {item.name} - Already correct')
        print()
        
    except RenewableData.DoesNotExist:
        print(f'❌ {code}: NOT FOUND IN DATABASE')
        errors += 1
        print()

print('=' * 100)
print(f'SUMMARY: Updated {updated} formulas, {errors} errors')
print('=' * 100)
print()

# Now verify some key calculations
print('=' * 100)
print('VERIFICATION OF KEY CALCULATIONS')
print('=' * 100)
print()

test_codes = ['10.2', '10.3', '10.4', '10.5', '10.6', '10.7', '10.9.1']
for code in test_codes:
    try:
        item = RenewableData.objects.get(code=code)
        status, target = item.get_calculated_values()
        print(f'{code}: {item.name}')
        print(f'  Formula: {item.formula}')
        if status is not None:
            print(f'  Status: {status:.2f}, Target: {target:.2f}')
        else:
            print(f'  Status: None, Target: None')
        print()
    except RenewableData.DoesNotExist:
        print(f'{code}: NOT FOUND')
        print()
