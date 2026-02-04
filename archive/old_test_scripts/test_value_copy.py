import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()
from simulator.models import RenewableData

# Check 4.3.4.2 values
code_4342 = RenewableData.objects.get(code='4.3.4.2')
print('Code 4.3.4.2 values:')
print(f'  Status: {code_4342.status_value}')
print(f'  Target: {code_4342.target_value}')
print()

# Check 10.7.1 values (should be same as 4.3.4.2)
code_1071 = RenewableData.objects.get(code='10.7.1')
print('Code 10.7.1:')
print(f'  Formula: {code_1071.formula}')
calc_status, calc_target = code_1071.get_calculated_values()
print(f'  Calculated Status: {calc_status}')
print(f'  Calculated Target: {calc_target}')
print()
match = calc_status == code_4342.status_value and calc_target == code_4342.target_value
print(f'Match: {"✅ YES - Same values!" if match else "❌ NO - Different values"}')
