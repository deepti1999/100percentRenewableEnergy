import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import Formula, FormulaVariable

# Find status formulas with renewable_target variables (WRONG!)
print('=== STATUS formulas with renewable_target variables (WRONG!) ===')
wrong_status = []
for f in Formula.objects.filter(category='renewable', formula_type='status').prefetch_related('variables'):
    for v in f.variables.all():
        if v.source_type == 'renewable_target':
            wrong_status.append((f.key, v.id, v.variable_name, v.source_key))
            print(f'{f.key}: {v.variable_name} has source_type=renewable_target (should be renewable_status)')

print(f'Total: {len(wrong_status)}')

print()
print('=== ZIEL formulas with renewable_status variables (WRONG!) ===')
wrong_ziel = []
for f in Formula.objects.filter(category='renewable', formula_type='ziel').prefetch_related('variables'):
    for v in f.variables.all():
        if v.source_type == 'renewable_status':
            wrong_ziel.append((f.key, v.id, v.variable_name, v.source_key))
            print(f'{f.key}: {v.variable_name} has source_type=renewable_status (should be renewable_target)')

print(f'Total: {len(wrong_ziel)}')
