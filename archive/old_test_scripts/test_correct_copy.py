import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()
from simulator.models import RenewableData

# Get CALCULATED values for 4.3.4.2
code_4342 = RenewableData.objects.get(code='4.3.4.2')
calc_4342_status, calc_4342_target = code_4342.get_calculated_values()
print('Code 4.3.4.2:')
print(f'  Formula: {code_4342.formula}')
print(f'  Calculated Status: {calc_4342_status}')
print(f'  Calculated Target: {calc_4342_target}')
print()

# Get CALCULATED values for 10.7.1 (should be same as 4.3.4.2)
code_1071 = RenewableData.objects.get(code='10.7.1')
calc_1071_status, calc_1071_target = code_1071.get_calculated_values()
print('Code 10.7.1:')
print(f'  Formula: {code_1071.formula}')
print(f'  Calculated Status: {calc_1071_status}')
print(f'  Calculated Target: {calc_1071_target}')
print()

match = calc_1071_status == calc_4342_status and calc_1071_target == calc_4342_target
print(f'✅ Values match perfectly!' if match else f'❌ Values do not match')
print(f'10.7.1 correctly copies values from 4.3.4.2!' if match else '')
