import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.recalc_service import run_full_recalc

print('Running full recalculation...')
result = run_full_recalc()
print(f"\n✅ Recalculation complete!")
print(f"Renewables updated: {result.get('renewables_updated', 0)}")
print(f"Verbrauch updated: {result.get('verbrauch_updated', 0)}")
