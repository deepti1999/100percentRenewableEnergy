"""
Add missing category row 7.1.4 for WP-Erdr./Wasser - Antriebsstromaufnahme
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import RenewableData, Formula, FormulaVariable

# Check if 7.1.4 already exists
existing = RenewableData.objects.filter(code='7.1.4').first()
if existing:
    print(f"✓ Row 7.1.4 already exists: {existing.name}")
else:
    # Create the missing row 7.1.4
    new_row = RenewableData.objects.create(
        code='7.1.4',
        name='WP-Erdr./Wasser - Antriebsstromaufnahme',
        unit='GWh/a',
        status_value=0.0,
        target_value=0.0,
        is_fixed=False
    )
    print(f"✅ Created row 7.1.4: {new_row.name}")
    
    # Check if formula already exists
    formula = Formula.objects.filter(key='7.1.4').first()
    if formula:
        print(f"✓ Formula for 7.1.4 already exists")
        # Update expression if needed
        if formula.expression != 'renewable_7_1 * renewable_7_1_3':
            formula.expression = 'renewable_7_1 * renewable_7_1_3'
            formula.save()
            print(f"✅ Updated formula expression")
    else:
        # Create formula for 7.1.4: renewable_7_1 * renewable_7_1_3
        formula = Formula.objects.create(
            key='7.1.4',
            category='renewable',
            expression='renewable_7_1 * renewable_7_1_3',
            description='WP-Erdr./Wasser heat pump electricity consumption',
            is_active=True,
            is_fixed=False
        )
        print(f"✅ Created formula for 7.1.4")
    
    # Check and create formula variables
    var1 = FormulaVariable.objects.filter(formula=formula, variable_name='renewable_7_1').first()
    if not var1:
        var1 = FormulaVariable.objects.create(
            formula=formula,
            variable_name='renewable_7_1',
            source_type='renewable_target',
            source_key='7.1'
        )
        print(f"✅ Created variable renewable_7_1 → 7.1")
    else:
        print(f"✓ Variable renewable_7_1 already exists")
    
    var2 = FormulaVariable.objects.filter(formula=formula, variable_name='renewable_7_1_3').first()
    if not var2:
        var2 = FormulaVariable.objects.create(
            formula=formula,
            variable_name='renewable_7_1_3',
            source_type='renewable_target',
            source_key='7.1.3'
        )
        print(f"✅ Created variable renewable_7_1_3 → 7.1.3")
    else:
        print(f"✓ Variable renewable_7_1_3 already exists")

# Now update formulas that reference codes that come after 7.1.4
# Since 7.1.4.x codes already exist and are correctly numbered, we just need
# to ensure the parent category exists

print("\n✅ All done! Row 7.1.4 has been added.")
print("\nPlease run recalculation to update the values.")
