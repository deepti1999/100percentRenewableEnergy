import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import Formula, FormulaVariable, VerbrauchData
from django.core.cache import cache

print("Fixing 2.4.6 formulas with CORRECT references...")

# Delete old formulas
Formula.objects.filter(key='V_2.4.6').delete()
Formula.objects.filter(key='V_2.4.6_ziel').delete()

# Create CORRECT Status formula: V_2_4_6_status
status_formula = Formula.objects.create(
    key='V_2.4.6',
    category='verbrauch',
    expression='V_2_4_6_status',
    is_fixed=False
)

FormulaVariable.objects.create(
    formula=status_formula,
    variable_name='V_2_4_6_status',
    source_type='verbrauch_status',
    source_key='2.4.6',
    default_value=0.0
)

# Create CORRECT Ziel formula
ziel_formula = Formula.objects.create(
    key='V_2.4.6_ziel',
    category='verbrauch',
    expression='V_2_4_6_status * (1 - V_2_4_5_ziel / 100) + V_2_4_1_ziel * V_2_4_5_ziel / 100',
    is_fixed=False
)

FormulaVariable.objects.create(
    formula=ziel_formula,
    variable_name='V_2_4_6_status',
    source_type='verbrauch_status',
    source_key='2.4.6',
    default_value=0.0
)

FormulaVariable.objects.create(
    formula=ziel_formula,
    variable_name='V_2_4_5_ziel',
    source_type='verbrauch_ziel',
    source_key='2.4.5',
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
row = VerbrauchData.objects.get(code='2.4.6')
row.is_calculated = True
row.status_calculated = True
row.ziel_calculated = True
row.save()

# Clear cache
cache.delete('formula_V_2.4.6')
cache.delete('formula_V_2.4.6_ziel')

print("✅ Fixed 2.4.6 formulas:")
print(f"  Status: {status_formula.expression}")
print(f"  Ziel: {ziel_formula.expression}")
print("\nNow run: python3 manage.py runserver")
print("Then click 'Recalculate All' on the Verbrauch page")
