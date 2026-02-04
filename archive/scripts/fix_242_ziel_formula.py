import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import Formula, VerbrauchData

# Fix the V_2.4.2_ziel formula
print("Fixing V_2.4.2_ziel formula...")

formula = Formula.objects.get(key='V_2.4.2_ziel')

print(f"\nBEFORE:")
print(f"  Category: {formula.category}")
print(f"  Expression: {formula.expression}")

# Fix the formula
formula.category = 'verbrauch'
formula.expression = '(Verbrauch_2_4_1_ziel - Verbrauch_2_4_1) / Verbrauch_2_4_1 / 100'
formula.save()

print(f"\nAFTER:")
print(f"  Category: {formula.category}")
print(f"  Expression: {formula.expression}")

print("\n✅ Formula fixed!")

# Now recalculate row 2.4.2
print("\nRecalculating row 2.4.2...")
row = VerbrauchData.objects.get(code='2.4.2')

print(f"\nBEFORE recalc:")
print(f"  Status: {row.status}")
print(f"  Ziel: {row.ziel}")

# Force recalculation
row.save()
row.refresh_from_db()

print(f"\nAFTER recalc:")
print(f"  Status: {row.status}")
print(f"  Ziel: {row.ziel}")

print("\n✅ Done! Now refresh the Verbrauch page.")
