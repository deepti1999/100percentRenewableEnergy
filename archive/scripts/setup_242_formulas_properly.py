import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import Formula, FormulaVariable, VerbrauchData

print("=" * 70)
print("SETTING UP PROPER FORMULAS FOR 2.4.2 (Status + Ziel)")
print("=" * 70)

# Delete old formulas if they exist
Formula.objects.filter(key__in=['V_2.4.2', 'V_2.4.2_ziel']).delete()
print("✓ Deleted old formulas")

# 1. CREATE STATUS FORMULA
print("\n1. Creating STATUS formula...")
status_formula = Formula.objects.create(
    key='V_2.4.2',
    category='verbrauch',
    expression='Verbrauch_2_1_0',
    description='Status formula for 2.4.2',
    is_fixed=False
)
print(f"   ✓ Created: {status_formula.key}")

# Create variable for status formula
FormulaVariable.objects.create(
    formula=status_formula,
    variable_name='Verbrauch_2_1_0',
    source_type='verbrauch_status',
    source_key='2.1.0',
    is_required=True
)
print(f"   ✓ Added variable: Verbrauch_2_1_0 → 2.1.0 status")

# 2. CREATE ZIEL FORMULA
print("\n2. Creating ZIEL formula...")
ziel_formula = Formula.objects.create(
    key='V_2.4.2_ziel',
    category='verbrauch',
    expression='(V_2_4_1_ziel - V_2_4_1_status) / V_2_4_1_status / 100',
    description='Ziel formula for 2.4.2 (percentage change)',
    is_fixed=False
)
print(f"   ✓ Created: {ziel_formula.key}")

# Create variables for ziel formula
FormulaVariable.objects.create(
    formula=ziel_formula,
    variable_name='V_2_4_1_ziel',
    source_type='verbrauch_ziel',
    source_key='2.4.1',
    is_required=True
)
print(f"   ✓ Added variable: V_2_4_1_ziel → 2.4.1 ziel")

FormulaVariable.objects.create(
    formula=ziel_formula,
    variable_name='V_2_4_1_status',
    source_type='verbrauch_status',
    source_key='2.4.1',
    is_required=True
)
print(f"   ✓ Added variable: V_2_4_1_status → 2.4.1 status")

# 3. UPDATE VERBRAUCHDATA ROW 2.4.2
print("\n3. Updating VerbrauchData row 2.4.2...")
row = VerbrauchData.objects.get(code='2.4.2')
row.is_calculated = True
row.status_calculated = True
row.ziel_calculated = True
row.save()
print(f"   ✓ Enabled all calculated flags")

# Refresh to see new values
row.refresh_from_db()
print(f"\n   Status: {row.status}")
print(f"   Ziel: {row.ziel}")

print("\n" + "=" * 70)
print("✅ DONE! Now click 'Recalculate All' in the Verbrauch page")
print("=" * 70)
print("\nThis is how you set up ANY row with different status/ziel formulas:")
print("  1. Create formula with key 'V_X.X.X' for status")
print("  2. Create formula with key 'V_X.X.X_ziel' for ziel")
print("  3. Add FormulaVariables for each formula")
print("  4. Enable the calculated flags in VerbrauchData row")
