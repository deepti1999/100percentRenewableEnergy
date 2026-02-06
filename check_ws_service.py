"""Check WS 365 service values"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
import django
django.setup()

from simulator.ws_365_service import get_ws_365_data

data = get_ws_365_data(run_goal_seek=False)

print('=== FIRST 10 DAYS ===')
for row in data['daily_data'][:10]:
    print(f"Day {row['day']:3d}: Ladezust={row['ladezust_brutto']:10.2f}, Einspeich={row['einspeich']:8.2f}, Ausspeich.R={row['ausspeich_rueckverstr']:8.2f}")

print()
print('=== LAST 10 DAYS ===')
for row in data['daily_data'][-10:]:
    print(f"Day {row['day']:3d}: Ladezust={row['ladezust_brutto']:10.2f}, Einspeich={row['einspeich']:8.2f}, Ausspeich.R={row['ausspeich_rueckverstr']:8.2f}")

print()
print('=== SUMMARY ===')
print(f"Storage Day 1: {data['current']['ladezust_day1']:.2f}")
print(f"Storage Day 365: {data['current']['ladezust_day365']:.2f}")
print(f"Storage Drift: {data['current']['storage_drift']:.2f}")
print(f"Einspeich Sum: {data['current']['einspeich_sum']:.0f}")
print(f"Ausspeich Sum: {data['current']['ausspeich_sum']:.0f}")
