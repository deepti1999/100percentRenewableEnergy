import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import Formula, FormulaVariable, VerbrauchData
from django.core.cache import cache

print("=" * 70)
print("FIXING: Moving 2.4.9 formulas to 2.4.6 and creating new 2.4.9")
print("=" * 70)

# Step 1: Delete current 2.4.9 formulas and create for 2.4.6
Formula.objects.filter(key='V_2.4.9').delete()
Formula.objects.filter(key='V_2.4.9_ziel').delete()
Formula.objects.filter(key='V_2.4.6').delete()
Formula.objects.filter(key='V_2.4.6_ziel').delete()

# ========== CREATE 2.4.6 FORMULAS ==========
print("\n📝 Creating formulas for row 2.4.6:")

# 2.4.6 Status: 2.4.1 status
status_246 = Formula.objects.create(
    key='V_2.4.6',
    category='verbrauch',
    expression='V_2_4_1_status',
    is_fixed=False
)

FormulaVariable.objects.create(
    formula=status_246,
    variable_name='V_2_4_1_status',
    source_type='verbrauch_status',
    source_key='2.4.1',
    default_value=0.0
)

# 2.4.6 Ziel: 2.4.9 status * (1 - 2.4.7 ziel%) + 2.4.1 ziel * 2.4.7 ziel%
ziel_246 = Formula.objects.create(
    key='V_2.4.6_ziel',
    category='verbrauch',
    expression='V_2_4_9_status * (1 - V_2_4_7_ziel / 100) + V_2_4_1_ziel * V_2_4_7_ziel / 100',
    is_fixed=False
)

FormulaVariable.objects.create(
    formula=ziel_246,
    variable_name='V_2_4_9_status',
    source_type='verbrauch_status',
    source_key='2.4.9',
    default_value=0.0
)

FormulaVariable.objects.create(
    formula=ziel_246,
    variable_name='V_2_4_7_ziel',
    source_type='verbrauch_ziel',
    source_key='2.4.7',
    default_value=0.0
)

FormulaVariable.objects.create(
    formula=ziel_246,
    variable_name='V_2_4_1_ziel',
    source_type='verbrauch_ziel',
    source_key='2.4.1',
    default_value=0.0
)

row_246 = VerbrauchData.objects.get(code='2.4.6')
row_246.is_calculated = True
row_246.status_calculated = True
row_246.ziel_calculated = True
row_246.save()

print(f"  Status: {status_246.expression}")
print(f"  Ziel: {ziel_246.expression}")

# ========== CREATE 2.4.9 FORMULAS ==========
print("\n📝 Creating formulas for row 2.4.9:")

# 2.4.9 Status: Same as 2.4.2 pattern (reference to 2.1.0)
status_249 = Formula.objects.create(
    key='V_2.4.9',
    category='verbrauch',
    expression='Verbrauch_2_1_0',
    is_fixed=False
)

FormulaVariable.objects.create(
    formula=status_249,
    variable_name='Verbrauch_2_1_0',
    source_type='verbrauch_status',
    source_key='2.1.0',
    default_value=0.0
)

# 2.4.9 Ziel: (2.4.1 ziel - 2.4.1 status) / 2.4.1 ziel * 100
ziel_249 = Formula.objects.create(
    key='V_2.4.9_ziel',
    category='verbrauch',
    expression='(V_2_4_1_ziel - V_2_4_1_status) / V_2_4_1_ziel * 100',
    is_fixed=False
)

FormulaVariable.objects.create(
    formula=ziel_249,
    variable_name='V_2_4_1_status',
    source_type='verbrauch_status',
    source_key='2.4.1',
    default_value=0.0
)

FormulaVariable.objects.create(
    formula=ziel_249,
    variable_name='V_2_4_1_ziel',
    source_type='verbrauch_ziel',
    source_key='2.4.1',
    default_value=0.0
)

row_249 = VerbrauchData.objects.get(code='2.4.9')
row_249.is_calculated = True
row_249.status_calculated = True
row_249.ziel_calculated = True
row_249.save()

print(f"  Status: {status_249.expression}")
print(f"  Ziel: {ziel_249.expression}")

# Clear cache
cache.delete('formula_V_2.4.6')
cache.delete('formula_V_2.4.6_ziel')
cache.delete('formula_V_2.4.9')
cache.delete('formula_V_2.4.9_ziel')

# Recalculate
from simulator.verbrauch_recalculator import recalc_all_verbrauch
print("\n♻️  Recalculating all...")
recalc_all_verbrauch()

# Show results
print("\n" + "=" * 70)
print("RESULTS:")
print("=" * 70)

row_241 = VerbrauchData.objects.get(code='2.4.1')
row_247 = VerbrauchData.objects.get(code='2.4.7')
row_210 = VerbrauchData.objects.get(code='2.1.0')
row_246 = VerbrauchData.objects.get(code='2.4.6')
row_249 = VerbrauchData.objects.get(code='2.4.9')

print(f"\nInput values:")
print(f"  2.1.0 status: {row_210.status}")
print(f"  2.4.1 status: {row_241.status}, ziel: {row_241.ziel}")
print(f"  2.4.7 ziel: {row_247.ziel}%")

print(f"\nRow 2.4.6:")
print(f"  Status: {row_246.status} (expected: {row_241.status})")
expected_246_ziel = row_249.status * (1 - row_247.ziel / 100) + row_241.ziel * row_247.ziel / 100
print(f"  Ziel: {row_246.ziel} (expected: {expected_246_ziel})")

print(f"\nRow 2.4.9:")
print(f"  Status: {row_249.status} (expected: {row_210.status})")
expected_249_ziel = (row_241.ziel - row_241.status) / row_241.ziel * 100
print(f"  Ziel: {row_249.ziel} (expected: {expected_249_ziel})")

print("\n✅ Done!")
