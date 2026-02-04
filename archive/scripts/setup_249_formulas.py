import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import Formula, FormulaVariable, VerbrauchData
from django.core.cache import cache

# Delete any existing formulas for 2.4.9
Formula.objects.filter(key='V_2.4.9').delete()
Formula.objects.filter(key='V_2.4.9_ziel').delete()

# Create STATUS formula: 2.4.1 status
status_formula = Formula.objects.create(
    key='V_2.4.9',
    category='verbrauch',
    expression='V_2_4_1_status',
    is_fixed=False
)

FormulaVariable.objects.create(
    formula=status_formula,
    variable_name='V_2_4_1_status',
    source_type='verbrauch_status',
    source_key='2.4.1',
    default_value=0.0
)

# Create ZIEL formula: 2.4.9 status * (1 - 2.4.7 ziel%) + 2.4.1 ziel * 2.4.7 ziel%
ziel_formula = Formula.objects.create(
    key='V_2.4.9_ziel',
    category='verbrauch',
    expression='V_2_4_9_status * (1 - V_2_4_7_ziel / 100) + V_2_4_1_ziel * V_2_4_7_ziel / 100',
    is_fixed=False
)

# Add variables for ziel formula
FormulaVariable.objects.create(
    formula=ziel_formula,
    variable_name='V_2_4_9_status',
    source_type='verbrauch_status',
    source_key='2.4.9',
    default_value=0.0
)

FormulaVariable.objects.create(
    formula=ziel_formula,
    variable_name='V_2_4_7_ziel',
    source_type='verbrauch_ziel',
    source_key='2.4.7',
    default_value=0.0
)

FormulaVariable.objects.create(
    formula=ziel_formula,
    variable_name='V_2_4_1_ziel',
    source_type='verbrauch_ziel',
    source_key='2.4.1',
    default_value=0.0
)

# Update row flags
row = VerbrauchData.objects.get(code='2.4.9')
row.is_calculated = True
row.status_calculated = True
row.ziel_calculated = True
row.save()

# Clear cache
cache.delete('formula_V_2.4.9')
cache.delete('formula_V_2.4.9_ziel')

print('✅ Created formulas for row 2.4.9:')
print(f'\nStatus formula: {status_formula.expression}')
for var in status_formula.variables.all():
    print(f'  - {var.variable_name}: {var.source_type} -> {var.source_key}')

print(f'\nZiel formula: {ziel_formula.expression}')
for var in ziel_formula.variables.all():
    print(f'  - {var.variable_name}: {var.source_type} -> {var.source_key}')

# Recalculate
from simulator.verbrauch_recalculator import recalc_all_verbrauch
recalc_all_verbrauch()

# Show result
row_249 = VerbrauchData.objects.get(code='2.4.9')
row_241 = VerbrauchData.objects.get(code='2.4.1')
row_247 = VerbrauchData.objects.get(code='2.4.7')

print(f'\nInput values:')
print(f'  2.4.1 status: {row_241.status}')
print(f'  2.4.1 ziel: {row_241.ziel}')
print(f'  2.4.7 ziel: {row_247.ziel}%')

print(f'\nRow 2.4.9 result:')
print(f'  Status: {row_249.status} (expected: {row_241.status})')
expected_ziel = row_249.status * (1 - row_247.ziel / 100) + row_241.ziel * row_247.ziel / 100
print(f'  Ziel: {row_249.ziel}')
print(f'  Expected: {expected_ziel}')
print(f'\n✅ Success!' if abs(row_249.status - row_241.status) < 0.01 and abs(row_249.ziel - expected_ziel) < 0.01 else '❌ Check values')
