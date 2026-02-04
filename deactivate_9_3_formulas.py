"""
Deactivate formulas for 9.3.1 and 9.3.4 so they use fixed values instead of WS calculations.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import Formula, RenewableData

def deactivate_formulas():
    """Deactivate formulas for 9.3.1 and 9.3.4 and ensure fixed values are set."""
    
    FIXED_VALUES = {
        '9.3.1': 405047,
        '9.3.4': 189289
    }
    
    print("=" * 60)
    print("Deactivating formulas for 9.3.1 and 9.3.4")
    print("=" * 60)
    
    for code, fixed_value in FIXED_VALUES.items():
        # Deactivate formula
        formula = Formula.objects.filter(key=code, category='renewable', is_active=True).first()
        if formula:
            formula.is_active = False
            formula.save()
            print(f"✓ Deactivated formula for {code}")
        else:
            print(f"  No active formula for {code}")
        
        # Set fixed value and is_fixed flag
        item = RenewableData.objects.get(code=code)
        item.target_value = fixed_value
        item.is_fixed = True
        item._skip_cascade = True
        item.save()
        
        print(f"✓ Set {code} = {fixed_value} (is_fixed=True)")
        print()
    
    print("=" * 60)
    print("Complete! 9.3.1 and 9.3.4 now use fixed values")
    print("=" * 60)

if __name__ == '__main__':
    deactivate_formulas()
