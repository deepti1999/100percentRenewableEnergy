import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import Formula, VerbrauchData

# Fix the formula
formula = Formula.objects.get(key='V_2.4.2_ziel')
print(f"Found formula: {formula.key}")
print(f"Old expression: {formula.expression}")
print(f"Old category: {formula.category}")
print()

# Fix typos and category
formula.expression = "(Verbrauch_2_4_1_ziel - Verbrauch_2_4_1) / Verbrauch_2_4_1 / 100"
formula.category = "verbrauch"
formula.save()

print("✅ Formula fixed!")
print(f"New expression: {formula.expression}")
print(f"New category: {formula.category}")
print()

# Now recalculate row 2.4.2
row = VerbrauchData.objects.get(code='2.4.2')
print(f"Row 2.4.2 before recalc:")
print(f"  Status: {row.status}")
print(f"  Ziel: {row.ziel}")

# Force recalculation
row.save()
row.refresh_from_db()

print(f"\nRow 2.4.2 after recalc:")
print(f"  Status: {row.status}")
print(f"  Ziel: {row.ziel}")
print("\n✅ Done! Now refresh the Verbrauch page in your browser.")
