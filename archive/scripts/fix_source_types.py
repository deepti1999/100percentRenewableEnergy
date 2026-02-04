import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import Formula, FormulaVariable

print('=== Fixing STATUS formulas with renewable_target variables ===')

# Fix status formulas: renewable_target -> renewable_status
fixed_count = 0
for f in Formula.objects.filter(category='renewable', formula_type='status').prefetch_related('variables'):
    for v in f.variables.all():
        if v.source_type == 'renewable_target':
            print(f'Fixing {f.key}: {v.variable_name} renewable_target -> renewable_status')
            v.source_type = 'renewable_status'
            v.save()
            fixed_count += 1

print(f'\nFixed {fixed_count} status formula variables')

# Also check and fix landuse variables in status formulas
print('\n=== Checking landuse variables in STATUS formulas ===')
lu_fixed = 0
for f in Formula.objects.filter(category='renewable', formula_type='status').prefetch_related('variables'):
    for v in f.variables.all():
        if v.source_type == 'landuse_target':
            print(f'Fixing {f.key}: {v.variable_name} landuse_target -> landuse_status')
            v.source_type = 'landuse_status'
            v.save()
            lu_fixed += 1

print(f'\nFixed {lu_fixed} landuse variables in status formulas')

# Now check and fix ZIEL formulas
print('\n=== Fixing ZIEL formulas with renewable_status variables ===')
ziel_fixed = 0
for f in Formula.objects.filter(category='renewable', formula_type='ziel').prefetch_related('variables'):
    for v in f.variables.all():
        if v.source_type == 'renewable_status':
            print(f'Fixing {f.key}: {v.variable_name} renewable_status -> renewable_target')
            v.source_type = 'renewable_target'
            v.save()
            ziel_fixed += 1

print(f'\nFixed {ziel_fixed} ziel formula variables')

# Also check landuse variables in ziel formulas
print('\n=== Checking landuse variables in ZIEL formulas ===')
lu_ziel_fixed = 0
for f in Formula.objects.filter(category='renewable', formula_type='ziel').prefetch_related('variables'):
    for v in f.variables.all():
        if v.source_type == 'landuse_status':
            print(f'Fixing {f.key}: {v.variable_name} landuse_status -> landuse_target')
            v.source_type = 'landuse_target'
            v.save()
            lu_ziel_fixed += 1

print(f'\nFixed {lu_ziel_fixed} landuse variables in ziel formulas')

print(f'\n=== TOTAL FIXED: {fixed_count + lu_fixed + ziel_fixed + lu_ziel_fixed} ===')
