import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData, Formula

# Check RenewableData in section 10
renewable_10 = RenewableData.objects.filter(code__startswith='10.').order_by('code')
print(f"Found {renewable_10.count()} RenewableData items in section 10:")
for r in renewable_10[:20]:
    print(f"  {r.code}: {r.name}")

print("\n" + "="*60 + "\n")

# Check Formulas in section 10
formulas_10 = Formula.objects.filter(key__startswith='10.', category='renewable').order_by('key')
print(f"Found {formulas_10.count()} Formulas in section 10:")
for f in formulas_10[:20]:
    print(f"  {f.key}: {f.expression[:70] if f.expression else 'EMPTY'}...")
