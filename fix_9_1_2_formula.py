"""
Fix 9.1.2 formula variables to use target values instead of status values.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import Formula, FormulaVariable

def fix_formula_variables():
    """Update 9.1.2 formula variables to use renewable_code_target instead of renewable_status."""
    
    formula = Formula.objects.filter(key='9.1.2', category='renewable').first()
    
    if not formula:
        print("ERROR: Formula for 9.1.2 not found!")
        return
    
    print("=" * 60)
    print(f"Fixing Formula Variables for 9.1.2")
    print("=" * 60)
    print(f"Expression: {formula.expression}")
    print()
    
    # Update all variables to use renewable_code_target
    variables = formula.variables.all()
    
    for var in variables:
        old_type = var.source_type
        
        # Change from renewable_status to renewable_code_target
        if var.source_type in ['renewable_status', 'renewable_target']:
            var.source_type = 'renewable_code_target'
            var.save()
            
            print(f"✓ Updated {var.variable_name}")
            print(f"  Source type: {old_type} → {var.source_type}")
            print(f"  Source key: {var.source_key}")
            print()
    
    print("=" * 60)
    print("Fix complete!")
    print("=" * 60)

if __name__ == '__main__':
    fix_formula_variables()
