"""Test 9.3.1 and 9.3.4 WS365 formulas"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
import django
django.setup()

from simulator.models import RenewableData
from simulator.ws_365_service import get_ws_365_data

# Get WS 365 data
ws_data = get_ws_365_data(run_goal_seek=False)
einspeich_sum = ws_data['current']['einspeich_sum']
abregelung_sum = ws_data['current']['abregelung_sum']

print('=== WS 365 VALUES ===')
print(f"Einspeich Sum: {einspeich_sum:,.0f} GWh")
print(f"Einspeich / 0.65: {einspeich_sum / 0.65:,.0f} GWh")
print(f"Abregelung Sum: {abregelung_sum:,.0f} GWh")

print()
print('=== 9.3.1 CALCULATED ===')
r931 = RenewableData.objects.get(code='9.3.1')
calc_status, calc_target = r931.get_calculated_values()
print(f"Status: {calc_status:,.0f}")
print(f"Target: {calc_target:,.0f}")
print(f"Expected: {einspeich_sum / 0.65:,.0f}")
print(f"Match: {abs(calc_target - einspeich_sum / 0.65) < 1}")

print()
print('=== 9.3.4 CALCULATED ===')
r934 = RenewableData.objects.get(code='9.3.4')
calc_status, calc_target = r934.get_calculated_values()
print(f"Status: {calc_status:,.0f}")
print(f"Target: {calc_target:,.0f}")
print(f"Expected: {abregelung_sum:,.0f}")
print(f"Match: {abs(calc_target - abregelung_sum) < 1}")
