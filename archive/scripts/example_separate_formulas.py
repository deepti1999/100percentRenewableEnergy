"""
Example: Add Separate Status and Ziel Formulas for Item 2.4.2
==============================================================

This shows how to create TWO different formulas for an item where:
- STATUS uses one calculation
- ZIEL uses a different calculation

Run this script to add the example formulas to your database.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from simulator.models import Formula

def add_separate_formulas_example():
    """
    Example: Add formulas for item 2.4.2 where:
    - Status formula: 2.4.1 / 2.4.1%
    - Ziel formula: (2.4.1_target - 2.4.1_status) / 2.4.1_status
    """
    
    # STATUS FORMULA
    # Key format: V_X.X.X (no suffix)
    status_formula, created = Formula.objects.update_or_create(
        key='V_2.4.2',
        category='verbrauch',
        defaults={
            'expression': 'Verbrauch_2_4_1 / (Verbrauch_2_4_1_percent / 100)',
            'description': 'Status calculation: 2.4.1 divided by 2.4.1%',
            'is_fixed': False,
            'is_active': True,
        }
    )
    
    if created:
        print("✅ Created STATUS formula: V_2.4.2")
    else:
        print("✅ Updated STATUS formula: V_2.4.2")
    print(f"   Expression: {status_formula.expression}")
    
    # ZIEL FORMULA (DIFFERENT)
    # Key format: V_X.X.X_ziel (with _ziel suffix)
    ziel_formula, created = Formula.objects.update_or_create(
        key='V_2.4.2_ziel',
        category='verbrauch',
        defaults={
            'expression': '(Verbrauch_2_4_1_target - Verbrauch_2_4_1) / Verbrauch_2_4_1 * 100',
            'description': 'Ziel calculation: Percent change from status to target',
            'is_fixed': False,
            'is_active': True,
        }
    )
    
    if created:
        print("✅ Created ZIEL formula: V_2.4.2_ziel")
    else:
        print("✅ Updated ZIEL formula: V_2.4.2_ziel")
    print(f"   Expression: {ziel_formula.expression}")
    
    print("\n" + "="*60)
    print("SUCCESS! Now item 2.4.2 will use:")
    print("  - STATUS: Verbrauch_2_4_1 / (Verbrauch_2_4_1_percent / 100)")
    print("  - ZIEL:   (Verbrauch_2_4_1_target - Verbrauch_2_4_1) / Verbrauch_2_4_1 * 100")
    print("="*60)
    print("\nNext steps:")
    print("1. Open webapp: http://localhost:8000/verbrauch/")
    print("2. Click 'Save & Recalculate' button")
    print("3. Verify both status and ziel values are correct")


def add_renewable_separate_formulas_example():
    """
    Example for RenewableData: Item 9.2.1 with different target formula
    """
    
    # STATUS FORMULA
    status_formula, created = Formula.objects.update_or_create(
        key='9.2.1',
        category='renewable',
        defaults={
            'expression': 'Renewable_9_2 * Renewable_9_2_1_percent / 100',
            'description': 'Status: 9.2 times 9.2.1%',
            'is_fixed': False,
            'is_active': True,
        }
    )
    
    if created:
        print("✅ Created STATUS formula: 9.2.1")
    else:
        print("✅ Updated STATUS formula: 9.2.1")
    print(f"   Expression: {status_formula.expression}")
    
    # TARGET FORMULA (DIFFERENT)
    # Use _target suffix for renewable (not _ziel)
    target_formula, created = Formula.objects.update_or_create(
        key='9.2.1_target',
        category='renewable',
        defaults={
            'expression': 'Renewable_9_2_target * Renewable_9_2_1_target_percent / 100',
            'description': 'Target: Uses target values instead of status',
            'is_fixed': False,
            'is_active': True,
        }
    )
    
    if created:
        print("✅ Created TARGET formula: 9.2.1_target")
    else:
        print("✅ Updated TARGET formula: 9.2.1_target")
    print(f"   Expression: {target_formula.expression}")
    
    print("\n" + "="*60)
    print("SUCCESS! Now item 9.2.1 will use:")
    print("  - STATUS: Renewable_9_2 * Renewable_9_2_1_percent / 100")
    print("  - TARGET: Renewable_9_2_target * Renewable_9_2_1_target_percent / 100")
    print("="*60)


def show_existing_formulas(item_code='2.4.2', category='verbrauch'):
    """
    Check what formulas already exist for an item
    """
    prefix = 'V_' if category == 'verbrauch' else ''
    base_key = f'{prefix}{item_code}'
    ziel_key = f'{base_key}_ziel' if category == 'verbrauch' else f'{base_key}_target'
    
    print(f"\nChecking formulas for {item_code} (category={category}):")
    print("="*60)
    
    # Check base formula
    try:
        base = Formula.objects.get(key=base_key, category=category)
        print(f"✅ Status formula exists: {base_key}")
        print(f"   Expression: {base.expression}")
        print(f"   Active: {base.is_active}")
    except Formula.DoesNotExist:
        print(f"❌ No status formula: {base_key}")
    
    # Check ziel/target formula
    try:
        ziel = Formula.objects.get(key=ziel_key, category=category)
        print(f"✅ Ziel/Target formula exists: {ziel_key}")
        print(f"   Expression: {ziel.expression}")
        print(f"   Active: {ziel.is_active}")
    except Formula.DoesNotExist:
        print(f"❌ No ziel/target formula: {ziel_key}")
        print(f"   (Will use status formula for both)")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'check':
            # Check existing formulas
            item = sys.argv[2] if len(sys.argv) > 2 else '2.4.2'
            category = sys.argv[3] if len(sys.argv) > 3 else 'verbrauch'
            show_existing_formulas(item, category)
        
        elif command == 'verbrauch':
            # Add verbrauch example
            add_separate_formulas_example()
        
        elif command == 'renewable':
            # Add renewable example
            add_renewable_separate_formulas_example()
        
        else:
            print("Usage:")
            print("  python example_separate_formulas.py check [item] [category]")
            print("  python example_separate_formulas.py verbrauch")
            print("  python example_separate_formulas.py renewable")
    
    else:
        print("\n" + "="*60)
        print("EXAMPLE: Separate Status and Ziel/Target Formulas")
        print("="*60)
        print("\nThis script helps you add formulas where status and ziel")
        print("use DIFFERENT calculations.")
        print("\nOptions:")
        print("  1. Check existing formulas for an item")
        print("  2. Add VerbrauchData example (item 2.4.2)")
        print("  3. Add RenewableData example (item 9.2.1)")
        print("\nRun with:")
        print("  python example_separate_formulas.py check [item] [category]")
        print("  python example_separate_formulas.py verbrauch")
        print("  python example_separate_formulas.py renewable")
        print("\nExamples:")
        print("  python example_separate_formulas.py check 2.4.2 verbrauch")
        print("  python example_separate_formulas.py check 9.2.1 renewable")
        print("  python example_separate_formulas.py verbrauch")
        print("="*60)
