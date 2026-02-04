import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData

renewable = RenewableData.objects.get(code='1.1.1.1.2')
target_lookup = {'1.1': 199398.0, '1.1.1.1': 1.1, '1.1.1.1.1': 5250.0}
status_lookup = {'1.1': 34243.0, '1.1.1.1': 6.4, '1.1.1.1.1': 3878.0}

calc_status, calc_target = renewable.get_calculated_values(
    status_lookup=status_lookup,
    target_lookup=target_lookup
)

print(f'Formula: {renewable.formula}')
print(f'Calculated Status: {calc_status}')
print(f'Calculated Target: {calc_target}')
print(f'Expected Target: 11515.235')
if calc_target:
    print(f'Match: {"YES!" if abs(calc_target - 11515.235) < 0.01 else "NO"}')
else:
    print('Match: NO - calc_target is None')
