"""Test the updated diagram reference function"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
import django
django.setup()

from simulator.signals import compute_ws_diagram_reference
from simulator.ws_365_service import get_ws_365_data

diagram = compute_ws_diagram_reference()

print('=== ANNUAL ELECTRICITY DIAGRAM VALUES ===')
print(f"Q (Abregelung): {diagram['q_abregelung']:,.0f} GWh")
print(f"Elektrolyse Überschuss (n_output_branch): {diagram['n_output_branch']:,.0f} GWh")
print(f"Gasspeicher Strom T: {diagram['t_value']:,.0f} GWh")
print()
print('=== COMPARISON WITH WS 365 ===')
ws_data = get_ws_365_data(run_goal_seek=False)
print(f"WS 365 Abregelung Sum: {ws_data['current']['abregelung_sum']:,.0f} GWh")
print(f"WS 365 Einspeich Sum: {ws_data['current']['einspeich_sum']:,.0f} GWh")
print(f"WS 365 Einspeich/0.65: {ws_data['current']['einspeich_sum']/0.65:,.0f} GWh")
print(f"WS 365 Ausspeich Sum: {ws_data['current']['ausspeich_sum']:,.0f} GWh")
print()
print('=== MATCH CHECK ===')
print(f"Q matches: {abs(diagram['q_abregelung'] - ws_data['current']['abregelung_sum']) < 1}")
print(f"Elektrolyse matches: {abs(diagram['n_output_branch'] - ws_data['current']['einspeich_sum']/0.65) < 1}")
print(f"Gasspeicher matches: {abs(diagram['t_value'] - ws_data['current']['ausspeich_sum']) < 1}")
